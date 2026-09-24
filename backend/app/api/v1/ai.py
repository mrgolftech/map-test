from typing import Annotated

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.schemas.ai import (
    AIAnalyzeRequest,
    AIAnalyzeResponse,
    LLMCandidateRequest,
    LLMConfigResponse,
    LLMConfigSaveRequest,
    LLMConnectionResponse,
    LLMModelsResponse,
    LLMTestRequest,
)
from app.services.ai_analysis_service import AIAnalysisService
from app.services.llm_settings_service import LLMSettingsService

router = APIRouter(tags=["ai"])


@router.get("/settings/llm", response_model=LLMConfigResponse)
@router.get("/ai/config", response_model=LLMConfigResponse)
def llm_config(
    session: Annotated[Session, Depends(get_session)],
) -> LLMConfigResponse:
    return LLMConfigResponse(data=LLMSettingsService(session).status())


def require_settings_admin(
    session: Annotated[Session, Depends(get_session)],
    token: Annotated[str | None, Header(alias="X-LLM-Settings-Token")] = None,
) -> None:
    LLMSettingsService(session).authorize(token)


@router.put("/settings/llm", response_model=LLMConfigResponse)
def save_llm_config(
    request: LLMConfigSaveRequest,
    session: Annotated[Session, Depends(get_session)],
    _admin: Annotated[None, Depends(require_settings_admin)],
) -> LLMConfigResponse:
    return LLMConfigResponse(data=LLMSettingsService(session).save(request))


@router.post("/settings/llm/models", response_model=LLMModelsResponse)
def fetch_llm_models(
    request: LLMCandidateRequest,
    session: Annotated[Session, Depends(get_session)],
    _admin: Annotated[None, Depends(require_settings_admin)],
) -> LLMModelsResponse:
    return LLMModelsResponse(
        data=LLMSettingsService(session).list_models(request.base_url, request.api_key)
    )


@router.post("/settings/llm/test", response_model=LLMConnectionResponse)
@router.post("/ai/test", response_model=LLMConnectionResponse)
def test_llm(
    session: Annotated[Session, Depends(get_session)],
    _admin: Annotated[None, Depends(require_settings_admin)],
    request: LLMTestRequest | None = None,
) -> LLMConnectionResponse:
    candidate = request or LLMTestRequest()
    return LLMConnectionResponse(
        data=LLMSettingsService(session).test_connection(
            candidate.base_url, candidate.model, candidate.api_key
        )
    )


@router.post("/ai/analyze", response_model=AIAnalyzeResponse)
def analyze_ai(
    request: AIAnalyzeRequest,
    session: Annotated[Session, Depends(get_session)],
) -> AIAnalyzeResponse:
    return AIAnalyzeResponse(data=AIAnalysisService(session).analyze(request.analysis_id))


@router.post(
    "/analyses/{analysis_id}/ai",
    response_model=AIAnalyzeResponse,
)
def analyze_persisted(
    analysis_id: str,
    session: Annotated[Session, Depends(get_session)],
) -> AIAnalyzeResponse:
    return AIAnalyzeResponse(data=AIAnalysisService(session).analyze(analysis_id))
