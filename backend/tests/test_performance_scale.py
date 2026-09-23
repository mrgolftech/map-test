from app.analysis.engine import AnalysisEngine
from app.simulator.patterns import generate_pattern_dataset


def test_analysis_handles_more_than_ten_thousand_dies():
    dataset = generate_pattern_dataset(
        "EDGE",
        seed=20260924,
        fail_count=800,
        rows=128,
        columns=128,
    )

    assert dataset.summary.tested_die > 10_000

    result = AnalysisEngine().analyze(dataset)

    assert result.summary.tested_die == dataset.summary.tested_die
    assert result.summary.fail_die == 800
    assert result.bin_stats[0].count + result.bin_stats[1].count == result.summary.tested_die
    assert any(item.pattern == "EDGE" for item in result.patterns)
