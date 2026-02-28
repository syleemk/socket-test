from app.infrastructure.connection_manager import manager
from app.infrastructure.redis import get_redis


async def redis_subscriber() -> None:
    """Listens to all chat channels via pattern subscription and routes to WS clients."""
    r = get_redis()
    pubsub = r.pubsub()
    await pubsub.psubscribe("chat:channel:*")
    try:
        async for raw in pubsub.listen():
            if raw["type"] != "pmessage":
                continue
            channel_key = raw["channel"]
            if isinstance(channel_key, bytes):
                channel_key = channel_key.decode()
            channel_name = channel_key.removeprefix("chat:channel:")
            await manager.broadcast_to_channel(channel_name, raw["data"])
    finally:
        await pubsub.punsubscribe("chat:channel:*")
        await pubsub.close()
