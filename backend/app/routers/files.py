from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import Response

from app.config import Settings, get_settings
from app.schemas.box import BoxFileMetadata, BoxFolderListing
from app.services.box_client import BoxNotFoundError, BoxService, BoxServiceError, get_box_service

router = APIRouter()


def _dashboard_root_folder_id(settings: Settings = Depends(get_settings)) -> str:
    if not settings.box_dashboard_root_folder_id:
        raise HTTPException(
            status_code=400,
            detail="BOX_DASHBOARD_ROOT_FOLDER_ID is not configured",
        )
    return settings.box_dashboard_root_folder_id


@router.get("/folders", response_model=BoxFolderListing)
def get_dashboard_root_folder(
    box: BoxService = Depends(get_box_service),
    folder_id: str = Depends(_dashboard_root_folder_id),
) -> BoxFolderListing:
    return _list_folder(box, folder_id)


@router.get("/folders/{folder_id}", response_model=BoxFolderListing)
def get_folder(folder_id: str, box: BoxService = Depends(get_box_service)) -> BoxFolderListing:
    return _list_folder(box, folder_id)


@router.get("/files/{file_id}", response_model=BoxFileMetadata)
def get_file_metadata(file_id: str, box: BoxService = Depends(get_box_service)) -> BoxFileMetadata:
    try:
        return box.get_file_metadata(file_id)
    except BoxNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except BoxServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/files/{file_id}/content")
def download_file(file_id: str, box: BoxService = Depends(get_box_service)) -> Response:
    try:
        metadata = box.get_file_metadata(file_id)
        content = box.download_file(file_id)
    except BoxNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except BoxServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    safe_name = metadata.name.replace('"', "")
    return Response(
        content=content,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{safe_name}"'},
    )


@router.post("/folders/{folder_id}/files", response_model=BoxFileMetadata, status_code=201)
async def upload_file(
    folder_id: str, file: UploadFile, box: BoxService = Depends(get_box_service)
) -> BoxFileMetadata:
    content = await file.read()
    try:
        return box.upload_file(folder_id, file.filename, content)
    except BoxNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except BoxServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


def _list_folder(box: BoxService, folder_id: str) -> BoxFolderListing:
    try:
        return box.list_folder(folder_id)
    except BoxNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except BoxServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
