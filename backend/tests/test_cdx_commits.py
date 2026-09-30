import hashlib

from app.schemas.box import BoxFolder, BoxFolderRef
from app.services.cdx_commits import MAX_UPLOAD_BYTES
from tests.conftest import DASHBOARD_ROOT_ID, TEST_USER, post_cdx_commit

VEHICLE_FOLDER = BoxFolder(
    id="4", name="Zephyr", path=[BoxFolderRef(id=DASHBOARD_ROOT_ID, name="CDX")]
)


def test_create_cdx_commit_uploads_hashes_and_records(client, box):
    response = post_cdx_commit(client)

    assert response.status_code == 201
    body = response.json()
    assert body["sha256_hash"] == hashlib.sha256(b"pack-bytes").hexdigest()
    assert body["box_file_id"] == "file-pack.step"
    assert body["box_file_version"] == "v1"
    assert body["subsystem"] == "battery"
    assert body["author_name"] == TEST_USER.name
    assert body["xrpl_tx_hash"] is None
    box.upload_file.assert_called_once_with("4", "pack.step", b"pack-bytes")

    fetched = client.get(f"/api/cdx-commits/{body['id']}").json()
    assert (fetched["id"], fetched["sha256_hash"]) == (body["id"], body["sha256_hash"])


def test_design_review_goes_to_subsystem_design_reviews_folder(client, box):
    review = ("review.pdf", b"review-bytes", "application/pdf")

    body = post_cdx_commit(client, design_review=review).json()

    box.ensure_folder.assert_called_once_with("3", "Design Reviews")
    box.upload_file.assert_any_call("design-reviews-folder", "review.pdf", b"review-bytes")
    assert body["design_review_box_file_id"] == "file-review.pdf"
    assert body["design_review_sha256_hash"] == hashlib.sha256(b"review-bytes").hexdigest()


def test_commit_outside_subsystem_has_no_subsystem(client, box):
    box.get_folder.return_value = VEHICLE_FOLDER

    body = post_cdx_commit(client, design_review=("review.pdf", b"r", "application/pdf")).json()

    assert body["subsystem"] is None
    box.ensure_folder.assert_not_called()
    box.upload_file.assert_any_call("4", "review.pdf", b"r")


def test_blank_message_is_rejected_before_uploading(client, box):
    response = post_cdx_commit(client, message="   ")

    assert response.status_code == 422
    box.upload_file.assert_not_called()


def test_empty_file_is_rejected(client, box):
    response = post_cdx_commit(client, file=("empty.txt", b"", "text/plain"))

    assert response.status_code == 422
    box.upload_file.assert_not_called()


def test_oversized_file_is_rejected(client, box):
    response = post_cdx_commit(client, file=("huge.bin", b"x" * (MAX_UPLOAD_BYTES + 1), "x/y"))

    assert response.status_code == 413
    box.upload_file.assert_not_called()


def test_list_filters_by_subsystem_newest_first(client, box):
    first = post_cdx_commit(client, message="first").json()
    second = post_cdx_commit(client, message="second").json()
    box.get_folder.return_value = VEHICLE_FOLDER
    post_cdx_commit(client, message="no subsystem")

    listed = client.get("/api/cdx-commits", params={"subsystem": "battery"}).json()

    assert [c["id"] for c in listed] == [second["id"], first["id"]]


def test_unknown_cdx_commit_returns_404(client):
    assert client.get("/api/cdx-commits/999").status_code == 404


def test_cdx_commits_require_login(anonymous_client):
    assert anonymous_client.get("/api/cdx-commits").status_code == 401


def test_list_limit_is_validated(client):
    assert client.get("/api/cdx-commits", params={"limit": 0}).status_code == 422
    assert client.get("/api/cdx-commits", params={"limit": 201}).status_code == 422
