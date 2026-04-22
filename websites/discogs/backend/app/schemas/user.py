from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str | None = Field(default=None, max_length=120)


class UserLogin(BaseModel):
    username_or_email: str
    password: str


class UserOut(BaseModel):
    id: UUID
    username: str
    email: EmailStr
    display_name: str | None = None
    avatar_url: str | None = None
    location: str | None = None
    seller_rating: float
    created_at: datetime

    class Config:
        from_attributes = True

