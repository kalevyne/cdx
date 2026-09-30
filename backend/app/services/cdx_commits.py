"""Creating and reading CDX commits: upload → Box → SHA-256 → `cdx_commits` row.

A CDX commit is an engineer's file upload through the dashboard (not a git
commit — see CLAUDE.md). The row is written as soon as Box has the file; XRPL
anchoring fills in the `xrpl_*` fields afterwards.
"""

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import CdxCommit
from app.schemas.auth import SessionUser
from app.schemas.box import BoxFolderRef
from app.services.box_client import BoxService
from app.services.hashing import sha256_hex
from app.subsystems import DESIGN_REVIEWS_FOLDER, subsystem_for_folder_name

# Box's limit for a single (non-chunked) upload. Larger files would need Box's
# chunked upload API, which CDX doesn't use yet.
MAX_UPLOAD_BYTES = 50 * 1024 * 1024


class CdxCommitNotFoundError(Exception):
    pass


class InvalidCdxCommitError(Exception):
    pass


class FileTooLargeError(InvalidCdxCommitError):
    pass


@dataclass(frozen=True)
class CommitFile:
    name: str
    content: bytes


def create_cdx_commit(
    db: Session,
    box: BoxService,
    *,
    folder_id: str,
    file: CommitFile,
    message: str,
    author: SessionUser,
    design_review: CommitFile | None = None,
) -> CdxCommit:
    message = message.strip()
    if not message:
        raise InvalidCdxCommitError("A commit message is required")
    for commit_file in (file, design_review):
        if commit_file:
            _validate_file(commit_file)

    folder = box.get_folder(folder_id)
    subsystem, subsystem_folder = _find_subsystem([*folder.path, folder])

    uploaded = box.upload_file(folder_id, file.name, file.content)
    review = None
    if design_review:
        # Design reviews live in the subsystem's "Design Reviews" folder when the
        # commit is inside a subsystem, next to the committed file otherwise.
        review_folder_id = (
            box.ensure_folder(subsystem_folder.id, DESIGN_REVIEWS_FOLDER)
            if subsystem_folder
            else folder_id
        )
        review = box.upload_file(review_folder_id, design_review.name, design_review.content)

    cdx_commit = CdxCommit(
        box_file_id=uploaded.id,
        box_file_version=uploaded.version_id,
        box_folder_id=folder_id,
        file_name=uploaded.name,
        file_size=len(file.content),
        sha256_hash=sha256_hex(file.content),
        design_review_box_file_id=review.id if review else None,
        design_review_sha256_hash=sha256_hex(design_review.content) if design_review else None,
        subsystem=subsystem,
        author_box_user_id=author.box_user_id,
        author_name=author.name,
        message=message,
    )
    db.add(cdx_commit)
    db.commit()
    db.refresh(cdx_commit)
    return cdx_commit


def list_cdx_commits(
    db: Session, *, subsystem: str | None = None, limit: int = 50
) -> list[CdxCommit]:
    query = select(CdxCommit).order_by(CdxCommit.created_at.desc(), CdxCommit.id.desc())
    if subsystem:
        query = query.where(CdxCommit.subsystem == subsystem)
    return list(db.scalars(query.limit(limit)))


def get_cdx_commit(db: Session, cdx_commit_id: int) -> CdxCommit:
    cdx_commit = db.get(CdxCommit, cdx_commit_id)
    if cdx_commit is None:
        raise CdxCommitNotFoundError(f"CDX commit {cdx_commit_id} not found")
    return cdx_commit


def _validate_file(commit_file: CommitFile) -> None:
    if not commit_file.name.strip():
        raise InvalidCdxCommitError("Uploaded files need a file name")
    if not commit_file.content:
        raise InvalidCdxCommitError(f"{commit_file.name} is empty")
    if len(commit_file.content) > MAX_UPLOAD_BYTES:
        raise FileTooLargeError(
            f"{commit_file.name} is larger than {MAX_UPLOAD_BYTES // (1024 * 1024)} MB"
        )


def _find_subsystem(path: list[BoxFolderRef]) -> tuple[str | None, BoxFolderRef | None]:
    """The subsystem a folder belongs to, from its nearest subsystem-named ancestor."""
    for folder in reversed(path):
        slug = subsystem_for_folder_name(folder.name)
        if slug:
            return slug, folder
    return None, None
