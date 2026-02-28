from collections.abc import AsyncGenerator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from typing import TypeVar

from app.database import AsyncSessionLocal
from app.infrastructure.repositories.channel_repository import ChannelRepository  # noqa: E402
from app.infrastructure.repositories.message_repository import MessageRepository  # noqa: E402
from app.infrastructure.repositories.user_repository import UserRepository  # noqa: E402

T = TypeVar("T")


def make_repo_factory(repo_class: type[T]) -> Callable[[], AbstractAsyncContextManager[T]]:
    @asynccontextmanager
    async def factory() -> AsyncGenerator[T, None]:
        async with AsyncSessionLocal() as session:
            yield repo_class(session)  # type: ignore[call-arg]

    return factory


message_repo_factory = make_repo_factory(MessageRepository)
channel_repo_factory = make_repo_factory(ChannelRepository)
user_repo_factory = make_repo_factory(UserRepository)
