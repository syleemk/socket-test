from fastapi import APIRouter, Depends, HTTPException

from app.dependencies.auth import get_current_user
from app.domain.channel import (
    ChannelAlreadyExistsError,
    ChannelNotFoundError,
    ChannelPermissionError,
)
from app.infrastructure.repositories import channel_repo_factory
from app.models import Channel, User
from app.schemas.channel import ChannelResponse, CreateChannelRequest
from app.services.channel_service import ChannelService

router = APIRouter(prefix="/channels", tags=["channels"])

_channel_service = ChannelService(channel_repo_factory=channel_repo_factory)


def _to_response(channel: Channel) -> ChannelResponse:
    return ChannelResponse(
        id=channel.id,
        name=channel.name,
        created_by=channel.created_by,
        is_private=channel.is_private,
        created_at=channel.created_at.isoformat() if channel.created_at else "",
    )


@router.get("", response_model=list[ChannelResponse])
async def list_channels() -> list[ChannelResponse]:
    channels = await _channel_service.list_channels()
    return [_to_response(c) for c in channels]


@router.post("", response_model=ChannelResponse, status_code=201)
async def create_channel(
    body: CreateChannelRequest,
    current_user: User = Depends(get_current_user),
) -> ChannelResponse:
    try:
        channel = await _channel_service.create_channel(
            name=body.name,
            created_by=current_user.username,
        )
        return _to_response(channel)
    except ChannelAlreadyExistsError:
        raise HTTPException(status_code=409, detail="Channel name already exists")


@router.delete("/{channel_name}", status_code=204)
async def delete_channel(
    channel_name: str,
    current_user: User = Depends(get_current_user),
) -> None:
    try:
        await _channel_service.delete_channel(
            channel_name=channel_name,
            requesting_user=current_user.username,
        )
    except ChannelNotFoundError:
        raise HTTPException(status_code=404, detail="Channel not found")
    except ChannelPermissionError:
        raise HTTPException(status_code=403, detail="Only the creator can delete this channel")
