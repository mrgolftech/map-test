import json

import app.services.ai_analysis_service as ai_service_module
import app.services.llm_settings_service as settings_module
import httpx
from app.core.config import get_settings
from app.db.session import get_session
from app.services.llm_settings_service import LLMSettingsService
from app.simulator.patterns import generate_pattern_dataset

TOKEN = "settings-admin-token-with-enough-length"
CONFIG = {
    "base_url": "https://models.example.test/v1",
    "model": "selected-model",
    "api_key": "private-upstream-api-key",
}


def enable_encryption_secret(monkeypatch):
    monkeypatch.setenv("LLM_SETTINGS_ADMIN_TOKEN", TOKEN)
    get_settings.cache_clear()


def test_settings_encrypt_persisted_key(client, monkeypatch):
    enable_encryption_secret(monkeypatch)

    saved = client.put("/api/v1/settings/llm", json=CONFIG)
    assert saved.status_code == 200, saved.text
    assert saved.json()["data"] == {
        "configured": True,
        "base_url": CONFIG["base_url"],
        "model": CONFIG["model"],
        "api_key_configured": True,
    }
    assert CONFIG["api_key"] not in saved.text
    assert CONFIG["api_key"] not in client.get("/api/v1/settings/llm").text

    session = next(get_session())
    try:
        from app.db.models import LLMRuntimeConfig

        ciphertext = session.get(LLMRuntimeConfig, 1).encrypted_api_key
        assert CONFIG["api_key"] not in ciphertext
        assert LLMSettingsService(session).effective_settings().llm_api_key == CONFIG["api_key"]
    finally:
        session.close()

    dataset = generate_pattern_dataset("EDGE", fail_count=48)
    saved_analysis = client.post(
        "/api/v1/analyses",
        json={
            "dataset": dataset.model_dump(mode="json", by_alias=True),
            "sources": [],
            "validation_issues": [],
        },
    )
    assert saved_analysis.status_code == 200
    analysis_id = saved_analysis.json()["data"]["id"]

    class FakeProvider:
        def complete(self, **_kwargs):
            return json.dumps(
                {
                    "executive_summary": "Deterministic summary reviewed.",
                    "key_findings": [],
                    "spatial_patterns": [],
                    "possible_causes": [],
                    "recommended_checks": [],
                    "confidence": 0.5,
                    "limitations": [],
                }
            )

    monkeypatch.setattr(ai_service_module, "create_provider", lambda _settings: FakeProvider())
    analyzed = client.post(f"/api/v1/analyses/{analysis_id}/ai")
    assert analyzed.status_code == 200, analyzed.text
    assert analyzed.json()["data"]["model"] == "selected-model"


def test_models_and_candidate_connection_use_selected_key_without_saving(client, monkeypatch):
    enable_encryption_secret(monkeypatch)
    seen = []

    def respond(request):
        seen.append(request)
        if request.url.path.endswith("/models"):
            return httpx.Response(200, json={"data": [{"id": "beta"}, {"id": "alpha"}]})
        return httpx.Response(
            200, json={"choices": [{"message": {"content": "OK"}, "finish_reason": "stop"}]}
        )

    transport = httpx.MockTransport(respond)
    original_client = httpx.Client
    monkeypatch.setattr(
        settings_module.httpx,
        "Client",
        lambda **kwargs: original_client(**{**kwargs, "transport": transport}),
    )
    candidate = {"base_url": CONFIG["base_url"], "api_key": CONFIG["api_key"]}
    models = client.post("/api/v1/settings/llm/models", json=candidate)
    assert models.status_code == 200, models.text
    assert models.json()["data"] == ["alpha", "beta"]
    connected = client.post("/api/v1/settings/llm/test", json=CONFIG)
    assert connected.status_code == 200, connected.text
    assert connected.json()["data"]["model"] == "selected-model"
    assert [request.url.path for request in seen] == ["/v1/models", "/v1/chat/completions"]
    assert all(
        request.headers["Authorization"] == "Bearer private-upstream-api-key" for request in seen
    )
    assert client.get("/api/v1/settings/llm").json()["data"]["configured"] is False


def test_models_invalid_response_and_upstream_error(client, monkeypatch):
    enable_encryption_secret(monkeypatch)
    original_client = httpx.Client
    candidate = {"base_url": CONFIG["base_url"], "api_key": CONFIG["api_key"]}
    for upstream, expected in [
        (httpx.Response(200, content=b"not json"), "LLM_INVALID_RESPONSE"),
        (httpx.Response(200, json={"data": []}), "LLM_INVALID_RESPONSE"),
        (httpx.Response(401), "LLM_UPSTREAM_ERROR"),
    ]:
        transport = httpx.MockTransport(lambda _request, value=upstream: value)

        def make_client(*, chosen_transport):
            return lambda **kwargs: original_client(**{**kwargs, "transport": chosen_transport})

        monkeypatch.setattr(
            settings_module.httpx,
            "Client",
            make_client(chosen_transport=transport),
        )
        response = client.post("/api/v1/settings/llm/models", json=candidate)
        assert response.status_code == 502
        assert response.json()["error"]["code"] == expected
    assert client.get("/api/v1/settings/llm").status_code == 200


def test_invalid_api_url_rejected(client, monkeypatch):
    enable_encryption_secret(monkeypatch)
    for value in [
        "http://localhost:9000/v1",
        "http://127.0.0.1/v1",
        "https://models.example.test:99999/v1",
    ]:
        response = client.put(
            "/api/v1/settings/llm", json={**CONFIG, "base_url": value}
        )
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "LLM_URL_INVALID"


def test_invalid_key_validation_does_not_echo_key(client, monkeypatch):
    enable_encryption_secret(monkeypatch)
    invalid_key = "sensitive-" + "x" * 4096
    response = client.put(
        "/api/v1/settings/llm",
        json={**CONFIG, "api_key": invalid_key},
    )
    assert response.status_code == 422
    assert invalid_key not in response.text
