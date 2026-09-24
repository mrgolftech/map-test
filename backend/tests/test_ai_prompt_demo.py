from app.ai.prompt import compact_analysis_payload
from app.analysis.engine import AnalysisEngine
from app.simulator.patterns import generate_pattern_dataset


def test_production_scale_ai_payload_keeps_main_cluster_and_secondary_ring():
    dataset = generate_pattern_dataset(
        "PRODUCTION_PROFILE_SCALE", seed=20260924, fail_count=5560, rows=88, columns=128
    )
    payload = compact_analysis_payload(AnalysisEngine().analyze(dataset))

    assert any(
        pattern["soft_bin"] == 18 and pattern["pattern"] == "LOCALIZED_CLUSTER"
        for pattern in payload["patterns"]
    )
    assert any(
        pattern["soft_bin"] == 36 and pattern["pattern"] == "RING"
        for pattern in payload["patterns"]
    )
    assert (
        next(item["count"] for item in payload["top_fail_bins"] if item["soft_bin"] == 18) == 3180
    )
    assert next(item["count"] for item in payload["top_fail_bins"] if item["soft_bin"] == 36) == 25
    assert len(payload["patterns"]) <= 12
