"""Maps service-layer exceptions to HTTP responses in one place, so routers don't
repeat the same try/except blocks. Add new exception types to _STATUS_CODES."""

from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.config import ConfigurationError
from app.services.box_client import BoxNotFoundError, BoxServiceError
from app.services.cdx_commits import (
    CdxCommitNotFoundError,
    FileTooLargeError,
    InvalidCdxCommitError,
)
from app.services.dashboard import SubsystemNotFoundError
from app.services.file_downloads import DownloadsBusyError, PreviewTooLargeError
from app.services.xrpl_client import XrplError, XrplNotConfiguredError

# Subclasses resolve to their own entry first (e.g. FileTooLargeError → 413).
_STATUS_CODES: dict[type[Exception], int] = {
    BoxNotFoundError: 404,
    BoxServiceError: 502,
    CdxCommitNotFoundError: 404,
    InvalidCdxCommitError: 422,
    FileTooLargeError: 413,
    SubsystemNotFoundError: 404,
    PreviewTooLargeError: 413,
    DownloadsBusyError: 503,
    XrplError: 502,
    XrplNotConfiguredError: 503,
    ConfigurationError: 503,
}


def register_error_handlers(app: FastAPI) -> None:
    for exc_type, status_code in _STATUS_CODES.items():
        app.add_exception_handler(exc_type, _json_error(status_code))


def _json_error(status_code: int) -> Callable[[Request, Exception], Awaitable[JSONResponse]]:
    async def handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=status_code, content={"detail": str(exc)})

    return handler
