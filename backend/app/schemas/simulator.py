from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.wafer import WaferDataset


class SyntheticPattern(StrEnum):
    RANDOM = "RANDOM"
    EDGE = "EDGE"
    CENTER = "CENTER"
    RING = "RING"
    TOP = "TOP"
    BOTTOM = "BOTTOM"
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    QUADRANT = "QUADRANT"
    CLUSTER = "CLUSTER"
    LINE = "LINE"
    MULTI_PATTERN = "MULTI_PATTERN"
    MIXED_FAILURES = "MIXED_FAILURES"
    LONG_TAIL_MULTI_BIN = "LONG_TAIL_MULTI_BIN"
    PRODUCTION_PROFILE_COMPACT = "PRODUCTION_PROFILE_COMPACT"
    PRODUCTION_PROFILE_SCALE = "PRODUCTION_PROFILE_SCALE"


class DemoLotScenario(StrEnum):
    EDGE_DRIFT = "EDGE_DRIFT"
    MIXED_PATTERNS = "MIXED_PATTERNS"
    STABLE_RANDOM = "STABLE_RANDOM"
    PROFILE_DRIFT = "PROFILE_DRIFT"


class SyntheticWaferRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pattern: SyntheticPattern = SyntheticPattern.EDGE
    fail_count: int = Field(default=48, ge=1, le=65535)
    seed: int = 20260924
    product_id: str = Field(default="DEMO_WAFER", min_length=1, max_length=128)
    lot_id: str = Field(default="DEMO001", min_length=1, max_length=128)
    wafer_id: str = Field(default="01", min_length=1, max_length=64)
    rows: int = Field(default=24, ge=8, le=256)
    columns: int = Field(default=32, ge=8, le=256)


class SyntheticWaferResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    data: WaferDataset
    meta: dict[str, object] = Field(default_factory=dict)


class DemoLotRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scenario: DemoLotScenario = DemoLotScenario.EDGE_DRIFT
    seed: int = 20260924


class DemoLotData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scenario: DemoLotScenario
    description: str
    datasets: list[WaferDataset]


class DemoLotResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    data: DemoLotData
    meta: dict[str, object] = Field(default_factory=dict)
