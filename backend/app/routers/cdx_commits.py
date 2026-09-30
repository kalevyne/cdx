from fastapi import APIRouter, Depends, Form, UploadFile
from sqlalchemy.orm import Session

from app.auth import require_user
from app.db import get_session
from app.schemas.auth import SessionUser
from app.schemas.cdx_commit import CdxCommitRead
from app.services import cdx_commits
from app.services.box_client import BoxService, get_box_service
from app.services.cdx_commits import CommitFile

router = APIRouter(prefix="/cdx-commits", dependencies=[Depends(require_user)])


# Sync (not async) routes: Box and DB calls block, so FastAPI runs these in a
# worker thread instead of on the event loop.
@router.post("", response_model=CdxCommitRead, status_code=201)
def create_cdx_commit(
    file: UploadFile,
    folder_id: str = Form(),
    message: str = Form(),
    design_review: UploadFile | None = None,
    user: SessionUser = Depends(require_user),
    db: Session = Depends(get_session),
    box: BoxService = Depends(get_box_service),
) -> CdxCommitRead:
    return cdx_commits.create_cdx_commit(
        db,
        box,
        folder_id=folder_id,
        file=_to_commit_file(file),
        message=message,
        author=user,
        design_review=_to_commit_file(design_review) if design_review else None,
    )


@router.get("", response_model=list[CdxCommitRead])
def list_cdx_commits(
    subsystem: str | None = None, limit: int = 50, db: Session = Depends(get_session)
) -> list[CdxCommitRead]:
    return cdx_commits.list_cdx_commits(db, subsystem=subsystem, limit=min(limit, 200))


@router.get("/{cdx_commit_id}", response_model=CdxCommitRead)
def get_cdx_commit(cdx_commit_id: int, db: Session = Depends(get_session)) -> CdxCommitRead:
    return cdx_commits.get_cdx_commit(db, cdx_commit_id)


def _to_commit_file(upload: UploadFile) -> CommitFile:
    return CommitFile(name=upload.filename or "", content=upload.file.read())
