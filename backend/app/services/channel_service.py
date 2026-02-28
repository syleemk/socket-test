from collections.abc import Callable
from contextlib import AbstractAsyncContextManager

from app.domain.channel import (
    ChannelAlreadyExistsError,
    ChannelNotFoundError,
    ChannelPermissionError,
)
from app.infrastructure.repositories.channel_repository import ChannelRepository
from app.models import Channel

ChannelRepoFactory = Callable[[], AbstractAsyncContextManager[ChannelRepository]]


class ChannelService:
    def __init__(self, channel_repo_factory: ChannelRepoFactory):
        self.channel_repo_factory = channel_repo_factory

    async def list_channels(self) -> list[Channel]:
        async with self.channel_repo_factory() as repo:
            return await repo.get_all()

    async def create_channel(self, name: str, created_by: str) -> Channel:
        async with self.channel_repo_factory() as repo:
            existing = await repo.get_by_name(name)
            if existing:
                raise ChannelAlreadyExistsError(f"Channel '{name}' already exists")
            return await repo.create(name=name, created_by=created_by)

    async def delete_channel(self, channel_name: str, requesting_user: str) -> None:
        async with self.channel_repo_factory() as repo:
            channel = await repo.get_by_name(channel_name)
            if not channel:
                raise ChannelNotFoundError(f"Channel '{channel_name}' not found")
            if channel.created_by != requesting_user:
                raise ChannelPermissionError("Only the creator can delete this channel")
            await repo.delete(channel)
