from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from app.core.config import get_settings

_engine: Engine | None = None


def _ensure_sqlite_parent(database_url: str) -> None:
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        return
    database_path = database_url.removeprefix(prefix)
    if database_path == ":memory:":
        return
    Path(database_path).expanduser().resolve().parent.mkdir(
        parents=True,
        exist_ok=True,
    )


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        database_url = get_settings().database_url
        _ensure_sqlite_parent(database_url)
        connect_args = (
            {"check_same_thread": False}
            if database_url.startswith("sqlite")
            else {}
        )
        _engine = create_engine(
            database_url,
            connect_args=connect_args,
            pool_pre_ping=True,
        )
    return _engine
