from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    environment: str = "dev"
    api_title: str = "Discogs Clone API"
    api_version: str = "0.1.0"

    # Networking
    cors_origins: str = 'http://localhost:12042, http://localhost:12093, http://0.0.0.0:12093, http://127.0.0.1:12093'

    # DB
    # Default to SQLite for local/dev (Docker is not always available in the environment).
    # You can override with Postgres (or any supported DB) via DATABASE_URL.
    database_url: str = "sqlite+pysqlite:///../.data/discogs.db"

    # Auth
    jwt_secret: str = "dev_secret_change_me"
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 60 * 24  # 24h


settings = Settings()

