from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.schemas.history import (
    AnalysisCreateRequest,
    AnalysisDeleteData,
    AnalysisDeleteResponse,
    AnalysisDetailResponse,
    AnalysisListResponse,
    PaginationMeta,
)
from app.services.analysis_history_service import AnalysisHistoryService

router = APIRouter(prefix="/analyses", tags=["analyses"])


@router.post("", response_model=AnalysisDetailResponse)
def create_analysis(
    request: AnalysisCreateRequest,
    session: Annotated[Session, Depends(get_session)],
) -> AnalysisDetailResponse:
    detail = AnalysisHistoryService(session).create(request)
    return AnalysisDetailResponse(data=detail)


@router.get("", response_model=AnalysisListResponse)
def list_analyses(
    session: Annotated[Session, Depends(get_session)],
    product_id: str | None = None,
    lot_id: str | None = None,
    wafer_id: str | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    yield_min: Annotated[float | None, Query(ge=0.0, le=1.0)] = None,
    yield_max: Annotated[float | None, Query(ge=0.0, le=1.0)] = None,
    main_fail_bin: Annotated[int | None, Query(ge=1)] = None,
    pattern: str | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> AnalysisListResponse:
    items, total = AnalysisHistoryService(session).list(
        product_id=product_id,
        lot_id=lot_id,
        wafer_id=wafer_id,
        created_from=created_from,
        created_to=created_to,
        yield_min=yield_min,
        yield_max=yield_max,
        main_fail_bin=main_fail_bin,
        pattern=pattern,
        page=page,
        page_size=page_size,
    )
    return AnalysisListResponse(
        data=items,
        meta=PaginationMeta(page=page, page_size=page_size, total=total),
    )


@router.get("/{analysis_id}", response_model=AnalysisDetailResponse)
def get_analysis(
    analysis_id: str,
    session: Annotated[Session, Depends(get_session)],
) -> AnalysisDetailResponse:
    return AnalysisDetailResponse(
        data=AnalysisHistoryService(session).get(analysis_id)
    )


@router.delete("/{analysis_id}", response_model=AnalysisDeleteResponse)
def delete_analysis(
    analysis_id: str,
    session: Annotated[Session, Depends(get_session)],
) -> AnalysisDeleteResponse:
    AnalysisHistoryService(session).delete(analysis_id)
    return AnalysisDeleteResponse(
        data=AnalysisDeleteData(id=analysis_id, deleted=True)
    )
