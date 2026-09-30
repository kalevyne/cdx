from collections.abc import Callable
from functools import lru_cache
from io import BytesIO
from typing import TypeVar

from box_sdk_gen import (
    BoxAPIError,
    BoxClient,
    BoxOAuth,
    CreateFolderParent,
    FileTokenStorage,
    OAuthConfig,
    TokenStorage,
    UploadFileAttributes,
    UploadFileAttributesParentField,
)

from app.config import Settings, get_settings
from app.schemas.box import BoxFileMetadata, BoxFolderListing, BoxItem

T = TypeVar("T")

# Box's maximum page size for folder listings.
_FOLDER_PAGE_LIMIT = 1000


class BoxNotFoundError(Exception):
    """Raised when a requested Box file or folder doesn't exist, or isn't visible
    to the Box account CDX is authorized as."""


class BoxServiceError(Exception):
    """Raised for Box API failures other than not-found."""


def make_box_oauth(settings: Settings, token_storage: TokenStorage) -> BoxOAuth:
    """The one place CDX builds a Box OAuth 2.0 client from its app credentials.
    `token_storage` decides whose tokens it holds: the backend's own connection
    (a persisted file) or a single engineer's login (in memory)."""
    return BoxOAuth(
        OAuthConfig(
            client_id=settings.box_client_id,
            client_secret=settings.box_client_secret,
            token_storage=token_storage,
        )
    )


def call_box(fn: Callable[[], T], resource_id: str) -> T:
    """Run a Box SDK call, translating Box API errors into CDX's exceptions."""
    try:
        return fn()
    except BoxAPIError as exc:
        if exc.response_info.status_code == 404:
            raise BoxNotFoundError(f"Box resource not found: {resource_id}") from exc
        raise BoxServiceError(f"Box API error for {resource_id}: {exc}") from exc


class BoxService:
    """Thin wrapper around box-sdk-gen, authenticated via OAuth 2.0 (User
    Authentication) as whichever Box account completed the one-time authorization
    in `backend/scripts/box_oauth_setup.py` — that account's own Box permissions
    determine what CDX can see. See backend/README.md for setup. Tokens persist
    to `settings.box_token_storage_path` and refresh automatically."""

    def __init__(self, settings: Settings) -> None:
        auth = make_box_oauth(settings, FileTokenStorage(settings.box_token_storage_path))
        self._client = BoxClient(auth=auth)

    def list_folder(self, folder_id: str) -> BoxFolderListing:
        folder = call_box(lambda: self._client.folders.get_folder_by_id(folder_id), folder_id)
        return BoxFolderListing(
            folder_id=folder_id, folder_name=folder.name, items=self._list_items(folder_id)
        )

    def ensure_folder(self, parent_id: str, name: str) -> str:
        """Return the ID of the subfolder `name` under `parent_id`, creating it if
        it doesn't exist yet. Safe to re-run."""
        for item in self._list_items(parent_id):
            if item.type == "folder" and item.name == name:
                return item.id
        created = call_box(
            lambda: self._client.folders.create_folder(name, CreateFolderParent(id=parent_id)),
            parent_id,
        )
        return created.id

    def get_file_metadata(self, file_id: str) -> BoxFileMetadata:
        file = call_box(
            lambda: self._client.files.get_file_by_id(
                file_id, fields=["id", "name", "size", "parent", "modified_at", "sha1"]
            ),
            file_id,
        )
        return self._to_file_metadata(file)

    def download_file(self, file_id: str) -> bytes:
        stream = call_box(lambda: self._client.downloads.download_file(file_id), file_id)
        return stream.read()

    def upload_file(self, folder_id: str, filename: str, content: bytes) -> BoxFileMetadata:
        attributes = UploadFileAttributes(
            name=filename,
            parent=UploadFileAttributesParentField(id=folder_id),
        )
        result = call_box(
            lambda: self._client.uploads.upload_file(attributes, BytesIO(content)),
            folder_id,
        )
        metadata = self._to_file_metadata(result.entries[0])
        # Box's response reflects the parent it actually stored the file under;
        # pin it to the folder_id we uploaded to rather than trust the response shape.
        return metadata.model_copy(update={"parent_id": folder_id})

    def _list_items(self, folder_id: str) -> list[BoxItem]:
        result = call_box(
            lambda: self._client.folders.get_folder_items(
                folder_id,
                fields=["id", "type", "name", "size", "modified_at"],
                limit=_FOLDER_PAGE_LIMIT,
            ),
            folder_id,
        )
        return [
            BoxItem(
                id=entry.id,
                type=entry.type.value,
                name=entry.name,
                size=getattr(entry, "size", None),
                modified_at=getattr(entry, "modified_at", None),
            )
            for entry in result.entries
        ]

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


@lru_cache
def get_box_service() -> BoxService:
    return BoxService(get_settings())
