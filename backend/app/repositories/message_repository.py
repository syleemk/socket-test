from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Message


class MessageRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_history(self, channel_name: str, limit: int) -> list[Message]:
        result = await self.session.execute(
            select(Message).where(Message.channel_name == channel_name).order_by(Message.created_at.desc()).limit(limit)
        )
        return list(reversed(result.scalars().all()))

    async def save(self, username: str, text: str, channel_name: str) -> Message:
        msg = Message(username=username, text=text, channel_name=channel_name)
        self.session.add(msg)
        await self.session.commit()
        return msg
