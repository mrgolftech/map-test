from app.simulator.patterns import generate_pattern_dataset


def persist(
    client,
    *,
    wafer_id: str,
    fail_count: int,
    pattern: str = "EDGE",
    product_id: str = "DEMO_LOT",
    lot_id: str = "LOT-COMPARE",
    flow_id: str = "CP1",
    tester: str = "SIM-LOT",
) -> dict:
    dataset = generate_pattern_dataset(pattern, fail_count=fail_count)
    dataset.metadata.product_id = product_id
    dataset.metadata.lot_id = lot_id
    dataset.metadata.wafer_id = wafer_id
    dataset.metadata.flow_id = flow_id
    dataset.metadata.tester = tester

    response = client.post(
        "/api/v1/analyses",
        json={
            "dataset": dataset.model_dump(mode="json", by_alias=True),
            "sources": [],
            "validation_issues": [],
        },
    )
    assert response.status_code == 200
    return response.json()["data"]


def test_compare_analyses_returns_yield_bin_spatial_and_preview(client):
    first = persist(client, wafer_id="01", fail_count=32)
    second = persist(client, wafer_id="02", fail_count=48)

    response = client.post(
        "/api/v1/analyses/compare",
        json={"analysis_ids": [first["id"], second["id"]]},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["product_id"] == "DEMO_LOT"
    assert data["lot_id"] == "LOT-COMPARE"
    assert data["compatibility"]["compatible"] is True
    assert data["yield_stats"]["wafer_count"] == 2
    assert data["yield_stats"]["average"] is not None
    assert len(data["yield_trend"]) == 2
    assert [item["wafer_id"] for item in data["highest_yield_wafers"]] == ["01"]
    assert [item["wafer_id"] for item in data["lowest_yield_wafers"]] == ["02"]
    assert data["highest_yield_wafers"][0]["yield"] > data["lowest_yield_wafers"][0]["yield"]

    bin18 = next(
        item for item in data["bin_aggregates"]
        if item["soft_bin"] == 18
    )
    assert bin18["wafer_count"] == 2
    assert len(bin18["trend"]) == 2
    assert bin18["mean_edge_enrichment"] is not None

    assert len(data["wafers"]) == 2
    preview = data["wafers"][0]["preview"]
    assert preview["rows"] == 24
    assert preview["columns"] == 32
    assert len(preview["map_rows"]) == 24
    assert all(len(row) == 32 for row in preview["map_rows"])


def test_compare_flags_product_mismatch_as_incompatible(client):
    first = persist(
        client,
        wafer_id="01",
        fail_count=32,
        product_id="PRODUCT-A",
    )
    second = persist(
        client,
        wafer_id="02",
        fail_count=32,
        product_id="PRODUCT-B",
    )

    response = client.post(
        "/api/v1/analyses/compare",
        json={"analysis_ids": [first["id"], second["id"]]},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["compatibility"]["compatible"] is False
    assert any(
        item["code"] == "PRODUCT_MISMATCH"
        and item["severity"] == "ERROR"
        for item in data["compatibility"]["issues"]
    )
    assert any(
        "descriptive only" in item
        for item in data["limitations"]
    )


def test_compare_surfaces_tester_difference_as_warning(client):
    first = persist(
        client,
        wafer_id="01",
        fail_count=32,
        tester="TESTER-A",
    )
    second = persist(
        client,
        wafer_id="02",
        fail_count=32,
        tester="TESTER-B",
    )

    response = client.post(
        "/api/v1/analyses/compare",
        json={"analysis_ids": [first["id"], second["id"]]},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["compatibility"]["compatible"] is True
    assert any(
        item["code"] == "TESTER_DIFFERENT"
        and item["severity"] == "WARNING"
        for item in data["compatibility"]["issues"]
    )


def test_iqr_yield_outlier_is_transparent_and_deterministic(client):
    ids = []
    for index, fail_count in enumerate((20, 22, 24, 26, 200), start=1):
        created = persist(
            client,
            wafer_id=f"{index:02d}",
            fail_count=fail_count,
        )
        ids.append(created["id"])

    response = client.post(
        "/api/v1/analyses/compare",
        json={"analysis_ids": ids},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    stats = data["yield_stats"]
    assert stats["iqr"] is not None
    assert stats["outlier_lower_bound"] is not None
    assert stats["outlier_upper_bound"] is not None

    outliers = [item for item in data["yield_trend"] if item["is_outlier"]]
    assert len(outliers) == 1
    assert outliers[0]["wafer_id"] == "05"
    assert "outside IQR bounds" in outliers[0]["outlier_reason"]


def test_fewer_than_four_wafers_do_not_force_outlier_flag(client):
    first = persist(client, wafer_id="01", fail_count=20)
    second = persist(client, wafer_id="02", fail_count=200)

    response = client.post(
        "/api/v1/analyses/compare",
        json={"analysis_ids": [first["id"], second["id"]]},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["yield_stats"]["outlier_lower_bound"] is None
    assert all(not item["is_outlier"] for item in data["yield_trend"])
    assert any(
        "requires at least 4 wafers" in item
        for item in data["limitations"]
    )


def test_compare_rejects_missing_and_duplicate_analysis_ids(client):
    created = persist(client, wafer_id="01", fail_count=32)

    duplicate = client.post(
        "/api/v1/analyses/compare",
        json={"analysis_ids": [created["id"], created["id"]]},
    )
    assert duplicate.status_code == 422
    assert duplicate.json()["error"]["code"] == "COMPARE_DUPLICATE_ANALYSIS_ID"

    missing = client.post(
        "/api/v1/analyses/compare",
        json={"analysis_ids": [created["id"], "missing-id"]},
    )
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "ANALYSIS_NOT_FOUND"


def test_lot_list_and_summary(client):
    persist(client, wafer_id="01", fail_count=32)
    persist(client, wafer_id="02", fail_count=48)

    lots = client.get("/api/v1/lots")
    assert lots.status_code == 200
    assert lots.json()["data"] == [
        {
            "product_id": "DEMO_LOT",
            "lot_id": "LOT-COMPARE",
            "wafer_count": 2,
            "average_yield": lots.json()["data"][0]["average_yield"],
            "minimum_yield": lots.json()["data"][0]["minimum_yield"],
            "maximum_yield": lots.json()["data"][0]["maximum_yield"],
            "last_created_at": lots.json()["data"][0]["last_created_at"],
        }
    ]

    summary = client.get(
        "/api/v1/lots/LOT-COMPARE/summary?product_id=DEMO_LOT"
    )
    assert summary.status_code == 200
    data = summary.json()["data"]
    assert len(data["wafers"]) == 2
    assert data["lot_id"] == "LOT-COMPARE"


def test_lot_id_requires_product_when_ambiguous(client):
    persist(
        client,
        wafer_id="01",
        fail_count=32,
        product_id="PRODUCT-A",
        lot_id="SHARED-LOT",
    )
    persist(
        client,
        wafer_id="02",
        fail_count=32,
        product_id="PRODUCT-B",
        lot_id="SHARED-LOT",
    )

    response = client.get("/api/v1/lots/SHARED-LOT/summary")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "LOT_AMBIGUOUS"


def test_yield_extrema_preserve_ties(client):
    first = persist(client, wafer_id="01", fail_count=32)
    second = persist(client, wafer_id="02", fail_count=32)
    third = persist(client, wafer_id="03", fail_count=80)

    response = client.post(
        "/api/v1/analyses/compare",
        json={"analysis_ids": [first["id"], second["id"], third["id"]]},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert {item["wafer_id"] for item in data["highest_yield_wafers"]} == {"01", "02"}
    assert [item["wafer_id"] for item in data["lowest_yield_wafers"]] == ["03"]
