from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class AnalysisRecord(Base):
    __tablename__ = "analysis"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    product_id: Mapped[str | None] = mapped_column(String(160), nullable=True)
    lot_id: Mapped[str | None] = mapped_column(String(160), nullable=True)
    wafer_id: Mapped[str | None] = mapped_column(String(160), nullable=True)
    flow_id: Mapped[str | None] = mapped_column(String(160), nullable=True)

    yield_value: Mapped[float | None] = mapped_column("yield", Float, nullable=True)
    tested_die: Mapped[int] = mapped_column(Integer, nullable=False)
    pass_die: Mapped[int] = mapped_column(Integer, nullable=False)
    fail_die: Mapped[int] = mapped_column(Integer, nullable=False)

    main_fail_bin: Mapped[int | None] = mapped_column(Integer, nullable=True)
    main_pattern: Mapped[str | None] = mapped_column(String(80), nullable=True)
    validation_status: Mapped[str] = mapped_column(String(16), nullable=False)

    dataset_json: Mapped[str] = mapped_column(Text, nullable=False)
    analysis_summary_json: Mapped[str] = mapped_column(Text, nullable=False)
    sources_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    validation_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")

    __table_args__ = (
        Index("ix_analysis_created_at", "created_at"),
        Index("ix_analysis_product_id", "product_id"),
        Index("ix_analysis_lot_id", "lot_id"),
        Index("ix_analysis_wafer_id", "wafer_id"),
        Index("ix_analysis_yield", "yield"),
        Index("ix_analysis_main_fail_bin", "main_fail_bin"),
        Index("ix_analysis_main_pattern", "main_pattern"),
    )
