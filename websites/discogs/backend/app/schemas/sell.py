from __future__ import annotations

from pydantic import BaseModel, Field


class ListingCreateIn(BaseModel):
    release_id: int
    media_condition: str = Field(min_length=1, max_length=40)
    sleeve_condition: str = Field(min_length=1, max_length=40)
    price_cents: int = Field(ge=1)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    ships_from: str = Field(min_length=1, max_length=80)
    comments: str | None = None
    quantity: int = Field(default=1, ge=1, le=99)


class ListingUpdateIn(BaseModel):
    media_condition: str | None = Field(default=None, min_length=1, max_length=40)
    sleeve_condition: str | None = Field(default=None, min_length=1, max_length=40)
    price_cents: int | None = Field(default=None, ge=1)
    ships_from: str | None = Field(default=None, min_length=1, max_length=80)
    comments: str | None = None
    quantity: int | None = Field(default=None, ge=1, le=99)
    status: str | None = Field(default=None, pattern="^(active|inactive)$")

