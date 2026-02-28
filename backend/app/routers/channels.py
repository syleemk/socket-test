from fastapi import APIRouter, HTTPException

from app.database import AsyncSessionLocal
from app.repositories.channel_repository import ChannelRepository
from app.schemas import CreateChannelRequest, ChannelInfo

router = APIRouter(prefix="/channels", tags=["channels"])


async def _get_repo() -> ChannelRepository:
    async with AsyncSessionLocal() as session:
        return ChannelRepository(session)


@router.get("", response_model=list[ChannelInfo])
async def list_channels():
    async with AsyncSessionLocal() as session:
        repo = ChannelRepository(session)
        channels = await repo.get_all()
        return [
            ChannelInfo(
                id=c.id,
                name=c.name,
                created_by=c.created_by,
                is_private=c.is_private,
                created_at=c.created_at.isoformat() if c.created_at else "",
            )
            for c in channels
        ]


@router.post("", response_model=ChannelInfo, status_code=201)
async def create_channel(body: CreateChannelRequest):
    async with AsyncSessionLocal() as session:
        repo = ChannelRepository(session)
        existing = await repo.get_by_name(body.name)
        if existing:
            raise HTTPException(status_code=409, detail="Channel name already exists")
        channel = await repo.create(
            name=body.name,
            created_by=body.created_by,
        )
        return ChannelInfo(
            id=channel.id,
            name=channel.name,
            created_by=channel.created_by,
            is_private=channel.is_private,
            created_at=channel.created_at.isoformat() if channel.created_at else "",
        )


@router.delete("/{channel_name}", status_code=204)
async def delete_channel(channel_name: str, username: str):
    async with AsyncSessionLocal() as session:
        repo = ChannelRepository(session)
        channel = await repo.get_by_name(channel_name)
        if not channel:
            raise HTTPException(status_code=404, detail="Channel not found")
        if channel.created_by != username:
            raise HTTPException(status_code=403, detail="Only the creator can delete this channel")
        await repo.delete(channel)
