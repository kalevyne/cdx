"""Session helpers and FastAPI dependencies for the logged-in engineer.

The session is a signed cookie (Starlette's SessionMiddleware, configured in
app/main.py). Routes that need a logged-in engineer depend on `require_user`.
"""

from fastapi import Depends, HTTPException, Request

from app.schemas.auth import SessionUser

_USER_KEY = "user"


def log_in(request: Request, user: SessionUser) -> None:
    request.session[_USER_KEY] = user.model_dump()


def log_out(request: Request) -> None:
    request.session.clear()


def get_current_user(request: Request) -> SessionUser | None:
    data = request.session.get(_USER_KEY)
    return SessionUser.model_validate(data) if data else None


def require_user(user: SessionUser | None = Depends(get_current_user)) -> SessionUser:
    if user is None:
        raise HTTPException(status_code=401, detail="Log in with Box first")
    return user
