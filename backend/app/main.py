import threading
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from app.config import get_settings
from app.db import run_migrations
from app.errors import register_error_handlers
from app.routers import auth, cdx_commits, dashboard, files, status
from app.services.anchoring import anchor_pending_cdx_commits
from app.services.xrpl_client import get_xrpl_client


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    run_migrations()
    # Catch up on anchoring in the background so startup isn't held up by XRPL.
    threading.Thread(
        target=anchor_pending_cdx_commits, args=(get_xrpl_client(),), daemon=True
    ).start()
    yield


settings = get_settings()

app = FastAPI(title="CDX Backend", lifespan=lifespan)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret,
    same_site="lax",
    https_only=settings.session_cookie_secure,
)
register_error_handlers(app)
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(files.router, prefix="/api", tags=["box"])
app.include_router(cdx_commits.router, prefix="/api", tags=["cdx-commits"])
app.include_router(dashboard.router, prefix="/api", tags=["dashboard"])
app.include_router(status.router, tags=["status"])
