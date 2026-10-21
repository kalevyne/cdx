import base64
import hashlib
from io import BytesIO
from unittest.mock import MagicMock

import pytest
from box_sdk_gen import FileBaseTypeField, FolderBaseTypeField

from app.config import get_settings
from app.services.box_client import BoxNotFoundError, BoxService, BoxServiceError
from tests.conftest import DASHBOARD_ROOT_ID, box_api_error

# Box path above the dashboard: All Files (0) > CDX (the Dashboard root).
ABOVE_ROOT = [("0", "All Files"), (DASHBOARD_ROOT_ID, "CDX")]


def _named(mock: MagicMock, name: str) -> MagicMock:
    mock.name = name  # `name` is reserved by MagicMock's constructor
    return mock


def _path_collection(*ancestors: tuple[str, str]) -> MagicMock:
    return MagicMock(entries=[_named(MagicMock(id=i), n) for i, n in ancestors])


def _box_folder(folder_id: str, name: str, ancestors=ABOVE_ROOT) -> MagicMock:
    folder = MagicMock(id=folder_id, path_collection=_path_collection(*ancestors))
    return _named(folder, name)


def _box_file(file_id: str = "9", name: str = "pack.step", ancestors=ABOVE_ROOT, **attrs):
    """A stand-in for a box-sdk-gen file object inside the dashboard tree."""
    defaults = {"size": 4096, "modified_at": None, "sha_1": None}
    file_obj = MagicMock(
        id=file_id,
        file_version=MagicMock(id=f"v-{file_id}"),
        path_collection=_path_collection(*ancestors),
    )
    for key, value in {**defaults, **attrs}.items():
        setattr(file_obj, key, value)
    return _named(file_obj, name)


def _folder_items(*entries):
    return MagicMock(entries=list(entries))


def _folder_entry(folder_id: str, name: str):
    entry = MagicMock(id=folder_id, type=FolderBaseTypeField.FOLDER, size=None, modified_at=None)
    return _named(entry, name)


@pytest.fixture
def box_service():
    service = BoxService(get_settings())
    service._client = MagicMock()
    return service


def test_list_folder_maps_entries(box_service):
    entry = MagicMock(id="111", size=2048, modified_at=None)
    # box-sdk-gen returns a real enum here, not a plain string — this test guards
    # against regressing back to str(entry.type), which stringifies to
    # "FileBaseTypeField.FILE" instead of "file".
    entry.type = FileBaseTypeField.FILE
    _named(entry, "spec.pdf")
    box_service._client.folders.get_folder_by_id.return_value = _box_folder("42", "Zephyr")
    box_service._client.folders.get_folder_items.return_value = _folder_items(entry)

    listing = box_service.list_folder("42")

    assert (listing.id, listing.name) == ("42", "Zephyr")
    assert [(f.id, f.name) for f in listing.path] == [(DASHBOARD_ROOT_ID, "CDX")]
    assert len(listing.items) == 1
    assert (listing.items[0].id, listing.items[0].type) == ("111", "file")
    assert (listing.items[0].name, listing.items[0].size) == ("spec.pdf", 2048)


def test_dashboard_root_has_empty_path(box_service):
    box_service._client.folders.get_folder_by_id.return_value = _box_folder(
        DASHBOARD_ROOT_ID, "CDX", ancestors=ABOVE_ROOT[:1]
    )

    assert box_service.get_folder(DASHBOARD_ROOT_ID).path == []


def test_folders_outside_dashboard_root_are_not_found(box_service):
    box_service._client.folders.get_folder_by_id.return_value = _box_folder(
        "7", "Someone's taxes", ancestors=ABOVE_ROOT[:1]
    )

    with pytest.raises(BoxNotFoundError):
        box_service.list_folder("7")
    box_service._client.folders.get_folder_items.assert_not_called()


def test_files_outside_dashboard_root_are_not_found(box_service):
    box_service._client.files.get_file_by_id.return_value = _box_file(ancestors=ABOVE_ROOT[:1])

    with pytest.raises(BoxNotFoundError):
        box_service.get_file_metadata("9")


def test_get_file_metadata_maps_sha_1_attribute(box_service):
    # box-sdk-gen maps the JSON `sha1` field to the Python attribute `sha_1` —
    # this test guards against silently regressing back to the wrong name.
    box_service._client.files.get_file_by_id.return_value = _box_file(
        ancestors=[*ABOVE_ROOT, ("42", "Zephyr")], sha_1="abc123"
    )

    metadata = box_service.get_file_metadata("9")

    assert metadata.box_sha1 == "abc123"
    assert metadata.parent_id == "42"
    assert metadata.version_id == "v-9"
    assert [f.name for f in metadata.path] == ["CDX", "Zephyr"]


