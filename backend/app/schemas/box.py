from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class BoxItem(BaseModel):
    """A single entry returned when listing a folder's contents."""

    id: str
    type: Literal["file", "folder"]
    name: str
    size: int | None = None
    modified_at: datetime | None = None


class BoxFolderRef(BaseModel):
    id: str
    name: str


class BoxFolderListing(BaseModel):
    folder_id: str
    folder_name: str
    items: list[BoxItem]


class BoxFileMetadata(BaseModel):
    id: str
    name: str
    size: int
    parent_id: str | None = None
    modified_at: datetime | None = None
    # Box's own content checksum (SHA-1), used for Box-side integrity checks.
    # Not the CDX commit's anchor hash — that's a SHA-256 computed by the
    # hashing pipeline (app/services/hashing.py) and stored on cdx_commits.sha256_hash.
    box_sha1: str | None = None
    # Box's ID for this exact version of the file's content.
    version_id: str | None = None
