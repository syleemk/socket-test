import redis.asyncio as aioredis
from config import REDIS_URL, REDIS_CHANNEL, REDIS_ONLINE_USERS_KEY

CHANNEL = REDIS_CHANNEL
ONLINE_USERS_KEY = REDIS_ONLINE_USERS_KEY

_redis: aioredis.Redis | None = None


def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(REDIS_URL, decode_responses=True)
    return _redis
