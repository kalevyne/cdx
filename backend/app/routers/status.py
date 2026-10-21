from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.config import Settings, get_settings
from app.services.xrpl_client import XrplClient, get_xrpl_client

router = APIRouter()


class ServerStatus(BaseModel):
    anchoring_enabled: bool
    xrpl_network: str
    # Largest file a CDX commit accepts, so the UI can refuse bigger ones before
    # spending minutes uploading them.
    max_upload_bytes: int


@router.get("/health")
def health() -> dict[str, str]:
    """Liveness check for the host (render.yaml healthCheckPath)."""
    return {"status": "ok"}


@router.get("/api/status", response_model=ServerStatus)
def server_status(
    xrpl: XrplClient = Depends(get_xrpl_client), settings: Settings = Depends(get_settings)
) -> ServerStatus:
    """Public: lets the UI say "not configured" instead of "anchoring…" forever,
    and gives a quick pre-demo check that XRPL is set up."""
    return ServerStatus(
        anchoring_enabled=xrpl.is_configured,
        xrpl_network=xrpl.network,
        max_upload_bytes=settings.max_upload_bytes,
    )
