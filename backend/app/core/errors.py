from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: Any = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "unknown")


def error_payload(
    request: Request,
    code: str,
    message: str,
    details: Any = None,
) -> dict[str, Any]:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details,
            "request_id": _request_id(request),
        }
    }


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload(request, exc.code, exc.message, exc.details),
    )


async def http_error_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload(
            request,
            f"HTTP_{exc.status_code}",
            str(exc.detail),
        ),
    )


async def validation_error_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    issues = exc.errors()
    sensitive_path = (
        request.url.path.startswith("/api/v1/settings/llm")
        or request.url.path == "/api/v1/ai/test"
        or request.url.path == "/api/v1/auth/login"
    )
    if sensitive_path:
        # Pydantic may include submitted values in validation errors; never echo credentials.
        issues = [
            {key: value for key, value in issue.items() if key in {"loc", "type", "msg"}}
            for issue in issues
        ]
    return JSONResponse(
        status_code=422,
        content=error_payload(
            request,
            "REQUEST_VALIDATION_ERROR",
            "Request validation failed.",
            issues,
        ),
    )


async def unhandled_error_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content=error_payload(
            request,
            "INTERNAL_ERROR",
            "Internal server error.",
        ),
    )
