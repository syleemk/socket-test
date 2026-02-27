import json
from datetime import datetime, timezone
from collections.abc import Callable
from contextlib import AbstractAsyncContextManager

from redis.asyncio import Redis

from app.repositories.message_repository import MessageRepository
from app.core.redis import CHANNEL, ONLINE_USERS_KEY
from app.config import MESSAGE_HISTORY_LIMIT
from app.schemas import MessageHistoryItem

RepoFactory = Callable[[], AbstractAsyncContextManager[MessageRepository]]


def _now_str() -> str:
    return datetime.now(timezone.utc).astimezone().strftime("%H:%M")


class ChatService:
    def __init__(self, redis: Redis, repo_factory: RepoFactory):
        self.redis = redis
        self.repo_factory = repo_factory

    async def get_history(self, limit: int = MESSAGE_HISTORY_LIMIT) -> list[MessageHistoryItem]:
        async with self.repo_factory() as repo:
            messages = await repo.get_history(limit)
        return [
            MessageHistoryItem(
                username=m.username,
                text=m.text,
                time=m.created_at.strftime("%H:%M") if m.created_at else "",
            )
            for m in messages
        ]

    async def handle_join(self, username: str) -> None:
        await self.redis.sadd(ONLINE_USERS_KEY, username)
        online_count = await self.redis.scard(ONLINE_USERS_KEY)
        await self.redis.publish(
            CHANNEL,
            json.dumps(
                {
                    "type": "system",
                    "text": f"{username}님이 입장했습니다.",
                    "count": online_count,
                }
            ),
        )

    async def handle_message(self, username: str, text: str) -> None:
        async with self.repo_factory() as repo:
            await repo.save(username, text)
        await self.redis.publish(
            CHANNEL,
            json.dumps(
                {
                    "type": "message",
                    "username": username,
                    "text": text,
                    "time": _now_str(),
                }
            ),
        )

    async def handle_leave(self, username: str) -> None:
        await self.redis.srem(ONLINE_USERS_KEY, username)
        online_count = await self.redis.scard(ONLINE_USERS_KEY)
        await self.redis.publish(
            CHANNEL,
            json.dumps(
                {
                    "type": "system",
                    "text": f"{username}님이 퇴장했습니다.",
                    "count": online_count,
                }
            ),
        )
