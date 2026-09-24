import json

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.ai.openai_compatible import OpenAICompatibleProvider
from app.ai.prompt import SYSTEM_PROMPT, build_user_prompt
from app.ai.provider import AIProvider
from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.repositories.analysis_repository import AnalysisRepository
from app.schemas.ai import (
    AIAnalyzeResult,
    AIReport,
    LLMConfigStatus,
    LLMConnectionResult,
)
from app.services.analysis_history_service import AnalysisHistoryService
from app.services.lot_comparison_service import LotComparisonService


def create_provider(settings: Settings) -> AIProvider:
    if not (settings.llm_base_url and settings.llm_api_key and settings.llm_model):
        raise AppError(
            code="LLM_NOT_CONFIGURED",
            message="LLM provider is not configured.",
            status_code=503,
        )
    return OpenAICompatibleProvider(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
        model=settings.llm_model,
        timeout_seconds=settings.llm_timeout_seconds,
        max_retries=settings.llm_max_retries,
    )


def _strip_json_fence(value: str) -> str:
    text = value.strip()
    fence = chr(96) * 3
    if text.startswith(fence):
        lines = text.splitlines()
        if lines:
            lines = lines[1:]
        if lines and lines[-1].strip().startswith(fence):
            lines = lines[:-1]
        return "\n".join(lines).strip()
    return text


class AIAnalysisService:
    def __init__(
        self,
        session: Session,
        *,
        settings: Settings | None = None,
        provider: AIProvider | None = None,
    ) -> None:
        self._session = session
        self._settings = settings or get_settings()
        self._provider = provider

    def config_status(self) -> LLMConfigStatus:
        settings = self._settings
        return LLMConfigStatus(
            configured=bool(settings.llm_base_url and settings.llm_api_key and settings.llm_model),
            base_url=settings.llm_base_url or None,
            model=settings.llm_model or None,
            api_key_configured=bool(settings.llm_api_key),
        )

    def _get_provider(self) -> AIProvider:
        return self._provider or create_provider(self._settings)

    def test_connection(self) -> LLMConnectionResult:
        provider = self._get_provider()
        provider.test_connection()
        return LLMConnectionResult(
            ok=True,
            model=self._settings.llm_model or "unknown",
            message="LLM connection succeeded.",
        )

    def analyze(self, analysis_id: str) -> AIAnalyzeResult:
        history = AnalysisHistoryService(self._session)
        detail = history.get(analysis_id)
        lot_context = None
        if (
            detail.lot_id
            and len(
                AnalysisRepository(self._session).list_by_lot(
                    lot_id=detail.lot_id,
                    product_id=detail.product_id,
                )
            )
            > 1
        ):
            lot = LotComparisonService(self._session).summarize_lot(
                lot_id=detail.lot_id,
                product_id=detail.product_id,
            )
            if lot.compatibility.compatible and lot.yield_stats.wafer_count > 1:
                lot_context = lot
        provider = self._get_provider()
        raw = provider.complete(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=build_user_prompt(detail.analysis, lot_context),
            max_tokens=self._settings.llm_max_output_tokens,
            temperature=0.2,
        )
        try:
            decoded = json.loads(_strip_json_fence(raw))
            report = AIReport.model_validate(decoded)
        except (json.JSONDecodeError, ValidationError, TypeError) as exc:
            raise AppError(
                code="LLM_SCHEMA_INVALID",
                message="LLM returned output that does not match the AI report schema.",
                status_code=502,
                details={"error_type": type(exc).__name__},
            ) from exc

        model = self._settings.llm_model or "unknown"
        history.save_ai_report(
            analysis_id,
            model=model,
            report=report,
        )
        return AIAnalyzeResult(
            analysis_id=analysis_id,
            model=model,
            report=report,
        )
