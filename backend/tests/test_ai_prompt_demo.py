from app.ai.prompt import SYSTEM_PROMPT, build_user_prompt, compact_analysis_payload
from app.analysis.engine import AnalysisEngine
from app.schemas.analysis import AnalysisConfig
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


def test_ai_prompt_explains_spatial_metrics_and_sends_effective_thresholds():
    dataset = generate_pattern_dataset(
        "EDGE", seed=20260924, fail_count=48, rows=24, columns=32
    )
    config = AnalysisConfig(
        center_radius=0.4,
        edge_radius=0.8,
        enrichment_threshold=1.7,
        neighbor_mode=4,
        cluster_ratio_threshold=0.3,
        min_cluster_size=5,
        directional_enrichment_threshold=1.8,
        line_concentration_threshold=0.4,
    )
    summary = AnalysisEngine().analyze(dataset, config=config)

    payload = compact_analysis_payload(summary)
    prompt = build_user_prompt(summary)

    assert payload["analysis_config"] == config.model_dump(mode="json")
    assert '"analysis_config":{"center_radius":0.4' in prompt
    assert "enrichment =" in SYSTEM_PROMPT
    assert "RANDOM means no implemented deterministic pattern threshold was met" in SYSTEM_PROMPT
    assert "not calibrated" in SYSTEM_PROMPT
    assert "validated probability" in SYSTEM_PROMPT
    assert "physical wafer dimensions" in SYSTEM_PROMPT
