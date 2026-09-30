from box_sdk_gen import AccessToken, FileTokenStorage

from app.config import get_settings
from app.db import get_sessionmaker, run_migrations
from app.services.box_token_storage import DatabaseTokenStorage, make_backend_token_storage


def test_database_token_storage_round_trips():
    run_migrations()
    storage = DatabaseTokenStorage(get_sessionmaker())
    assert storage.get() is None

    storage.store(AccessToken(access_token="a1", refresh_token="r1", expires_in=3600))
    storage.store(AccessToken(access_token="a2", refresh_token="r2", expires_in=3600))

    token = storage.get()
    assert (token.access_token, token.refresh_token) == ("a2", "r2")

    storage.clear()
    assert storage.get() is None


def test_token_storage_follows_setting(monkeypatch):
    assert isinstance(make_backend_token_storage(get_settings()), FileTokenStorage)

    monkeypatch.setenv("BOX_TOKEN_STORAGE", "database")
    get_settings.cache_clear()

    assert isinstance(make_backend_token_storage(get_settings()), DatabaseTokenStorage)
