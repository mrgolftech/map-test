from fastapi import APIRouter
from sqlalchemy import text

from app import __version__
from app.db.session import get_engine

router = APIRouter(tags=["system"])


@router.get("/health")
def health() -> dict[str, object]:
    with get_engine().connect() as connection:
        connection.execute(text("SELECT 1"))
    return {
        "data": {
            "status": "ok",
            "database": "ok",
        },
        "meta": {
            "version": __version__,
        },
    }
