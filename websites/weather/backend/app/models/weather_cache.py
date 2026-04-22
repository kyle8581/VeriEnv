from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel

from app.models.user import utcnow


class WeatherCache(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    location_id: uuid.UUID = Field(foreign_key="location.id", index=True, nullable=False)
    kind: str = Field(index=True, nullable=False)  # current|hourly|daily|alerts
    fetched_at: datetime = Field(default_factory=utcnow, nullable=False, index=True)
    expires_at: datetime = Field(nullable=False, index=True)
    payload: dict = Field(sa_column=Column(JSON), default_factory=dict)

