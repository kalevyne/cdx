"""Subsystem status for the dashboard cards and the public sponsor summary.

Which subsystems exist comes from app/subsystems.py; owner/stage/note come from
the `subsystem_metadata` table; activity numbers are aggregated from
`cdx_commits`.
"""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models import AnchorStatus, CdxCommit, SubsystemMetadata
from app.schemas.auth import SessionUser
from app.schemas.cdx_commit import PublicCdxCommit
from app.schemas.dashboard import (
    PublicSummary,
    SubsystemOverview,
    SubsystemSummary,
    SubsystemUpdate,
)
from app.services.cdx_commits import list_cdx_commits
from app.subsystems import SUBSYSTEMS, Subsystem

RECENT_COMMITS_PER_SUBSYSTEM = 3
PUBLIC_RECENT_ANCHORED = 8


class SubsystemNotFoundError(Exception):
    pass


@dataclass(frozen=True)
class _CommitStats:
    commit_count: int = 0
    anchored_count: int = 0
    last_commit_at: datetime | None = None


def subsystem_summaries(db: Session) -> list[SubsystemSummary]:
    stats = _commit_stats_by_subsystem(db)
    metadata = {row.slug: row for row in db.scalars(select(SubsystemMetadata))}
    return [_summary(db, s, stats.get(s.slug), metadata.get(s.slug)) for s in SUBSYSTEMS]


def update_subsystem(
    db: Session, slug: str, update: SubsystemUpdate, editor: SessionUser
) -> SubsystemSummary:
    subsystem = next((s for s in SUBSYSTEMS if s.slug == slug), None)
    if subsystem is None:
        raise SubsystemNotFoundError(f"No subsystem called {slug!r}")

    row = db.get(SubsystemMetadata, slug) or SubsystemMetadata(slug=slug)
    for field in update.model_fields_set:
        value = getattr(update, field)
        if isinstance(value, str):
            value = value.strip() or None  # a blank string clears the field
        setattr(row, field, value)
    row.updated_by = editor.name
    db.add(row)
    db.commit()
    return _summary(db, subsystem, _commit_stats_by_subsystem(db).get(slug), row)


def public_summary(db: Session) -> PublicSummary:
    stats = _commit_stats_by_subsystem(db)
    metadata = {row.slug: row for row in db.scalars(select(SubsystemMetadata))}
    totals = db.execute(
        select(
            func.count(CdxCommit.id),
            _anchored_count(),
            func.count(CdxCommit.author_box_user_id.distinct()),
        )
    ).one()
    recent_anchored = db.scalars(
        select(CdxCommit)
        .where(CdxCommit.anchor_status == AnchorStatus.ANCHORED)
        .order_by(CdxCommit.anchored_at.desc(), CdxCommit.id.desc())
        .limit(PUBLIC_RECENT_ANCHORED)
    )
    return PublicSummary(
        total_commits=totals[0],
        anchored_commits=totals[1] or 0,
        contributors=totals[2],
        subsystems=[_overview(s, stats.get(s.slug), metadata.get(s.slug)) for s in SUBSYSTEMS],
        recent_anchored=[PublicCdxCommit.model_validate(c) for c in recent_anchored],
    )


def _summary(
    db: Session,
    subsystem: Subsystem,
    stats: _CommitStats | None,
    metadata: SubsystemMetadata | None,
) -> SubsystemSummary:
    return SubsystemSummary(
        **_overview(subsystem, stats, metadata).model_dump(),
        owner_name=metadata.owner_name if metadata else None,
        status_note=metadata.status_note if metadata else None,
        updated_by=metadata.updated_by if metadata else None,
        recent_commits=list_cdx_commits(
            db, subsystem=subsystem.slug, limit=RECENT_COMMITS_PER_SUBSYSTEM
        ),
    )


def _overview(
    subsystem: Subsystem, stats: _CommitStats | None, metadata: SubsystemMetadata | None
) -> SubsystemOverview:
    stats = stats or _CommitStats()
    return SubsystemOverview(
        slug=subsystem.slug,
        name=subsystem.name,
        stage=metadata.stage if metadata else None,
        commit_count=stats.commit_count,
        anchored_count=stats.anchored_count,
        last_commit_at=stats.last_commit_at,
    )


def _anchored_count():
    return func.sum(case((CdxCommit.anchor_status == AnchorStatus.ANCHORED, 1), else_=0))


def _commit_stats_by_subsystem(db: Session) -> dict[str, _CommitStats]:
    rows = db.execute(
        select(
            CdxCommit.subsystem,
            func.count(CdxCommit.id),
            _anchored_count(),
            func.max(CdxCommit.created_at),
        ).group_by(CdxCommit.subsystem)
    )
    return {
        subsystem: _CommitStats(count, anchored or 0, last)
        for subsystem, count, anchored, last in rows
        if subsystem
    }
