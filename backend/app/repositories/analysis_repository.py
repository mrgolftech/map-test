from datetime import datetime

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.db.models import AnalysisRecord


class AnalysisRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, record: AnalysisRecord) -> AnalysisRecord:
        self._session.add(record)
        self._session.commit()
        self._session.refresh(record)
        return record

    def get(self, analysis_id: str) -> AnalysisRecord | None:
        return self._session.get(AnalysisRecord, analysis_id)

    def delete(self, record: AnalysisRecord) -> None:
        self._session.delete(record)
        self._session.commit()

    def list(
        self,
        *,
        product_id: str | None,
        lot_id: str | None,
        wafer_id: str | None,
        created_from: datetime | None,
        created_to: datetime | None,
        yield_min: float | None,
        yield_max: float | None,
        main_fail_bin: int | None,
        pattern: str | None,
        page: int,
        page_size: int,
    ) -> tuple[list[AnalysisRecord], int]:
        statement: Select[tuple[AnalysisRecord]] = select(AnalysisRecord)

        if product_id:
            statement = statement.where(AnalysisRecord.product_id == product_id)
        if lot_id:
            statement = statement.where(AnalysisRecord.lot_id == lot_id)
        if wafer_id:
            statement = statement.where(AnalysisRecord.wafer_id == wafer_id)
        if created_from:
            statement = statement.where(AnalysisRecord.created_at >= created_from)
        if created_to:
            statement = statement.where(AnalysisRecord.created_at <= created_to)
        if yield_min is not None:
            statement = statement.where(AnalysisRecord.yield_value >= yield_min)
        if yield_max is not None:
            statement = statement.where(AnalysisRecord.yield_value <= yield_max)
        if main_fail_bin is not None:
            statement = statement.where(AnalysisRecord.main_fail_bin == main_fail_bin)
        if pattern:
            statement = statement.where(AnalysisRecord.main_pattern == pattern)

        count_statement = select(func.count()).select_from(statement.subquery())
        total = int(self._session.scalar(count_statement) or 0)

        records = list(
            self._session.scalars(
                statement.order_by(AnalysisRecord.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        return records, total
