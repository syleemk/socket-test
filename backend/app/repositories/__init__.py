from collections.abc import Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from typing import TypeVar

from app.database import AsyncSessionLocal

T = TypeVar("T")


def make_repo_factory(repo_class: type[T]) -> Callable[[], AbstractAsyncContextManager[T]]:
    @asynccontextmanager
    async def factory():
        async with AsyncSessionLocal() as session:
            yield repo_class(session)

    return factory


from app.repositories.message_repository import MessageRepository
from app.repositories.channel_repository import ChannelRepository

message_repo_factory = make_repo_factory(MessageRepository)
channel_repo_factory = make_repo_factory(ChannelRepository)
