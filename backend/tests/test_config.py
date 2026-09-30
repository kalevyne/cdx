import pytest
from pydantic import ValidationError

from app.config import Settings


@pytest.mark.parametrize("name", ["BOX_CLIENT_ID", "BOX_CLIENT_SECRET", "SESSION_SECRET"])
def test_blank_required_settings_stop_startup(monkeypatch, name):
    monkeypatch.setenv(name, "")

    with pytest.raises(ValidationError, match=name.lower()):
        Settings(_env_file=None)


def test_postgres_urls_use_psycopg_driver(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgres://u:p@host/db")

    assert Settings(_env_file=None).database_url == "postgresql+psycopg://u:p@host/db"
