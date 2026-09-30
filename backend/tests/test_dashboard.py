from app.subsystems import SUBSYSTEMS
from tests.conftest import TEST_USER, post_cdx_commit


def _card(client, slug: str) -> dict:
    return next(c for c in client.get("/api/subsystems").json() if c["slug"] == slug)


def test_every_subsystem_has_a_card_even_without_activity(client):
    cards = client.get("/api/subsystems").json()

    assert [c["slug"] for c in cards] == [s.slug for s in SUBSYSTEMS]
    assert cards[0]["commit_count"] == 0
    assert cards[0]["stage"] is None
    assert cards[0]["recent_commits"] == []


def test_cards_aggregate_commits_per_subsystem(client, box):
    post_cdx_commit(client, message="first")
    post_cdx_commit(client, message="second")

    battery = _card(client, "battery")

    assert (battery["commit_count"], battery["anchored_count"]) == (2, 2)
    assert [c["message"] for c in battery["recent_commits"]] == ["second", "first"]
    assert battery["last_commit_at"] is not None
    assert _card(client, "solar")["commit_count"] == 0


def test_patch_updates_only_the_fields_sent(client):
    client.patch("/api/subsystems/battery", json={"owner_name": "Ada", "stage": "design"})
    response = client.patch("/api/subsystems/battery", json={"stage": "review"})

    assert response.status_code == 200
    card = response.json()
    assert (card["owner_name"], card["stage"]) == ("Ada", "review")
    assert card["updated_by"] == TEST_USER.name


def test_patch_with_blank_or_null_clears_a_field(client):
    client.patch("/api/subsystems/battery", json={"owner_name": "Ada", "status_note": "On track"})

    card = client.patch(
        "/api/subsystems/battery", json={"owner_name": "  ", "status_note": None}
    ).json()

    assert (card["owner_name"], card["status_note"]) == (None, None)


def test_patch_rejects_unknown_subsystems_and_stages(client):
    assert client.patch("/api/subsystems/warp-drive", json={}).status_code == 404
    assert client.patch("/api/subsystems/battery", json={"stage": "vibes"}).status_code == 422


def test_subsystems_require_login(anonymous_client):
    assert anonymous_client.get("/api/subsystems").status_code == 401


def test_public_summary_needs_no_login_and_hides_team_details(client, box, anonymous_client):
    client.patch("/api/subsystems/battery", json={"owner_name": "Ada", "stage": "testing"})
    post_cdx_commit(client)

    summary = anonymous_client.get("/api/public/summary").json()

    assert (summary["total_commits"], summary["anchored_commits"]) == (1, 1)
    assert summary["contributors"] == 1
    battery = next(s for s in summary["subsystems"] if s["slug"] == "battery")
    assert battery["stage"] == "testing"
    assert "owner_name" not in battery
    [recent] = summary["recent_anchored"]
    assert recent["xrpl_explorer_url"]
    assert "author_name" not in recent and "message" not in recent
