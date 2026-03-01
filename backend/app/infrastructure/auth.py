import base64
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any, cast

import bcrypt
from jose import jwt

from app.config import JWT_ALGORITHM, JWT_SECRET_KEY


def _prehash_password(plain: str) -> bytes:
    digest = hashlib.sha256(plain.encode("utf-8")).digest()
    return base64.b64encode(digest)


def hash_password(plain: str) -> str:
    hashed = cast(bytes, bcrypt.hashpw(_prehash_password(plain), bcrypt.gensalt()))
    return hashed.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return cast(bool, bcrypt.checkpw(_prehash_password(plain), hashed.encode("utf-8")))
    except ValueError:
        return False


def _create_token(
    subject: str,
    expires_delta: timedelta,
    token_type: str,
    username: str | None = None,
) -> str:
    expires_at = datetime.now(timezone.utc) + expires_delta
    payload = {
        "sub": subject,
        "exp": expires_at,
        "type": token_type,
    }
    if username is not None:
        payload["username"] = username
    return cast(str, jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM))


def create_access_token(
    subject: str,
    expires_delta: timedelta,
    username: str | None = None,
) -> str:
    return _create_token(
        subject=subject,
        expires_delta=expires_delta,
        token_type="access",
        username=username,
    )


def create_refresh_token(
    subject: str,
    expires_delta: timedelta,
    username: str | None = None,
) -> str:
    return _create_token(
        subject=subject,
        expires_delta=expires_delta,
        token_type="refresh",
        username=username,
    )


def decode_token(token: str) -> dict[str, Any]:
    return cast(dict[str, Any], jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM]))
