from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CdxCommitRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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
    xrpl_tx_hash: str | None
    xrpl_ledger_index: int | None
    created_at: datetime
    anchored_at: datetime | None
