import redis.asyncio as aioredis

from app.config import REDIS_URL

_redis: aioredis.Redis | None = None


def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(REDIS_URL, decode_responses=True)
    return _redis


def channel_key(name: str) -> str:
    return f"chat:channel:{name}"


def online_users_key(name: str) -> str:
    return f"chat:online_users:{name}"
