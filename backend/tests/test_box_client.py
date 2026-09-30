from unittest.mock import MagicMock

import pytest
from box_sdk_gen import FileBaseTypeField, FolderBaseTypeField

from app.config import get_settings
from app.services.box_client import BoxNotFoundError, BoxService, BoxServiceError
from tests.conftest import box_api_error


@pytest.fixture
def box_service():
    service = BoxService(get_settings())
    service._client = MagicMock()
    return service


def test_list_folder_maps_entries(box_service):
    folder = MagicMock()
    folder.name = "Dashboard Root"

    entry = MagicMock()
    entry.id = "111"
    # box-sdk-gen returns a real enum here, not a plain string — this test guards
    # against regressing back to str(entry.type), which stringifies to
    # "FileBaseTypeField.FILE" instead of "file".
    entry.type = FileBaseTypeField.FILE
    entry.name = "spec.pdf"
    entry.size = 2048
    entry.modified_at = None

    items_result = MagicMock()
    items_result.entries = [entry]

    box_service._client.folders.get_folder_by_id.return_value = folder
    box_service._client.folders.get_folder_items.return_value = items_result

    listing = box_service.list_folder("42")

    assert listing.folder_id == "42"
    assert listing.folder_name == "Dashboard Root"
    assert len(listing.items) == 1
    assert listing.items[0].id == "111"
    assert listing.items[0].type == "file"
    assert listing.items[0].name == "spec.pdf"
    assert listing.items[0].size == 2048


def _box_file(file_id: str = "9", name: str = "battery-pack.step", **attrs):
    """A stand-in for a box-sdk-gen file object."""
    defaults = {"size": 4096, "parent": None, "modified_at": None, "sha_1": None}
    file_obj = MagicMock(id=file_id, file_version=MagicMock(id=f"v-{file_id}"))
    file_obj.name = name  # `name` is reserved by MagicMock's constructor
    for key, value in {**defaults, **attrs}.items():
        setattr(file_obj, key, value)
    return file_obj


def test_get_file_metadata_maps_sha_1_attribute(box_service):
    # box-sdk-gen maps the JSON `sha1` field to the Python attribute `sha_1` —
    # this test guards against silently regressing back to the wrong name.
    box_service._client.files.get_file_by_id.return_value = _box_file(
        parent=MagicMock(id="42"), sha_1="abc123"
    )

    metadata = box_service.get_file_metadata("9")

    assert metadata.box_sha1 == "abc123"
    assert metadata.parent_id == "42"
    assert metadata.version_id == "v-9"


def test_download_file_reads_stream(box_service):
    stream = MagicMock()
    stream.read.return_value = b"file-bytes"
    box_service._client.downloads.download_file.return_value = stream

    content = box_service.download_file("9", version_id="v1")

    assert content == b"file-bytes"
    box_service._client.downloads.download_file.assert_called_once_with("9", version="v1")


def test_upload_file_creates_new_file(box_service):
    box_service._client.folders.get_folder_items.return_value = _folder_items()
    box_service._client.uploads.upload_file.return_value = MagicMock(
        entries=[_box_file("77", "notes.md")]
    )

    metadata = box_service.upload_file("42", "notes.md", b"hello world!")

    assert (metadata.id, metadata.parent_id, metadata.version_id) == ("77", "42", "v-77")
    box_service._client.uploads.upload_file_version.assert_not_called()


def test_upload_file_with_existing_name_uploads_new_version(box_service):
    existing = _box_file("77", "notes.md", type=FileBaseTypeField.FILE)
    box_service._client.folders.get_folder_items.return_value = _folder_items(existing)
    box_service._client.uploads.upload_file_version.return_value = MagicMock(
        entries=[_box_file("77", "notes.md")]
    )

    metadata = box_service.upload_file("42", "notes.md", b"v2")

    assert metadata.id == "77"
    assert box_service._client.uploads.upload_file_version.call_args.args[0] == "77"
    box_service._client.uploads.upload_file.assert_not_called()


def test_get_folder_path_ends_with_folder_itself(box_service):
    folder = MagicMock(id="3")
    folder.name = "Battery"
    root, vehicle = MagicMock(id="0"), MagicMock(id="2")
    root.name, vehicle.name = "All Files", "Zephyr"
    folder.path_collection.entries = [root, vehicle]
    box_service._client.folders.get_folder_by_id.return_value = folder

    path = box_service.get_folder_path("3")

    assert [(f.id, f.name) for f in path] == [
        ("0", "All Files"),
        ("2", "Zephyr"),
        ("3", "Battery"),
    ]


def test_404_translates_to_not_found(box_service):
    box_service._client.files.get_file_by_id.side_effect = box_api_error(404)

    with pytest.raises(BoxNotFoundError):
        box_service.get_file_metadata("missing")


def test_other_api_error_translates_to_service_error(box_service):
    box_service._client.files.get_file_by_id.side_effect = box_api_error(500)

    with pytest.raises(BoxServiceError):
        box_service.get_file_metadata("9")


def _folder_items(*entries):
    result = MagicMock()
    result.entries = list(entries)
    return result


def _folder_entry(folder_id: str, name: str):
    entry = MagicMock(id=folder_id, type=FolderBaseTypeField.FOLDER, size=None, modified_at=None)
    entry.name = name
    return entry


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