def test_open_file_content_reads_requested_version(box_service):
    box_service._client.files.get_file_by_id.return_value = _box_file()
    box_service._client.downloads.download_file.return_value = BytesIO(b"file-bytes")

    content = b"".join(box_service.open_file_content(box_service.get_file_metadata("9"), "v1"))

    assert content == b"file-bytes"
    box_service._client.downloads.download_file.assert_called_once_with("9", version="v1")


def test_open_file_content_reads_in_chunks(box_service, monkeypatch):
    monkeypatch.setattr("app.services.box_client._DOWNLOAD_CHUNK_BYTES", 4)
    box_service._client.files.get_file_by_id.return_value = _box_file()
    box_service._client.downloads.download_file.return_value = BytesIO(b"file-bytes")

    chunks = box_service.open_file_content(box_service.get_file_metadata("9"))

    assert list(chunks) == [b"file", b"-byt", b"es"]


def test_download_of_file_box_is_still_preparing_is_a_service_error(box_service):
    box_service._client.files.get_file_by_id.return_value = _box_file()
    # box-sdk-gen returns None for Box's "202 Accepted, retry later" answer.
    box_service._client.downloads.download_file.return_value = None

    with pytest.raises(BoxServiceError, match="isn't ready"):
        box_service.open_file_content(box_service.get_file_metadata("9"))


def test_upload_file_creates_new_file(box_service):
    box_service._client.folders.get_folder_items.return_value = _folder_items()
    box_service._client.uploads.upload_file.return_value = _folder_items(
        _box_file("77", "notes.md")
    )

    metadata = box_service.upload_file(DASHBOARD_ROOT_ID, "notes.md", BytesIO(b"hello world!"), 12)

    assert (metadata.id, metadata.parent_id, metadata.version_id) == (
        "77",
        DASHBOARD_ROOT_ID,
        "v-77",
    )
    box_service._client.uploads.upload_file_version.assert_not_called()


def test_upload_file_with_existing_name_uploads_new_version(box_service):
    existing = _box_file("77", "notes.md", type=FileBaseTypeField.FILE)
    box_service._client.folders.get_folder_items.return_value = _folder_items(existing)
    box_service._client.uploads.upload_file_version.return_value = _folder_items(
        _box_file("77", "notes.md")
    )

    metadata = box_service.upload_file(DASHBOARD_ROOT_ID, "notes.md", BytesIO(b"v2"), 2)

    assert metadata.id == "77"
    assert box_service._client.uploads.upload_file_version.call_args.args[0] == "77"
    box_service._client.uploads.upload_file.assert_not_called()


class FakeChunkedUploads:
    """Box's upload-session API, checking what Box checks: each part's SHA-1
    and byte range, then the whole file's SHA-1 at commit."""

    def __init__(self, part_size: int = 4) -> None:
        self.part_size = part_size
        self.sessions: list[tuple] = []
        self.received = bytearray()
        self.parts: list[MagicMock] = []
        self.busy_commits = 0  # commits answered "202, still processing" first
        self.fail_part: int | None = None
        self.aborted = False

    def _session(self) -> MagicMock:
        endpoints = MagicMock(upload_part="part-url", commit="commit-url", abort="abort-url")
        return MagicMock(part_size=self.part_size, session_endpoints=endpoints)

    def create_file_upload_session(self, folder_id, file_size, file_name):
        self.sessions.append(("new", folder_id, file_size, file_name))
        return self._session()

    def create_file_upload_session_for_existing_file(self, file_id, file_size, *, file_name):
        self.sessions.append(("version", file_id, file_size, file_name))
        return self._session()

    def upload_file_part_by_url(self, url, body, digest, content_range):
        if self.fail_part == len(self.parts):
            raise box_api_error(500)
        data = body.read()
        assert digest == f"sha={_b64_sha1(data)}"
        start = len(self.received)
        assert content_range.startswith(f"bytes {start}-{start + len(data) - 1}/")
        self.received += data
        self.parts.append(MagicMock(offset=start, size=len(data)))
        return MagicMock(part=self.parts[-1])

    def create_file_upload_session_commit_by_url(self, url, parts, digest):
        assert parts == self.parts
        assert digest == f"sha={_b64_sha1(bytes(self.received))}"
        if self.busy_commits:
            self.busy_commits -= 1
            return None
        return _folder_items(MagicMock(id="88"))

    def delete_file_upload_session_by_url(self, url):
        assert url == "abort-url"
        self.aborted = True


