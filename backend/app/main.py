from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

import app.models  # noqa: F401 — registers models on Base before create_all
from app.db import Base, get_engine
from app.routers import files


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    Base.metadata.create_all(bind=get_engine())
    yield


app = FastAPI(title="CDX Backend", lifespan=lifespan)
app.include_router(files.router, prefix="/api", tags=["box"])


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
