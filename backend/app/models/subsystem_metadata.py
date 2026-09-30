from datetime import datetime
from enum import StrEnum

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base, UTCDateTime, utcnow


class SubsystemStage(StrEnum):
    """Where a subsystem is in CalSol's design process, in order."""

    CONCEPT = "concept"
    DESIGN = "design"
    REVIEW = "review"
    MANUFACTURING = "manufacturing"
    TESTING = "testing"
    COMPLETE = "complete"


class SubsystemMetadata(Base):
    """Editable facts about a subsystem (owner, stage). Which subsystems exist is
    defined in app/subsystems.py; a subsystem without a row just has no owner or
    stage set yet."""

    __tablename__ = "subsystem_metadata"

    slug: Mapped[str] = mapped_column(String, primary_key=True)
    owner_name: Mapped[str | None] = mapped_column(String, nullable=True)
    stage: Mapped[SubsystemStage | None] = mapped_column(String, nullable=True)
    status_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_by: Mapped[str | None] = mapped_column(String, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime, nullable=False, default=utcnow, onupdate=utcnow
    )
