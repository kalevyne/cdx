from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import require_user
from app.db import get_session
from app.schemas.auth import SessionUser
from app.schemas.dashboard import PublicSummary, SubsystemSummary, SubsystemUpdate
from app.services import dashboard

router = APIRouter()


@router.get(
    "/subsystems", response_model=list[SubsystemSummary], dependencies=[Depends(require_user)]
)
def list_subsystems(db: Session = Depends(get_session)) -> list[SubsystemSummary]:
    return dashboard.subsystem_summaries(db)


@router.patch("/subsystems/{slug}", response_model=SubsystemSummary)
def update_subsystem(
    slug: str,
    update: SubsystemUpdate,
    user: SessionUser = Depends(require_user),
    db: Session = Depends(get_session),
) -> SubsystemSummary:
    return dashboard.update_subsystem(db, slug, update, user)


@router.get("/public/summary", response_model=PublicSummary)
def get_public_summary(db: Session = Depends(get_session)) -> PublicSummary:
    """No login needed: the read-only sponsor view (docs/DECISIONS.md #9)."""
    return dashboard.public_summary(db)
