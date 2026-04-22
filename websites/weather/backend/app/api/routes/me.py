from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr

from app.api.deps import get_current_user
from app.models.user import User


router = APIRouter(tags=["me"])


class MeResponse(BaseModel):
    id: str
    email: EmailStr
    name: str | None
    is_active: bool
    is_admin: bool


@router.get("/me", response_model=MeResponse)
def me(user: User = Depends(get_current_user)):
    return MeResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        is_active=user.is_active,
        is_admin=user.is_admin,
    )

