import base64
import hashlib
import time
from collections.abc import Callable, Iterator
from functools import lru_cache
from io import BytesIO
from typing import BinaryIO, TypeVar

from box_sdk_gen import (
    BoxAPIError,
    BoxClient,
    BoxOAuth,
    CreateFolderParent,
    FileFull,
    OAuthConfig,
    TokenStorage,
    UploadFileAttributes,
    UploadFileAttributesParentField,
    UploadFileVersionAttributes,
    UploadPart,
)

from app.config import Settings, get_settings
from app.schemas.auth import SessionUser
from app.schemas.box import BoxFileMetadata, BoxFolder, BoxFolderListing, BoxFolderRef, BoxItem
from app.services.box_token_storage import make_backend_token_storage

T = TypeVar("T")

# Box's maximum page size for folder listings.
_FOLDER_PAGE_LIMIT = 1000
# File content is read from Box in pieces this big, so relaying a download to
# the browser never holds more than one piece of it in memory.
_DOWNLOAD_CHUNK_BYTES = 64 * 1024
# Files this big or bigger go through Box's chunked upload API instead of a
# single request. Box caps single uploads at 50 MB, recommends chunking above
# 20 MB, and refuses upload sessions for anything smaller.
CHUNKED_UPLOAD_MIN_BYTES = 20 * 1024 * 1024
# Box answers a chunked-upload commit with 202 while it is still assembling the
# parts; ask again this many times, this many seconds apart, before giving up.
_COMMIT_ATTEMPTS = 10
_COMMIT_RETRY_SECONDS = 2.0
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
    through `get_folder`, and `open_file_content` a file resolved through
    `get_file_metadata`.

    File content is never held in memory whole: downloads are read piece by
    piece, and uploads from `CHUNKED_UPLOAD_MIN_BYTES` up are sent in Box's
    upload-session parts (a few MB each)."""

    def __init__(self, settings: Settings) -> None:
        auth = make_box_oauth(settings, make_backend_token_storage(settings))
        self._client = BoxClient(auth=auth)
        self._settings = settings

    def get_current_user(self) -> SessionUser:
        """The Box account the backend is connected as (decision #10)."""
        me = _call_box(lambda: self._client.users.get_user_me(fields=["id", "name", "login"]), "me")
        return SessionUser(box_user_id=me.id, name=me.name, login=me.login)

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

    def open_file_content(
        self, file: BoxFileMetadata, version_id: str | None = None
    ) -> Iterator[bytes]:
        """Start downloading a file the caller already resolved through
        `get_file_metadata` (current content, or a specific earlier version).
        The Box request is made here; the content is read chunk by chunk as the
        returned iterator is consumed."""
        stream = _call_box(
            lambda: self._client.downloads.download_file(file.id, version=version_id), file.id
        )
        if stream is None:
            # Box answers 202 with no body while it's still preparing a new upload.
            raise BoxServiceError(f"Box isn't ready to serve {file.id} yet; try again shortly")
        return iter(lambda: stream.read(_DOWNLOAD_CHUNK_BYTES), b"")

    def upload_file(
        self, folder_id: str, filename: str, content: BinaryIO, size: int
    ) -> BoxFileMetadata:
        """Upload `size` bytes read from `content` as `filename` into the folder.
        If a file with that name is already there, the upload becomes a new
        version of it (Box rejects duplicate names, and a re-commit of the same
        file should keep its history). Large files are uploaded in parts."""
        existing = next(
            (i for i in self._list_items(folder_id) if i.type == "file" and i.name == filename),
            None,
        )
        content.seek(0)
        if size >= CHUNKED_UPLOAD_MIN_BYTES:
            return self._upload_in_parts(folder_id, filename, content, size, existing)
        if existing:
            result = _call_box(
                lambda: self._client.uploads.upload_file_version(
                    existing.id,
                    UploadFileVersionAttributes(name=filename),
                    content,
                    fields=_FILE_FIELDS,
                ),
                existing.id,
            )
        else:
            attributes = UploadFileAttributes(
                name=filename, parent=UploadFileAttributesParentField(id=folder_id)
            )
            result = _call_box(
                lambda: self._client.uploads.upload_file(attributes, content, fields=_FILE_FIELDS),
                folder_id,
            )
        return self._to_file_metadata(result.entries[0])

    def _upload_in_parts(
        self,
        folder_id: str,
        filename: str,
        content: BinaryIO,
        size: int,
        existing: BoxItem | None,
    ) -> BoxFileMetadata:
        """Box's chunked upload: open an upload session, send the file in the
        part size Box chooses (each part with its SHA-1), then commit the parts
        with the whole file's SHA-1. Box checks both digests, so a corrupted
        part fails the upload instead of being stored. On any failure the
        session is aborted so Box discards the parts."""
        uploads = self._client.chunked_uploads
        resource_id = existing.id if existing else folder_id
        if existing:
            session = _call_box(
                lambda: uploads.create_file_upload_session_for_existing_file(
                    existing.id, size, file_name=filename
                ),
                resource_id,
            )
        else:
            session = _call_box(
                lambda: uploads.create_file_upload_session(folder_id, size, filename),
                resource_id,
            )
        endpoints = session.session_endpoints
        try:
            file_sha1 = hashlib.sha1()
            parts: list[UploadPart] = []
            offset = 0
            while offset < size:
                part = content.read(min(session.part_size, size - offset))
                if not part:
                    raise BoxServiceError(
                        f"{filename} ended after {offset} of {size} bytes during upload"
                    )
                file_sha1.update(part)
                content_range = f"bytes {offset}-{offset + len(part) - 1}/{size}"
                uploaded = _call_box(
                    lambda part=part, content_range=content_range: uploads.upload_file_part_by_url(
                        endpoints.upload_part, BytesIO(part), _sha1_digest(part), content_range
                    ),
                    resource_id,
                )
                parts.append(uploaded.part)
                offset += len(part)
            committed = self._commit_upload_session(
                endpoints.commit, parts, f"sha={_base64(file_sha1.digest())}", resource_id
            )
        except Exception:
            try:
                uploads.delete_file_upload_session_by_url(endpoints.abort)
            except Exception:
                pass  # Best effort: Box expires abandoned sessions after a day anyway.
            raise
        # The commit response doesn't take `fields`, so re-read the file with
        # the fields CDX records (path, version).
        return self.get_file_metadata(committed.id)

    def _commit_upload_session(
        self, commit_url: str, parts: list[UploadPart], digest: str, resource_id: str
    ) -> FileFull:
        for attempt in range(_COMMIT_ATTEMPTS):
            files = _call_box(
                lambda: self._client.chunked_uploads.create_file_upload_session_commit_by_url(
                    commit_url, parts, digest
                ),
                resource_id,
            )
            # box-sdk-gen returns None for Box's "202 Accepted, still processing parts".
            if files is not None:
                return files.entries[0]
            if attempt < _COMMIT_ATTEMPTS - 1:
                time.sleep(_COMMIT_RETRY_SECONDS)
        raise BoxServiceError(f"Box didn't finish assembling the upload for {resource_id}")

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


def _base64(digest: bytes) -> str:
    return base64.b64encode(digest).decode("ascii")


def _sha1_digest(part: bytes) -> str:
    """RFC 3230 `Digest` header value Box requires for each uploaded part."""
    return f"sha={_base64(hashlib.sha1(part).digest())}"


@lru_cache
def get_box_service() -> BoxService:
    return BoxService(get_settings())
