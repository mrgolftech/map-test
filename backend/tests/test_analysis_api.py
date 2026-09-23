from app.simulator.patterns import generate_pattern_dataset


def test_analysis_api_returns_deterministic_summary(client):
    dataset = generate_pattern_dataset("EDGE", fail_count=48)

    response = client.post(
        "/api/v1/analysis",
        json={
            "dataset": dataset.model_dump(mode="json", by_alias=True),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_version"] == "1.0"
    assert payload["summary"]["tested_die"] == dataset.summary.tested_die
    assert payload["summary"]["fail_die"] == 48
    assert any(
        item["pattern"] == "EDGE" and item["soft_bin"] == 18
        for item in payload["patterns"]
    )


def test_analysis_api_accepts_threshold_override(client):
    dataset = generate_pattern_dataset("EDGE", fail_count=48)

    response = client.post(
        "/api/v1/analysis",
        json={
            "dataset": dataset.model_dump(mode="json", by_alias=True),
            "config": {
                "center_radius": 0.45,
                "edge_radius": 0.75,
                "neighbor_mode": 8,
                "enrichment_threshold": 1.3,
                "cluster_ratio_threshold": 0.25,
                "min_cluster_size": 4,
                "directional_enrichment_threshold": 1.5,
                "line_concentration_threshold": 0.35,
            },
        },
    )

    assert response.status_code == 200
    assert response.json()["config"]["enrichment_threshold"] == 1.3


def test_analysis_api_rejects_inconsistent_canonical_dataset(client):
    dataset = generate_pattern_dataset("EDGE", fail_count=48)
    payload = dataset.model_dump(mode="json", by_alias=True)
    payload["summary"]["tested_die"] -= 1

    response = client.post(
        "/api/v1/analysis",
        json={"dataset": payload},
    )

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "ANALYSIS_DATASET_INVALID"
    assert any(
        issue["code"] == "CANONICAL_TESTED_MISMATCH"
        for issue in error["details"]["issues"]
    )


def test_analysis_api_rejects_die_result_summary_mismatch(client):
    dataset = generate_pattern_dataset("EDGE", fail_count=48)
    payload = dataset.model_dump(mode="json", by_alias=True)
    pass_index = next(
        index
        for index, die in enumerate(dataset.dies)
        if die.result.value == "PASS"
    )
    payload["dies"][pass_index]["result"] = "FAIL"

    response = client.post(
        "/api/v1/analysis",
        json={"dataset": payload},
    )

    assert response.status_code == 422
    issues = response.json()["error"]["details"]["issues"]
    assert any(
        issue["code"] == "CANONICAL_RESULT_COUNT_MISMATCH"
        for issue in issues
    )
