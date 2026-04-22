from __future__ import annotations

from sqlmodel import Session, SQLModel, create_engine

from app.core.config import settings


def _sqlite_connect_args(db_url: str) -> dict:
    if db_url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args=_sqlite_connect_args(settings.DATABASE_URL),
)


def init_db() -> None:
    # Ensure models are imported so SQLModel registers tables.
    from app import models as _models  # noqa: F401

    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session

