from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole
from app.schemas.common import ORMModel


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserPublic(ORMModel):
    id: int
    email: EmailStr
    full_name: str
    role: UserRole


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=200)
    password: str = Field(min_length=8, max_length=200)

