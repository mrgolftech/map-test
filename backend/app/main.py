from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware
from starlette.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.errors import (
    AppError,
    app_error_handler,
    http_error_handler,
    unhandled_error_handler,
    validation_error_handler,
)


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
    )
    session_secret = settings.admin_session_secret or str(uuid4())
    app.add_middleware(
        SessionMiddleware,
        secret_key=session_secret,
        session_cookie="wafer_admin_session",
        max_age=settings.admin_session_max_age_seconds,
        same_site="lax",
        https_only=settings.admin_cookie_secure,
    )

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        request.state.request_id = request.headers.get(
            "x-request-id",
            str(uuid4()),
        )
        response = await call_next(request)
        response.headers["x-request-id"] = request.state.request_id
        return response

    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)
    app.include_router(api_router, prefix=settings.api_prefix)

    static_dir = Path(settings.static_dir)
    assets_dir = static_dir / "assets"
    index_file = static_dir / "index.html"

    if assets_dir.is_dir():
        app.mount(
            "/assets",
            StaticFiles(directory=assets_dir),
            name="assets",
        )

    if index_file.is_file():

        @app.get("/{full_path:path}", include_in_schema=False)
        def spa_fallback(full_path: str) -> FileResponse:
            requested = static_dir / full_path
            if (
                full_path
                and requested.is_file()
                and static_dir in requested.resolve().parents
            ):
                return FileResponse(requested)
            return FileResponse(index_file)

    return app


app = create_app()
