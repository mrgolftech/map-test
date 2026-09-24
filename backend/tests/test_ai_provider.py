import json

import httpx
import pytest
from app.ai.openai_compatible import OpenAICompatibleProvider
from app.core.errors import AppError


def test_openai_compatible_provider_uses_server_side_bearer_and_returns_content():
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["authorization"] = request.headers.get("authorization")
        captured["path"] = request.url.path
        captured["payload"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": '{"executive_summary":"ok"}'}}]},
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

    assert (
        provider.complete(
            system_prompt="system",
            user_prompt="user",
            max_tokens=8,
            temperature=0.0,
        )
        == "OK"
    )
    assert calls == 2


def test_truncated_completion_is_reported_before_json_parsing():
    provider = OpenAICompatibleProvider(
        base_url="https://example.test/v1",
        api_key="secret-key",
        model="demo-model",
        transport=httpx.MockTransport(
            lambda _request: httpx.Response(
                200,
                json={
                    "choices": [
                        {"finish_reason": "length", "message": {"content": '{"executive_summary":'}}
                    ]
                },
            )
        ),
    )

    with pytest.raises(AppError) as caught:
        provider.complete(system_prompt="system", user_prompt="user", max_tokens=8, temperature=0.0)

    assert caught.value.code == "LLM_INVALID_RESPONSE"
    assert caught.value.details == {"finish_reason": "length"}


@pytest.mark.parametrize(
    ("payload", "expected_code"),
    [
        ({"choices": []}, "LLM_INVALID_RESPONSE"),
        ({"choices": [{"message": {"content": ""}}]}, "LLM_INVALID_RESPONSE"),
        ({"choices": [{"message": {"content": None}}]}, "LLM_INVALID_RESPONSE"),
    ],
)
def test_empty_llm_responses_have_explicit_error(payload, expected_code):
    provider = OpenAICompatibleProvider(
        base_url="https://example.test/v1",
        api_key="secret-key",
        model="demo-model",
        transport=httpx.MockTransport(lambda _request: httpx.Response(200, json=payload)),
    )
    with pytest.raises(AppError) as caught:
        provider.complete(system_prompt="system", user_prompt="user", max_tokens=8, temperature=0.0)
    assert caught.value.code == expected_code


@pytest.mark.parametrize("status", [401, 404, 429, 500])
def test_upstream_http_failures_do_not_expose_credentials(status):
    provider = OpenAICompatibleProvider(
        base_url="https://example.test/v1",
        api_key="secret-key",
        model="demo-model",
        max_retries=0,
        transport=httpx.MockTransport(lambda _request: httpx.Response(status)),
    )
    with pytest.raises(AppError) as caught:
        provider.complete(system_prompt="system", user_prompt="user", max_tokens=8, temperature=0.0)
    assert caught.value.code == "LLM_UPSTREAM_ERROR"
    assert caught.value.details == {"upstream_status": status}
    assert "secret-key" not in str(caught.value)


def test_timeout_has_upstream_error_without_http_status():
    def timeout(_request):
        raise httpx.ReadTimeout("timed out")

    provider = OpenAICompatibleProvider(
        base_url="https://example.test/v1",
        api_key="secret-key",
        model="demo-model",
        max_retries=0,
        transport=httpx.MockTransport(timeout),
    )
    with pytest.raises(AppError) as caught:
        provider.complete(system_prompt="system", user_prompt="user", max_tokens=8, temperature=0.0)
    assert caught.value.code == "LLM_UPSTREAM_ERROR"
    assert caught.value.details == {"upstream_status": None}
