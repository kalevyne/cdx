import pytest

from app.schemas.box import BoxFileMetadata
from app.services.anchoring import MEMO_COMMIT_ID, MEMO_SHA256, anchor_pending_cdx_commits
from app.services.hashing import sha256_hex
from app.services.xrpl_client import XrplError
from tests.conftest import post_cdx_commit


def test_commit_is_anchored_after_the_response(client, box, fake_xrpl):
    created = post_cdx_commit(client).json()
    assert created["anchor_status"] == "pending"  # the response doesn't wait on XRPL

    anchored = client.get(f"/api/cdx-commits/{created['id']}").json()

    assert anchored["anchor_status"] == "anchored"
    assert anchored["xrpl_network"] == "testnet"
    assert anchored["xrpl_explorer_url"].endswith(anchored["xrpl_tx_hash"])
    assert anchored["anchored_at"] is not None
    assert fake_xrpl.ledger[anchored["xrpl_tx_hash"]] == {
        MEMO_COMMIT_ID: str(created["id"]),
        MEMO_SHA256: sha256_hex(b"pack-bytes"),
    }


def test_design_review_hash_is_anchored_too(client, box, fake_xrpl):
    review = ("review.pdf", b"review-bytes", "application/pdf")
    cdx_commit_id = post_cdx_commit(client, design_review=review).json()["id"]

    tx_hash = client.get(f"/api/cdx-commits/{cdx_commit_id}").json()["xrpl_tx_hash"]

    assert fake_xrpl.ledger[tx_hash]["cdx/design-review-sha256"] == sha256_hex(b"review-bytes")


def test_failed_anchoring_is_recorded_and_retryable(client, box, fake_xrpl):
    fake_xrpl.fail_with = XrplError("tecUNFUNDED_PAYMENT")
    cdx_commit_id = post_cdx_commit(client).json()["id"]

    failed = client.get(f"/api/cdx-commits/{cdx_commit_id}").json()
    assert (failed["anchor_status"], failed["anchor_error"]) == ("failed", "tecUNFUNDED_PAYMENT")

    fake_xrpl.fail_with = None
    assert client.post(f"/api/cdx-commits/{cdx_commit_id}/anchor").status_code == 202

    retried = client.get(f"/api/cdx-commits/{cdx_commit_id}").json()
    assert (retried["anchor_status"], retried["anchor_error"]) == ("anchored", None)


def test_unconfigured_xrpl_leaves_commits_pending(client, box, fake_xrpl):
    fake_xrpl.is_configured = False
    cdx_commit_id = post_cdx_commit(client).json()["id"]

    assert client.get(f"/api/cdx-commits/{cdx_commit_id}").json()["anchor_status"] == "pending"
    assert client.post(f"/api/cdx-commits/{cdx_commit_id}/anchor").status_code == 503


def test_startup_sweep_anchors_pending_commits(client, box, fake_xrpl):
    fake_xrpl.is_configured = False
    cdx_commit_id = post_cdx_commit(client).json()["id"]

    fake_xrpl.is_configured = True
    anchor_pending_cdx_commits(fake_xrpl)

    assert client.get(f"/api/cdx-commits/{cdx_commit_id}").json()["anchor_status"] == "anchored"


@pytest.fixture
def anchored_commit_id(client, box):
    cdx_commit_id = post_cdx_commit(client).json()["id"]
    box.download_file.return_value = (
        BoxFileMetadata(id="file-pack.step", name="pack.step", size=10),
        b"pack-bytes",
    )
    return cdx_commit_id


def test_verification_matches_box_and_ledger(client, box, anchored_commit_id):
    result = client.get(f"/api/cdx-commits/{anchored_commit_id}/verification").json()

    assert result["verified"] is True
    assert (result["box"]["status"], result["ledger"]["status"]) == ("match", "match")
    box.download_file.assert_called_once_with("file-pack.step", "v1")


def test_verification_detects_a_changed_file(client, box, anchored_commit_id):
    box.download_file.return_value = (box.download_file.return_value[0], b"tampered")

    result = client.get(f"/api/cdx-commits/{anchored_commit_id}/verification").json()

    assert result["verified"] is False
    assert result["box"]["status"] == "mismatch"
    assert result["box"]["observed_sha256"] == sha256_hex(b"tampered")


def test_verification_detects_a_different_ledger_memo(client, fake_xrpl, anchored_commit_id):
    tx_hash = client.get(f"/api/cdx-commits/{anchored_commit_id}").json()["xrpl_tx_hash"]
    fake_xrpl.ledger[tx_hash][MEMO_SHA256] = "0" * 64

    result = client.get(f"/api/cdx-commits/{anchored_commit_id}/verification").json()

    assert (result["verified"], result["ledger"]["status"]) == (False, "mismatch")


def test_verification_before_anchoring_is_unavailable(client, box, fake_xrpl):
    fake_xrpl.is_configured = False
    cdx_commit_id = post_cdx_commit(client).json()["id"]
    box.download_file.return_value = (None, b"pack-bytes")

    result = client.get(f"/api/cdx-commits/{cdx_commit_id}/verification").json()

    assert result["ledger"] == {
        "status": "unavailable",
        "observed_sha256": None,
        "detail": "Not anchored yet",
    }
    assert result["verified"] is False


def test_status_reports_whether_anchoring_is_enabled(client, fake_xrpl):
    assert client.get("/api/status").json() == {
        "anchoring_enabled": True,
        "xrpl_network": "testnet",
    }
    fake_xrpl.is_configured = False
    assert client.get("/api/status").json()["anchoring_enabled"] is False
