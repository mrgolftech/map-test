from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.wafer import WaferDataset


class SourceFormat(StrEnum):
    PAT = "PAT"
    CP1 = "CP1"
    UNKNOWN = "UNKNOWN"


class SourceRole(StrEnum):
    METADATA = "metadata"
    MAP = "map"
    COMBINED = "combined"
    UNKNOWN = "unknown"


class ValidationSeverity(StrEnum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class ValidationStage(StrEnum):
    DETECT = "DETECT"
    PARSE = "PARSE"
    ASSEMBLE = "ASSEMBLE"
    CANONICAL = "CANONICAL"


class ParseStatus(StrEnum):
    VALID = "VALID"
    WARNING = "WARNING"
    INVALID = "INVALID"


class ValidationIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    severity: ValidationSeverity
    stage: ValidationStage
    code: str
    message: str
    source_file: str | None = None
    line: int | None = Field(default=None, ge=1)
    row: int | None = Field(default=None, ge=0)
    column: int | None = Field(default=None, ge=0)
    details: dict[str, Any] | None = None


class SourceDescriptor(BaseModel):
    model_config = ConfigDict(extra="forbid")

    filename: str
    size: int = Field(ge=0)
    sha256: str = Field(min_length=64, max_length=64)
    detected_format: SourceFormat
    parser_id: str
    role: SourceRole
    detection_evidence: list[str]


class SourceMetadata(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    product_id: str | None = None
    product_hint: str | None = None
    lot_id: str | None = None
    wafer_id: str | None = None
    flow_id: str | None = None
    subcon: str | None = None
    tester: str | None = None
    test_program: str | None = None
    probe_card: str | None = None
    start_time: datetime | None = None
    stop_time: datetime | None = None
    notch: str | None = None
    rows: int | None = Field(default=None, ge=1)
    columns: int | None = Field(default=None, ge=1)
    tested_die: int | None = Field(default=None, ge=0)
    pass_die: int | None = Field(default=None, ge=0)
    yield_: float | None = Field(
        default=None,
        alias="yield",
        serialization_alias="yield",
        ge=0.0,
        le=1.0,
    )


class SourceBinDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bin: int = Field(ge=1)
    char: str | None = Field(default=None, min_length=1, max_length=1)
    description: str | None = None
    declared_count: int | None = Field(default=None, ge=0)
    declared_percentage: float | None = Field(default=None, ge=0.0, le=1.0)


class SourceParseResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: SourceDescriptor
    metadata: SourceMetadata
    map_rows: list[str] | None = None
    bins: list[SourceBinDefinition] = Field(default_factory=list)
    issues: list[ValidationIssue] = Field(default_factory=list)


class ParseResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset: WaferDataset | None = None
    sources: list[SourceDescriptor]
    validation_issues: list[ValidationIssue]
    status: ParseStatus
