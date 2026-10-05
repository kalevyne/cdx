"""Read-only Box access: browse folders, read file metadata/content. Writes go
through CDX commits (routers/cdx_commits.py) so every upload is hashed and
recorded. Errors from BoxService are mapped to HTTP responses in app/errors.py."""

from urllib.parse import quote

from fastapi import APIRouter, Depends, Header
from fastapi.responses import Response, StreamingResponse

from app.auth import require_user
from app.config import Settings, get_settings
from app.schemas.box import BoxFileMetadata, BoxFolderListing
from app.services.box_client import BoxService, get_box_service
from app.services.file_downloads import (
    MAX_PREVIEW_BYTES,
    DownloadSlots,
    FileDownload,
    get_download_slots,
    open_download,
)

router = APIRouter(dependencies=[Depends(require_user)])


@router.get("/folders", response_model=BoxFolderListing)
def get_dashboard_root_folder(
    box: BoxService = Depends(get_box_service), settings: Settings = Depends(get_settings)
) -> BoxFolderListing:
    return box.list_folder(settings.require_dashboard_root_folder_id())


@router.get("/folders/{folder_id}", response_model=BoxFolderListing)
def get_folder(folder_id: str, box: BoxService = Depends(get_box_service)) -> BoxFolderListing:
    return box.list_folder(folder_id)


@router.get("/files/{file_id}", response_model=BoxFileMetadata)
def get_file_metadata(file_id: str, box: BoxService = Depends(get_box_service)) -> BoxFileMetadata:
    return box.get_file_metadata(file_id)


@router.get("/files/{file_id}/content")
# The same download with the file's name as the last URL segment, which is what
# a browser falls back to naming the saved file when it ignores (or a proxy
# drops) Content-Disposition. The name is not used to find the file.
@router.get("/files/{file_id}/content/{filename}")
def download_file(
    file_id: str,
    version_id: str | None = None,
    if_none_match: str | None = Header(default=None),
    box: BoxService = Depends(get_box_service),
    slots: DownloadSlots = Depends(get_download_slots),
) -> Response:
    """The file's current content, or a specific version (e.g. the one a CDX commit recorded)."""
    return _content_response(
        open_download(box, slots, file_id, version_id, cached_etags=_etags(if_none_match))
    )


@router.get("/files/{file_id}/preview")
def preview_file(
    file_id: str,
    version_id: str | None = None,
    if_none_match: str | None = Header(default=None),
    box: BoxService = Depends(get_box_service),
    slots: DownloadSlots = Depends(get_download_slots),
) -> Response:
    """Same bytes as `/content`, for the in-app preview: refused with a 413
    when the file is over the preview size cap."""
    return _content_response(
        open_download(
            box,
            slots,
            file_id,
            version_id,
            max_bytes=MAX_PREVIEW_BYTES,
            cached_etags=_etags(if_none_match),
        )
    )


def _content_response(download: FileDownload) -> Response:
    headers = {
        # Uploaded files are never rendered from the app's own origin: always
        # an opaque attachment, whatever the file claims to be.
        "Content-Disposition": _attachment_header(download.metadata.name),
        "X-Content-Type-Options": "nosniff",
        # Browsers may keep a copy but must ask before reusing it, so a
        # logged-out browser can't read files out of its cache.
        "Cache-Control": "private, no-cache",
    }
    if download.etag:
        headers["ETag"] = download.etag
    if download.body is None:
        return Response(status_code=304, headers=headers)
    return StreamingResponse(download.body, media_type="application/octet-stream", headers=headers)


def _etags(if_none_match: str | None) -> frozenset[str]:
    """The ETags in an If-None-Match header (proxies may mark them weak, `W/`)."""
    return frozenset(
        tag.strip().removeprefix("W/") for tag in (if_none_match or "").split(",") if tag.strip()
    )


def _attachment_header(filename: str) -> str:
    """RFC 6266 Content-Disposition: an ASCII fallback name for old clients plus
    the exact UTF-8 name (headers can't carry raw non-Latin-1 characters)."""
    ascii_name = filename.encode("ascii", "ignore").decode().replace('"', "").replace("\\", "")
    fallback = ascii_name.strip() or "download"
    return f"attachment; filename=\"{fallback}\"; filename*=UTF-8''{quote(filename)}"
