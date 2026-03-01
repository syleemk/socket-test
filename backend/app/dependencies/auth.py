from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError

from app.domain.user import UserNotFoundError
from app.infrastructure.auth import decode_token
from app.infrastructure.redis import get_redis
from app.infrastructure.repositories import user_repo_factory
from app.models import User
from app.services.auth_service import AuthService

_bearer = HTTPBearer(auto_error=False)
_auth_service = AuthService(user_repo_factory=user_repo_factory, redis=get_redis())


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = decode_token(credentials.credentials)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token type")

    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject:
        raise HTTPException(status_code=401, detail="Invalid token subject")

    try:
        return await _auth_service.get_user_by_email(subject)
    except UserNotFoundError:
        raise HTTPException(status_code=401, detail="User not found")
