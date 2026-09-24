from fastapi import APIRouter, Request

from app.core.auth import authenticated_admin, verify_admin_credentials
from app.core.config import get_settings
from app.schemas.auth import AdminLoginRequest, AdminSession, AdminSessionResponse

router = APIRouter(prefix="/auth", tags=["auth"])


def _status(request: Request) -> AdminSession:
    settings = get_settings()
    username = authenticated_admin(request)
    return AdminSession(
        authenticated=username is not None,
        configured=settings.admin_auth_configured,
        username=username,
    )


@router.get("/session", response_model=AdminSessionResponse)
def session_status(request: Request) -> AdminSessionResponse:
    return AdminSessionResponse(data=_status(request))


@router.post("/login", response_model=AdminSessionResponse)
def login(request: Request, payload: AdminLoginRequest) -> AdminSessionResponse:
    username = verify_admin_credentials(payload.username, payload.password)
    request.session.clear()
    request.session["admin_username"] = username
    return AdminSessionResponse(data=_status(request))


@router.post("/logout", response_model=AdminSessionResponse)
def logout(request: Request) -> AdminSessionResponse:
    request.session.clear()
    return AdminSessionResponse(data=_status(request))
