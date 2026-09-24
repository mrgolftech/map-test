from app.core.config import get_settings
from fastapi.testclient import TestClient


def test_protected_api_requires_login(raw_client: TestClient):
    response = raw_client.get("/api/v1/dashboard")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_REQUIRED"

    health = raw_client.get("/api/v1/health")
    assert health.status_code == 200


def test_admin_login_session_and_logout(raw_client: TestClient):
    initial = raw_client.get("/api/v1/auth/session")
    assert initial.status_code == 200
    assert initial.json()["data"] == {
        "authenticated": False,
        "configured": True,
        "username": None,
    }

    bad = raw_client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "wrong-password"},
    )
    assert bad.status_code == 401
    assert bad.json()["error"]["code"] == "AUTH_INVALID_CREDENTIALS"

    login = raw_client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "test-admin-password"},
    )
    assert login.status_code == 200
    assert login.json()["data"]["authenticated"] is True
    assert login.json()["data"]["username"] == "admin"
    assert raw_client.get("/api/v1/dashboard").status_code == 200

    logout = raw_client.post("/api/v1/auth/logout")
    assert logout.status_code == 200
    assert logout.json()["data"]["authenticated"] is False
    assert raw_client.get("/api/v1/dashboard").status_code == 401


def test_unconfigured_admin_login_returns_503(raw_client: TestClient, monkeypatch):
    monkeypatch.setenv("ADMIN_PASSWORD", "")
    get_settings.cache_clear()

    response = raw_client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "anything"},
    )
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "ADMIN_AUTH_NOT_CONFIGURED"
