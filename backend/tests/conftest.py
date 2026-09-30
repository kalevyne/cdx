import os
from unittest.mock import MagicMock

import pytest
from box_sdk_gen import BoxAPIError
from fastapi.testclient import TestClient

DASHBOARD_ROOT_ID = "100"

# Set before any test module imports app.main, which reads settings at import time.
os.environ.update(
    {
        "BOX_CLIENT_ID": "test-client-id",
        "BOX_CLIENT_SECRET": "test-client-secret",
        "BOX_DASHBOARD_ROOT_FOLDER_ID": DASHBOARD_ROOT_ID,
        "SESSION_SECRET": "test-session-secret",
        "FRONTEND_URL": "http://frontend.test",
    }
)

from app.auth import require_user  # noqa: E402
from app.schemas.auth import SessionUser  # noqa: E402
from app.schemas.box import BoxFileMetadata, BoxFolder, BoxFolderRef  # noqa: E402
from app.services.xrpl_client import AnchorReceipt  # noqa: E402

TEST_USER = SessionUser(box_user_id="u1", name="Ada Engineer", login="ada@berkeley.edu")


# A typical commit target folder: CDX (Dashboard root) > Zephyr > Battery > CAD.
BATTERY_CAD = BoxFolder(
    id="4",
    name="CAD",
    path=[
        BoxFolderRef(id=DASHBOARD_ROOT_ID, name="CDX"),
        BoxFolderRef(id="2", name="Zephyr"),
        BoxFolderRef(id="3", name="Battery"),
    ],
)


def post_cdx_commit(client, message="Initial pack layout", **extra_files):
    files = {"file": ("pack.step", b"pack-bytes", "application/octet-stream"), **extra_files}
    return client.post(
        "/api/cdx-commits", data={"folder_id": BATTERY_CAD.id, "message": message}, files=files
    )


def box_api_error(status_code: int) -> BoxAPIError:
    return BoxAPIError(
        request_info=MagicMock(), response_info=MagicMock(status_code=status_code), message="x"
    )


@pytest.fixture(autouse=True)
def _isolated_settings(tmp_path, monkeypatch):
    # A fresh SQLite file per test; the app's lifespan migrates it on startup.
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")

    from app.config import get_settings
    from app.db import get_engine, get_sessionmaker
    from app.services.xrpl_client import get_xrpl_client

    caches = (get_settings, get_engine, get_sessionmaker, get_xrpl_client)
    for cached in caches:
        cached.cache_clear()
    yield
    for cached in caches:
        cached.cache_clear()


class FakeXrpl:
    """Stands in for XrplClient: records anchors in memory like a tiny ledger."""

    def __init__(self) -> None:
        self.network = "testnet"
        self.is_configured = True
        self.fail_with: Exception | None = None
        self.ledger: dict[str, dict[str, str]] = {}

    def anchor(self, memos: dict[str, str]) -> AnchorReceipt:
        if self.fail_with:
            raise self.fail_with
        tx_hash = f"TX{len(self.ledger) + 1:062d}"
        self.ledger[tx_hash] = dict(memos)
        return AnchorReceipt(network=self.network, tx_hash=tx_hash, ledger_index=1000)

    def fetch_memos(self, tx_hash: str) -> dict[str, str]:
        return self.ledger[tx_hash]


@pytest.fixture
def box_service_mock():
    return MagicMock()


@pytest.fixture
def box(box_service_mock):
    """Box mocked well enough to commit into BATTERY_CAD."""
    box_service_mock.get_folder.return_value = BATTERY_CAD
    box_service_mock.ensure_folder.return_value = "design-reviews-folder"
    box_service_mock.upload_file.side_effect = lambda folder_id, name, content: BoxFileMetadata(
        id=f"file-{name}", name=name, size=len(content), parent_id=folder_id, version_id="v1"
    )
    return box_service_mock


@pytest.fixture
def fake_xrpl():
    return FakeXrpl()


@pytest.fixture
def client(box_service_mock, fake_xrpl):
    """A TestClient logged in as TEST_USER, with Box and XRPL faked out."""
    from app.main import app
    from app.services.box_client import get_box_service
    from app.services.xrpl_client import get_xrpl_client

    app.dependency_overrides[get_box_service] = lambda: box_service_mock
    app.dependency_overrides[get_xrpl_client] = lambda: fake_xrpl
    app.dependency_overrides[require_user] = lambda: TEST_USER
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def anonymous_client():
    """A TestClient with no logged-in engineer."""
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
