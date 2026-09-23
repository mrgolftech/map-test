from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.analysis import AnalysisSummary
from app.schemas.parsing import SourceDescriptor, ValidationIssue
from app.schemas.wafer import WaferDataset


class AnalysisCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset: WaferDataset
    sources: list[SourceDescriptor] = Field(default_factory=list)
    validation_issues: list[ValidationIssue] = Field(default_factory=list)


class AnalysisListItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    id: str
    created_at: datetime
    product_id: str | None
    lot_id: str | None
    wafer_id: str | None
    flow_id: str | None
    yield_: float | None = Field(
        default=None,
        alias="yield",
        serialization_alias="yield",
    )
    tested_die: int
    pass_die: int
    fail_die: int
    main_fail_bin: int | None
    main_pattern: str | None
    validation_status: str


class AnalysisDetail(AnalysisListItem):
    dataset: WaferDataset
    analysis: AnalysisSummary
    sources: list[SourceDescriptor]
    validation_issues: list[ValidationIssue]


class PaginationMeta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    page: int
    page_size: int
    total: int


class AnalysisDetailResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    data: AnalysisDetail
    meta: dict[str, Any] = Field(default_factory=dict)


class AnalysisListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    data: list[AnalysisListItem]
    meta: PaginationMeta


class AnalysisDeleteData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    deleted: bool


class AnalysisDeleteResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    data: AnalysisDeleteData
    meta: dict[str, Any] = Field(default_factory=dict)
