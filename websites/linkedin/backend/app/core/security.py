from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# bcrypt + passlib has compatibility issues in some environments.
# Argon2 is a modern, production-grade password hashing scheme.
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def _now_utc() -> datetime:
    return datetime.now(UTC)


def _encode(payload: dict[str, Any]) -> str:
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def _decode(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.secret_key, algorithms=["HS256"])


def new_jti() -> str:
    return secrets.token_urlsafe(24)


def mint_access_token(*, user_id: str) -> str:
    now = _now_utc()
    exp = now + timedelta(seconds=settings.access_token_ttl_seconds)
    return _encode(
        {
            "sub": user_id,
            "type": "access",
            "jti": new_jti(),
            "iat": int(now.timestamp()),
            "exp": int(exp.timestamp()),
        }
    )


def mint_refresh_token(*, user_id: str) -> tuple[str, datetime]:
    now = _now_utc()
    exp = now + timedelta(seconds=settings.refresh_token_ttl_seconds)
    token = _encode(
        {
            "sub": user_id,
            "type": "refresh",
            "jti": new_jti(),
            "iat": int(now.timestamp()),
            "exp": int(exp.timestamp()),
        }
    )
    return token, exp


def token_sha256(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class TokenError(Exception):
    pass


def decode_token(token: str) -> dict[str, Any]:
    try:
        payload = _decode(token)
    except JWTError as e:
        raise TokenError("Invalid token") from e
    return payload

