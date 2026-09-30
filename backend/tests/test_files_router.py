from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.box import BoxFileMetadata, BoxFolderListing, BoxItem
from app.services.box_client import BoxNotFoundError, get_box_service


def _client_with_box_service(mock_service) -> TestClient:
    app.dependency_overrides[get_box_service] = lambda: mock_service
    return TestClient(app)


def test_get_folder_returns_listing():
    mock_service = MagicMock()
    mock_service.list_folder.return_value = BoxFolderListing(
        folder_id="42",
        folder_name="Dashboard",
        items=[BoxItem(id="1", type="file", name="a.txt")],
    )
    with _client_with_box_service(mock_service) as client:
        response = client.get("/api/folders/42")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["folder_name"] == "Dashboard"


def test_get_dashboard_root_folder_uses_configured_id():
    mock_service = MagicMock()
    mock_service.list_folder.return_value = BoxFolderListing(
        folder_id="0", folder_name="Dashboard Root", items=[]
    )
    with _client_with_box_service(mock_service) as client:
        response = client.get("/api/folders")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    mock_service.list_folder.assert_called_once_with("0")


def test_get_file_not_found_returns_404():
    mock_service = MagicMock()
    mock_service.get_file_metadata.side_effect = BoxNotFoundError("nope")
    with _client_with_box_service(mock_service) as client:
        response = client.get("/api/files/999")

    app.dependency_overrides.clear()
    assert response.status_code == 404


def test_upload_file_returns_created_metadata():
    mock_service = MagicMock()
    mock_service.upload_file.return_value = BoxFileMetadata(
        id="77", name="notes.md", size=12, parent_id="42"
    )
    with _client_with_box_service(mock_service) as client:
        response = client.post(
            "/api/folders/42/files",
            files={"file": ("notes.md", b"hello world!", "text/plain")},
        )

    app.dependency_overrides.clear()
    assert response.status_code == 201
    assert response.json()["id"] == "77"


def test_download_file_returns_bytes_with_filename():
    mock_service = MagicMock()
    mock_service.get_file_metadata.return_value = BoxFileMetadata(
        id="9", name="notes.md", size=5, parent_id="42"
    )
    mock_service.download_file.return_value = b"hello"
    with _client_with_box_service(mock_service) as client:
        response = client.get("/api/files/9/content")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.content == b"hello"
    assert "notes.md" in response.headers["content-disposition"]
