from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class OrderItemOut(BaseModel):
    listing_id: int | None
    price_cents: int
    quantity: int


class OrderOut(BaseModel):
    id: int
    status: str
    total_cents: int
    currency: str
    created_at: datetime
    items: list[OrderItemOut]

