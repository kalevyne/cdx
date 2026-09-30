"""Box OAuth login for engineers. Curl-testable flow:

curl -i http://127.0.0.1:8000/api/auth/login      # 307 → Box consent URL
# open that URL in a browser, approve; Box redirects to /api/auth/callback,
# which sets the `session` cookie and redirects to FRONTEND_URL
curl -b 'session=<cookie from the browser>' http://127.0.0.1:8000/api/auth/me
"""

import logging
import secrets
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import RedirectResponse

from app.auth import log_in, log_out, require_user
from app.config import Settings, get_settings
from app.schemas.auth import SessionUser
from app.services.box_login import (
    BoxLoginDeniedError,
    BoxLoginError,
    BoxLoginService,
    get_box_login_service,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth")

_STATE_KEY = "oauth_state"


@router.get("/login")
def login(
    request: Request, login_service: BoxLoginService = Depends(get_box_login_service)
) -> RedirectResponse:
    state = secrets.token_urlsafe(24)
    request.session[_STATE_KEY] = state
    return RedirectResponse(login_service.authorize_url(state))


@router.get("/callback")
def callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    login_service: BoxLoginService = Depends(get_box_login_service),
    settings: Settings = Depends(get_settings),
) -> RedirectResponse:
    expected_state = request.session.pop(_STATE_KEY, None)
    if not code or not state or state != expected_state:
        return _redirect_to_frontend(settings, login_error="failed")

    try:
        user = login_service.complete_login(code)
    except BoxLoginDeniedError as exc:
        logger.info("Login denied: %s", exc)
        return _redirect_to_frontend(settings, login_error="no_access")
    except BoxLoginError:
        logger.exception("Box login failed")
        return _redirect_to_frontend(settings, login_error="failed")

    log_in(request, user)
    return _redirect_to_frontend(settings)


@router.get("/me", response_model=SessionUser)
def me(user: SessionUser = Depends(require_user)) -> SessionUser:
    return user


@router.post("/logout", status_code=204)
def logout(request: Request) -> Response:
    log_out(request)
    return Response(status_code=204)


def _redirect_to_frontend(settings: Settings, **query: str) -> RedirectResponse:
    url = settings.frontend_url
    if query:
        url = f"{url}/?{urlencode(query)}"
    # 303 so the browser follows with a GET regardless of how it arrived.
    return RedirectResponse(url, status_code=303)
