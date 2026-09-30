"""create subsystem_metadata

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-30 20:13:44.267836
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | Sequence[str] | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "subsystem_metadata",
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("owner_name", sa.String(), nullable=True),
        sa.Column("stage", sa.String(), nullable=True),
        sa.Column("status_note", sa.Text(), nullable=True),
        sa.Column("updated_by", sa.String(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("slug"),
    )


def downgrade() -> None:
    op.drop_table("subsystem_metadata")
