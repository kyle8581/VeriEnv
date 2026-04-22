from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ListingOut(BaseModel):
    id: int
    release_id: int
    seller: dict  # {username, seller_rating, location}
    media_condition: str
    sleeve_condition: str
    price_cents: int
    currency: str
    ships_from: str
    comments: str | None = None
    quantity: int
    status: str
    created_at: datetime


class ListingsPageOut(BaseModel):
    release: dict  # {id,title,artist,cover_image_url}
    total: int
    items: list[ListingOut]

