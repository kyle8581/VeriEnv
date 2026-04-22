from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Token(ORMModel):
    access_token: str
    token_type: str = "bearer"


class UserPublic(ORMModel):
    id: int
    email: EmailStr
    full_name: str | None = None
    role: str
    created_at: datetime


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=200)
    full_name: str | None = Field(default=None, max_length=200)


class AmenityPublic(ORMModel):
    id: int
    name: str


class ListingImagePublic(ORMModel):
    id: int
    url: str
    sort_order: int


class ListingPublic(ORMModel):
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
    move_in_date: date | None
    description: str
    phone: str
    management_name: str
    specials: str | None
    has_videos: bool
    has_virtual_tour: bool
    created_at: datetime
    images: list[ListingImagePublic] = []
    amenities: list[AmenityPublic] = []


class ListingSearchResponse(BaseModel):
    total: int
    items: list[ListingPublic]


class SavedSearchCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    query: str = Field(min_length=1, max_length=120)
    filters: dict[str, Any] = Field(default_factory=dict)


class SavedSearchPublic(ORMModel):
    id: int
    user_id: int
    name: str
    query: str
    filters: dict[str, Any]
    created_at: datetime


class ContactRequestCreate(BaseModel):
    listing_id: int
    contact_email: EmailStr
    contact_name: str | None = Field(default=None, max_length=200)
    message: str = Field(min_length=1, max_length=4000)


class ContactRequestPublic(ORMModel):
    id: int
    listing_id: int
    user_id: int | None
    contact_email: EmailStr
    contact_name: str | None
    message: str
    created_at: datetime


class LocationPublic(ORMModel):
    id: int
    name: str
    state: str
    kind: str
    latitude: float
    longitude: float

