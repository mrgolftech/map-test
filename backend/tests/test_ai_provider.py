import json

import httpx
from app.ai.openai_compatible import OpenAICompatibleProvider


def test_openai_compatible_provider_uses_server_side_bearer_and_returns_content():
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["authorization"] = request.headers.get("authorization")
        captured["path"] = request.url.path
        captured["payload"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "choices": [
                    {"message": {"content": '{"executive_summary":"ok"}'}}
                ]
            },
        )

    provider = OpenAICompatibleProvider(
        base_url="https://example.test/v1",
        api_key="secret-key",
        model="demo-model",
        transport=httpx.MockTransport(handler),
        sleep=lambda _seconds: None,
    )

    content = provider.complete(
        system_prompt="system",
        user_prompt="user",
        max_tokens=128,
        temperature=0.2,
    )

    assert content == '{"executive_summary":"ok"}'
    assert captured["authorization"] == "Bearer secret-key"
    assert captured["path"] == "/v1/chat/completions"
    assert captured["payload"]["model"] == "demo-model"


def test_openai_compatible_provider_retries_transient_failure():
    calls = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(503, json={"error": "temporary"})
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "OK"}}]},
        )

    provider = OpenAICompatibleProvider(
        base_url="https://example.test/v1",
        api_key="secret-key",
        model="demo-model",
        max_retries=1,
        transport=httpx.MockTransport(handler),
        sleep=lambda _seconds: None,
    )

    assert provider.complete(
        system_prompt="system",
        user_prompt="user",
        max_tokens=8,
        temperature=0.0,
    ) == "OK"
    assert calls == 2
