import json

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.ai.openai_compatible import OpenAICompatibleProvider
from app.ai.prompt import SYSTEM_PROMPT, build_user_prompt
from app.ai.provider import AIProvider
from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.schemas.ai import (
    AIAnalyzeResult,
    AIReport,
    LLMConfigStatus,
    LLMConnectionResult,
)
from app.services.analysis_history_service import AnalysisHistoryService


def create_provider(settings: Settings) -> AIProvider:
    if not (
        settings.llm_base_url
        and settings.llm_api_key
        and settings.llm_model
    ):
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
            configured=bool(
                settings.llm_base_url
                and settings.llm_api_key
                and settings.llm_model
            ),
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
        detail = AnalysisHistoryService(self._session).get(analysis_id)
        provider = self._get_provider()
        raw = provider.complete(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=build_user_prompt(detail.analysis),
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

        return AIAnalyzeResult(
            analysis_id=analysis_id,
            model=self._settings.llm_model or "unknown",
            report=report,
        )
