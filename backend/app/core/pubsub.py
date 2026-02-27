import redis.asyncio as aioredis

from app.routers.manager import manager
from app.core.redis import get_redis, CHANNEL


async def redis_subscriber():
    """Dedicated asyncio task that listens to Redis pub/sub and broadcasts to all WS clients."""
    r: aioredis.Redis = get_redis()
    pubsub = r.pubsub()
    await pubsub.subscribe(CHANNEL)
    try:
        async for raw in pubsub.listen():
            if raw["type"] != "message":
                continue
            await manager.broadcast(raw["data"])
    finally:
        await pubsub.unsubscribe(CHANNEL)
        await pubsub.aclose()
