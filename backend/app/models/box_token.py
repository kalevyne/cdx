from datetime import datetime

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base, UTCDateTime, utcnow


class BoxToken(Base):
    """The backend's own Box OAuth token (decision #10), when
    BOX_TOKEN_STORAGE=database. As sensitive as a password: it grants access to
    whatever Box account authorized CDX."""

    __tablename__ = "box_tokens"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    token_json: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime, nullable=False, default=utcnow, onupdate=utcnow
    )
