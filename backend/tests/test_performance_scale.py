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


def test_analysis_handles_more_than_twenty_thousand_dies():
    dataset = generate_pattern_dataset(
        "EDGE",
        seed=20260924,
        fail_count=1200,
        rows=180,
        columns=180,
    )

    assert dataset.summary.tested_die > 20_000

    result = AnalysisEngine().analyze(dataset)

    assert result.summary.tested_die == dataset.summary.tested_die
    assert result.summary.fail_die == 1200
    assert any(item.pattern == "EDGE" for item in result.patterns)


def test_compare_handles_twenty_five_wafers(client):
    analysis_ids: list[str] = []
    for index in range(25):
        dataset = generate_pattern_dataset(
            "EDGE",
            seed=20260924 + index,
            fail_count=24 + index,
        )
        dataset.metadata.product_id = "SCALE_PRODUCT"
        dataset.metadata.lot_id = "SCALE_LOT"
        dataset.metadata.wafer_id = f"{index + 1:02d}"
        response = client.post(
            "/api/v1/analyses",
            json={
                "dataset": dataset.model_dump(mode="json", by_alias=True),
                "sources": [],
                "validation_issues": [],
            },
        )
        assert response.status_code == 200
        analysis_ids.append(response.json()["data"]["id"])

    response = client.post(
        "/api/v1/analyses/compare",
        json={"analysis_ids": analysis_ids},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["yield_stats"]["wafer_count"] == 25
    assert len(data["yield_trend"]) == 25
    assert len(data["wafers"]) == 25
    assert sum(item["preview"] is not None for item in data["wafers"]) == 12
