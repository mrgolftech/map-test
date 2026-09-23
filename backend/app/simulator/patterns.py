from datetime import datetime
from math import hypot
from random import Random
from typing import Literal

from app.parsers.bin_codec import soft_bin_to_char
from app.schemas.wafer import (
    BinRecord,
    DieRecord,
    DieResult,
    WaferDataset,
    WaferMetadata,
    WaferSummary,
)
from app.simulator.generator import SyntheticWaferConfig, active_coordinates

PatternName = Literal["RANDOM", "EDGE", "CENTER", "RING", "QUADRANT", "CLUSTER", "LINE"]


def _normalized(
    coordinates: list[tuple[int, int]],
) -> dict[tuple[int, int], tuple[float, float, float]]:
    rows = [row for row, _ in coordinates]
    columns = [column for _, column in coordinates]
    center_row = (min(rows) + max(rows)) / 2.0
    center_column = (min(columns) + max(columns)) / 2.0
    half_rows = max((max(rows) - min(rows)) / 2.0, 1.0)
    half_columns = max((max(columns) - min(columns)) / 2.0, 1.0)

    values: dict[tuple[int, int], tuple[float, float, float]] = {}
    max_radius = 0.0
    for row, column in coordinates:
        x = (column - center_column) / half_columns
        y = (center_row - row) / half_rows
        radius = hypot(x, y)
        values[(row, column)] = (x, y, radius)
        max_radius = max(max_radius, radius)

    return {
        coordinate: (x, y, radius / max(max_radius, 1.0))
        for coordinate, (x, y, radius) in values.items()
    }


def _select_fail_coordinates(
    pattern: PatternName,
    coordinates: list[tuple[int, int]],
    *,
    fail_count: int,
    seed: int,
) -> set[tuple[int, int]]:
    geometry = _normalized(coordinates)
    rng = Random(seed)

    if pattern == "RANDOM":
        return set(rng.sample(coordinates, fail_count))

    if pattern == "EDGE":
        ranked = sorted(coordinates, key=lambda item: geometry[item][2], reverse=True)
        return set(ranked[:fail_count])

    if pattern == "CENTER":
        ranked = sorted(coordinates, key=lambda item: geometry[item][2])
        return set(ranked[:fail_count])

    if pattern == "RING":
        ranked = sorted(
            coordinates,
            key=lambda item: abs(geometry[item][2] - 0.62),
        )
        return set(ranked[:fail_count])

    if pattern == "QUADRANT":
        q1 = [
            item
            for item in coordinates
            if geometry[item][0] >= 0 and geometry[item][1] >= 0
        ]
        ranked = sorted(q1, key=lambda item: geometry[item][2])
        return set(ranked[:fail_count])

    if pattern == "CLUSTER":
        target_x, target_y = 0.35, -0.25
        ranked = sorted(
            coordinates,
            key=lambda item: hypot(
                geometry[item][0] - target_x,
                geometry[item][1] - target_y,
            ),
        )
        return set(ranked[:fail_count])

    if pattern == "LINE":
        center_row = round(sum(row for row, _ in coordinates) / len(coordinates))
        ranked = sorted(
            coordinates,
            key=lambda item: (
                abs(item[0] - center_row),
                abs(geometry[item][0]),
            ),
        )
        return set(ranked[:fail_count])

    raise ValueError(f"Unsupported synthetic pattern: {pattern}")


def generate_pattern_dataset(
    pattern: PatternName,
    *,
    seed: int = 20260924,
    fail_count: int = 48,
) -> WaferDataset:
    config = SyntheticWaferConfig(
        product_id=f"DEMO_{pattern}",
        lot_id="PATTERN001",
        wafer_id="01",
        seed=seed,
        bins=[],
    )
    coordinates = active_coordinates(config)
    if fail_count <= 0 or fail_count >= len(coordinates):
        raise ValueError("fail_count must leave both PASS and FAIL dies.")

    fail_coordinates = _select_fail_coordinates(
        pattern,
        coordinates,
        fail_count=fail_count,
        seed=seed,
    )
    if len(fail_coordinates) != fail_count:
        raise ValueError(
            f"Pattern {pattern} cannot provide {fail_count} unique fail coordinates."
        )

    pass_char = soft_bin_to_char(1)
    fail_char = soft_bin_to_char(18)
    if pass_char is None or fail_char is None:
        raise ValueError("Synthetic PASS/FAIL bins are not encodable.")

    dies: list[DieRecord] = []
    for row, column in sorted(coordinates):
        failed = (row, column) in fail_coordinates
        dies.append(
            DieRecord(
                row=row,
                column=column,
                source_char=fail_char if failed else pass_char,
                soft_bin=18 if failed else 1,
                result=DieResult.FAIL if failed else DieResult.PASS,
                description="Pout_min" if failed else "PASS",
            )
        )

    tested = len(dies)
    passed = tested - fail_count
    return WaferDataset(
        metadata=WaferMetadata(
            product_id=config.product_id,
            lot_id=config.lot_id,
            wafer_id=config.wafer_id,
            flow_id="CP1",
            subcon="SYNTHETIC",
            tester="SIM-PATTERN",
            test_program="SYNTH_PATTERN_V1",
            probe_card="SIM-PC-01",
            start_time=datetime(2026, 1, 2, 8, 0, 0),
            stop_time=datetime(2026, 1, 2, 9, 0, 0),
            notch="DOWN",
            rows=config.rows,
            columns=config.columns,
        ),
        dies=dies,
        bins=[
            BinRecord(
                bin=1,
                char=pass_char,
                description="PASS",
                count=passed,
                percentage=passed / tested,
            ),
            BinRecord(
                bin=18,
                char=fail_char,
                description="Pout_min",
                count=fail_count,
                percentage=fail_count / tested,
            ),
        ],
        summary=WaferSummary(
            tested_die=tested,
            pass_die=passed,
            fail_die=fail_count,
            yield_=passed / tested,
        ),
    )
