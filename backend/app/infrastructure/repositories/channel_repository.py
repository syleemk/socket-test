from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Channel


class ChannelRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, name: str, created_by: str, is_private: bool = False) -> Channel:
        channel = Channel(name=name, created_by=created_by, is_private=is_private)
        self.session.add(channel)
        await self.session.commit()
        return channel

    async def get_all(self) -> list[Channel]:
        result = await self.session.execute(
            select(Channel).order_by(Channel.created_at.asc())
        )
        return list(result.scalars().all())

    async def get_by_name(self, name: str) -> Channel | None:
        result = await self.session.execute(
            select(Channel).where(Channel.name == name)
        )
        return result.scalar_one_or_none()

    async def delete(self, channel: Channel) -> None:
        await self.session.delete(channel)
        await self.session.commit()
