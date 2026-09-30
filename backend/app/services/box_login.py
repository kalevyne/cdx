"""Engineer login via Box OAuth 2.0 — the dashboard's only auth (CLAUDE.md).

This is separate from the backend's own Box connection (`box_client.BoxService`):
here each engineer authorizes the same Box app as *themselves*, CDX reads who
they are, checks that their own Box account can see the Dashboard root folder
(Box-native access control), and then discards their token. All later Box I/O
goes through the backend's connection — see docs/DECISIONS.md #11.
"""

from functools import lru_cache

from box_sdk_gen import (
    BoxAPIError,
    BoxClient,
    BoxSDKError,
    GetAuthorizeUrlOptions,
    InMemoryTokenStorage,
)

from app.config import Settings, get_settings
from app.schemas.auth import SessionUser
from app.services.box_client import make_box_oauth


class BoxLoginError(Exception):
    """The Box OAuth exchange failed (bad/expired code, Box unavailable)."""


class BoxLoginDeniedError(Exception):
    """The engineer authenticated with Box but can't see the Dashboard root folder."""


class BoxLoginService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def authorize_url(self, state: str) -> str:
        auth = make_box_oauth(self._settings, InMemoryTokenStorage())
        return auth.get_authorize_url(
            options=GetAuthorizeUrlOptions(
                redirect_uri=self._settings.box_login_redirect_uri, state=state
            )
        )

    def complete_login(self, code: str) -> SessionUser:
        root_folder_id = self._settings.require_dashboard_root_folder_id()
        auth = make_box_oauth(self._settings, InMemoryTokenStorage())
        try:
            auth.get_tokens_authorization_code_grant(code)
            client = BoxClient(auth=auth)
            me = client.users.get_user_me(fields=["id", "name", "login"])
        except BoxSDKError as exc:
            raise BoxLoginError(f"Box login failed: {exc}") from exc

        try:
            client.folders.get_folder_by_id(root_folder_id, fields=["id"])
        except BoxAPIError as exc:
            if exc.response_info.status_code in (403, 404):
                raise BoxLoginDeniedError(
                    f"{me.login} can't access the CDX Dashboard root folder in Box"
                ) from exc
            raise BoxLoginError(f"Box access check failed: {exc}") from exc

        return SessionUser(box_user_id=me.id, name=me.name, login=me.login)


@lru_cache
def get_box_login_service() -> BoxLoginService:
    return BoxLoginService(get_settings())
