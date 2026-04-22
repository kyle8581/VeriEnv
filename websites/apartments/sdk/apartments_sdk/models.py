from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserPublic(BaseModel):
    id: int
    email: EmailStr
    full_name: str | None = None
    role: str
    created_at: datetime


class AmenityPublic(BaseModel):
    id: int
    name: str


class ListingImagePublic(BaseModel):
    id: int
    url: str
    sort_order: int


class ListingPublic(BaseModel):
    id: int
    name: str
    street: str
    city: str
    state: str
    postal_code: str
    latitude: float
    longitude: float
    min_price: int
    max_price: int
    min_beds: int
    max_beds: int
    property_type: str
    move_in_date: date | None = None
    description: str
    phone: str
    management_name: str
    specials: str | None = None
    has_videos: bool
    has_virtual_tour: bool
    created_at: datetime
    images: list[ListingImagePublic] = []
    amenities: list[AmenityPublic] = []


class ListingSearchResponse(BaseModel):
    total: int
    items: list[ListingPublic]


class SavedSearchPublic(BaseModel):
    id: int
    user_id: int
    name: str
    query: str
    filters: dict[str, Any]
    created_at: datetime


class ContactRequestPublic(BaseModel):
    id: int
    listing_id: int
    user_id: int | None
    contact_email: EmailStr
    contact_name: str | None
    message: str
    created_at: datetime


class LocationPublic(BaseModel):
    id: int
    name: str
    state: str
    kind: str
    latitude: float
    longitude: float

