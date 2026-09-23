from app.simulator.patterns import generate_pattern_dataset


def persist(client, wafer_id: str, fail_count: int):
    dataset = generate_pattern_dataset("EDGE", fail_count=fail_count)
    dataset.metadata.product_id = "DASH"
    dataset.metadata.lot_id = "LOT-DASH"
    dataset.metadata.wafer_id = wafer_id
    response = client.post(
        "/api/v1/analyses",
        json={
            "dataset": dataset.model_dump(mode="json", by_alias=True),
            "sources": [],
            "validation_issues": [],
        },
    )
    assert response.status_code == 200


def test_dashboard_summary_tracks_persisted_analysis(client):
    empty = client.get("/api/v1/dashboard/summary")
    assert empty.status_code == 200
    assert empty.json()["data"]["analysis_count"] == 0

    persist(client, "01", 20)
    persist(client, "02", 40)

    response = client.get("/api/v1/dashboard/summary")
    assert response.status_code == 200
    data = response.json()["data"]

    assert data["analysis_count"] == 2
    assert data["lot_count"] == 1
    assert data["average_yield"] is not None
    assert data["minimum_yield"] <= data["maximum_yield"]
    assert data["latest_created_at"] is not None
