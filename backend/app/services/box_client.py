from functools import lru_cache
from io import BytesIO

from box_sdk_gen import (
    BoxAPIError,
    BoxCCGAuth,
    BoxClient,
    CCGConfig,
    UploadFileAttributes,
    UploadFileAttributesParentField,
)

from app.config import Settings, get_settings
from app.schemas.box import BoxFileMetadata, BoxFolderListing, BoxItem


class BoxNotFoundError(Exception):
    """Raised when a requested Box file or folder doesn't exist, or isn't shared
    with the CDX service account."""


class BoxServiceError(Exception):
    """Raised for Box API failures other than not-found."""


class BoxService:
    """Thin wrapper around box-sdk-gen, authenticated as the CDX service account
    (Client Credentials Grant). The service account only sees folders it has been
    added to as a collaborator in Box — see backend/README.md for setup."""

    def __init__(self, settings: Settings) -> None:
        auth = BoxCCGAuth(
            CCGConfig(
                client_id=settings.box_client_id,
                client_secret=settings.box_client_secret,
                enterprise_id=settings.box_enterprise_id,
            )
        )
        self._client = BoxClient(auth=auth)

    def list_folder(self, folder_id: str) -> BoxFolderListing:
        folder = self._call(lambda: self._client.folders.get_folder_by_id(folder_id), folder_id)
        result = self._call(
            lambda: self._client.folders.get_folder_items(
                folder_id, fields=["id", "type", "name", "size", "modified_at"]
            ),
            folder_id,
        )
        items = [
            BoxItem(
                id=entry.id,
                type=str(entry.type),
                name=entry.name,
                size=getattr(entry, "size", None),
                modified_at=getattr(entry, "modified_at", None),
            )
            for entry in result.entries
        ]
        return BoxFolderListing(folder_id=folder_id, folder_name=folder.name, items=items)

    def get_file_metadata(self, file_id: str) -> BoxFileMetadata:
        file = self._call(
            lambda: self._client.files.get_file_by_id(
                file_id, fields=["id", "name", "size", "parent", "modified_at", "sha1"]
            ),
            file_id,
        )
        return self._to_file_metadata(file)

    def download_file(self, file_id: str) -> bytes:
        stream = self._call(lambda: self._client.downloads.download_file(file_id), file_id)
        return stream.read()

    def upload_file(self, folder_id: str, filename: str, content: bytes) -> BoxFileMetadata:
        attributes = UploadFileAttributes(
            name=filename,
            parent=UploadFileAttributesParentField(id=folder_id),
        )
        result = self._call(
            lambda: self._client.uploads.upload_file(attributes, BytesIO(content)),
            folder_id,
        )
        metadata = self._to_file_metadata(result.entries[0])
        # Box's response reflects the parent it actually stored the file under;
        # pin it to the folder_id we uploaded to rather than trust the response shape.
        return metadata.model_copy(update={"parent_id": folder_id})

    @staticmethod
    def _to_file_metadata(file) -> BoxFileMetadata:
        return BoxFileMetadata(
            id=file.id,
            name=file.name,
            size=file.size,
            parent_id=file.parent.id if getattr(file, "parent", None) else None,
            modified_at=getattr(file, "modified_at", None),
            # box-sdk-gen maps the JSON `sha1` field to the Python attribute `sha_1`.
            box_sha1=getattr(file, "sha_1", None),
        )

    @staticmethod
    def _call(fn, resource_id: str):
        try:
            return fn()
        except BoxAPIError as exc:
            if exc.response_info.status_code == 404:
                raise BoxNotFoundError(f"Box resource not found: {resource_id}") from exc
            raise BoxServiceError(f"Box API error for {resource_id}: {exc}") from exc


@lru_cache
def get_box_service() -> BoxService:
    return BoxService(get_settings())
