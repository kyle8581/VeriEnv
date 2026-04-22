from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlmodel import Session, select

from app.core.db import get_session
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import RefreshToken, User


router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=256)
    name: str | None = Field(default=None, max_length=120)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class AuthResponse(BaseModel):
    access_token: str
    access_expires_at: datetime
    refresh_token: str
    refresh_expires_at: datetime
    token_type: str = "bearer"


def _utcnow() -> datetime:
    return datetime.utcnow()


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, session: Session = Depends(get_session)):
    existing = session.exec(select(User).where(User.email == payload.email)).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        email=str(payload.email).lower(),
        name=payload.name,
        hashed_password=hash_password(payload.password),
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    access_token, access_exp = create_access_token(subject=str(user.id), email=user.email)
    refresh_token, jti, refresh_exp = create_refresh_token(subject=str(user.id), email=user.email)

    session.add(
        RefreshToken(
            user_id=user.id,
            jti=jti,
            expires_at=refresh_exp,
        )
    )
    session.commit()

    return AuthResponse(
        access_token=access_token,
        access_expires_at=access_exp,
        refresh_token=refresh_token,
        refresh_expires_at=refresh_exp,
    )


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == str(payload.email).lower())).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User is disabled")

    access_token, access_exp = create_access_token(subject=str(user.id), email=user.email)
    refresh_token, jti, refresh_exp = create_refresh_token(subject=str(user.id), email=user.email)

    session.add(RefreshToken(user_id=user.id, jti=jti, expires_at=refresh_exp))
    session.commit()

    return AuthResponse(
        access_token=access_token,
        access_expires_at=access_exp,
        refresh_token=refresh_token,
        refresh_expires_at=refresh_exp,
    )


@router.post("/refresh", response_model=AuthResponse)
def refresh(payload: RefreshRequest, session: Session = Depends(get_session)):
    data = decode_token(payload.refresh_token)
    if data.get("typ") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")
    jti = data.get("jti")
    sub = data.get("sub")
    email = data.get("email")
    if not jti or not sub or not email:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    rt = session.exec(select(RefreshToken).where(RefreshToken.jti == jti)).first()
    if not rt or rt.revoked_at is not None:
        raise HTTPException(status_code=401, detail="Refresh token revoked")
    if rt.expires_at <= _utcnow():
        raise HTTPException(status_code=401, detail="Refresh token expired")

    user = session.get(User, uuid.UUID(sub))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid user")

    # Rotate refresh token
    rt.revoked_at = _utcnow()
    session.add(rt)

    access_token, access_exp = create_access_token(subject=str(user.id), email=user.email)
    refresh_token, new_jti, refresh_exp = create_refresh_token(subject=str(user.id), email=user.email)
    session.add(RefreshToken(user_id=user.id, jti=new_jti, expires_at=refresh_exp))
    session.commit()

    return AuthResponse(
        access_token=access_token,
        access_expires_at=access_exp,
        refresh_token=refresh_token,
        refresh_expires_at=refresh_exp,
    )


@router.post("/logout")
def logout(payload: RefreshRequest, session: Session = Depends(get_session)):
    data = decode_token(payload.refresh_token)
    if data.get("typ") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")
    jti = data.get("jti")
    if not jti:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    rt = session.exec(select(RefreshToken).where(RefreshToken.jti == jti)).first()
    if rt and rt.revoked_at is None:
        rt.revoked_at = _utcnow()
        session.add(rt)
        session.commit()

    return {"status": "ok"}

