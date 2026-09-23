from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DashboardSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    analysis_count: int
    lot_count: int
    average_yield: float | None
    minimum_yield: float | None
    maximum_yield: float | None
    latest_created_at: datetime | None


class DashboardSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    data: DashboardSummary
    meta: dict[str, object] = Field(default_factory=dict)
