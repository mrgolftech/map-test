def test_generate_demo_wafer(client):
    response = client.post(
        "/api/v1/simulator/wafer",
        json={
            "pattern": "CENTER",
            "fail_count": 40,
            "seed": 123,
            "product_id": "DEMO",
            "lot_id": "LOT-DEMO",
            "wafer_id": "07",
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["metadata"]["product_id"] == "DEMO"
    assert data["metadata"]["lot_id"] == "LOT-DEMO"
    assert data["metadata"]["wafer_id"] == "07"
    assert data["summary"]["fail_die"] == 40
    assert data["summary"]["tested_die"] == len(data["dies"])
    assert response.json()["meta"]["pattern"] == "CENTER"


def test_demo_edge_drift_lot_is_compatible_and_has_designed_outlier(client):
    response = client.post(
        "/api/v1/simulator/lot",
        json={"scenario": "EDGE_DRIFT", "seed": 20260924},
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["scenario"] == "EDGE_DRIFT"
    assert len(payload["datasets"]) == 5
    assert [item["metadata"]["wafer_id"] for item in payload["datasets"]] == [
        "01",
        "02",
        "03",
        "04",
        "05",
    ]
    assert [item["summary"]["fail_die"] for item in payload["datasets"]] == [
        20,
        22,
        24,
        26,
        200,
    ]
    assert {item["metadata"]["lot_id"] for item in payload["datasets"]} == {
        "DEMO-EDGE_DRIFT"
    }


def test_simulator_rejects_impossible_fail_count(client):
    response = client.post(
        "/api/v1/simulator/wafer",
        json={
            "pattern": "EDGE",
            "rows": 8,
            "columns": 8,
            "fail_count": 100,
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "SIMULATOR_INVALID_CONFIG"
