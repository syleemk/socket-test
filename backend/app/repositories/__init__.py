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
