from __future__ import annotations

from pydantic import BaseModel


class CartListingOut(BaseModel):
    listing_id: int
    release_id: int
    release_title: str
    seller_username: str
    price_cents: int
    currency: str


class CartItemOut(BaseModel):
    id: int
    quantity: int
    listing: CartListingOut


class CartOut(BaseModel):
    items: list[CartItemOut]
    total_cents: int
    currency: str = "USD"


class CartAddIn(BaseModel):
    listing_id: int
    quantity: int = 1

