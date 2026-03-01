from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from datetime import timedelta

from redis.asyncio import Redis

from app.config import ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS
from app.domain.user import (
    InvalidCredentialsError,
    InvalidTokenError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from app.infrastructure.auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.infrastructure.repositories.user_repository import UserRepository
from app.models import User

UserRepoFactory = Callable[[], AbstractAsyncContextManager[UserRepository]]


class AuthService:
    def __init__(self, user_repo_factory: UserRepoFactory, redis: Redis):
        self.user_repo_factory = user_repo_factory
        self.redis = redis

    async def register(self, username: str, email: str, password: str) -> User:
        async with self.user_repo_factory() as repo:
            existing_email = await repo.get_by_email(email)
            if existing_email:
                raise UserAlreadyExistsError("Email already exists")

            return await repo.create(
                username=username,
                email=email,
                hashed_password=hash_password(password),
            )

    async def login(self, email: str, password: str) -> tuple[str, str, str]:
        async with self.user_repo_factory() as repo:
            user = await repo.get_by_email(email)

        if user is None or not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError("Invalid email or password")

        access_token = create_access_token(
            subject=user.email,
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
            username=user.username,
        )
        refresh_token = create_refresh_token(
            subject=user.email,
            expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
            username=user.username,
        )

        refresh_ttl_seconds = REFRESH_TOKEN_EXPIRE_DAYS * 86400
        await self.redis.set(
            self._refresh_key(user.email),
            refresh_token,
            ex=refresh_ttl_seconds,
        )

        return access_token, refresh_token, user.username

    async def refresh(self, refresh_token: str) -> str:
        try:
            payload = decode_token(refresh_token)
        except Exception as exc:
            raise InvalidTokenError("Invalid refresh token") from exc

        if payload.get("type") != "refresh":
            raise InvalidTokenError("Invalid token type")

        email = payload.get("sub")
        if not isinstance(email, str) or not email:
            raise InvalidTokenError("Invalid token subject")
        username = payload.get("username")
        if not isinstance(username, str) or not username:
            raise InvalidTokenError("Invalid token username")

        stored = await self.redis.get(self._refresh_key(email))
        if stored != refresh_token:
            raise InvalidTokenError("Refresh token does not match")

        return create_access_token(
            subject=email,
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
            username=username,
        )

    async def logout(self, email: str) -> None:
        await self.redis.delete(self._refresh_key(email))

    async def get_user_by_username(self, username: str) -> User:
        async with self.user_repo_factory() as repo:
            user = await repo.get_by_username(username)
        if user is None:
            raise UserNotFoundError("User not found")
        return user

    async def get_user_by_email(self, email: str) -> User:
        async with self.user_repo_factory() as repo:
            user = await repo.get_by_email(email)
        if user is None:
            raise UserNotFoundError("User not found")
        return user

    @staticmethod
    def _refresh_key(email: str) -> str:
        return f"auth:refresh:{email}"
