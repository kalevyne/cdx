import hashlib

import pytest

from app.schemas.box import BoxFileMetadata, BoxFolder, BoxFolderRef
from app.services.cdx_commits import MAX_UPLOAD_BYTES
from tests.conftest import DASHBOARD_ROOT_ID, TEST_USER

# The commit target folder: CDX (Dashboard root) > Zephyr > Battery > CAD.
BATTERY_CAD = BoxFolder(
    id="4",
    name="CAD",
    path=[
        BoxFolderRef(id=DASHBOARD_ROOT_ID, name="CDX"),
        BoxFolderRef(id="2", name="Zephyr"),
        BoxFolderRef(id="3", name="Battery"),
    ],
)
VEHICLE_FOLDER = BoxFolder(
    id="4", name="Zephyr", path=[BoxFolderRef(id=DASHBOARD_ROOT_ID, name="CDX")]
)


@pytest.fixture
def box(box_service_mock):
    box_service_mock.get_folder.return_value = BATTERY_CAD
    box_service_mock.ensure_folder.return_value = "design-reviews-folder"
    box_service_mock.upload_file.side_effect = lambda folder_id, name, content: BoxFileMetadata(
        id=f"file-{name}", name=name, size=len(content), parent_id=folder_id, version_id="v1"
    )
    return box_service_mock


def _commit(client, message="Initial pack layout", **extra_files):
    files = {"file": ("pack.step", b"pack-bytes", "application/octet-stream"), **extra_files}
    return client.post("/api/cdx-commits", data={"folder_id": "4", "message": message}, files=files)


def test_create_cdx_commit_uploads_hashes_and_records(client, box):
    response = _commit(client)

    assert response.status_code == 201
    body = response.json()
    assert body["sha256_hash"] == hashlib.sha256(b"pack-bytes").hexdigest()
    assert body["box_file_id"] == "file-pack.step"
    assert body["box_file_version"] == "v1"
    assert body["subsystem"] == "battery"
    assert body["author_name"] == TEST_USER.name
    assert body["xrpl_tx_hash"] is None
    box.upload_file.assert_called_once_with("4", "pack.step", b"pack-bytes")

    assert client.get(f"/api/cdx-commits/{body['id']}").json() == body


def test_design_review_goes_to_subsystem_design_reviews_folder(client, box):
    review = ("review.pdf", b"review-bytes", "application/pdf")

    body = _commit(client, design_review=review).json()

    box.ensure_folder.assert_called_once_with("3", "Design Reviews")
    box.upload_file.assert_any_call("design-reviews-folder", "review.pdf", b"review-bytes")
    assert body["design_review_box_file_id"] == "file-review.pdf"
    assert body["design_review_sha256_hash"] == hashlib.sha256(b"review-bytes").hexdigest()


def test_commit_outside_subsystem_has_no_subsystem(client, box):
    box.get_folder.return_value = VEHICLE_FOLDER

    body = _commit(client, design_review=("review.pdf", b"r", "application/pdf")).json()

    assert body["subsystem"] is None
    box.ensure_folder.assert_not_called()
    box.upload_file.assert_any_call("4", "review.pdf", b"r")


def test_blank_message_is_rejected_before_uploading(client, box):
    response = _commit(client, message="   ")

    assert response.status_code == 422
    box.upload_file.assert_not_called()


def test_empty_file_is_rejected(client, box):
    response = _commit(client, file=("empty.txt", b"", "text/plain"))

    assert response.status_code == 422
    box.upload_file.assert_not_called()


def test_oversized_file_is_rejected(client, box):
    response = _commit(client, file=("huge.bin", b"x" * (MAX_UPLOAD_BYTES + 1), "x/y"))

    assert response.status_code == 413
    box.upload_file.assert_not_called()


def test_list_filters_by_subsystem_newest_first(client, box):
    first = _commit(client, message="first").json()
    second = _commit(client, message="second").json()
    box.get_folder.return_value = VEHICLE_FOLDER
    _commit(client, message="no subsystem")

    listed = client.get("/api/cdx-commits", params={"subsystem": "battery"}).json()

    assert [c["id"] for c in listed] == [second["id"], first["id"]]


def test_unknown_cdx_commit_returns_404(client):
    assert client.get("/api/cdx-commits/999").status_code == 404


def test_cdx_commits_require_login(anonymous_client):
    assert anonymous_client.get("/api/cdx-commits").status_code == 401
