from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import AnalysisRecord
from app.db.session import get_session
from app.repositories.analysis_repository import AnalysisRepository
from app.schemas.dashboard import DashboardSummary, DashboardSummaryResponse

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummaryResponse)
def dashboard_summary(
    session: Annotated[Session, Depends(get_session)],
) -> DashboardSummaryResponse:
    row = session.execute(
        select(
            func.count(AnalysisRecord.id).label("analysis_count"),
            func.avg(AnalysisRecord.yield_value).label("average_yield"),
            func.min(AnalysisRecord.yield_value).label("minimum_yield"),
            func.max(AnalysisRecord.yield_value).label("maximum_yield"),
            func.max(AnalysisRecord.created_at).label("latest_created_at"),
        )
    ).mappings().one()

    lots = AnalysisRepository(session).list_lots()
    return DashboardSummaryResponse(
        data=DashboardSummary(
            analysis_count=int(row["analysis_count"] or 0),
            lot_count=len(lots),
            average_yield=row["average_yield"],
            minimum_yield=row["minimum_yield"],
            maximum_yield=row["maximum_yield"],
            latest_created_at=row["latest_created_at"],
        )
    )
