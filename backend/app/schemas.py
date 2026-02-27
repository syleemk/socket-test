from typing import TypedDict


class MessageHistoryItem(TypedDict):
    username: str
    text: str
    time: str
