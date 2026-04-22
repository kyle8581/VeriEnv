from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, Text, UniqueConstraint
from sqlmodel import Field, SQLModel

from app.models.user import utcnow


class Category(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("slug"),)

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(nullable=False, index=True)
    slug: str = Field(nullable=False, index=True)


class Article(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("slug"),)

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    category_id: uuid.UUID = Field(foreign_key="category.id", index=True, nullable=False)

    title: str = Field(nullable=False, index=True)
    slug: str = Field(nullable=False, index=True)
    summary: str = Field(sa_column=Column(Text, nullable=False))
    body_md: str = Field(sa_column=Column(Text, nullable=False))
    hero_image_url: str = Field(nullable=False)

    is_video: bool = Field(default=False, index=True)
    source: str = Field(default="Weather Portal", index=True)
    reading_minutes: int = Field(default=4)

    published_at: datetime = Field(default_factory=utcnow, index=True, nullable=False)
    created_at: datetime = Field(default_factory=utcnow, nullable=False)


class Photo(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str = Field(nullable=False, index=True)
    image_url: str = Field(nullable=False)
    caption: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    location_id: uuid.UUID | None = Field(default=None, foreign_key="location.id", index=True)
    published_at: datetime = Field(default_factory=utcnow, index=True, nullable=False)


class Deal(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str = Field(nullable=False, index=True)
    image_url: str = Field(nullable=False)
    provider: str = Field(default="GoodDeals", index=True)
    price_usd: float | None = Field(default=None)
    badge: str | None = Field(default=None, index=True)
    cta_url: str = Field(nullable=False)
    created_at: datetime = Field(default_factory=utcnow, nullable=False)

