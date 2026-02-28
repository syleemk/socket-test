from datetime import datetime, timedelta, timezone
from typing import Any, cast

from jose import jwt
from passlib.context import CryptContext

from app.config import JWT_ALGORITHM, JWT_SECRET_KEY

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return cast(str, _pwd_context.hash(plain))


def verify_password(plain: str, hashed: str) -> bool:
    return cast(bool, _pwd_context.verify(plain, hashed))


def _create_token(subject: str, expires_delta: timedelta, token_type: str) -> str:
    expires_at = datetime.now(timezone.utc) + expires_delta
    payload = {
        "sub": subject,
        "exp": expires_at,
        "type": token_type,
    }
    return cast(str, jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM))


def create_access_token(subject: str, expires_delta: timedelta) -> str:
    return _create_token(subject=subject, expires_delta=expires_delta, token_type="access")


def create_refresh_token(subject: str, expires_delta: timedelta) -> str:
    return _create_token(subject=subject, expires_delta=expires_delta, token_type="refresh")


def decode_token(token: str) -> dict[str, Any]:
    return cast(dict[str, Any], jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM]))
