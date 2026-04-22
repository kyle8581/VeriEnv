from __future__ import annotations

import uuid
from datetime import datetime

from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    # Store naive UTC timestamps to avoid sqlite tz pitfalls.
    return datetime.utcnow()


class User(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: str = Field(index=True, nullable=False, unique=True)
    name: str | None = Field(default=None, index=True)
    hashed_password: str
    is_active: bool = Field(default=True)
    is_admin: bool = Field(default=False)
    created_at: datetime = Field(default_factory=utcnow, nullable=False)


class RefreshToken(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", index=True, nullable=False)
    jti: str = Field(index=True, nullable=False, unique=True)
    expires_at: datetime = Field(nullable=False)
    revoked_at: datetime | None = Field(default=None, nullable=True)
    created_at: datetime = Field(default_factory=utcnow, nullable=False)

