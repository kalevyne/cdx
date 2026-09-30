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
        box_service.download_file("9")
    box_service._client.downloads.download_file.assert_not_called()


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


def test_download_file_reads_stream(box_service):
    box_service._client.files.get_file_by_id.return_value = _box_file()
    box_service._client.downloads.download_file.return_value = MagicMock(
        read=MagicMock(return_value=b"file-bytes")
    )

    metadata, content = box_service.download_file("9", version_id="v1")

    assert (metadata.id, content) == ("9", b"file-bytes")
    box_service._client.downloads.download_file.assert_called_once_with("9", version="v1")


def test_upload_file_creates_new_file(box_service):
    box_service._client.folders.get_folder_items.return_value = _folder_items()
    box_service._client.uploads.upload_file.return_value = _folder_items(
        _box_file("77", "notes.md")
    )

    metadata = box_service.upload_file(DASHBOARD_ROOT_ID, "notes.md", b"hello world!")

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

    metadata = box_service.upload_file(DASHBOARD_ROOT_ID, "notes.md", b"v2")

    assert metadata.id == "77"
    assert box_service._client.uploads.upload_file_version.call_args.args[0] == "77"
    box_service._client.uploads.upload_file.assert_not_called()


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
