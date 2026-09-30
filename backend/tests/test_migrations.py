from alembic.autogenerate import compare_metadata
from alembic.runtime.migration import MigrationContext

import app.models  # noqa: F401 — registers models on Base.metadata
from app.db import Base, get_engine, run_migrations


def test_migrations_match_models():
    """Fails when a model changes without a matching Alembic migration.
    Fix: `alembic revision --autogenerate -m "..."` (see alembic.ini)."""
    run_migrations()

    with get_engine().connect() as connection:
        diff = compare_metadata(MigrationContext.configure(connection), Base.metadata)

    assert diff == []


def test_migrations_are_idempotent():
    run_migrations()
    run_migrations()
