from app.schemas.box import BoxFileMetadata, BoxFolderListing, BoxFolderRef, BoxItem
from app.services.box_client import BoxNotFoundError, BoxServiceError
from app.services.file_downloads import MAX_PREVIEW_BYTES, DownloadSlots, get_download_slots
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


def _box_has_file(box_service_mock, content=b"hello", **metadata):
    fields = {"id": "9", "name": "notes.md", "size": len(content), "version_id": "v2"}
    box_service_mock.get_file_metadata.return_value = BoxFileMetadata(**{**fields, **metadata})
    box_service_mock.open_file_content.side_effect = lambda file, version_id=None: iter([content])


def test_download_file_returns_bytes_with_filename(client, box_service_mock):
    _box_has_file(box_service_mock)

    response = client.get("/api/files/9/content")

    assert response.status_code == 200
    assert response.content == b"hello"
    assert "notes.md" in response.headers["content-disposition"]


def test_download_url_may_end_with_the_file_name(client, box_service_mock):
    # Browsers that ignore Content-Disposition name the file after the URL.
    _box_has_file(box_service_mock)

    response = client.get("/api/files/9/content/notes.md", params={"version_id": "v1"})

    assert (response.status_code, response.content) == (200, b"hello")
    metadata = box_service_mock.get_file_metadata.return_value
    box_service_mock.open_file_content.assert_called_once_with(metadata, "v1")


def test_box_routes_require_login(anonymous_client):
    assert anonymous_client.get("/api/folders/42").status_code == 401
    assert anonymous_client.get("/api/files/9/preview").status_code == 401


def test_download_specific_version(client, box_service_mock):
    _box_has_file(box_service_mock, content=b"old")

    response = client.get("/api/files/9/content", params={"version_id": "v1"})

    assert response.content == b"old"
    metadata = box_service_mock.get_file_metadata.return_value
    box_service_mock.open_file_content.assert_called_once_with(metadata, "v1")


def test_download_non_ascii_filename(client, box_service_mock):
    _box_has_file(box_service_mock, name='设计 "v2".pdf')

    response = client.get("/api/files/9/content")

    assert response.status_code == 200
    assert (
        "filename*=UTF-8''%E8%AE%BE%E8%AE%A1%20%22v2%22.pdf"
        in (response.headers["content-disposition"])
    )


def test_file_content_is_never_served_as_a_renderable_type(client, box_service_mock):
    _box_has_file(box_service_mock, name="page.html", content=b"<script>alert(1)</script>")

    for route in ("content", "preview"):
        response = client.get(f"/api/files/9/{route}")

        assert response.headers["content-type"] == "application/octet-stream"
        assert response.headers["content-disposition"].startswith("attachment")
        assert response.headers["x-content-type-options"] == "nosniff"


def test_unchanged_file_is_not_downloaded_again(client, box_service_mock):
    _box_has_file(box_service_mock)
    first = client.get("/api/files/9/preview")
    assert first.headers["cache-control"] == "private, no-cache"
    box_service_mock.open_file_content.reset_mock()

    # Proxies that compress a response mark its ETag weak; it still matches.
    for etag in (first.headers["etag"], f"W/{first.headers['etag']}"):
        response = client.get("/api/files/9/preview", headers={"If-None-Match": etag})

        assert response.status_code == 304
        assert response.content == b""
    box_service_mock.open_file_content.assert_not_called()


def test_new_version_is_downloaded_despite_cached_copy(client, box_service_mock):
    _box_has_file(box_service_mock)
    stale_etag = client.get("/api/files/9/content").headers["etag"]
    _box_has_file(box_service_mock, content=b"newer", version_id="v3")

    response = client.get("/api/files/9/content", headers={"If-None-Match": stale_etag})

    assert (response.status_code, response.content) == (200, b"newer")


def test_preview_returns_bytes(client, box_service_mock):
    _box_has_file(box_service_mock)

    response = client.get("/api/files/9/preview", params={"version_id": "v1"})

    assert (response.status_code, response.content) == (200, b"hello")


def test_preview_refuses_large_file_without_downloading_it(client, box_service_mock):
    _box_has_file(box_service_mock, name="chassis.step", size=MAX_PREVIEW_BYTES + 1)

    response = client.get("/api/files/9/preview")

    assert response.status_code == 413
    assert "chassis.step is larger than 20 MB" in response.json()["detail"]
    box_service_mock.open_file_content.assert_not_called()
    # Downloading it is still allowed.
    assert client.get("/api/files/9/content").status_code == 200


def test_missing_file_content_returns_404(client, box_service_mock):
    box_service_mock.get_file_metadata.side_effect = BoxNotFoundError("nope")

    assert client.get("/api/files/999/content").status_code == 404
    assert client.get("/api/files/999/preview").status_code == 404
    box_service_mock.open_file_content.assert_not_called()


def test_downloads_beyond_the_concurrency_limit_get_503(client, box_service_mock, monkeypatch):
    from app.main import app

    slots = DownloadSlots(limit=1)
    app.dependency_overrides[get_download_slots] = lambda: slots
    _box_has_file(box_service_mock)

    slots.acquire()  # another download is in flight
    busy = client.get("/api/files/9/content")
    slots.release()

    assert busy.status_code == 503
    box_service_mock.open_file_content.assert_not_called()
    # Each finished download gives its slot back, so the next ones go through.
    assert [client.get("/api/files/9/content").status_code for _ in range(3)] == [200, 200, 200]


def test_failed_box_download_gives_its_slot_back(client, box_service_mock):
    from app.main import app

    slots = DownloadSlots(limit=1)
    app.dependency_overrides[get_download_slots] = lambda: slots
    _box_has_file(box_service_mock)
    box_service_mock.open_file_content.side_effect = BoxServiceError("boom")

    assert client.get("/api/files/9/content").status_code == 502

    slots.acquire()  # would raise DownloadsBusyError if the slot had leaked