def _b64_sha1(data: bytes) -> str:
    return base64.b64encode(hashlib.sha1(data).digest()).decode()


@pytest.fixture
def chunked(box_service, monkeypatch):
    """Chunked uploads from 10 bytes, in 4-byte parts, with no commit retry delay."""
    monkeypatch.setattr("app.services.box_client.CHUNKED_UPLOAD_MIN_BYTES", 10)
    monkeypatch.setattr("app.services.box_client._COMMIT_RETRY_SECONDS", 0)
    fake = FakeChunkedUploads()
    box_service._client.chunked_uploads = fake
    box_service._client.folders.get_folder_items.return_value = _folder_items()
    box_service._client.files.get_file_by_id.return_value = _box_file("88", "pack.step")
    return fake


def test_large_file_is_uploaded_in_parts(box_service, chunked):
    content = b"0123456789"

    metadata = box_service.upload_file(DASHBOARD_ROOT_ID, "pack.step", BytesIO(content), 10)

    assert chunked.sessions == [("new", DASHBOARD_ROOT_ID, 10, "pack.step")]
    assert bytes(chunked.received) == content
    assert [p.size for p in chunked.parts] == [4, 4, 2]
    assert (metadata.id, metadata.version_id) == ("88", "v-88")
    box_service._client.files.get_file_by_id.assert_called_once()
    assert box_service._client.files.get_file_by_id.call_args.args == ("88",)
    box_service._client.uploads.upload_file.assert_not_called()
    assert not chunked.aborted


def test_large_file_with_existing_name_becomes_new_version(box_service, chunked):
    existing = _box_file("77", "pack.step", type=FileBaseTypeField.FILE)
    box_service._client.folders.get_folder_items.return_value = _folder_items(existing)

    box_service.upload_file(DASHBOARD_ROOT_ID, "pack.step", BytesIO(b"0123456789"), 10)

    assert chunked.sessions == [("version", "77", 10, "pack.step")]
    box_service._client.uploads.upload_file_version.assert_not_called()


def test_chunked_upload_waits_for_box_to_assemble_parts(box_service, chunked):
    chunked.busy_commits = 2

    metadata = box_service.upload_file(DASHBOARD_ROOT_ID, "pack.step", BytesIO(b"0" * 10), 10)

    assert metadata.id == "88"


def test_chunked_upload_gives_up_if_box_never_assembles_parts(box_service, chunked):
    chunked.busy_commits = 100

    with pytest.raises(BoxServiceError, match="didn't finish"):
        box_service.upload_file(DASHBOARD_ROOT_ID, "pack.step", BytesIO(b"0" * 10), 10)
    assert chunked.aborted


def test_failed_part_aborts_the_upload_session(box_service, chunked):
    chunked.fail_part = 1

    with pytest.raises(BoxServiceError):
        box_service.upload_file(DASHBOARD_ROOT_ID, "pack.step", BytesIO(b"0" * 10), 10)
    assert chunked.aborted
    box_service._client.files.get_file_by_id.assert_not_called()


def test_file_shorter_than_its_size_aborts_the_upload_session(box_service, chunked):
    with pytest.raises(BoxServiceError, match="ended after 8 of 12 bytes"):
        box_service.upload_file(DASHBOARD_ROOT_ID, "pack.step", BytesIO(b"0" * 8), 12)
    assert chunked.aborted


def test_ensure_folder_reuses_existing_folder(box_service):
    box_service._client.folders.get_folder_items.return_value = _folder_items(
        _folder_entry("5", "Battery")
    )

    assert box_service.ensure_folder("1", "Battery") == "5"
    box_service._client.folders.create_folder.assert_not_called()


def test_ensure_folder_creates_missing_folder(box_service):
    box_service._client.folders.get_folder_items.return_value = _folder_items(
        _folder_entry("5", "Battery")
    )
    box_service._client.folders.create_folder.return_value = MagicMock(id="6")

    assert box_service.ensure_folder("1", "Solar") == "6"
    name, parent = box_service._client.folders.create_folder.call_args.args
    assert (name, parent.id) == ("Solar", "1")


def test_404_translates_to_not_found(box_service):
    box_service._client.files.get_file_by_id.side_effect = box_api_error(404)

    with pytest.raises(BoxNotFoundError):
        box_service.get_file_metadata("missing")


def test_other_api_error_translates_to_service_error(box_service):
    box_service._client.files.get_file_by_id.side_effect = box_api_error(500)

    with pytest.raises(BoxServiceError):
        box_service.get_file_metadata("9")
