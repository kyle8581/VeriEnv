from __future__ import annotations

from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    APP_NAME: str = "coursera-clone"
    ENV: str = "dev"

    # Server
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 12038

    # Security
    SECRET_KEY: str = "dev-secret-change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24h

    # CORS
    CORS_ORIGINS: list[AnyHttpUrl] = []

    # DB
    DATABASE_URL: str = "sqlite:///./data/app.db"

    # Seeding
    SEED_ON_STARTUP: bool = True


settings = Settings()

