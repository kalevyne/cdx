"""create cdx_commits

Revision ID: 0001
Revises:
Create Date: 2026-09-30 19:47:12.696632
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "cdx_commits",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("box_file_id", sa.String(), nullable=False),
        sa.Column("box_file_version", sa.String(), nullable=True),
        sa.Column("box_folder_id", sa.String(), nullable=False),
        sa.Column("file_name", sa.String(), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("sha256_hash", sa.String(length=64), nullable=False),
        sa.Column("design_review_box_file_id", sa.String(), nullable=True),
        sa.Column("design_review_sha256_hash", sa.String(length=64), nullable=True),
        sa.Column("subsystem", sa.String(), nullable=True),
        sa.Column("author_box_user_id", sa.String(), nullable=False),
        sa.Column("author_name", sa.String(), nullable=False),
        sa.Column("message", sa.String(), nullable=False),
        sa.Column("xrpl_tx_hash", sa.String(), nullable=True),
        sa.Column("xrpl_ledger_index", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("anchored_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("cdx_commits", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_cdx_commits_box_file_id"), ["box_file_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_cdx_commits_box_folder_id"), ["box_folder_id"], unique=False
        )
        batch_op.create_index(batch_op.f("ix_cdx_commits_subsystem"), ["subsystem"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("cdx_commits", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_cdx_commits_subsystem"))
        batch_op.drop_index(batch_op.f("ix_cdx_commits_box_folder_id"))
        batch_op.drop_index(batch_op.f("ix_cdx_commits_box_file_id"))

    op.drop_table("cdx_commits")
