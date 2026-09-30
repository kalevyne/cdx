"""add anchoring status to cdx_commits

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-30 20:07:12.875119
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | Sequence[str] | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("cdx_commits", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("anchor_status", sa.String(), server_default="pending", nullable=False)
        )
        batch_op.add_column(sa.Column("anchor_error", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("xrpl_network", sa.String(), nullable=True))
        batch_op.create_index(
            batch_op.f("ix_cdx_commits_anchor_status"), ["anchor_status"], unique=False
        )


def downgrade() -> None:
    with op.batch_alter_table("cdx_commits", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_cdx_commits_anchor_status"))
        batch_op.drop_column("xrpl_network")
        batch_op.drop_column("anchor_error")
        batch_op.drop_column("anchor_status")
