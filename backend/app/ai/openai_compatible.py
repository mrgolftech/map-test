import time
from collections.abc import Callable

import httpx
from app.ai.provider import AIProvider
from app.core.errors import AppError


class OpenAICompatibleProvider(AIProvider):
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: float = 45.0,
        max_retries: int = 2,
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._timeout_seconds = timeout_seconds
        self._max_retries = max_retries
        self._transport = transport
        self._sleep = sleep

    @property
    def _endpoint(self) -> str:
        return f"{self._base_url}/chat/completions"

    def _request(self, payload: dict[str, object]) -> dict[str, object]:
        last_error: Exception | None = None
        for attempt in range(self._max_retries + 1):
            try:
                with httpx.Client(
                    timeout=self._timeout_seconds,
                    transport=self._transport,
                ) as client:
                    response = client.post(
                        self._endpoint,
                        headers={
                            "Authorization": f"Bearer {self._api_key}",
                            "Content-Type": "application/json",
                        },
                        json=payload,
                    )
                if response.status_code == 429 or response.status_code >= 500:
                    if attempt < self._max_retries:
                        self._sleep(0.25 * (attempt + 1))
                        continue
                response.raise_for_status()
                value = response.json()
                if not isinstance(value, dict):
                    raise ValueError("LLM response must be a JSON object.")
                return value
            except (httpx.HTTPError, ValueError) as exc:
                last_error = exc
                if attempt < self._max_retries:
                    self._sleep(0.25 * (attempt + 1))
                    continue
                break

        status_code = (
            last_error.response.status_code
            if isinstance(last_error, httpx.HTTPStatusError)
            else None
        )
        raise AppError(
            code="LLM_UPSTREAM_ERROR",
            message="LLM provider request failed.",
            status_code=502,
            details={"upstream_status": status_code},
        )

    def complete(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int,
        temperature: float,
    ) -> str:
        payload: dict[str, object] = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        response = self._request(payload)
        choices = response.get("choices")
        if not isinstance(choices, list) or not choices:
            raise AppError(
                code="LLM_INVALID_RESPONSE",
                message="LLM response did not contain choices.",
                status_code=502,
            )
        first = choices[0]
        if not isinstance(first, dict):
            raise AppError(
                code="LLM_INVALID_RESPONSE",
                message="LLM response choice was invalid.",
                status_code=502,
            )
        message = first.get("message")
        if not isinstance(message, dict):
            raise AppError(
                code="LLM_INVALID_RESPONSE",
                message="LLM response did not contain a message.",
                status_code=502,
            )
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise AppError(
                code="LLM_INVALID_RESPONSE",
                message="LLM response content was empty.",
                status_code=502,
            )
        return content

    def test_connection(self) -> None:
        self.complete(
            system_prompt="You are a connectivity check.",
            user_prompt="Reply with OK.",
            max_tokens=8,
            temperature=0.0,
        )
