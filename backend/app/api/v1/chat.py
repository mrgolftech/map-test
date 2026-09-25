from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.schemas.chat import (
    AnalysisChatRequest,
    ChatThreadResponse,
    ComparisonChatRequest,
)
from app.services.ai_chat_service import AIChatService

router = APIRouter(prefix="/ai/chat", tags=["ai-chat"])


@router.get("/analyses/{analysis_id}", response_model=ChatThreadResponse)
def get_analysis_chat(
    analysis_id: str,
    session: Annotated[Session, Depends(get_session)],
) -> ChatThreadResponse:
    return ChatThreadResponse(
        data=AIChatService(session).get_analysis_thread(analysis_id)
    )


@router.post("/analyses/{analysis_id}", response_model=ChatThreadResponse)
def ask_analysis_chat(
    analysis_id: str,
    request: AnalysisChatRequest,
    session: Annotated[Session, Depends(get_session)],
) -> ChatThreadResponse:
    return ChatThreadResponse(
        data=AIChatService(session).ask_analysis(analysis_id, request.question)
    )


@router.get("/comparison", response_model=ChatThreadResponse)
def get_comparison_chat(
    session: Annotated[Session, Depends(get_session)],
    analysis_ids: Annotated[list[str], Query(min_length=2, max_length=25)],
) -> ChatThreadResponse:
    return ChatThreadResponse(
        data=AIChatService(session).get_comparison_thread(analysis_ids)
    )


@router.post("/comparison", response_model=ChatThreadResponse)
def ask_comparison_chat(
    request: ComparisonChatRequest,
    session: Annotated[Session, Depends(get_session)],
) -> ChatThreadResponse:
    return ChatThreadResponse(
        data=AIChatService(session).ask_comparison(
            request.analysis_ids,
            request.question,
        )
    )
