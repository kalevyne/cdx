"""Alembic environment: points migrations at the app's own settings and models,
so there's exactly one place (DATABASE_URL) that decides which database is used."""

from alembic import context
from sqlalchemy import engine_from_config, pool

import app.models  # noqa: F401 — registers models on Base.metadata
from app.config import get_settings
from app.db import Base, UTCDateTime

config = context.config
config.set_main_option("sqlalchemy.url", get_settings().database_url)
target_metadata = Base.metadata


def _render_item(type_: str, obj: object, autogen_context: object) -> str | bool:
    # UTCDateTime's timezone handling is Python-side only; the column itself is a
    # plain timezone-aware DateTime, so migrations don't need to import app code.
    if type_ == "type" and isinstance(obj, UTCDateTime):
        return "sa.DateTime(timezone=True)"
    return False


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        render_as_batch=True,
        render_item=_render_item,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        # Batch mode lets ALTER TABLE-style migrations work on SQLite too.
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
            render_item=_render_item,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
