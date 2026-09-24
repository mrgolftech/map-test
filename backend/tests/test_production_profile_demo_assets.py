import json
from pathlib import Path

import pytest
from app.analysis.engine import AnalysisEngine
from app.core.config import get_settings
from app.parsers.base import RawSource
from app.schemas.parsing import ParseStatus
from app.services.file_parse_service import FileParseService
from app.simulator.demo_assets import (
    render_production_profile_demo_assets,
    write_production_profile_demo_assets,
)

FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "production_profile_demo"


def _manifest() -> dict:
    return json.loads((FIXTURE_ROOT / "manifest.json").read_text(encoding="utf-8"))


def _parse_pair(
    assets: dict[str, str],
    *,
    pat_path: str,
    cp1_path: str,
):
    result = FileParseService(get_settings()).parse_sources(
        [
            RawSource(Path(pat_path).name, assets[pat_path].encode()),
            RawSource(Path(cp1_path).name, assets[cp1_path].encode()),
        ]
    )
    assert result.status == ParseStatus.VALID
    assert result.dataset is not None
    return result.dataset


def _patterns_for(summary, soft_bin: int) -> set[str]:
    return {
        item.pattern
        for item in summary.patterns
        if item.soft_bin == soft_bin
    }


def test_production_profile_demo_assets_match_manifest_and_real_parser():
    manifest = _manifest()
    assets = render_production_profile_demo_assets(seed=manifest["seed"])

    assert len(assets) == 14

    for scenario_name in (
        "PRODUCTION_PROFILE_COMPACT",
        "PRODUCTION_PROFILE_SCALE",
    ):
        expected = manifest["scenarios"][scenario_name]
        dataset = _parse_pair(
            assets,
            pat_path=expected["pat"],
            cp1_path=expected["cp1"],
        )

        assert dataset.metadata.rows == expected["rows"]
        assert dataset.metadata.columns == expected["columns"]
        assert dataset.summary.tested_die == expected["tested"]
        assert dataset.summary.pass_die == expected["pass"]
        assert dataset.summary.fail_die == expected["fail"]
        assert dataset.summary.yield_ == pytest.approx(expected["yield"])
        assert {str(item.bin): item.count for item in dataset.bins} == expected["bin_counts"]

        summary = AnalysisEngine().analyze(dataset)
        for soft_bin, pattern in expected["expected_patterns"].items():
            assert pattern in _patterns_for(summary, int(soft_bin))


def test_profile_drift_assets_match_manifest_and_parse_independently():
    manifest = _manifest()
    expected = manifest["scenarios"]["PROFILE_DRIFT"]
    assets = render_production_profile_demo_assets(seed=manifest["seed"])

    yields: list[float] = []
    for wafer in expected["wafers"]:
        wafer_id = wafer["wafer_id"]
        dataset = _parse_pair(
            assets,
            pat_path=f"production_profile_lot/PROFILE_DRIFT.{wafer_id}.PAT",
            cp1_path=f"production_profile_lot/PROFILE_DRIFT_{wafer_id}.CP1",
        )

        assert dataset.metadata.lot_id == expected["lot_id"]
        assert dataset.metadata.wafer_id == wafer_id
        assert dataset.metadata.rows == expected["rows"]
        assert dataset.metadata.columns == expected["columns"]
        assert dataset.summary.tested_die == wafer["tested"]
        assert dataset.summary.pass_die == wafer["pass"]
        assert dataset.summary.fail_die == wafer["fail"]
        assert dataset.summary.yield_ == pytest.approx(wafer["yield"])
        assert {str(item.bin): item.count for item in dataset.bins} == wafer["bin_counts"]
        yields.append(dataset.summary.yield_ or 0.0)

    assert yields == sorted(yields, reverse=True)


def test_production_profile_demo_assets_can_be_materialized_for_upload(tmp_path):
    written = write_production_profile_demo_assets(tmp_path)

    assert len(written) == 14
    assert all(path.exists() and path.stat().st_size > 0 for path in written)
    assert (tmp_path / "production_profile_compact" / "PROFILE_COMPACT.01.PAT").exists()
    assert (tmp_path / "production_profile_scale" / "PROFILE_SCALE.CP1").exists()
    assert (tmp_path / "production_profile_lot" / "PROFILE_DRIFT_05.CP1").exists()
