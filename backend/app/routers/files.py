"""Read-only Box access: browse folders, read file metadata/content. Writes go
through CDX commits (routers/cdx_commits.py) so every upload is hashed and
recorded. Errors from BoxService are mapped to HTTP responses in app/errors.py."""

from fastapi import APIRouter, Depends
from fastapi.responses import Response

from app.auth import require_user
from app.config import Settings, get_settings
from app.schemas.box import BoxFileMetadata, BoxFolderListing
from app.services.box_client import BoxService, get_box_service

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
def download_file(
    file_id: str, version_id: str | None = None, box: BoxService = Depends(get_box_service)
) -> Response:
    """The file's current content, or a specific version (e.g. the one a CDX commit recorded)."""
    metadata, content = box.download_file(file_id, version_id)
    safe_name = metadata.name.replace('"', "")
    return Response(
        content=content,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{safe_name}"'},
    )
