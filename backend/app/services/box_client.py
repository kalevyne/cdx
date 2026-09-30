from collections.abc import Callable
from functools import lru_cache
from io import BytesIO
from typing import TypeVar

from box_sdk_gen import (
    BoxAPIError,
    BoxClient,
    BoxOAuth,
    CreateFolderParent,
    OAuthConfig,
    TokenStorage,
    UploadFileAttributes,
    UploadFileAttributesParentField,
    UploadFileVersionAttributes,
)

from app.config import Settings, get_settings
from app.schemas.box import BoxFileMetadata, BoxFolder, BoxFolderListing, BoxFolderRef, BoxItem
from app.services.box_token_storage import make_backend_token_storage

T = TypeVar("T")

# Box's maximum page size for folder listings.
_FOLDER_PAGE_LIMIT = 1000
_FOLDER_FIELDS = ["id", "name", "path_collection"]
_FILE_FIELDS = [
    "id",
    "name",
    "size",
    "parent",
    "path_collection",
    "modified_at",
    "sha1",
    "file_version",
]


class BoxNotFoundError(Exception):
    """Raised when a requested Box file or folder doesn't exist, isn't visible to
    the Box account CDX is authorized as, or is outside the Dashboard root."""


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


def _call_box(fn: Callable[[], T], resource_id: str) -> T:
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
    in `backend/scripts/box_oauth_setup.py`. See backend/README.md for setup.
    Tokens persist per `settings.box_token_storage` and refresh automatically.

    Scope: that Box account can usually see far more than the dashboard tree
    (docs/DECISIONS.md #10/#11), so every method that looks an item up by ID
    raises BoxNotFoundError for anything outside BOX_DASHBOARD_ROOT_FOLDER_ID.
    `upload_file`/`ensure_folder` take a folder the caller already resolved
    through `get_folder`."""

    def __init__(self, settings: Settings) -> None:
        auth = make_box_oauth(settings, make_backend_token_storage(settings))
        self._client = BoxClient(auth=auth)
        self._settings = settings

    def get_folder(self, folder_id: str) -> BoxFolder:
        folder = _call_box(
            lambda: self._client.folders.get_folder_by_id(folder_id, fields=_FOLDER_FIELDS),
            folder_id,
        )
        is_root = folder.id == self._settings.require_dashboard_root_folder_id()
        return BoxFolder(
            id=folder.id, name=folder.name, path=[] if is_root else self._dashboard_path(folder)
        )

    def list_folder(self, folder_id: str) -> BoxFolderListing:
        folder = self.get_folder(folder_id)
        return BoxFolderListing(**folder.model_dump(), items=self._list_items(folder_id))

    def ensure_folder(self, parent_id: str, name: str) -> str:
        """Return the ID of the subfolder `name` under `parent_id`, creating it if
        it doesn't exist yet. Safe to re-run."""
        for item in self._list_items(parent_id):
            if item.type == "folder" and item.name == name:
                return item.id
        created = _call_box(
            lambda: self._client.folders.create_folder(name, CreateFolderParent(id=parent_id)),
            parent_id,
        )
        return created.id

    def get_file_metadata(self, file_id: str) -> BoxFileMetadata:
        file = _call_box(
            lambda: self._client.files.get_file_by_id(file_id, fields=_FILE_FIELDS), file_id
        )
        return self._to_file_metadata(file)

    def download_file(
        self, file_id: str, version_id: str | None = None
    ) -> tuple[BoxFileMetadata, bytes]:
        """The file's metadata plus its current content, or the content of a
        specific earlier version."""
        metadata = self.get_file_metadata(file_id)
        stream = _call_box(
            lambda: self._client.downloads.download_file(file_id, version=version_id), file_id
        )
        return metadata, stream.read()

    def upload_file(self, folder_id: str, filename: str, content: bytes) -> BoxFileMetadata:
        """Upload `content` as `filename` into the folder. If a file with that name
        is already there, the upload becomes a new version of it (Box rejects
        duplicate names, and a re-commit of the same file should keep its history)."""
        existing = next(
            (i for i in self._list_items(folder_id) if i.type == "file" and i.name == filename),
            None,
        )
        if existing:
            result = _call_box(
                lambda: self._client.uploads.upload_file_version(
                    existing.id,
                    UploadFileVersionAttributes(name=filename),
                    BytesIO(content),
                    fields=_FILE_FIELDS,
                ),
                existing.id,
            )
        else:
            attributes = UploadFileAttributes(
                name=filename, parent=UploadFileAttributesParentField(id=folder_id)
            )
            result = _call_box(
                lambda: self._client.uploads.upload_file(
                    attributes, BytesIO(content), fields=_FILE_FIELDS
                ),
                folder_id,
            )
        return self._to_file_metadata(result.entries[0])

    def _list_items(self, folder_id: str) -> list[BoxItem]:
        result = _call_box(
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

    def _dashboard_path(self, item) -> list[BoxFolderRef]:
        """The item's ancestors from the Dashboard root down, or BoxNotFoundError
        if the item isn't inside the Dashboard root."""
        root_id = self._settings.require_dashboard_root_folder_id()
        ancestors = [BoxFolderRef(id=f.id, name=f.name) for f in item.path_collection.entries]
        ancestor_ids = [f.id for f in ancestors]
        if root_id not in ancestor_ids:
            raise BoxNotFoundError(f"Box resource not found: {item.id}")
        return ancestors[ancestor_ids.index(root_id) :]

    def _to_file_metadata(self, file) -> BoxFileMetadata:
        path = self._dashboard_path(file)
        return BoxFileMetadata(
            id=file.id,
            name=file.name,
            size=file.size,
            parent_id=path[-1].id,
            path=path,
            modified_at=getattr(file, "modified_at", None),
            # box-sdk-gen maps the JSON `sha1` field to the Python attribute `sha_1`.
            box_sha1=getattr(file, "sha_1", None),
            version_id=file.file_version.id if getattr(file, "file_version", None) else None,
        )


@lru_cache
def get_box_service() -> BoxService:
    return BoxService(get_settings())
