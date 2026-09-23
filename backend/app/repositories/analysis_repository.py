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

    def save(self, record: AnalysisRecord) -> AnalysisRecord:
        self._session.add(record)
        self._session.commit()
        self._session.refresh(record)
        return record

    def get(self, analysis_id: str) -> AnalysisRecord | None:
        return self._session.get(AnalysisRecord, analysis_id)

    def get_many(self, analysis_ids: list[str]) -> list[AnalysisRecord]:
        if not analysis_ids:
            return []
        records = list(
            self._session.scalars(
                select(AnalysisRecord).where(AnalysisRecord.id.in_(analysis_ids))
            )
        )
        by_id = {record.id: record for record in records}
        return [
            by_id[analysis_id]
            for analysis_id in analysis_ids
            if analysis_id in by_id
        ]

    def list_by_lot(
        self,
        *,
        lot_id: str,
        product_id: str | None = None,
    ) -> list[AnalysisRecord]:
        statement: Select[tuple[AnalysisRecord]] = (
            select(AnalysisRecord)
            .where(AnalysisRecord.lot_id == lot_id)
            .order_by(AnalysisRecord.created_at.asc())
        )
        if product_id is not None:
            statement = statement.where(AnalysisRecord.product_id == product_id)
        return list(self._session.scalars(statement))

    def list_lots(self) -> list[dict[str, object]]:
        statement = (
            select(
                AnalysisRecord.product_id.label("product_id"),
                AnalysisRecord.lot_id.label("lot_id"),
                func.count(AnalysisRecord.id).label("wafer_count"),
                func.avg(AnalysisRecord.yield_value).label("average_yield"),
                func.min(AnalysisRecord.yield_value).label("minimum_yield"),
                func.max(AnalysisRecord.yield_value).label("maximum_yield"),
                func.max(AnalysisRecord.created_at).label("last_created_at"),
            )
            .where(AnalysisRecord.lot_id.is_not(None))
            .group_by(AnalysisRecord.product_id, AnalysisRecord.lot_id)
            .order_by(func.max(AnalysisRecord.created_at).desc())
        )
        return [dict(row) for row in self._session.execute(statement).mappings()]

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
