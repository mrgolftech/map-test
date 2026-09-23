from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.schemas.comparison import (
    CompareRequest,
    ComparisonResponse,
    LotListResponse,
)
from app.services.lot_comparison_service import LotComparisonService

router = APIRouter(tags=["comparison"])


@router.post("/analyses/compare", response_model=ComparisonResponse)
def compare_analyses(
    request: CompareRequest,
    session: Annotated[Session, Depends(get_session)],
) -> ComparisonResponse:
    data = LotComparisonService(session).compare_ids(request.analysis_ids)
    return ComparisonResponse(data=data)


@router.get("/lots", response_model=LotListResponse)
def list_lots(
    session: Annotated[Session, Depends(get_session)],
) -> LotListResponse:
    return LotListResponse(
        data=LotComparisonService(session).list_lots()
    )


@router.get("/lots/{lot_id}/summary", response_model=ComparisonResponse)
def lot_summary(
    lot_id: str,
    session: Annotated[Session, Depends(get_session)],
    product_id: Annotated[str | None, Query()] = None,
) -> ComparisonResponse:
    data = LotComparisonService(session).summarize_lot(
        lot_id=lot_id,
        product_id=product_id,
    )
    return ComparisonResponse(data=data)
