from __future__ import annotations

import uuid

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select

from app.core.db import get_session
from app.core.security import decode_token
from app.models.user import User


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
) -> User:
    data = decode_token(token)
    if data.get("typ") != "access":
        raise HTTPException(status_code=401, detail="Invalid token type")
    sub = data.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    user = session.exec(select(User).where(User.id == uuid.UUID(sub))).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid user")
    return user

