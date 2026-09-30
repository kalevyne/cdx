import os
from unittest.mock import MagicMock

import pytest
from box_sdk_gen import BoxAPIError
from fastapi.testclient import TestClient

# Set before any test module imports app.main, which reads settings at import time.
os.environ.update(
    {
        "BOX_CLIENT_ID": "test-client-id",
        "BOX_CLIENT_SECRET": "test-client-secret",
        "BOX_DASHBOARD_ROOT_FOLDER_ID": "0",
        "SESSION_SECRET": "test-session-secret",
        "FRONTEND_URL": "http://frontend.test",
    }
)

from app.auth import require_user  # noqa: E402
from app.schemas.auth import SessionUser  # noqa: E402

TEST_USER = SessionUser(box_user_id="u1", name="Ada Engineer", login="ada@berkeley.edu")


def box_api_error(status_code: int) -> BoxAPIError:
    return BoxAPIError(
        request_info=MagicMock(), response_info=MagicMock(status_code=status_code), message="x"
    )


@pytest.fixture(autouse=True)
def _isolated_settings(tmp_path, monkeypatch):
    # A fresh SQLite file per test; the app's lifespan migrates it on startup.
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")

    from app.config import get_settings
    from app.db import get_engine, get_sessionmaker

    caches = (get_settings, get_engine, get_sessionmaker)
    for cached in caches:
        cached.cache_clear()
    yield
    for cached in caches:
        cached.cache_clear()


@pytest.fixture
def box_service_mock():
    return MagicMock()


@pytest.fixture
def client(box_service_mock):
    """A TestClient logged in as TEST_USER, with Box mocked out."""
    from app.main import app
    from app.services.box_client import get_box_service

    app.dependency_overrides[get_box_service] = lambda: box_service_mock
    app.dependency_overrides[require_user] = lambda: TEST_USER
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def anonymous_client():
    """A TestClient with no logged-in engineer."""
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
