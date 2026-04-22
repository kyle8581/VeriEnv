from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel

from app.models.user import utcnow


class SubscriptionPlan(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(nullable=False, index=True)
    price_monthly_usd: float = Field(nullable=False)
    description: str = Field(nullable=False)
    features: list[str] = Field(sa_column=Column(JSON), default_factory=list)


class Subscription(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", index=True, nullable=False)
    plan_id: uuid.UUID = Field(foreign_key="subscriptionplan.id", index=True, nullable=False)
    status: str = Field(default="active", index=True)  # active|canceled|expired
    started_at: datetime = Field(default_factory=utcnow, nullable=False)
    ends_at: datetime | None = Field(default=None, nullable=True)
    created_at: datetime = Field(default_factory=utcnow, nullable=False)

