from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class DieResult(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"


class WaferMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: str | None = None
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
    rows: int = Field(ge=1)
    columns: int = Field(ge=1)


class DieRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    row: int = Field(ge=0)
    column: int = Field(ge=0)
    source_char: str = Field(min_length=1, max_length=1)
    soft_bin: int | None = Field(default=None, ge=1)
    hard_bin: int | None = Field(default=None, ge=1)
    result: DieResult
    description: str | None = None
    test_values: dict[str, float | int | str | None] | None = None


class BinRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bin: int = Field(ge=1)
    char: str | None = Field(default=None, min_length=1, max_length=1)
    description: str | None = None
    count: int = Field(ge=0)
    percentage: float = Field(ge=0.0, le=1.0)


class WaferSummary(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    tested_die: int = Field(ge=0)
    pass_die: int = Field(ge=0)
    fail_die: int = Field(ge=0)
    yield_: float | None = Field(
        default=None,
        alias="yield",
        serialization_alias="yield",
        ge=0.0,
        le=1.0,
    )


class WaferDataset(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metadata: WaferMetadata
    dies: list[DieRecord]
    bins: list[BinRecord]
    summary: WaferSummary
