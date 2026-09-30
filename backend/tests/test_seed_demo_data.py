from unittest.mock import MagicMock

import pytest

from app.db import get_sessionmaker, run_migrations
from app.schemas.box import BoxFileMetadata, BoxFolder, BoxFolderRef
from app.subsystems import SUBSYSTEMS
from scripts.seed_demo_data import (
    DEMO_COMMITS,
    DEMO_HEADER,
    DemoDataExistsError,
    seed_demo_data,
)
from tests.conftest import DASHBOARD_ROOT_ID, TEST_USER


class FolderTreeBox:
    """A Box stand-in with a real in-memory folder tree, so subsystem detection
    works the same way it does against Box."""

    def __init__(self) -> None:
        self.folders = {DASHBOARD_ROOT_ID: BoxFolder(id=DASHBOARD_ROOT_ID, name="CDX")}
        self.uploads: list[tuple[str, str, bytes]] = []

    def ensure_folder(self, parent_id: str, name: str) -> str:
        folder_id = f"{parent_id}/{name}"
        parent = self.folders[parent_id]
        path = [*parent.path, BoxFolderRef(id=parent.id, name=parent.name)]
        self.folders.setdefault(folder_id, BoxFolder(id=folder_id, name=name, path=path))
        return folder_id

    def get_folder(self, folder_id: str) -> BoxFolder:
        return self.folders[folder_id]

    def upload_file(self, folder_id: str, name: str, content: bytes) -> BoxFileMetadata:
        self.uploads.append((folder_id, name, content))
        return BoxFileMetadata(id=f"file-{len(self.uploads)}", name=name, size=len(content))


@pytest.fixture
def db():
    run_migrations()
    with get_sessionmaker()() as session:
        yield session


def _seed(db, fake_xrpl, box=None, **kwargs):
    return seed_demo_data(
        db,
        box or FolderTreeBox(),
        fake_xrpl,
        root_folder_id=DASHBOARD_ROOT_ID,
        vehicle="Zephyr",
        author=TEST_USER,
        log=MagicMock(),
        **kwargs,
    )


def test_seeds_every_subsystem_through_the_real_pipeline(db, fake_xrpl):
    box = FolderTreeBox()

    seeded = _seed(db, fake_xrpl, box)

    assert len(seeded) == len(DEMO_COMMITS)
    assert {c.subsystem for c in seeded} == {s.slug for s in SUBSYSTEMS}
    assert all(c.anchor_status == "anchored" for c in seeded)
    # Every sample file announces itself as demo data on its first line.
    assert all(DEMO_HEADER.encode() in content.splitlines()[0] for _, _, content in box.uploads)
    review_folders = {folder for folder, name, _ in box.uploads if name.endswith("-review.md")}
    assert all(folder.endswith("/Design Reviews") for folder in review_folders)


def test_refuses_to_seed_twice_without_force(db, fake_xrpl):
    _seed(db, fake_xrpl)

    with pytest.raises(DemoDataExistsError):
        _seed(db, fake_xrpl)
    assert len(_seed(db, fake_xrpl, force=True)) == len(DEMO_COMMITS)


def test_set_stages_only_fills_unset_stages(db, client, fake_xrpl):
    client.patch("/api/subsystems/battery", json={"stage": "concept"})

    _seed(db, fake_xrpl, set_stages=True)

    cards = {c["slug"]: c for c in client.get("/api/subsystems").json()}
    assert cards["battery"]["stage"] == "concept"
    assert cards["solar"]["stage"] == "testing"
    assert all(card["owner_name"] is None for card in cards.values())
