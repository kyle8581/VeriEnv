from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings


pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def _now() -> datetime:
    # Use naive UTC to avoid sqlite offset-aware comparison issues.
    return datetime.utcnow()


def create_access_token(*, subject: str, email: str) -> tuple[str, datetime]:
    expires_at = _now() + timedelta(seconds=settings.JWT_ACCESS_TTL_SECONDS)
    payload: dict[str, Any] = {
        "sub": subject,
        "email": email,
        "typ": "access",
        "exp": int(expires_at.timestamp()),
        "iat": int(_now().timestamp()),
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")
    return token, expires_at


def create_refresh_token(*, subject: str, email: str) -> tuple[str, str, datetime]:
    jti = str(uuid.uuid4())
    expires_at = _now() + timedelta(seconds=settings.JWT_REFRESH_TTL_SECONDS)
    payload: dict[str, Any] = {
        "sub": subject,
        "email": email,
        "typ": "refresh",
        "jti": jti,
        "exp": int(expires_at.timestamp()),
        "iat": int(_now().timestamp()),
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")
    return token, jti, expires_at


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
    except JWTError as e:
        raise ValueError("Invalid token") from e

