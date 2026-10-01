"""Password hashing (bcrypt via passlib) + JWT (PyJWT) helpers.

Doc reference: 3.1 — bcrypt hashing, short-lived access + refresh tokens,
account lock after 5 failed logins, revocation on logout.
"""
import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

from app.core.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_token(*, user_id: int, role: str, token_type: str, expires_delta: timedelta) -> tuple[str, str, datetime]:
    settings = get_settings()
    jti = str(uuid.uuid4())
    exp = _now() + expires_delta
    payload = {"sub": str(user_id), "role": role, "type": token_type, "jti": jti, "exp": exp, "iat": _now()}
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    return token, jti, exp


def create_access_token(*, user_id: int, role: str) -> tuple[str, str, datetime]:
    settings = get_settings()
    return create_token(
        user_id=user_id, role=role, token_type="access",
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(*, user_id: int, role: str) -> tuple[str, str, datetime]:
    settings = get_settings()
    return create_token(
        user_id=user_id, role=role, token_type="refresh",
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )


def decode_token(token: str) -> dict:
    settings = get_settings()
    return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])


def generate_raw_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(raw: str) -> str:
    """SHA-256 hex — deterministic so we can look the row up by hash."""
    return hashlib.sha256(raw.encode()).hexdigest()
