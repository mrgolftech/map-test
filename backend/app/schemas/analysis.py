from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.parsing import ValidationIssue
from app.schemas.wafer import WaferDataset, WaferMetadata, WaferSummary


class AnalysisConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    center_radius: float = Field(default=0.45, ge=0.0, lt=1.0)
    edge_radius: float = Field(default=0.75, gt=0.0, le=1.0)
    neighbor_mode: Literal[4, 8] = 8
    enrichment_threshold: float = Field(default=1.5, gt=1.0)
    cluster_ratio_threshold: float = Field(default=0.25, gt=0.0, le=1.0)
    min_cluster_size: int = Field(default=4, ge=2)
    directional_enrichment_threshold: float = Field(default=1.5, gt=1.0)
    line_concentration_threshold: float = Field(default=0.35, gt=0.0, le=1.0)


class BinStat(BaseModel):
    model_config = ConfigDict(extra="forbid")

    soft_bin: int
    char: str | None
    description: str | None
    count: int
    wafer_rate: float
    fail_share: float | None


class RegionMetric(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tested_die: int
    pass_die: int
    fail_die: int
    fail_rate: float | None


class BinRegionMetric(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tested_die: int
    bin_die: int
    region_rate: float | None
    whole_rate: float | None
    enrichment: float | None


class ClusterStats(BaseModel):
    model_config = ConfigDict(extra="forbid")

    component_count: int
    largest_component: int
    average_component_size: float | None
    cluster_ratio: float | None
    component_sizes: list[int]


class SpatialBinStat(BaseModel):
    model_config = ConfigDict(extra="forbid")

    soft_bin: int
    count: int
    center: BinRegionMetric
    mid: BinRegionMetric
    edge: BinRegionMetric
    top: BinRegionMetric
    bottom: BinRegionMetric
    left: BinRegionMetric
    right: BinRegionMetric
    q1: BinRegionMetric
    q2: BinRegionMetric
    q3: BinRegionMetric
    q4: BinRegionMetric
    cluster: ClusterStats
    max_row_fraction: float | None
    max_column_fraction: float | None


class PatternResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pattern: str
    soft_bin: int | None = None
    score: float = Field(ge=0.0, le=1.0)
    evidence: list[str]
    thresholds: dict[str, float | int | str]
    limitations: list[str] = Field(default_factory=list)


class AnalysisSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    metadata: WaferMetadata
    summary: WaferSummary
    validation: list[ValidationIssue] = Field(default_factory=list)
    config: AnalysisConfig
    bin_stats: list[BinStat]
    region_stats: dict[str, RegionMetric]
    spatial_by_bin: list[SpatialBinStat]
    patterns: list[PatternResult]
    top_findings: list[str]
    limitations: list[str]


class AnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset: WaferDataset
    config: AnalysisConfig | None = None
