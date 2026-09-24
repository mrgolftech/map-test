from pathlib import Path

from app.core.config import get_settings
from app.parsers.base import RawSource
from app.schemas.parsing import ParseStatus
from app.services.file_parse_service import FileParseService
from app.simulator.formats import serialize_cp1, serialize_pat
from app.simulator.generator import default_demo_config, generate_synthetic_dataset
from app.simulator.patterns import generate_pattern_dataset


def test_simulator_pat_cp_round_trip_preserves_canonical_facts():
    config = default_demo_config()
    expected = generate_synthetic_dataset(config)
    pat = serialize_pat(expected, filename="ROUNDTRIP.PAT", product_hint=config.product_hint)
    cp = serialize_cp1(expected)

    result = FileParseService(get_settings()).parse_sources(
        [
            RawSource("ROUNDTRIP.PAT", pat.encode()),
            RawSource("ROUNDTRIP.CP1", cp.encode()),
        ]
    )

    assert result.status == ParseStatus.VALID
    assert result.dataset is not None

    actual = result.dataset
    assert actual.metadata.product_id == expected.metadata.product_id
    assert actual.metadata.lot_id == expected.metadata.lot_id
    assert actual.metadata.wafer_id == expected.metadata.wafer_id
    assert actual.metadata.rows == expected.metadata.rows
    assert actual.metadata.columns == expected.metadata.columns
    assert actual.metadata.notch == expected.metadata.notch
    assert actual.summary == expected.summary
    assert {item.bin: item.count for item in actual.bins} == {
        item.bin: item.count for item in expected.bins
    }
    assert [
        (die.row, die.column, die.source_char, die.soft_bin, die.result)
        for die in actual.dies
    ] == [
        (die.row, die.column, die.source_char, die.soft_bin, die.result)
        for die in expected.dies
    ]


def test_mixed_failures_pat_cp_round_trip_preserves_all_fail_bins():
    expected = generate_pattern_dataset("MIXED_FAILURES", fail_count=300)
    fixture_dir = Path(__file__).parent / "fixtures" / "mixed_failures"
    pat = (fixture_dir / "DEMO.01.PAT").read_text(encoding="utf-8")
    cp = (fixture_dir / "DEMO.CP1").read_text(encoding="utf-8")
    assert pat == serialize_pat(expected, filename="DEMO.01.PAT")
    assert cp == serialize_cp1(expected)
    result = FileParseService(get_settings()).parse_sources(
        [RawSource("DEMO.01.PAT", pat.encode()), RawSource("DEMO.CP1", cp.encode())]
    )

    assert result.status == ParseStatus.VALID
    assert result.dataset is not None
    assert {item.bin: item.count for item in result.dataset.bins} == {
        item.bin: item.count for item in expected.bins
    }
    assert [
        (item.row, item.column, item.soft_bin) for item in result.dataset.dies
    ] == [
        (item.row, item.column, item.soft_bin) for item in expected.dies
    ]


def test_long_tail_multibin_pat_cp_fixture_round_trip():
    expected = generate_pattern_dataset(
        "LONG_TAIL_MULTI_BIN", rows=88, columns=128, fail_count=5560
    )
    fixture_dir = Path(__file__).parent / "fixtures" / "long_tail_multibin"
    pat = (fixture_dir / "DEMO_SCALE.01.PAT").read_text(encoding="utf-8")
    cp = (fixture_dir / "DEMO_SCALE.CP1").read_text(encoding="utf-8")
    assert pat == serialize_pat(expected, filename="DEMO_SCALE.01.PAT")
    assert cp == serialize_cp1(expected)

    result = FileParseService(get_settings()).parse_sources(
        [
            RawSource("DEMO_SCALE.01.PAT", pat.encode()),
            RawSource("DEMO_SCALE.CP1", cp.encode()),
        ]
    )
    assert result.status == ParseStatus.VALID
    assert result.dataset is not None
    assert result.dataset.summary == expected.summary
    assert {item.bin: item.count for item in result.dataset.bins} == {
        item.bin: item.count for item in expected.bins
    }
    assert [
        (item.row, item.column, item.soft_bin) for item in result.dataset.dies
    ] == [
        (item.row, item.column, item.soft_bin) for item in expected.dies
    ]


def _assert_profile_round_trip(pattern: str, *, rows: int, columns: int, fail_count: int):
    expected = generate_pattern_dataset(
        pattern,
        rows=rows,
        columns=columns,
        fail_count=fail_count,
        seed=20260924,
    )
    pat = serialize_pat(expected, filename=f"{pattern}.PAT")
    cp = serialize_cp1(expected)

    result = FileParseService(get_settings()).parse_sources(
        [
            RawSource(f"{pattern}.PAT", pat.encode()),
            RawSource(f"{pattern}.CP1", cp.encode()),
        ]
    )

    assert result.status == ParseStatus.VALID
    assert result.dataset is not None
    actual = result.dataset
    assert actual.summary == expected.summary
    assert {item.bin: item.count for item in actual.bins} == {
        item.bin: item.count for item in expected.bins
    }
    assert [
        (item.row, item.column, item.source_char, item.soft_bin, item.result)
        for item in actual.dies
    ] == [
        (item.row, item.column, item.source_char, item.soft_bin, item.result)
        for item in expected.dies
    ]


def test_production_profile_compact_pat_cp_round_trip():
    _assert_profile_round_trip(
        "PRODUCTION_PROFILE_COMPACT",
        rows=24,
        columns=32,
        fail_count=322,
    )


def test_production_profile_scale_pat_cp_round_trip():
    _assert_profile_round_trip(
        "PRODUCTION_PROFILE_SCALE",
        rows=88,
        columns=128,
        fail_count=5560,
    )
