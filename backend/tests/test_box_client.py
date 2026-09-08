from unittest.mock import MagicMock

import pytest
from box_sdk_gen import BoxAPIError

from app.config import get_settings
from app.services.box_client import BoxNotFoundError, BoxService, BoxServiceError


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
    entry.type = "file"
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
    assert listing.items[0].name == "spec.pdf"
    assert listing.items[0].size == 2048


def test_get_file_metadata_maps_sha_1_attribute(box_service):
    # box-sdk-gen maps the JSON `sha1` field to the Python attribute `sha_1` —
    # this test guards against silently regressing back to the wrong name.
    file_obj = MagicMock()
    file_obj.id = "9"
    file_obj.name = "battery-pack.step"
    file_obj.size = 4096
    file_obj.parent = MagicMock(id="42")
    file_obj.modified_at = None
    file_obj.sha_1 = "abc123"

    box_service._client.files.get_file_by_id.return_value = file_obj

    metadata = box_service.get_file_metadata("9")

    assert metadata.box_sha1 == "abc123"
    assert metadata.parent_id == "42"


def test_download_file_reads_stream(box_service):
    stream = MagicMock()
    stream.read.return_value = b"file-bytes"
    box_service._client.downloads.download_file.return_value = stream

    content = box_service.download_file("9")

    assert content == b"file-bytes"


def test_upload_file_returns_metadata(box_service):
    uploaded = MagicMock()
    uploaded.id = "77"
    uploaded.name = "notes.md"
    uploaded.size = 12
    uploaded.parent = None
    uploaded.modified_at = None
    uploaded.sha_1 = "deadbeef"

    result = MagicMock()
    result.entries = [uploaded]
    box_service._client.uploads.upload_file.return_value = result

    metadata = box_service.upload_file("42", "notes.md", b"hello world!")

    assert metadata.id == "77"
    assert metadata.parent_id == "42"
    box_service._client.uploads.upload_file.assert_called_once()


def test_404_translates_to_not_found(box_service):
    response_info = MagicMock(status_code=404)
    error = BoxAPIError(request_info=MagicMock(), response_info=response_info, message="not found")
    box_service._client.files.get_file_by_id.side_effect = error

    with pytest.raises(BoxNotFoundError):
        box_service.get_file_metadata("missing")


def test_other_api_error_translates_to_service_error(box_service):
    response_info = MagicMock(status_code=500)
    error = BoxAPIError(request_info=MagicMock(), response_info=response_info, message="boom")
    box_service._client.files.get_file_by_id.side_effect = error

    with pytest.raises(BoxServiceError):
        box_service.get_file_metadata("9")
