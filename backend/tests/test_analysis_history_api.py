from app.simulator.patterns import generate_pattern_dataset


def create_payload(
    pattern: str = "EDGE",
    *,
    product_id: str = "DEMO_HISTORY",
    lot_id: str = "LOT-H1",
    wafer_id: str = "01",
    fail_count: int = 48,
) -> dict:
    dataset = generate_pattern_dataset(pattern, fail_count=fail_count)
    dataset.metadata.product_id = product_id
    dataset.metadata.lot_id = lot_id
    dataset.metadata.wafer_id = wafer_id
    return {
        "dataset": dataset.model_dump(mode="json", by_alias=True),
        "sources": [],
        "validation_issues": [],
    }


def test_create_and_restore_analysis(client):
    response = client.post(
        "/api/v1/analyses",
        json=create_payload(),
    )

    assert response.status_code == 200
    payload = response.json()
    detail = payload["data"]
    analysis_id = detail["id"]

    assert detail["product_id"] == "DEMO_HISTORY"
    assert detail["lot_id"] == "LOT-H1"
    assert detail["wafer_id"] == "01"
    assert detail["main_fail_bin"] == 18
    assert detail["main_pattern"]
    assert detail["dataset"]["summary"]["fail_die"] == 48
    assert detail["analysis"]["schema_version"] == "1.0"

    restored = client.get(f"/api/v1/analyses/{analysis_id}")
    assert restored.status_code == 200
    restored_detail = restored.json()["data"]
    assert restored_detail["id"] == analysis_id
    assert restored_detail["dataset"] == detail["dataset"]
    assert restored_detail["analysis"] == detail["analysis"]


def test_list_analysis_returns_summary_without_full_dataset(client):
    for wafer_id in ("01", "02"):
        response = client.post(
            "/api/v1/analyses",
            json=create_payload(wafer_id=wafer_id),
        )
        assert response.status_code == 200

    response = client.get("/api/v1/analyses?page=1&page_size=20")
    assert response.status_code == 200
    payload = response.json()

    assert payload["meta"] == {
        "page": 1,
        "page_size": 20,
        "total": 2,
    }
    assert len(payload["data"]) == 2
    assert "dataset" not in payload["data"][0]
    assert "analysis" not in payload["data"][0]


def test_history_filters_product_lot_wafer_yield_bin_and_pattern(client):
    edge = client.post(
        "/api/v1/analyses",
        json=create_payload(
            "EDGE",
            product_id="P-A",
            lot_id="LOT-A",
            wafer_id="01",
            fail_count=48,
        ),
    )
    assert edge.status_code == 200
    edge_data = edge.json()["data"]

    center = client.post(
        "/api/v1/analyses",
        json=create_payload(
            "CENTER",
            product_id="P-B",
            lot_id="LOT-B",
            wafer_id="02",
            fail_count=64,
        ),
    )
    assert center.status_code == 200

    queries = [
        ("product_id=P-A", edge_data["id"]),
        ("lot_id=LOT-A", edge_data["id"]),
        ("wafer_id=01", edge_data["id"]),
        ("main_fail_bin=18", None),
        (f"pattern={edge_data['main_pattern']}", None),
        ("yield_min=0.90&yield_max=0.92", edge_data["id"]),
    ]

    for query, expected_id in queries:
        response = client.get(f"/api/v1/analyses?{query}")
        assert response.status_code == 200
        data = response.json()["data"]
        assert data
        if expected_id is not None:
            assert {item["id"] for item in data} == {expected_id}


def test_history_pagination(client):
    for index in range(3):
        response = client.post(
            "/api/v1/analyses",
            json=create_payload(wafer_id=f"{index + 1:02d}"),
        )
        assert response.status_code == 200

    page1 = client.get("/api/v1/analyses?page=1&page_size=2").json()
    page2 = client.get("/api/v1/analyses?page=2&page_size=2").json()

    assert page1["meta"]["total"] == 3
    assert len(page1["data"]) == 2
    assert len(page2["data"]) == 1


def test_delete_analysis(client):
    created = client.post(
        "/api/v1/analyses",
        json=create_payload(),
    ).json()["data"]

    response = client.delete(f"/api/v1/analyses/{created['id']}")
    assert response.status_code == 200
    assert response.json()["data"] == {
        "id": created["id"],
        "deleted": True,
    }

    missing = client.get(f"/api/v1/analyses/{created['id']}")
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "ANALYSIS_NOT_FOUND"


def test_create_analysis_recomputes_summary_server_side(client):
    payload = create_payload("EDGE")
    response = client.post("/api/v1/analyses", json=payload)

    assert response.status_code == 200
    data = response.json()["data"]
    assert any(
        pattern["pattern"] == "EDGE"
        for pattern in data["analysis"]["patterns"]
    )


def test_create_analysis_rejects_validation_error(client):
    payload = create_payload()
    payload["validation_issues"] = [
        {
            "severity": "ERROR",
            "stage": "PARSE",
            "code": "SYNTHETIC_BLOCKER",
            "message": "Synthetic blocking issue.",
            "source_file": "demo.PAT",
            "line": None,
            "row": None,
            "column": None,
            "details": None,
        }
    ]

    response = client.post("/api/v1/analyses", json=payload)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "ANALYSIS_DATASET_INVALID"
