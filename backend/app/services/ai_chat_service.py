"""Grounded, persisted follow-up chat for a saved report or wafer comparison."""

import hashlib
import json
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.openai_compatible import OpenAICompatibleProvider
from app.ai.provider import AIProvider
from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.db.models import (
    AIConversationMessage,
    AIConversationThread,
)
from app.repositories.analysis_repository import AnalysisRepository
from app.schemas.analysis import AnalysisSummary
from app.schemas.chat import (
    ChatAnswerPayload,
    ChatCitation,
    ChatMessage,
    ChatThreadData,
)
from app.schemas.history import AnalysisDetail
from app.services.analysis_history_service import AnalysisHistoryService
from app.services.llm_settings_service import LLMSettingsService
from app.services.lot_comparison_service import LotComparisonService

CHAT_SYSTEM_PROMPT = """You are a wafer test data engineering assistant. Answer in Chinese.
Use only the supplied saved AI report, deterministic analysis facts, comparison
facts, and conversation. Do not invent counts, rates, metadata, causes, or
physical locations. Every concrete data claim must cite one or more supplied
evidence IDs in citation_ids. Do not fabricate IDs. If evidence is insufficient,
say exactly what cannot be concluded and set insufficient_evidence=true. Keep
possible causes explicitly hypothetical and suggest measurable next checks.
Do not treat normalized map regions as physical wafer coordinates or a pattern
classification as confirmed root cause. Output one JSON object only, with keys:
answer, citation_ids, insufficient_evidence, limitations. Keep answer concise
and use plain text (no Markdown or raw HTML)."""


def _json_from_response(value: str) -> str:
    text = value.strip()
    fence = chr(96) * 3
    if text.startswith(fence):
        lines = text.splitlines()
        lines = lines[1:]
        if lines and lines[-1].strip().startswith(fence):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def _percent(value: float | None) -> str:
    return "不可用" if value is None else f"{value * 100:.2f}%"


def _number(value: float | int | None, digits: int = 3) -> str:
    if value is None:
        return "不可用"
    if isinstance(value, int):
        return str(value)
    return f"{value:.{digits}f}"


