from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class CompatibilitySeverity(StrEnum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class CompatibilityIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    severity: CompatibilitySeverity
    code: str
    message: str
    details: dict[str, object] | None = None


class CompatibilityResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    compatible: bool
    issues: list[CompatibilityIssue]


class YieldAggregate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    wafer_count: int
    valid_yield_count: int
    average: float | None
    median: float | None
    std_dev: float | None
    minimum: float | None
    maximum: float | None
    q1: float | None
    q3: float | None
    iqr: float | None
    outlier_lower_bound: float | None
    outlier_upper_bound: float | None


class YieldTrendPoint(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    analysis_id: str
    wafer_id: str | None
    test_time: datetime
    yield_: float | None = Field(
        default=None,
        alias="yield",
        serialization_alias="yield",
    )
    is_outlier: bool
    outlier_reason: str | None = None


class YieldExtremum(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    analysis_id: str
    wafer_id: str | None
    yield_: float = Field(alias="yield", serialization_alias="yield")


class BinTrendPoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    analysis_id: str
    wafer_id: str | None
    test_time: datetime
    wafer_rate: float
    fail_share: float | None
    edge_enrichment: float | None
    center_enrichment: float | None


class BinAggregate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    soft_bin: int
    char: str | None
    description: str | None
    wafer_count: int
    mean_wafer_rate: float
    std_wafer_rate: float
    mean_fail_share: float | None
    mean_edge_enrichment: float | None
    mean_center_enrichment: float | None
    trend: list[BinTrendPoint]


class PatternDistributionItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pattern: str
    count: int
    percentage: float


class PreviewBin(BaseModel):
    model_config = ConfigDict(extra="forbid")

    soft_bin: int
    char: str | None
    description: str | None


class WaferMapPreview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rows: int
    columns: int
    notch: str | None
    map_rows: list[str]
    bins: list[PreviewBin]


class WaferComparisonRow(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    analysis_id: str
    product_id: str | None
    lot_id: str | None
    wafer_id: str | None
    flow_id: str | None
    test_time: datetime
    yield_: float | None = Field(
        default=None,
        alias="yield",
        serialization_alias="yield",
    )
    tested_die: int
    pass_die: int
    fail_die: int
    main_fail_bin: int | None
    main_fail_rate: float | None
    edge_enrichment: float | None
    center_enrichment: float | None
    cluster_ratio: float | None
    main_pattern: str | None
    tester: str | None
    test_program: str | None
    probe_card: str | None
    is_outlier: bool
    preview: WaferMapPreview | None = None


class CompareRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    analysis_ids: list[str] = Field(min_length=2, max_length=25)


class ComparisonData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: str | None
    lot_id: str | None
    compatibility: CompatibilityResult
    yield_stats: YieldAggregate
    yield_trend: list[YieldTrendPoint]
    highest_yield_wafers: list[YieldExtremum]
    lowest_yield_wafers: list[YieldExtremum]
    bin_aggregates: list[BinAggregate]
    pattern_distribution: list[PatternDistributionItem]
    wafers: list[WaferComparisonRow]
    limitations: list[str]


class ComparisonResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    data: ComparisonData
    meta: dict[str, object] = Field(default_factory=dict)


class LotListItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: str | None
    lot_id: str
    wafer_count: int
    average_yield: float | None
    minimum_yield: float | None
    maximum_yield: float | None
    last_created_at: datetime


class LotListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    data: list[LotListItem]
    meta: dict[str, object] = Field(default_factory=dict)
