from pydantic import BaseModel


class MessageHistoryItem(BaseModel):
    username: str
    text: str
    time: str
