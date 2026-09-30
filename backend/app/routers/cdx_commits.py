from fastapi import APIRouter, BackgroundTasks, Depends, Form, Query, UploadFile
from sqlalchemy.orm import Session

from app.auth import require_user
from app.db import get_session
from app.models import AnchorStatus
from app.schemas.auth import SessionUser
from app.schemas.cdx_commit import CdxCommitRead, CdxCommitVerification
from app.services import anchoring, cdx_commits
from app.services.box_client import BoxService, get_box_service
from app.services.cdx_commits import CommitFile
from app.services.xrpl_client import XrplClient, XrplNotConfiguredError, get_xrpl_client

router = APIRouter(prefix="/cdx-commits", dependencies=[Depends(require_user)])


# Sync (not async) routes: Box, DB and XRPL calls block, so FastAPI runs these
# in a worker thread instead of on the event loop.
@router.post("", response_model=CdxCommitRead, status_code=201)
def create_cdx_commit(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    folder_id: str = Form(),
    message: str = Form(),
    design_review: UploadFile | None = None,
    user: SessionUser = Depends(require_user),
    db: Session = Depends(get_session),
    box: BoxService = Depends(get_box_service),
    xrpl: XrplClient = Depends(get_xrpl_client),
) -> CdxCommitRead:
    cdx_commit = cdx_commits.create_cdx_commit(
        db,
        box,
        folder_id=folder_id,
        file=_to_commit_file(file),
        message=message,
        author=user,
        design_review=_to_commit_file(design_review) if design_review else None,
    )
    # Anchoring waits for ledger validation (seconds), so it runs after the response.
    background_tasks.add_task(anchoring.anchor_in_background, cdx_commit.id, xrpl)
    return cdx_commit


@router.get("", response_model=list[CdxCommitRead])
def list_cdx_commits(
    subsystem: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_session),
) -> list[CdxCommitRead]:
    return cdx_commits.list_cdx_commits(db, subsystem=subsystem, limit=limit)


@router.get("/{cdx_commit_id}", response_model=CdxCommitRead)
def get_cdx_commit(cdx_commit_id: int, db: Session = Depends(get_session)) -> CdxCommitRead:
    return cdx_commits.get_cdx_commit(db, cdx_commit_id)


@router.post("/{cdx_commit_id}/anchor", response_model=CdxCommitRead, status_code=202)
def retry_anchoring(
    cdx_commit_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_session),
    xrpl: XrplClient = Depends(get_xrpl_client),
) -> CdxCommitRead:
    """Queue another anchoring attempt for a commit that isn't anchored yet."""
    cdx_commit = cdx_commits.get_cdx_commit(db, cdx_commit_id)
    if cdx_commit.anchor_status != AnchorStatus.ANCHORED:
        if not xrpl.is_configured:
            raise XrplNotConfiguredError("XRPL anchoring isn't configured on this server")
        cdx_commit.anchor_status = AnchorStatus.PENDING
        db.commit()
        background_tasks.add_task(anchoring.anchor_in_background, cdx_commit.id, xrpl)
    return cdx_commit


@router.get("/{cdx_commit_id}/verification", response_model=CdxCommitVerification)
def verify_cdx_commit(
    cdx_commit_id: int,
    db: Session = Depends(get_session),
    box: BoxService = Depends(get_box_service),
    xrpl: XrplClient = Depends(get_xrpl_client),
) -> CdxCommitVerification:
    return anchoring.verify_cdx_commit(db, box, xrpl, cdx_commit_id)


def _to_commit_file(upload: UploadFile) -> CommitFile:
    return CommitFile(name=upload.filename or "", content=upload.file.read())
