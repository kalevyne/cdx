from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    box_client_id: str
    box_client_secret: str
    box_enterprise_id: str
    box_dashboard_root_folder_id: str | None = None

    database_url: str = "sqlite:///./cdx.db"


@lru_cache
def get_settings() -> Settings:
    return Settings()
