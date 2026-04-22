from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, extra="ignore")

    # App
    app_name: str = "linkedin-clone"
    environment: str = "development"
    api_prefix: str = "/api"

    # Security
    secret_key: str = "dev-insecure-secret-change-me"
    access_token_ttl_seconds: int = 60 * 30  # 30 minutes
    refresh_token_ttl_seconds: int = 60 * 60 * 24 * 14  # 14 days

    # CORS
    cors_allow_origins: str = "http://localhost:12078,http://localhost:12079,http://0.0.0.0:12078,http://0.0.0.0:12079,http://localhost:12431,http://0.0.0.0:12431,https://linkedin.verienv.com,http://linkedin.verienv.com,https://api-linkedin.verienv.com,http://api-linkedin.verienv.com"

    # DB
    # Use a path that is stable when starting from the repo root (scripts run from root).
    database_url: str = "sqlite:///./backend/var/app.db"


settings = Settings()

