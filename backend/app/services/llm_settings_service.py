"""Server-side LLM settings, guarded by an administrator token."""

import base64
import hashlib
import hmac
import ipaddress
from datetime import UTC, datetime
from urllib.parse import urlsplit

import httpx
from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy.orm import Session

from app.ai.openai_compatible import OpenAICompatibleProvider
from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.db.models import LLMRuntimeConfig
from app.schemas.ai import LLMConfigSaveRequest, LLMConfigStatus, LLMConnectionResult


def validate_base_url(value: str) -> str:
    url = value.strip().rstrip("/")
    parts = urlsplit(url)
    host = parts.hostname
    if (
        parts.scheme not in {"http", "https"}
        or not host
        or parts.username
        or parts.password
        or parts.query
        or parts.fragment
        or host.lower() == "localhost"
        or host.lower().endswith(".localhost")
    ):
        raise AppError("LLM_URL_INVALID", "A valid HTTP(S) API base URL is required.", 422)
    try:
        _ = parts.port
    except ValueError as exc:
        raise AppError("LLM_URL_INVALID", "A valid API port is required.", 422) from exc
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        if address.is_loopback or address.is_link_local or address.is_unspecified:
            raise AppError("LLM_URL_INVALID", "Local and link-local API URLs are not allowed.", 422)
    if parts.path.endswith("/chat/completions") or parts.path.endswith("/models"):
        raise AppError("LLM_URL_INVALID", "Use the API base URL, such as /v1.", 422)
    return url


class LLMSettingsService:
    def __init__(self, session: Session, settings: Settings | None = None) -> None:
        self.session = session
        self.settings = settings or get_settings()

    def _secret(self) -> str:
        token = self.settings.llm_settings_admin_token
        if len(token) < 24:
            raise AppError(
                "LLM_SETTINGS_DISABLED",
                "Set LLM_SETTINGS_ADMIN_TOKEN (at least 24 characters) on the server.",
                503,
            )
        return token

    def authorize(self, supplied: str | None) -> None:
        secret = self._secret()
        if not supplied or not hmac.compare_digest(secret, supplied):
            raise AppError("LLM_SETTINGS_FORBIDDEN", "Administrator token is invalid.", 403)

    def _fernet(self) -> Fernet:
        key = base64.urlsafe_b64encode(hashlib.sha256(self._secret().encode()).digest())
        return Fernet(key)

    def effective_settings(self) -> Settings:
        record = self.session.get(LLMRuntimeConfig, 1)
        if record is None:
            return self.settings
        try:
            api_key = self._fernet().decrypt(record.encrypted_api_key.encode()).decode()
        except (InvalidToken, UnicodeDecodeError) as exc:
            raise AppError(
                "LLM_SETTINGS_UNREADABLE",
                "Saved LLM settings cannot be decrypted with the current administrator token.",
                503,
            ) from exc
        return self.settings.model_copy(
            update={
                "llm_base_url": record.base_url,
                "llm_model": record.model,
                "llm_api_key": api_key,
            }
        )

    def status(self) -> LLMConfigStatus:
        active = self.effective_settings()
        return LLMConfigStatus(
            configured=bool(active.llm_base_url and active.llm_model and active.llm_api_key),
            base_url=active.llm_base_url or None,
            model=active.llm_model or None,
            api_key_configured=bool(active.llm_api_key),
        )

    def credentials(self, base_url: str, api_key: str | None) -> tuple[str, str]:
        url = validate_base_url(base_url)
        active = self.effective_settings()
        key = (
            api_key.strip()
            if api_key
            else (active.llm_api_key if url == active.llm_base_url.rstrip("/") else "")
        )
        if not key:
            raise AppError("LLM_NOT_CONFIGURED", "Enter an API key before testing.", 422)
        return url, key

    def save(self, request: LLMConfigSaveRequest) -> LLMConfigStatus:
        url, key = self.credentials(request.base_url, request.api_key)
        model = request.model.strip()
        if not model:
            raise AppError("LLM_MODEL_INVALID", "Select a model.", 422)
        record = self.session.get(LLMRuntimeConfig, 1)
        if record is None:
            record = LLMRuntimeConfig(id=1)
            self.session.add(record)
        record.base_url = url
        record.model = model
        record.encrypted_api_key = self._fernet().encrypt(key.encode()).decode()
        record.updated_at = datetime.now(UTC)
        self.session.commit()
        return self.status()

    def list_models(self, base_url: str, api_key: str | None) -> list[str]:
        url, key = self.credentials(base_url, api_key)
        try:
            with httpx.Client(timeout=15, follow_redirects=False) as client:
                with client.stream(
                    "GET", f"{url}/models", headers={"Authorization": f"Bearer {key}"}
                ) as response:
                    response.raise_for_status()
                    chunks: list[bytes] = []
                    size = 0
                    for chunk in response.iter_bytes():
                        size += len(chunk)
                        if size > 1024 * 1024:
                            raise AppError("LLM_INVALID_RESPONSE", "Model list is too large.", 502)
                        chunks.append(chunk)
            payload = httpx.Response(200, content=b"".join(chunks)).json()
        except httpx.HTTPStatusError as exc:
            raise AppError(
                "LLM_UPSTREAM_ERROR",
                "Could not fetch the model list.",
                502,
                {"upstream_status": exc.response.status_code},
            ) from exc
        except httpx.HTTPError as exc:
            raise AppError("LLM_UPSTREAM_ERROR", "Could not fetch the model list.", 502) from exc
        except ValueError as exc:
            raise AppError("LLM_INVALID_RESPONSE", "Model list is not valid JSON.", 502) from exc
        data = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(data, list):
            raise AppError("LLM_INVALID_RESPONSE", "Model list response has no data array.", 502)
        models = sorted(
            {
                item["id"]
                for item in data
                if isinstance(item, dict) and isinstance(item.get("id"), str) and item["id"]
            }
        )
        if not models or len(models) > 500:
            raise AppError("LLM_INVALID_RESPONSE", "Model list is empty or too large.", 502)
        return models

    def test_connection(
        self, base_url: str | None = None, model: str | None = None, api_key: str | None = None
    ) -> LLMConnectionResult:
        active = self.effective_settings()
        url, key = self.credentials(base_url or active.llm_base_url, api_key)
        selected = (model or active.llm_model).strip()
        if not selected:
            raise AppError("LLM_MODEL_INVALID", "Select a model before testing.", 422)
        OpenAICompatibleProvider(
            base_url=url,
            api_key=key,
            model=selected,
            timeout_seconds=active.llm_timeout_seconds,
            max_retries=active.llm_max_retries,
        ).test_connection()
        return LLMConnectionResult(ok=True, model=selected, message="LLM connection succeeded.")
