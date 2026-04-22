from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


def _sqlite_connect_args(url: str) -> dict:
    # Needed for SQLite with threads in FastAPI
    if url.startswith("sqlite:"):
        return {"check_same_thread": False}
    return {}


engine = create_engine(
    settings.DATABASE_URL,
    connect_args=_sqlite_connect_args(settings.DATABASE_URL),
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

