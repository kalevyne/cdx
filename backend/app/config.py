from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ConfigurationError(Exception):
    """Raised when a request needs a setting that isn't configured."""


# A required setting left blank (e.g. `.env` copied from `.env.example` and not
# filled in) should stop startup, not surface later as a confusing Box error.
_RequiredText = Field(min_length=1)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    box_client_id: str = _RequiredText
    box_client_secret: str = _RequiredText
    # Redirect URI for the one-time backend authorization (scripts/box_oauth_setup.py).
    box_redirect_uri: str = "http://127.0.0.1:8000/api/box/oauth/callback"
    # Redirect URI for engineers logging in to the dashboard (routers/auth.py).
    # Must also be registered on the Box app; see backend/README.md.
    box_login_redirect_uri: str = "http://127.0.0.1:8000/api/auth/callback"
    # Where the backend's own Box token lives: see app/services/box_token_storage.py.
    box_token_storage: Literal["file", "database"] = "file"
    box_token_storage_path: str = ".box_tokens"
    box_dashboard_root_folder_id: str | None = None

    # How many file downloads/previews may be relayed from Box at once; further
    # requests get a 503 until one finishes (app/services/file_downloads.py).
    max_concurrent_downloads: int = Field(default=8, ge=1)

    database_url: str = "sqlite:///./cdx.db"

    # Signs the session cookie. Generate with:
    #   python -c "import secrets; print(secrets.token_urlsafe(32))"
    session_secret: str = _RequiredText
    # True in any deployment served over HTTPS.
    session_cookie_secure: bool = False
    # Where the login callback sends the browser afterwards.
    frontend_url: str = "http://127.0.0.1:5173"

    # XRPL anchoring (app/services/xrpl_client.py). Testnet only until mainnet
    # wallet custody is decided (docs/DECISIONS.md #6).
    xrpl_network: Literal["testnet", "mainnet"] = "testnet"
    xrpl_testnet_wallet_seed: str | None = None
    # Anchors are 1-drop Payments (decision #9), and XRPL rejects payments to
    # yourself, so they go to this funded account (any address CDX controls).
    xrpl_anchor_destination: str | None = None

    @field_validator("database_url")
    @classmethod
    def _use_psycopg_driver(cls, url: str) -> str:
        # Managed Postgres hosts hand out `postgres://` / `postgresql://` URLs;
        # SQLAlchemy needs the driver named explicitly to use psycopg 3.
        for prefix in ("postgres://", "postgresql://"):
            if url.startswith(prefix):
                return "postgresql+psycopg://" + url.removeprefix(prefix)
        return url

    def require_dashboard_root_folder_id(self) -> str:
        if not self.box_dashboard_root_folder_id:
            raise ConfigurationError("BOX_DASHBOARD_ROOT_FOLDER_ID is not configured")
        return self.box_dashboard_root_folder_id


@lru_cache
def get_settings() -> Settings:
    return Settings()
