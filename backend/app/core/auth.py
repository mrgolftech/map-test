import secrets

from fastapi import Request

from app.core.config import Settings, get_settings
from app.core.errors import AppError


def _configured(settings: Settings) -> None:
    if not settings.admin_auth_configured:
        raise AppError(
            "ADMIN_AUTH_NOT_CONFIGURED",
            "Administrator login is not configured on the server.",
            503,
        )


def verify_admin_credentials(username: str, password: str) -> str:
    settings = get_settings()
    _configured(settings)
    expected_username = settings.admin_username.strip()
    username_ok = secrets.compare_digest(username.strip(), expected_username)
    password_ok = secrets.compare_digest(password, settings.admin_password)
    if not (username_ok and password_ok):
        raise AppError(
            "AUTH_INVALID_CREDENTIALS",
            "Administrator username or password is invalid.",
            401,
        )
    return expected_username


def authenticated_admin(request: Request) -> str | None:
    settings = get_settings()
    if not settings.admin_auth_configured:
        return None
    value = request.session.get("admin_username")
    if not isinstance(value, str):
        return None
    expected = settings.admin_username.strip()
    if not secrets.compare_digest(value, expected):
        return None
    return expected


def require_admin(request: Request) -> str:
    settings = get_settings()
    _configured(settings)
    username = authenticated_admin(request)
    if username is None:
        raise AppError(
            "AUTH_REQUIRED",
            "Administrator sign-in is required.",
            401,
        )
    return username
