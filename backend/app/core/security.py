from __future__ import annotations

import base64
import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt

from app.core.config import get_settings

ALGORITHM = "HS256"
_ITERATIONS = 100_000
_SALT_BYTES = 16


def _decode(value: str) -> bytes:
    return base64.b64decode(value.encode("utf-8"))


def _encode(value: bytes) -> str:
    return base64.b64encode(value).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        salt_b64, hash_b64 = hashed_password.split(":", 1)
    except ValueError:
        return False
    salt = _decode(salt_b64)
    expected_hash = _decode(hash_b64)
    candidate_hash = hashlib.pbkdf2_hmac(
        "sha256", plain_password.encode("utf-8"), salt, _ITERATIONS
    )
    return secrets.compare_digest(candidate_hash, expected_hash)


def get_password_hash(password: str) -> str:
    salt = secrets.token_bytes(_SALT_BYTES)
    derived = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, _ITERATIONS
    )
    return f"{_encode(salt)}:{_encode(derived)}"


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    settings = get_settings()
    expire = datetime.now(UTC) + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode = {"sub": subject, "exp": expire}
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> str | None:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[ALGORITHM])
    except JWTError:
        return None
    return payload.get("sub")