class AIChatService:
    def __init__(
        self,
        session: Session,
        *,
        settings: Settings | None = None,
        provider: AIProvider | None = None,
    ) -> None:
        self._session = session
        self._settings = LLMSettingsService(
            session, settings or get_settings()
        ).effective_settings()
        self._provider = provider

    def _get_provider(self) -> AIProvider:
        if self._provider is not None:
            return self._provider
        if not (
            self._settings.llm_base_url
            and self._settings.llm_api_key
            and self._settings.llm_model
        ):
            raise AppError(
                code="LLM_NOT_CONFIGURED",
                message="LLM provider is not configured.",
                status_code=503,
            )
        return OpenAICompatibleProvider(
            base_url=self._settings.llm_base_url,
            api_key=self._settings.llm_api_key,
            model=self._settings.llm_model,
            timeout_seconds=self._settings.llm_timeout_seconds,
            max_retries=self._settings.llm_max_retries,
        )

    @staticmethod
    def _context_key(scope: str, context_ids: list[str]) -> str:
        encoded = json.dumps(
            {"scope": scope, "ids": context_ids},
            ensure_ascii=False,
            separators=(",", ":"),
        )
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    def _thread(
        self, scope: str, context_ids: list[str]
    ) -> AIConversationThread | None:
        key = self._context_key(scope, context_ids)
        return self._session.scalar(
            select(AIConversationThread).where(
                AIConversationThread.scope == scope,
                AIConversationThread.context_key == key,
            )
        )

    def get_thread(self, scope: str, context_ids: list[str]) -> ChatThreadData:
        thread = self._thread(scope, context_ids)
        messages = []
        if thread is not None:
            rows = self._session.scalars(
                select(AIConversationMessage)
                .where(AIConversationMessage.thread_id == thread.id)
                .order_by(
                    AIConversationMessage.created_at,
                    AIConversationMessage.id,
                )
            )
            messages = [
                ChatMessage(
                    id=row.id,
                    role=row.role,
                    content=row.content,
                    citations=json.loads(row.citations_json),
                    limitations=json.loads(row.limitations_json),
                    insufficient_evidence=row.insufficient_evidence,
                    model=row.model,
                    created_at=row.created_at,
                )
                for row in rows
            ]
        return ChatThreadData(
            thread_id=thread.id if thread else None,
            scope=scope,
            context_ids=context_ids,
            messages=messages,
        )

    @staticmethod
    def _fact(
        catalog: dict[str, ChatCitation],
        evidence_id: str,
        label: str,
        value: str,
        analysis_id: str | None = None,
    ) -> dict[str, str | None]:
        citation = ChatCitation(
            id=evidence_id,
            label=label,
            value=value[:500],
            analysis_id=analysis_id,
        )
        catalog[evidence_id] = citation
        return citation.model_dump(mode="json")

    def _analysis_context(
        self, analysis_id: str
    ) -> tuple[dict[str, object], dict[str, ChatCitation], AnalysisDetail]:
        detail = AnalysisHistoryService(self._session).get(analysis_id)
        if detail.ai_report is None:
            raise AppError(
                code="AI_REPORT_REQUIRED",
                message=(
                    "Generate and save the AI report before asking follow-up questions."
                ),
                status_code=409,
            )

        catalog: dict[str, ChatCitation] = {}
        facts: list[dict[str, str | None]] = []
        summary = detail.analysis.summary
        facts.append(self._fact(catalog, "summary.yield", "Yield", _percent(summary.yield_)))
        facts.append(self._fact(catalog, "summary.tested", "Tested Die", str(summary.tested_die)))
        facts.append(self._fact(catalog, "summary.pass", "Pass Die", str(summary.pass_die)))
        facts.append(self._fact(catalog, "summary.fail", "Fail Die", str(summary.fail_die)))

        for stat in detail.analysis.bin_stats:
            if stat.fail_share is None or stat.count <= 0:
                continue
            prefix = f"bin.{stat.soft_bin}"
            facts.extend(
                [
                    self._fact(
                        catalog,
                        f"{prefix}.count",
                        f"Bin {stat.soft_bin} Die 数",
                        str(stat.count),
                    ),
                    self._fact(
                        catalog,
                        f"{prefix}.fail_share",
                        f"Bin {stat.soft_bin} 占 Fail 比例",
                        _percent(stat.fail_share),
                    ),
                ]
            )
        for stat in detail.analysis.spatial_by_bin:
            if stat.soft_bin not in {
                item.soft_bin
                for item in detail.analysis.bin_stats
                if item.fail_share is not None and item.count > 0
            }:
                continue
            prefix = f"bin.{stat.soft_bin}.spatial"
            for name, region in (
                ("center", stat.center),
                ("mid", stat.mid),
                ("edge", stat.edge),
                ("top", stat.top),
                ("bottom", stat.bottom),
                ("left", stat.left),
                ("right", stat.right),
                ("q1", stat.q1),
                ("q2", stat.q2),
                ("q3", stat.q3),
                ("q4", stat.q4),
            ):
                if region.enrichment is not None:
                    facts.append(
                        self._fact(
                            catalog,
                            f"{prefix}.{name}_enrichment",
                            f"Bin {stat.soft_bin} {name.upper()} 富集度",
                            _number(region.enrichment),
                        )
                    )
            facts.extend(
                [
                    self._fact(
                        catalog,
                        f"{prefix}.cluster_ratio",
                        f"Bin {stat.soft_bin} 聚集比例",
                        _percent(stat.cluster.cluster_ratio),
                    ),
                    self._fact(
                        catalog,
                        f"{prefix}.largest_component",
                        f"Bin {stat.soft_bin} 最大连通区域",
                        str(stat.cluster.largest_component),
                    ),
                ]
            )
        for index, pattern in enumerate(detail.analysis.patterns):
            facts.append(
                self._fact(
                    catalog,
                    f"pattern.{index}",
                    f"Bin {pattern.soft_bin} {pattern.pattern} 模式",
                    f"score={pattern.score:.3f}; evidence={'; '.join(pattern.evidence)}",
                )
            )

        report = detail.ai_report.model_dump(mode="json")
        report_facts: list[dict[str, str | None]] = []
        report_facts.append(
            self._fact(
                catalog,
                "report.summary",
                "已保存 AI 报告摘要",
                detail.ai_report.executive_summary,
            )
        )
        for index, finding in enumerate(detail.ai_report.key_findings):
            report_facts.append(
                self._fact(
                    catalog,
                    f"report.finding.{index}",
                    f"AI 报告发现：{finding.title}",
                    finding.detail,
                )
            )
        context = {
            "analysis_id": analysis_id,
            "metadata": detail.dataset.metadata.model_dump(mode="json"),
            "deterministic_facts": facts,
            "saved_ai_report": report,
            "report_references": report_facts,
            "analysis_limitations": detail.analysis.limitations,
        }
        return context, catalog, detail

    def _comparison_context(
        self, analysis_ids: list[str]
    ) -> tuple[dict[str, object], dict[str, ChatCitation]]:
        if len(set(analysis_ids)) != len(analysis_ids):
            raise AppError(
                code="COMPARE_DUPLICATE_ANALYSIS_ID",
                message="Comparison analysis IDs must be unique.",
                status_code=422,
            )
        comparison = LotComparisonService(self._session).compare_ids(analysis_ids)
        records = AnalysisRepository(self._session).get_many(analysis_ids)
        summaries = {
            record.id: AnalysisSummary.model_validate_json(
                record.analysis_summary_json
            )
            for record in records
        }
        catalog: dict[str, ChatCitation] = {}
        facts: list[dict[str, str | None]] = []
        facts.extend(
            [
                self._fact(
                    catalog,
                    "comparison.yield.average",
                    "Wafer 平均 Yield",
                    _percent(comparison.yield_stats.average),
                ),
                self._fact(
                    catalog,
                    "comparison.yield.median",
                    "Wafer Yield 中位数",
                    _percent(comparison.yield_stats.median),
                ),
                self._fact(
                    catalog,
                    "comparison.yield.std_dev",
                    "Wafer Yield 标准差",
                    _percent(comparison.yield_stats.std_dev),
                ),
                self._fact(
                    catalog,
                    "comparison.compatibility",
                    "数据可比性",
                    "可比较" if comparison.compatibility.compatible else "存在兼容性问题",
                ),
            ]
        )
        for wafer in comparison.wafers:
            wid = wafer.analysis_id
            label = f"Wafer {wafer.wafer_id or wid[:8]}"
            for suffix, title, value in (
                ("yield", "Yield", _percent(wafer.yield_)),
                ("main_fail_bin", "主 Fail Bin", str(wafer.main_fail_bin or "无")),
                ("main_fail_rate", "主 Fail Bin 占比", _percent(wafer.main_fail_rate)),
                ("edge_enrichment", "Edge 富集度", _number(wafer.edge_enrichment)),
                ("center_enrichment", "Center 富集度", _number(wafer.center_enrichment)),
                ("cluster_ratio", "聚集比例", _percent(wafer.cluster_ratio)),
                ("main_pattern", "主空间模式", wafer.main_pattern or "未识别"),
            ):
                facts.append(
                    self._fact(
                        catalog,
                        f"wafer.{wid}.{suffix}",
                        f"{label} {title}",
                        value,
                        analysis_id=wid,
                    )
                )
            summary = summaries[wid]
            for pattern_index, pattern in enumerate(summary.patterns):
                facts.append(
                    self._fact(
                        catalog,
                        f"wafer.{wid}.pattern.{pattern_index}",
                        f"{label} Bin {pattern.soft_bin} {pattern.pattern}",
                        f"score={pattern.score:.3f}; evidence={'; '.join(pattern.evidence)}",
                        analysis_id=wid,
                    )
                )
        for bin_stat in comparison.bin_aggregates:
            facts.append(
                self._fact(
                    catalog,
                    f"bin.{bin_stat.soft_bin}.mean_fail_share",
                    f"Bin {bin_stat.soft_bin} 平均 Fail 占比",
                    _percent(bin_stat.mean_fail_share),
                )
            )
            for point in bin_stat.trend:
                facts.append(
                    self._fact(
                        catalog,
                        f"bin.{bin_stat.soft_bin}.wafer.{point.analysis_id}.wafer_rate",
                        (
                            f"Bin {bin_stat.soft_bin} Wafer 占比"
                            f"（{point.wafer_id or point.analysis_id[:8]}）"
                        ),
                        _percent(point.wafer_rate),
                        analysis_id=point.analysis_id,
                    )
                )
                if point.fail_share is not None:
                    facts.append(
                        self._fact(
                            catalog,
                            f"bin.{bin_stat.soft_bin}.wafer.{point.analysis_id}.fail_share",
                            (
                                f"Bin {bin_stat.soft_bin} Fail 占比"
                                f"（{point.wafer_id or point.analysis_id[:8]}）"
                            ),
                            _percent(point.fail_share),
                            analysis_id=point.analysis_id,
                        )
                    )
        return {
            "analysis_ids": analysis_ids,
            "compatibility": comparison.compatibility.model_dump(mode="json"),
            "yield_stats": comparison.yield_stats.model_dump(mode="json"),
            "yield_trend": [
                item.model_dump(mode="json", by_alias=True)
                for item in comparison.yield_trend
            ],
            "bin_aggregates": [
                item.model_dump(mode="json") for item in comparison.bin_aggregates
            ],
            "pattern_distribution": [
                item.model_dump(mode="json")
                for item in comparison.pattern_distribution
            ],
            "wafer_facts": facts,
            "limitations": comparison.limitations,
        }, catalog

    def _messages(self, thread: AIConversationThread | None) -> list[AIConversationMessage]:
        if thread is None:
            return []
        return list(
            self._session.scalars(
                select(AIConversationMessage)
                .where(AIConversationMessage.thread_id == thread.id)
                .order_by(
                    AIConversationMessage.created_at.desc(),
                    AIConversationMessage.id.desc(),
                )
                .limit(12)
            )
        )[::-1]

    def ask(
        self,
        *,
        scope: str,
        context_ids: list[str],
        question: str,
        context: dict[str, object],
        catalog: dict[str, ChatCitation],
    ) -> ChatThreadData:
        clean_question = question.strip()
        if not clean_question:
            raise AppError(
                code="CHAT_QUESTION_EMPTY",
                message="Question cannot be blank.",
                status_code=422,
            )
        thread = self._thread(scope, context_ids)
        transcript = [
            {"role": row.role, "content": row.content}
            for row in self._messages(thread)
        ]
        user_prompt = json.dumps(
            {
                "context": context,
                "available_evidence": [
                    citation.model_dump(mode="json")
                    for citation in catalog.values()
                ],
                "conversation": transcript,
                "question": clean_question,
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )
        raw = self._get_provider().complete(
            system_prompt=CHAT_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_tokens=min(self._settings.llm_max_output_tokens, 2000),
            temperature=0.2,
        )
        try:
            answer = ChatAnswerPayload.model_validate(
                json.loads(_json_from_response(raw))
            )
        except (json.JSONDecodeError, ValidationError, TypeError) as exc:
            raise AppError(
                code="LLM_SCHEMA_INVALID",
                message="LLM returned output that does not match the chat answer schema.",
                status_code=502,
                details={"error_type": type(exc).__name__},
            ) from exc

        valid_ids = list(dict.fromkeys(
            item for item in answer.citation_ids if item in catalog
        ))
        citations = [catalog[item] for item in valid_ids]
        limitations = list(answer.limitations)
        insufficient = answer.insufficient_evidence
        if len(valid_ids) != len(answer.citation_ids):
            insufficient = True
            limitations.append("模型返回了不存在的引用，已从回答中剔除。")
        if not citations and not insufficient:
            insufficient = True
            limitations.append("回答没有引用可验证的分析指标，请结合原始数据复核。")
        content = answer.answer
        if insufficient and "证据不足" not in content:
            content = f"{content}\n\n证据不足：当前数据无法支持未被引用指标覆盖的结论。"

        now = datetime.now(UTC)
        assistant_time = now + timedelta(microseconds=1)
        if thread is None:
            thread = AIConversationThread(
                id=str(uuid4()),
                scope=scope,
                context_key=self._context_key(scope, context_ids),
                context_ids_json=json.dumps(context_ids, separators=(",", ":")),
                created_at=now,
                updated_at=now,
            )
            self._session.add(thread)
            self._session.flush()

        model = self._settings.llm_model or "unknown"
        self._session.add_all(
            [
                AIConversationMessage(
                    id=str(uuid4()),
                    thread_id=thread.id,
                    role="user",
                    content=clean_question,
                    citations_json="[]",
                    limitations_json="[]",
                    insufficient_evidence=False,
                    created_at=now,
                ),
                AIConversationMessage(
                    id=str(uuid4()),
                    thread_id=thread.id,
                    role="assistant",
                    content=content,
                    citations_json=json.dumps(
                        [item.model_dump(mode="json") for item in citations],
                        ensure_ascii=False,
                        separators=(",", ":"),
                    ),
                    limitations_json=json.dumps(
                        limitations,
                        ensure_ascii=False,
                        separators=(",", ":"),
                    ),
                    insufficient_evidence=insufficient,
                    model=model,
                    created_at=assistant_time,
                ),
            ]
        )
        thread.updated_at = assistant_time
        self._session.commit()
        return self.get_thread(scope, context_ids)

    def ask_analysis(self, analysis_id: str, question: str) -> ChatThreadData:
        context, catalog, _ = self._analysis_context(analysis_id)
        return self.ask(
            scope="analysis",
            context_ids=[analysis_id],
            question=question,
            context=context,
            catalog=catalog,
        )

    def get_analysis_thread(self, analysis_id: str) -> ChatThreadData:
        AnalysisHistoryService(self._session).get(analysis_id)
        return self.get_thread("analysis", [analysis_id])

    def ask_comparison(
        self, analysis_ids: list[str], question: str
    ) -> ChatThreadData:
        context_ids = sorted(analysis_ids)
        context, catalog = self._comparison_context(context_ids)
        return self.ask(
            scope="comparison",
            context_ids=context_ids,
            question=question,
            context=context,
            catalog=catalog,
        )

    def get_comparison_thread(self, analysis_ids: list[str]) -> ChatThreadData:
        if len(set(analysis_ids)) != len(analysis_ids):
            raise AppError(
                code="COMPARE_DUPLICATE_ANALYSIS_ID",
                message="Comparison analysis IDs must be unique.",
                status_code=422,
            )
        context_ids = sorted(analysis_ids)
        LotComparisonService(self._session).compare_ids(context_ids)
        return self.get_thread("comparison", context_ids)
