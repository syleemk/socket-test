from pydantic import BaseModel


class ChannelResponse(BaseModel):
    id: int
    name: str
    created_by: str
    is_private: bool
    created_at: str


class CreateChannelRequest(BaseModel):
    name: str
    created_by: str
