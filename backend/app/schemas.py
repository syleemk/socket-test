from typing import TypedDict
from pydantic import BaseModel


class MessageHistoryItem(TypedDict):
    username: str
    text: str
    time: str


class ChannelInfo(TypedDict):
    id: int
    name: str
    created_by: str
    is_private: bool
    created_at: str


class CreateChannelRequest(BaseModel):
    name: str
    created_by: str
