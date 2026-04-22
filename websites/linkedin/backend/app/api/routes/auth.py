from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.schemas import AuthLoginRequest, AuthRegisterRequest, TokenPair, UserPublic
from app.core.security import (
    TokenError,
    decode_token,
    hash_password,
    mint_access_token,
    mint_refresh_token,
    token_sha256,
    verify_password,
)
from app.db.models import RefreshToken, User
from app.db.session import get_db

from pydantic import BaseModel

router = APIRouter()


def _now() -> datetime:
    return datetime.now(UTC)


def _user_public(u: User, *, include_email: bool = False) -> UserPublic:
    return UserPublic(
        id=u.id,
        email=u.email if include_email else None,
        first_name=u.first_name,
        last_name=u.last_name,
        headline=u.headline,
        location=u.location,
        avatar_url=u.avatar_url,
    )


def _issue_tokens(db: Session, *, user: User) -> TokenPair:
    access = mint_access_token(user_id=user.id)
    refresh, exp = mint_refresh_token(user_id=user.id)
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=token_sha256(refresh),
            expires_at=exp,
        )
    )
    db.commit()
    return TokenPair(access_token=access, refresh_token=refresh)


@router.post("/register", response_model=TokenPair)
def register(payload: AuthRegisterRequest, db: Session = Depends(get_db)) -> TokenPair:
    user = User(
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        first_name=payload.first_name,
        last_name=payload.last_name,
        headline="",
        location="",
        avatar_url="",
        banner_url="",
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    db.refresh(user)
    return _issue_tokens(db, user=user)


@router.post("/login", response_model=TokenPair)
def login(payload: AuthLoginRequest, db: Session = Depends(get_db)) -> TokenPair:
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    return _issue_tokens(db, user=user)


@router.get("/me", response_model=UserPublic)
def me(user: User = Depends(get_current_user)) -> UserPublic:
    return _user_public(user, include_email=True)


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/refresh", response_model=TokenPair)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenPair:
    try:
        decoded = decode_token(payload.refresh_token)
    except TokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    if decoded.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token type")

    token_hash = token_sha256(payload.refresh_token)
    rt = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    if rt is None or rt.revoked_at is not None or rt.expires_at <= _now():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired or revoked")

    user = db.scalar(select(User).where(User.id == rt.user_id))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    # Rotate token: revoke the current refresh token, mint a new pair.
    rt.revoked_at = _now()
    db.add(rt)
    db.commit()
    return _issue_tokens(db, user=user)


class LogoutRequest(BaseModel):
    refresh_token: str


@router.post("/logout")
def logout(payload: LogoutRequest, db: Session = Depends(get_db)) -> dict:
    token_hash = token_sha256(payload.refresh_token)
    rt = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    if rt is None:
        return {"ok": True}
    if rt.revoked_at is None:
        rt.revoked_at = _now()
        db.add(rt)
        db.commit()
    return {"ok": True}

