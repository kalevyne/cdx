from datetime import datetime
from enum import StrEnum

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base, UTCDateTime, utcnow


class AnchorStatus(StrEnum):
    PENDING = "pending"  # Waiting to be anchored (or XRPL isn't configured yet).
    ANCHORED = "anchored"  # Hash is in a validated XRPL transaction.
    FAILED = "failed"  # The last attempt failed; see anchor_error. Retryable.


class CdxCommit(Base):
    """A CDX commit — an engineer's file upload through the dashboard, hashed and
    anchored to XRPL. Not a git commit; see CLAUDE.md on that distinction."""

    __tablename__ = "cdx_commits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # The committed file, as stored in Box.
    box_file_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    box_file_version: Mapped[str | None] = mapped_column(String, nullable=True)
    box_folder_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    file_name: Mapped[str] = mapped_column(String, nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    # Optional design review document attached to the commit.
    design_review_box_file_id: Mapped[str | None] = mapped_column(String, nullable=True)
    design_review_sha256_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Slug from app/subsystems.py, derived from the Box folder path.
    subsystem: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    author_box_user_id: Mapped[str] = mapped_column(String, nullable=False)
    author_name: Mapped[str] = mapped_column(String, nullable=False)
    message: Mapped[str] = mapped_column(String, nullable=False)

    # XRPL anchoring (app/services/anchoring.py). The xrpl_* fields are filled
    # in once the anchoring transaction is validated.
    anchor_status: Mapped[AnchorStatus] = mapped_column(
        String, nullable=False, default=AnchorStatus.PENDING, server_default="pending", index=True
    )
    anchor_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    xrpl_network: Mapped[str | None] = mapped_column(String, nullable=True)
    xrpl_tx_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    xrpl_ledger_index: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, default=utcnow)
    anchored_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
