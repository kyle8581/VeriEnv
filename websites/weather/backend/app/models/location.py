from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel

from app.models.user import utcnow


class Location(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("slug"),)

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(nullable=False, index=True)
    state: str | None = Field(default=None, index=True)
    country: str = Field(default="US", index=True)
    zip_code: str | None = Field(default=None, index=True)

    latitude: float = Field(nullable=False, index=True)
    longitude: float = Field(nullable=False, index=True)
    timezone: str = Field(default="America/New_York", nullable=False)

    slug: str = Field(nullable=False, index=True)

    created_at: datetime = Field(default_factory=utcnow, nullable=False)


class SavedLocation(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", index=True, nullable=False)
    location_id: uuid.UUID = Field(foreign_key="location.id", index=True, nullable=False)
    created_at: datetime = Field(default_factory=utcnow, nullable=False)

