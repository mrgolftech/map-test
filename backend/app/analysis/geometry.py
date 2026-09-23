from dataclasses import dataclass
from math import hypot

from app.schemas.analysis import AnalysisConfig
from app.schemas.wafer import DieRecord


@dataclass(frozen=True, slots=True)
class DieGeometry:
    x: float
    y: float
    radius: float
    radial_region: str
    vertical_region: str
    horizontal_region: str
    quadrant: str


def build_geometry(
    dies: list[DieRecord],
    config: AnalysisConfig,
) -> dict[tuple[int, int], DieGeometry]:
    if not dies:
        return {}

    rows = [die.row for die in dies]
    columns = [die.column for die in dies]
    min_row, max_row = min(rows), max(rows)
    min_column, max_column = min(columns), max(columns)

    center_row = (min_row + max_row) / 2.0
    center_column = (min_column + max_column) / 2.0
    half_rows = max((max_row - min_row) / 2.0, 1.0)
    half_columns = max((max_column - min_column) / 2.0, 1.0)

    normalized: dict[tuple[int, int], tuple[float, float, float]] = {}
    max_radius = 0.0
    for die in dies:
        x = (die.column - center_column) / half_columns
        y = (center_row - die.row) / half_rows
        radius = hypot(x, y)
        normalized[(die.row, die.column)] = (x, y, radius)
        max_radius = max(max_radius, radius)

    max_radius = max(max_radius, 1.0)
    result: dict[tuple[int, int], DieGeometry] = {}
    for coordinate, (x, y, raw_radius) in normalized.items():
        radius = raw_radius / max_radius
        if radius < config.center_radius:
            radial_region = "center"
        elif radius < config.edge_radius:
            radial_region = "mid"
        else:
            radial_region = "edge"

        vertical_region = "top" if y >= 0 else "bottom"
        horizontal_region = "right" if x >= 0 else "left"
        if x >= 0 and y >= 0:
            quadrant = "q1"
        elif x < 0 <= y:
            quadrant = "q2"
        elif x < 0 and y < 0:
            quadrant = "q3"
        else:
            quadrant = "q4"

        result[coordinate] = DieGeometry(
            x=x,
            y=y,
            radius=radius,
            radial_region=radial_region,
            vertical_region=vertical_region,
            horizontal_region=horizontal_region,
            quadrant=quadrant,
        )

    return result
