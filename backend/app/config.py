from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ConfigurationError(Exception):
    """Raised when a request needs a setting that isn't configured."""


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    box_client_id: str
    box_client_secret: str
    # Redirect URI for the one-time backend authorization (scripts/box_oauth_setup.py).
    box_redirect_uri: str = "http://127.0.0.1:8000/api/box/oauth/callback"
    # Redirect URI for engineers logging in to the dashboard (routers/auth.py).
    # Must also be registered on the Box app; see backend/README.md.
    box_login_redirect_uri: str = "http://127.0.0.1:8000/api/auth/callback"
    box_token_storage_path: str = ".box_tokens"
    box_dashboard_root_folder_id: str | None = None

    database_url: str = "sqlite:///./cdx.db"

    # Signs the session cookie. Generate with:
    #   python -c "import secrets; print(secrets.token_urlsafe(32))"
    session_secret: str
    # True in any deployment served over HTTPS.
    session_cookie_secure: bool = False
    # Where the login callback sends the browser afterwards.
    frontend_url: str = "http://127.0.0.1:5173"

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
