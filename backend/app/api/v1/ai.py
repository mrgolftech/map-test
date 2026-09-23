from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.schemas.ai import (
    AIAnalyzeRequest,
    AIAnalyzeResponse,
    LLMConfigResponse,
    LLMConnectionResponse,
)
from app.services.ai_analysis_service import AIAnalysisService

router = APIRouter(tags=["ai"])


@router.get("/settings/llm", response_model=LLMConfigResponse)
@router.get("/ai/config", response_model=LLMConfigResponse)
def llm_config(
    session: Annotated[Session, Depends(get_session)],
) -> LLMConfigResponse:
    return LLMConfigResponse(
        data=AIAnalysisService(session).config_status()
    )


@router.post("/settings/llm/test", response_model=LLMConnectionResponse)
@router.post("/ai/test", response_model=LLMConnectionResponse)
def test_llm(
    session: Annotated[Session, Depends(get_session)],
) -> LLMConnectionResponse:
    return LLMConnectionResponse(
        data=AIAnalysisService(session).test_connection()
    )


@router.post("/ai/analyze", response_model=AIAnalyzeResponse)
def analyze_ai(
    request: AIAnalyzeRequest,
    session: Annotated[Session, Depends(get_session)],
) -> AIAnalyzeResponse:
    return AIAnalyzeResponse(
        data=AIAnalysisService(session).analyze(request.analysis_id)
    )


@router.post(
    "/analyses/{analysis_id}/ai",
    response_model=AIAnalyzeResponse,
)
def analyze_persisted(
    analysis_id: str,
    session: Annotated[Session, Depends(get_session)],
) -> AIAnalyzeResponse:
    return AIAnalyzeResponse(
        data=AIAnalysisService(session).analyze(analysis_id)
    )
