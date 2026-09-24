from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from pathlib import Path

from app.schemas.wafer import WaferDataset
from app.simulator.formats import serialize_cp1, serialize_pat
from app.simulator.patterns import generate_pattern_dataset

DEFAULT_SEED = 20260924
PRODUCT_ID = "DEMO_RF_PROFILE"


def _configure_metadata(
    dataset: WaferDataset,
    *,
    lot_id: str,
    wafer_id: str,
    start_time: datetime,
) -> WaferDataset:
    dataset.metadata.product_id = PRODUCT_ID
    dataset.metadata.lot_id = lot_id
    dataset.metadata.wafer_id = wafer_id
    dataset.metadata.start_time = start_time
    dataset.metadata.stop_time = start_time + timedelta(hours=1)
    return dataset


def build_production_profile_demo_datasets(
    *,
    seed: int = DEFAULT_SEED,
) -> dict[str, WaferDataset]:
    compact = _configure_metadata(
        generate_pattern_dataset(
            "PRODUCTION_PROFILE_COMPACT",
            seed=seed,
            fail_count=322,
            rows=24,
            columns=32,
        ),
        lot_id="SYNTH-PROFILE-COMPACT",
        wafer_id="01",
        start_time=datetime(2026, 1, 3, 8, 0, 0),
    )
    scale = _configure_metadata(
        generate_pattern_dataset(
            "PRODUCTION_PROFILE_SCALE",
            seed=seed,
            fail_count=5560,
            rows=88,
            columns=128,
        ),
        lot_id="SYNTH-PROFILE-SCALE",
        wafer_id="01",
        start_time=datetime(2026, 1, 3, 10, 0, 0),
    )

    datasets: dict[str, WaferDataset] = {
        "production_profile_compact": compact,
        "production_profile_scale": scale,
    }

    fail_counts = (4900, 5100, 5300, 5560, 6600)
    cluster_fractions = (0.18, 0.20, 0.22, 0.27, 0.35)
    lot_start = datetime(2026, 1, 4, 8, 0, 0)
    for index, (fail_count, cluster_fraction) in enumerate(
        zip(fail_counts, cluster_fractions, strict=True),
        start=1,
    ):
        wafer_id = f"{index:02d}"
        dataset = _configure_metadata(
            generate_pattern_dataset(
                "PRODUCTION_PROFILE_SCALE",
                seed=seed + index - 1,
                fail_count=fail_count,
                rows=88,
                columns=128,
                profile_cluster_fraction=cluster_fraction,
            ),
            lot_id="SYNTH-PROFILE-DRIFT",
            wafer_id=wafer_id,
            start_time=lot_start + timedelta(minutes=(index - 1) * 20),
        )
        datasets[f"production_profile_lot_{wafer_id}"] = dataset

    return datasets


def render_production_profile_demo_assets(
    *,
    seed: int = DEFAULT_SEED,
) -> dict[str, str]:
    datasets = build_production_profile_demo_datasets(seed=seed)
    assets: dict[str, str] = {}

    compact = datasets["production_profile_compact"]
    assets[
        "production_profile_compact/PROFILE_COMPACT.01.PAT"
    ] = serialize_pat(compact, filename="PROFILE_COMPACT.01.PAT")
    assets[
        "production_profile_compact/PROFILE_COMPACT.CP1"
    ] = serialize_cp1(compact)

    scale = datasets["production_profile_scale"]
    assets[
        "production_profile_scale/PROFILE_SCALE.01.PAT"
    ] = serialize_pat(scale, filename="PROFILE_SCALE.01.PAT")
    assets[
        "production_profile_scale/PROFILE_SCALE.CP1"
    ] = serialize_cp1(scale)

    for index in range(1, 6):
        wafer_id = f"{index:02d}"
        dataset = datasets[f"production_profile_lot_{wafer_id}"]
        assets[
            f"production_profile_lot/PROFILE_DRIFT.{wafer_id}.PAT"
        ] = serialize_pat(
            dataset,
            filename=f"PROFILE_DRIFT.{wafer_id}.PAT",
        )
        assets[
            f"production_profile_lot/PROFILE_DRIFT_{wafer_id}.CP1"
        ] = serialize_cp1(dataset)

    return assets


def write_production_profile_demo_assets(
    output_dir: Path,
    *,
    seed: int = DEFAULT_SEED,
) -> list[Path]:
    written: list[Path] = []
    for relative_path, content in render_production_profile_demo_assets(seed=seed).items():
        target = output_dir / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        written.append(target)
    return written


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate fixed synthetic PAT/CP demo assets."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("generated/production_profile_demo"),
    )
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args()

    written = write_production_profile_demo_assets(args.output, seed=args.seed)
    for path in written:
        print(path)


if __name__ == "__main__":
    main()
