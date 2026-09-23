from datetime import datetime
from random import Random

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.parsers.bin_codec import soft_bin_to_char
from app.schemas.wafer import (
    BinRecord,
    DieRecord,
    DieResult,
    WaferDataset,
    WaferMetadata,
    WaferSummary,
)


class SyntheticBinSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    soft_bin: int = Field(ge=1)
    description: str
    count: int = Field(ge=0)


class SyntheticWaferConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: str = "DEMO_RFIC_A"
    product_hint: str = "DEMO"
    lot_id: str = "SYNTH001"
    wafer_id: str = "01"
    flow_id: str = "CP1"
    rows: int = Field(default=24, ge=4)
    columns: int = Field(default=32, ge=4)
    notch: str = "DOWN"
    seed: int = 20260923
    radius_scale: float = Field(default=0.92, gt=0.1, le=1.0)
    bins: list[SyntheticBinSpec] = Field(
        default_factory=lambda: [
            SyntheticBinSpec(soft_bin=1, description="PASS", count=358),
            SyntheticBinSpec(soft_bin=16, description="BER_RESULT", count=50),
            SyntheticBinSpec(soft_bin=18, description="Pout_min", count=60),
            SyntheticBinSpec(soft_bin=20, description="Pout_max_2402", count=30),
            SyntheticBinSpec(soft_bin=22, description="Pout_max_2480", count=10),
            SyntheticBinSpec(soft_bin=27, description="GADC", count=4),
        ]
    )

    @model_validator(mode="after")
    def validate_bin_chars(self) -> "SyntheticWaferConfig":
        unsupported = [
            item.soft_bin for item in self.bins if soft_bin_to_char(item.soft_bin) is None
        ]
        if unsupported:
            raise ValueError(f"Soft bins are not encodable in one map character: {unsupported}")
        if len({item.soft_bin for item in self.bins}) != len(self.bins):
            raise ValueError("Synthetic bin definitions must be unique.")
        return self


def active_coordinates(config: SyntheticWaferConfig) -> list[tuple[int, int]]:
    center_row = (config.rows - 1) / 2.0
    center_column = (config.columns - 1) / 2.0
    row_radius = config.rows / 2.0
    column_radius = config.columns / 2.0

    coordinates: list[tuple[int, int]] = []
    for row in range(config.rows):
        for column in range(config.columns):
            y = (row - center_row) / row_radius
            x = (column - center_column) / column_radius
            if x * x + y * y <= config.radius_scale * config.radius_scale:
                coordinates.append((row, column))
    return coordinates


def generate_synthetic_dataset(config: SyntheticWaferConfig) -> WaferDataset:
    coordinates = active_coordinates(config)
    requested = sum(item.count for item in config.bins)
    if requested != len(coordinates):
        raise ValueError(
            "Synthetic bin counts must exactly equal active die count "
            f"({requested} != {len(coordinates)})."
        )

    shuffled = coordinates.copy()
    Random(config.seed).shuffle(shuffled)

    assignment: dict[tuple[int, int], SyntheticBinSpec] = {}
    offset = 0
    for bin_spec in config.bins:
        for coordinate in shuffled[offset : offset + bin_spec.count]:
            assignment[coordinate] = bin_spec
        offset += bin_spec.count

    pass_bins = {
        item.soft_bin for item in config.bins if "PASS" in item.description.upper()
    } or {1}

    dies: list[DieRecord] = []
    for row, column in sorted(coordinates):
        spec = assignment[(row, column)]
        char = soft_bin_to_char(spec.soft_bin)
        if char is None:
            raise ValueError(f"Soft Bin {spec.soft_bin} has no one-character encoding.")
        dies.append(
            DieRecord(
                row=row,
                column=column,
                source_char=char,
                soft_bin=spec.soft_bin,
                result=(
                    DieResult.PASS
                    if spec.soft_bin in pass_bins
                    else DieResult.FAIL
                ),
                description=spec.description,
            )
        )

    tested = len(dies)
    passed = sum(1 for die in dies if die.result == DieResult.PASS)
    failed = tested - passed

    bins = [
        BinRecord(
            bin=item.soft_bin,
            char=soft_bin_to_char(item.soft_bin),
            description=item.description,
            count=item.count,
            percentage=item.count / tested,
        )
        for item in config.bins
    ]

    return WaferDataset(
        metadata=WaferMetadata(
            product_id=config.product_id,
            lot_id=config.lot_id,
            wafer_id=config.wafer_id,
            flow_id=config.flow_id,
            subcon="SYNTHETIC",
            tester="SIM-01",
            test_program="SYNTH_CP_V1",
            probe_card="SIM-PC-01",
            start_time=datetime(2026, 1, 1, 8, 0, 0),
            stop_time=datetime(2026, 1, 1, 9, 0, 0),
            notch=config.notch.upper(),
            rows=config.rows,
            columns=config.columns,
        ),
        dies=dies,
        bins=bins,
        summary=WaferSummary(
            tested_die=tested,
            pass_die=passed,
            fail_die=failed,
            yield_=passed / tested,
        ),
    )


def default_demo_config() -> SyntheticWaferConfig:
    return SyntheticWaferConfig()
