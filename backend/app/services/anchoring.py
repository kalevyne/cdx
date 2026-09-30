"""Anchoring CDX commits to XRPL, and verifying them afterwards.

A CDX commit is saved as `pending`; `anchor_cdx_commit` then submits its hashes
as memos and records the transaction (`anchored`) or the error (`failed`,
retryable). It runs as a background task, so committing never waits on the
ledger. `verify_cdx_commit` re-derives everything from Box and the public
ledger, trusting nothing CDX's own database says except the tx hash.
"""

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_sessionmaker, utcnow
from app.models import AnchorStatus, CdxCommit
from app.schemas.cdx_commit import CdxCommitVerification, CheckStatus, VerificationCheck
from app.services.box_client import BoxNotFoundError, BoxService, BoxServiceError
from app.services.cdx_commits import get_cdx_commit
from app.services.hashing import sha256_hex
from app.services.xrpl_client import XrplClient, XrplError

logger = logging.getLogger(__name__)

# Memo types written into every anchor transaction.
MEMO_COMMIT_ID = "cdx/commit-id"
MEMO_SHA256 = "cdx/sha256"
MEMO_DESIGN_REVIEW_SHA256 = "cdx/design-review-sha256"


def anchor_memos(cdx_commit: CdxCommit) -> dict[str, str]:
    memos = {MEMO_COMMIT_ID: str(cdx_commit.id), MEMO_SHA256: cdx_commit.sha256_hash}
    if cdx_commit.design_review_sha256_hash:
        memos[MEMO_DESIGN_REVIEW_SHA256] = cdx_commit.design_review_sha256_hash
    return memos


def anchor_cdx_commit(db: Session, xrpl: XrplClient, cdx_commit_id: int) -> CdxCommit:
    """Anchor one commit. No-op if it's already anchored or XRPL isn't configured
    (it stays `pending` and the startup sweep picks it up once it is)."""
    cdx_commit = get_cdx_commit(db, cdx_commit_id)
    if cdx_commit.anchor_status == AnchorStatus.ANCHORED or not xrpl.is_configured:
        return cdx_commit

    try:
        receipt = xrpl.anchor(anchor_memos(cdx_commit))
    except XrplError as exc:
        logger.warning("Anchoring CDX commit %s failed: %s", cdx_commit_id, exc)
        cdx_commit.anchor_status = AnchorStatus.FAILED
        cdx_commit.anchor_error = str(exc)
    else:
        cdx_commit.anchor_status = AnchorStatus.ANCHORED
        cdx_commit.anchor_error = None
        cdx_commit.xrpl_network = receipt.network
        cdx_commit.xrpl_tx_hash = receipt.tx_hash
        cdx_commit.xrpl_ledger_index = receipt.ledger_index
        cdx_commit.anchored_at = utcnow()
    db.commit()
    return cdx_commit


def anchor_in_background(cdx_commit_id: int, xrpl: XrplClient) -> None:
    """Entry point for background tasks: uses its own DB session, never raises."""
    with get_sessionmaker()() as db:
        try:
            anchor_cdx_commit(db, xrpl, cdx_commit_id)
        except Exception:
            logger.exception("Unexpected error anchoring CDX commit %s", cdx_commit_id)


def anchor_pending_cdx_commits(xrpl: XrplClient) -> None:
    """Anchor everything still `pending` — commits made before XRPL was
    configured, or whose background task was lost to a restart."""
    if not xrpl.is_configured:
        return
    with get_sessionmaker()() as db:
        pending_ids = db.scalars(
            select(CdxCommit.id)
            .where(CdxCommit.anchor_status == AnchorStatus.PENDING)
            .order_by(CdxCommit.id)
        ).all()
    for cdx_commit_id in pending_ids:
        anchor_in_background(cdx_commit_id, xrpl)


def verify_cdx_commit(
    db: Session, box: BoxService, xrpl: XrplClient, cdx_commit_id: int
) -> CdxCommitVerification:
    cdx_commit = get_cdx_commit(db, cdx_commit_id)
    box_check = _check_box(box, cdx_commit)
    ledger_check = _check_ledger(xrpl, cdx_commit)
    return CdxCommitVerification(
        expected_sha256=cdx_commit.sha256_hash,
        box=box_check,
        ledger=ledger_check,
        verified=box_check.status == ledger_check.status == CheckStatus.MATCH,
    )


def _check_box(box: BoxService, cdx_commit: CdxCommit) -> VerificationCheck:
    try:
        _, content = box.download_file(cdx_commit.box_file_id, cdx_commit.box_file_version)
    except (BoxNotFoundError, BoxServiceError) as exc:
        return VerificationCheck(status=CheckStatus.UNAVAILABLE, detail=str(exc))
    return _compare(cdx_commit.sha256_hash, sha256_hex(content), source="Box's copy of the file")


def _check_ledger(xrpl: XrplClient, cdx_commit: CdxCommit) -> VerificationCheck:
    if not cdx_commit.xrpl_tx_hash:
        return VerificationCheck(status=CheckStatus.UNAVAILABLE, detail="Not anchored yet")
    if cdx_commit.xrpl_network != xrpl.network:
        return VerificationCheck(
            status=CheckStatus.UNAVAILABLE,
            detail=f"Anchored on XRPL {cdx_commit.xrpl_network}; this server reads {xrpl.network}",
        )
    try:
        memos = xrpl.fetch_memos(cdx_commit.xrpl_tx_hash)
    except XrplError as exc:
        return VerificationCheck(status=CheckStatus.UNAVAILABLE, detail=str(exc))
    observed = memos.get(MEMO_SHA256)
    if observed is None:
        return VerificationCheck(
            status=CheckStatus.MISMATCH, detail="The transaction has no CDX hash memo"
        )
    return _compare(cdx_commit.sha256_hash, observed, source="The ledger memo")


def _compare(expected: str, observed: str, *, source: str) -> VerificationCheck:
    if observed == expected:
        return VerificationCheck(
            status=CheckStatus.MATCH, observed_sha256=observed, detail=f"{source} matches"
        )
    return VerificationCheck(
        status=CheckStatus.MISMATCH,
        observed_sha256=observed,
        detail=f"{source} does not match the recorded hash",
    )
