from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, computed_field

from app.models import AnchorStatus
from app.services.xrpl_client import explorer_tx_url


class LedgerAnchor(BaseModel):
    """Fields locating a commit's anchor on the XRP Ledger (shared by the
    private and public commit views)."""

    model_config = ConfigDict(from_attributes=True)

    anchor_status: AnchorStatus
    xrpl_network: str | None
    xrpl_tx_hash: str | None

    @computed_field
    @property
    def xrpl_explorer_url(self) -> str | None:
        if not (self.xrpl_network and self.xrpl_tx_hash):
            return None
        return explorer_tx_url(self.xrpl_network, self.xrpl_tx_hash)


class CdxCommitRead(LedgerAnchor):
    id: int
    box_file_id: str
    box_file_version: str | None
    box_folder_id: str
    file_name: str
    file_size: int
    sha256_hash: str
    design_review_box_file_id: str | None
    design_review_sha256_hash: str | None
    subsystem: str | None
    author_name: str
    message: str
    anchor_error: str | None
    xrpl_ledger_index: int | None
    created_at: datetime
    anchored_at: datetime | None


class PublicCdxCommit(LedgerAnchor):
    """What the public sponsor page may show about a commit: no author, no
    message, no Box IDs — just that a file was recorded, and its proof."""

    subsystem: str | None
    file_name: str
    sha256_hash: str
    created_at: datetime


class CheckStatus(StrEnum):
    MATCH = "match"
    MISMATCH = "mismatch"
    UNAVAILABLE = "unavailable"  # Couldn't check (not anchored yet, service down, ...).


class VerificationCheck(BaseModel):
    status: CheckStatus
    observed_sha256: str | None = None
    detail: str


class CdxCommitVerification(BaseModel):
    """Independent re-checks of a CDX commit's recorded SHA-256: against the
    file's bytes in Box, and against the memo on the public ledger."""

    expected_sha256: str
    box: VerificationCheck
    ledger: VerificationCheck
    verified: bool
