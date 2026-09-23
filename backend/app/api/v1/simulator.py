from datetime import timedelta

from fastapi import APIRouter

from app.core.errors import AppError
from app.schemas.simulator import (
    DemoLotData,
    DemoLotRequest,
    DemoLotResponse,
    DemoLotScenario,
    SyntheticPattern,
    SyntheticWaferRequest,
    SyntheticWaferResponse,
)
from app.simulator.patterns import generate_pattern_dataset

router = APIRouter(prefix="/simulator", tags=["simulator"])


def _wafer(
    *,
    pattern: SyntheticPattern,
    fail_count: int,
    seed: int,
    product_id: str,
    lot_id: str,
    wafer_id: str,
    rows: int = 24,
    columns: int = 32,
    time_offset_minutes: int = 0,
):
    try:
        dataset = generate_pattern_dataset(
            pattern.value,
            seed=seed,
            fail_count=fail_count,
            rows=rows,
            columns=columns,
        )
    except ValueError as exc:
        raise AppError(
            code="SIMULATOR_INVALID_CONFIG",
            message=str(exc),
            status_code=422,
        ) from exc
    dataset.metadata.product_id = product_id
    dataset.metadata.lot_id = lot_id
    dataset.metadata.wafer_id = wafer_id
    if dataset.metadata.start_time is not None:
        dataset.metadata.start_time += timedelta(minutes=time_offset_minutes)
    if dataset.metadata.stop_time is not None:
        dataset.metadata.stop_time += timedelta(minutes=time_offset_minutes)
    return dataset


@router.post("/wafer", response_model=SyntheticWaferResponse)
def generate_demo_wafer(
    request: SyntheticWaferRequest,
) -> SyntheticWaferResponse:
    dataset = _wafer(
        pattern=request.pattern,
        fail_count=request.fail_count,
        seed=request.seed,
        product_id=request.product_id,
        lot_id=request.lot_id,
        wafer_id=request.wafer_id,
        rows=request.rows,
        columns=request.columns,
    )
    return SyntheticWaferResponse(
        data=dataset,
        meta={
            "synthetic": True,
            "pattern": request.pattern.value,
            "seed": request.seed,
        },
    )


@router.post("/lot", response_model=DemoLotResponse)
def generate_demo_lot(
    request: DemoLotRequest,
) -> DemoLotResponse:
    if request.scenario == DemoLotScenario.EDGE_DRIFT:
        patterns = [SyntheticPattern.EDGE] * 5
        fail_counts = [20, 22, 24, 26, 200]
        description = (
            "Five compatible wafers with increasing edge failures; "
            "the final wafer is designed to trigger IQR yield outlier detection."
        )
    elif request.scenario == DemoLotScenario.MIXED_PATTERNS:
        patterns = [
            SyntheticPattern.EDGE,
            SyntheticPattern.CENTER,
            SyntheticPattern.RING,
            SyntheticPattern.CLUSTER,
            SyntheticPattern.LINE,
        ]
        fail_counts = [48] * 5
        description = (
            "Five compatible wafers with different deterministic spatial patterns."
        )
    else:
        patterns = [SyntheticPattern.RANDOM] * 5
        fail_counts = [32, 34, 33, 35, 32]
        description = "Five stable random wafers without an injected yield outlier."

    lot_id = f"DEMO-{request.scenario.value}"
    datasets = [
        _wafer(
            pattern=pattern,
            fail_count=fail_count,
            seed=request.seed + index,
            product_id="DEMO_LOT_PRODUCT",
            lot_id=lot_id,
            wafer_id=f"{index + 1:02d}",
            time_offset_minutes=index * 20,
        )
        for index, (pattern, fail_count) in enumerate(
            zip(patterns, fail_counts, strict=True)
        )
    ]

    return DemoLotResponse(
        data=DemoLotData(
            scenario=request.scenario,
            description=description,
            datasets=datasets,
        ),
        meta={"synthetic": True, "seed": request.seed},
    )
