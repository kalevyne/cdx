from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.services.xrpl_client import XrplClient, get_xrpl_client

router = APIRouter()


class ServerStatus(BaseModel):
    anchoring_enabled: bool
    xrpl_network: str


@router.get("/health")
def health() -> dict[str, str]:
    """Liveness check for the host (render.yaml healthCheckPath)."""
    return {"status": "ok"}


@router.get("/api/status", response_model=ServerStatus)
def server_status(xrpl: XrplClient = Depends(get_xrpl_client)) -> ServerStatus:
    """Public: lets the UI say "not configured" instead of "anchoring…" forever,
    and gives a quick pre-demo check that XRPL is set up."""
    return ServerStatus(anchoring_enabled=xrpl.is_configured, xrpl_network=xrpl.network)
