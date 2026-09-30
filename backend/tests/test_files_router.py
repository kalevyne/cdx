from app.schemas.box import BoxFileMetadata, BoxFolderListing, BoxFolderRef, BoxItem
from app.services.box_client import BoxNotFoundError, BoxServiceError
from tests.conftest import DASHBOARD_ROOT_ID


def test_get_folder_returns_listing(client, box_service_mock):
    box_service_mock.list_folder.return_value = BoxFolderListing(
        id="42",
        name="Zephyr",
        path=[BoxFolderRef(id=DASHBOARD_ROOT_ID, name="CDX")],
        items=[BoxItem(id="1", type="file", name="a.txt")],
    )

    response = client.get("/api/folders/42")

    assert response.status_code == 200
    assert response.json()["name"] == "Zephyr"
    assert response.json()["path"] == [{"id": DASHBOARD_ROOT_ID, "name": "CDX"}]


def test_get_dashboard_root_folder_uses_configured_id(client, box_service_mock):
    box_service_mock.list_folder.return_value = BoxFolderListing(
        id=DASHBOARD_ROOT_ID, name="CDX", items=[]
    )

    response = client.get("/api/folders")

    assert response.status_code == 200
    box_service_mock.list_folder.assert_called_once_with(DASHBOARD_ROOT_ID)


def test_unconfigured_dashboard_root_returns_503(client, monkeypatch):
    from app.config import get_settings

    monkeypatch.setenv("BOX_DASHBOARD_ROOT_FOLDER_ID", "")
    get_settings.cache_clear()

    response = client.get("/api/folders")

    assert response.status_code == 503


def test_get_file_not_found_returns_404(client, box_service_mock):
    box_service_mock.get_file_metadata.side_effect = BoxNotFoundError("nope")

    response = client.get("/api/files/999")

    assert response.status_code == 404


def test_box_failure_returns_502(client, box_service_mock):
    box_service_mock.list_folder.side_effect = BoxServiceError("boom")

    response = client.get("/api/folders/42")

    assert response.status_code == 502


def test_download_file_returns_bytes_with_filename(client, box_service_mock):
    box_service_mock.download_file.return_value = (
        BoxFileMetadata(id="9", name="notes.md", size=5, parent_id="42"),
        b"hello",
    )

    response = client.get("/api/files/9/content")

    assert response.status_code == 200
    assert response.content == b"hello"
    assert "notes.md" in response.headers["content-disposition"]


def test_box_routes_require_login(anonymous_client):
    assert anonymous_client.get("/api/folders/42").status_code == 401


def test_download_specific_version(client, box_service_mock):
    box_service_mock.download_file.return_value = (
        BoxFileMetadata(id="9", name="notes.md", size=5, parent_id="42"),
        b"old",
    )

    response = client.get("/api/files/9/content", params={"version_id": "v1"})

    assert response.content == b"old"
    box_service_mock.download_file.assert_called_once_with("9", "v1")


def test_download_non_ascii_filename(client, box_service_mock):
    box_service_mock.download_file.return_value = (
        BoxFileMetadata(id="9", name='设计 "v2".pdf', size=5, parent_id="42"),
        b"hello",
    )

    response = client.get("/api/files/9/content")

    assert response.status_code == 200
    assert (
        "filename*=UTF-8''%E8%AE%BE%E8%AE%A1%20%22v2%22.pdf"
        in (response.headers["content-disposition"])
    )
