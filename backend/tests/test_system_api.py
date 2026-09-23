def test_health(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["data"] == {
        "status": "ok",
        "database": "ok",
    }
    assert payload["meta"]["version"] == "0.1.0"
    assert response.headers["x-request-id"]


def test_version(client):
    response = client.get("/api/v1/version")
    assert response.status_code == 200
    assert response.json()["data"]["version"] == "0.1.0"


def test_error_contract_for_unknown_route(client):
    response = client.get("/api/v1/not-found")
    assert response.status_code == 404
    error = response.json()["error"]
    assert error["code"] == "HTTP_404"
    assert error["request_id"]
