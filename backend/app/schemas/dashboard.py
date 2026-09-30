from datetime import datetime

from pydantic import BaseModel

from app.models import SubsystemStage
from app.schemas.cdx_commit import CdxCommitRead, PublicCdxCommit


class SubsystemOverview(BaseModel):
    """Per-subsystem status that's safe to show publicly."""

    slug: str
    name: str
    stage: SubsystemStage | None
    commit_count: int
    anchored_count: int
    last_commit_at: datetime | None


class SubsystemSummary(SubsystemOverview):
    """A dashboard card: the public overview plus team-internal details."""

    owner_name: str | None
    status_note: str | None
    updated_by: str | None
    recent_commits: list[CdxCommitRead]


class SubsystemUpdate(BaseModel):
    """PATCH body: only the fields sent are changed; send null to clear one."""

    owner_name: str | None = None
    stage: SubsystemStage | None = None
    status_note: str | None = None


class PublicSummary(BaseModel):
    total_commits: int
    anchored_commits: int
    contributors: int
    subsystems: list[SubsystemOverview]
    recent_anchored: list[PublicCdxCommit]
