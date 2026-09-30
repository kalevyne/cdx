from unittest.mock import MagicMock
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.services import box_login
from app.services.box_login import (
    BoxLoginDeniedError,
    BoxLoginError,
    BoxLoginService,
    get_box_login_service,
)
from tests.conftest import DASHBOARD_ROOT_ID, TEST_USER, box_api_error


@pytest.fixture
def login_service_mock():
    service = MagicMock()
    service.authorize_url.side_effect = lambda state: f"https://box.test/authorize?state={state}"
    return service


@pytest.fixture
def auth_client(login_service_mock):
    from app.main import app

    app.dependency_overrides[get_box_login_service] = lambda: login_service_mock
    with TestClient(app, follow_redirects=False) as client:
        yield client
    app.dependency_overrides.clear()


def _start_login(client: TestClient) -> str:
    response = client.get("/api/auth/login")
    assert response.status_code == 307
    return parse_qs(urlparse(response.headers["location"]).query)["state"][0]


def test_login_then_me_returns_user(auth_client, login_service_mock):
    login_service_mock.complete_login.return_value = TEST_USER
    state = _start_login(auth_client)

    callback = auth_client.get("/api/auth/callback", params={"code": "c", "state": state})

    assert callback.status_code == 303
    assert callback.headers["location"] == "http://frontend.test"
    login_service_mock.complete_login.assert_called_once_with("c")
    assert auth_client.get("/api/auth/me").json() == TEST_USER.model_dump()


def test_callback_rejects_mismatched_state(auth_client, login_service_mock):
    _start_login(auth_client)

    callback = auth_client.get("/api/auth/callback", params={"code": "c", "state": "forged"})

    assert "login_error=failed" in callback.headers["location"]
    login_service_mock.complete_login.assert_not_called()
    assert auth_client.get("/api/auth/me").status_code == 401


@pytest.mark.parametrize(
    ("error", "expected"),
    [(BoxLoginDeniedError("x"), "no_access"), (BoxLoginError("x"), "failed")],
)
def test_callback_reports_login_failures(auth_client, login_service_mock, error, expected):
    login_service_mock.complete_login.side_effect = error
    state = _start_login(auth_client)

    callback = auth_client.get("/api/auth/callback", params={"code": "c", "state": state})

    assert f"login_error={expected}" in callback.headers["location"]
    assert auth_client.get("/api/auth/me").status_code == 401


def test_logout_clears_session(auth_client, login_service_mock):
    login_service_mock.complete_login.return_value = TEST_USER
    state = _start_login(auth_client)
    auth_client.get("/api/auth/callback", params={"code": "c", "state": state})

    assert auth_client.post("/api/auth/logout").status_code == 204
    assert auth_client.get("/api/auth/me").status_code == 401


@pytest.fixture
def box_user_client(monkeypatch):
    """Patch the Box SDK client the login service builds for the engineer."""
    client = MagicMock()
    client.users.get_user_me.return_value = MagicMock(
        id=TEST_USER.box_user_id, login=TEST_USER.login
    )
    client.users.get_user_me.return_value.name = TEST_USER.name
    monkeypatch.setattr(box_login, "make_box_oauth", lambda *args: MagicMock())
    monkeypatch.setattr(box_login, "BoxClient", lambda auth: client)
    return client


def test_complete_login_checks_dashboard_root_access(box_user_client):
    user = BoxLoginService(get_settings()).complete_login("code")

    assert user == TEST_USER
    box_user_client.folders.get_folder_by_id.assert_called_once_with(
        DASHBOARD_ROOT_ID, fields=["id"]
    )


@pytest.mark.parametrize("status_code", [403, 404])
def test_complete_login_denies_engineers_without_root_access(box_user_client, status_code):
    box_user_client.folders.get_folder_by_id.side_effect = box_api_error(status_code)

    with pytest.raises(BoxLoginDeniedError):
        BoxLoginService(get_settings()).complete_login("code")


def test_complete_login_wraps_other_box_errors(box_user_client):
    box_user_client.folders.get_folder_by_id.side_effect = box_api_error(500)

    with pytest.raises(BoxLoginError):
        BoxLoginService(get_settings()).complete_login("code")
