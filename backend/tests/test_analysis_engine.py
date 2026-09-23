import pytest

from app.analysis.engine import AnalysisEngine
from app.simulator.generator import default_demo_config, generate_synthetic_dataset
from app.simulator.patterns import generate_pattern_dataset


def _patterns_for(summary, soft_bin: int) -> set[str]:
    return {
        item.pattern
        for item in summary.patterns
        if item.soft_bin == soft_bin
    }


def test_analysis_preserves_summary_and_bin_facts():
    dataset = generate_synthetic_dataset(default_demo_config())
    summary = AnalysisEngine().analyze(dataset)

    assert summary.schema_version == "1.0"
    assert summary.summary == dataset.summary
    assert {item.soft_bin: item.count for item in summary.bin_stats} == {
        item.bin: item.count for item in dataset.bins
    }

    assert (
        summary.region_stats["center"].tested_die
        + summary.region_stats["mid"].tested_die
        + summary.region_stats["edge"].tested_die
        == dataset.summary.tested_die
    )
    assert (
        summary.region_stats["top"].tested_die
        + summary.region_stats["bottom"].tested_die
        == dataset.summary.tested_die
    )
    assert sum(
        summary.region_stats[name].tested_die
        for name in ("q1", "q2", "q3", "q4")
    ) == dataset.summary.tested_die


def test_spatial_bin_region_counts_conserve_bin_count():
    dataset = generate_synthetic_dataset(default_demo_config())
    summary = AnalysisEngine().analyze(dataset)

    for stat in summary.spatial_by_bin:
        assert stat.center.bin_die + stat.mid.bin_die + stat.edge.bin_die == stat.count
        assert stat.top.bin_die + stat.bottom.bin_die == stat.count
        assert stat.left.bin_die + stat.right.bin_die == stat.count
        assert stat.q1.bin_die + stat.q2.bin_die + stat.q3.bin_die + stat.q4.bin_die == stat.count


def test_enrichment_matches_defined_formula():
    dataset = generate_pattern_dataset("EDGE", fail_count=48)
    summary = AnalysisEngine().analyze(dataset)
    stat = next(item for item in summary.spatial_by_bin if item.soft_bin == 18)

    expected = (
        (stat.edge.bin_die / stat.edge.tested_die)
        / (stat.count / dataset.summary.tested_die)
    )
    assert stat.edge.enrichment == pytest.approx(expected)


@pytest.mark.parametrize(
    ("scenario", "expected_pattern", "fail_count"),
    [
        ("EDGE", "EDGE", 48),
        ("CENTER", "CENTER", 48),
        ("RING", "RING", 48),
        ("QUADRANT", "QUADRANT", 48),
        ("CLUSTER", "LOCALIZED_CLUSTER", 48),
        ("LINE", "LINE", 24),
    ],
)
def test_synthetic_patterns_are_detected(scenario, expected_pattern, fail_count):
    dataset = generate_pattern_dataset(scenario, fail_count=fail_count)
    summary = AnalysisEngine().analyze(dataset)

    assert expected_pattern in _patterns_for(summary, 18)


def test_pattern_results_include_numeric_evidence_and_thresholds():
    dataset = generate_pattern_dataset("EDGE", fail_count=48)
    summary = AnalysisEngine().analyze(dataset)
    edge = next(
        item
        for item in summary.patterns
        if item.soft_bin == 18 and item.pattern == "EDGE"
    )

    assert edge.score >= 0.60
    assert any(item.startswith("edge_enrichment=") for item in edge.evidence)
    assert edge.thresholds["enrichment_threshold"] == 1.5
