from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class CdxCommit(Base):
    """A CDX commit — an engineer's file upload through the dashboard, hashed and
    anchored to XRPL. Not a git commit; see CLAUDE.md on that distinction."""

    __tablename__ = "cdx_commits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    box_file_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    box_file_version: Mapped[str | None] = mapped_column(String, nullable=True)
    subsystem: Mapped[str | None] = mapped_column(String, nullable=True)
    author: Mapped[str] = mapped_column(String, nullable=False)
    message: Mapped[str] = mapped_column(String, nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String, nullable=False)
    xrpl_tx_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    xrpl_ledger_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    anchored_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
