from __future__ import annotations

from datetime import datetime, timedelta, timezone
import os
from typing import Any, Iterable

import bcrypt
from jose import JWTError, jwt


SECRET_KEY = os.getenv("XM_SECRET_KEY", "xm-dev-secret-key-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv("XM_TOKEN_EXPIRE_HOURS", "12"))


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            password_hash.encode("utf-8"),
        )
    except ValueError:
        return False


def create_access_token(
    *,
    user_id: str,
    username: str,
    role: str,
    allowed_roles: Iterable[str] | None = None,
    portal: str | None = None,
    expires_hours: int = ACCESS_TOKEN_EXPIRE_HOURS,
    extra: dict[str, Any] | None = None,
) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=expires_hours)
    payload: dict[str, Any] = {
        "sub": user_id,
        "username": username,
        "role": role,
        "allowed_roles": list(allowed_roles or []),
        "portal": portal or role,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise ValueError("invalid token") from exc

