from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "apartments-api"
    environment: str = "development"  # development|test|production

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    database_url: str = "sqlite:///./app.db"

    jwt_secret_key: str = "dev-only-change-me"
    jwt_algorithm: str = "HS256"
    jwt_access_token_exp_minutes: int = 60 * 24 * 7  # 7 days

    cors_allow_origins: str = "http://localhost:3000,http://0.0.0.0:3000,http://localhost:19000,http://0.0.0.0:19000,http://localhost:12000,http://0.0.0.0:12000"


settings = Settings()

