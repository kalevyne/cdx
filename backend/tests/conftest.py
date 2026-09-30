import pytest


@pytest.fixture(autouse=True)
def _box_env(monkeypatch):
    monkeypatch.setenv("BOX_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("BOX_CLIENT_SECRET", "test-client-secret")
    monkeypatch.setenv("BOX_DASHBOARD_ROOT_FOLDER_ID", "0")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")

    from app.config import get_settings
    from app.db import get_engine

    get_settings.cache_clear()
    get_engine.cache_clear()
    yield
    get_settings.cache_clear()
    get_engine.cache_clear()
