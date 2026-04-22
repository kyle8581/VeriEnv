from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    ENV: str = "dev"

    # Use an absolute sqlite path so running from different CWDs is stable.
    DATABASE_URL: str = f"sqlite:///{(Path(__file__).resolve().parents[2] / 'weather.db')}"

    JWT_SECRET: str = "change-me"
    JWT_ACCESS_TTL_SECONDS: int = 900
    JWT_REFRESH_TTL_SECONDS: int = 60 * 60 * 24 * 14

    CORS_ORIGINS: str = "http://localhost:12141,http://localhost:12125,http://0.0.0.0:12125,https://weather.verienv.com"

    OPEN_METEO_BASE_URL: str = "https://api.open-meteo.com/v1"
    OPEN_METEO_GEO_BASE_URL: str = "https://geocoding-api.open-meteo.com/v1"

    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()

