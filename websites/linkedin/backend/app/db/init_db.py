from __future__ import annotations

from app.db.base import Base
from app.db.session import engine


def init_db() -> None:
    # Import models so they register with Base.metadata
    from app.db import models  # noqa: F401

    Base.metadata.create_all(bind=engine)

