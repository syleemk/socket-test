import json
from datetime import datetime, timezone
from collections.abc import Callable
from contextlib import AbstractAsyncContextManager

from redis.asyncio import Redis

from app.repositories.message_repository import MessageRepository
from app.core.redis import channel_key, online_users_key
from app.config import MESSAGE_HISTORY_LIMIT

MessageRepoFactory = Callable[[], AbstractAsyncContextManager[MessageRepository]]


def _now_str() -> str:
    return datetime.now(timezone.utc).strftime("%H:%M")


class ChatService:
    def __init__(self, redis: Redis, message_repo_factory: MessageRepoFactory):
        self.redis = redis
        self.message_repo_factory = message_repo_factory

    async def handle_join(self, username: str, channel_name: str) -> None:
        await self.redis.sadd(online_users_key(channel_name), username)
        online_count = await self.redis.scard(online_users_key(channel_name))
        await self.redis.publish(channel_key(channel_name), json.dumps({
            "type": "system",
            "text": f"{username}님이 입장했습니다.",
            "count": online_count,
        }))

    async def handle_message(self, username: str, text: str, channel_name: str) -> None:
        async with self.message_repo_factory() as repo:
            await repo.save(username, text, channel_name)
        await self.redis.publish(channel_key(channel_name), json.dumps({
            "type": "message",
            "username": username,
            "text": text,
            "time": _now_str(),
        }))

    async def handle_leave(self, username: str, channel_name: str) -> None:
        await self.redis.srem(online_users_key(channel_name), username)
        online_count = await self.redis.scard(online_users_key(channel_name))
        await self.redis.publish(channel_key(channel_name), json.dumps({
            "type": "system",
            "text": f"{username}님이 퇴장했습니다.",
            "count": online_count,
        }))

    async def get_history(self, channel_name: str) -> list[dict]:
        async with self.message_repo_factory() as repo:
            messages = await repo.get_history(channel_name, MESSAGE_HISTORY_LIMIT)
        return [
            {
                "username": m.username,
                "text": m.text,
                "time": m.created_at.strftime("%H:%M") if m.created_at else "",
            }
            for m in messages
        ]
