import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite:///./.test-data/test.db"
os.environ["STATIC_DIR"] = "./.missing-static"

from app.core.config import get_settings  # noqa: E402
from app.db import session as db_session  # noqa: E402
from app.main import create_app  # noqa: E402


@pytest.fixture(autouse=True)
def reset_state(tmp_path: Path):
    os.environ["DATABASE_URL"] = f"sqlite:///{tmp_path / 'test.db'}"
    get_settings.cache_clear()
    db_session._engine = None
    yield
    if db_session._engine is not None:
        db_session._engine.dispose()
        db_session._engine = None
    get_settings.cache_clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())
