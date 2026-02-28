import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.infrastructure.connection_manager import manager
from app.infrastructure.redis import get_redis
from app.infrastructure.repositories import message_repo_factory
from app.services.chat_service import ChatService

router = APIRouter()


@router.websocket("/ws/{channel_name}/{username}")
async def websocket_endpoint(websocket: WebSocket, channel_name: str, username: str) -> None:
    await websocket.accept()

    chat_service = ChatService(
        redis=get_redis(),
        message_repo_factory=message_repo_factory,
    )

    history = await chat_service.get_history(channel_name)
    await websocket.send_text(json.dumps({"type": "history", "messages": history}))

    manager.add(channel_name, username, websocket)
    await chat_service.handle_join(username, channel_name)

    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)

            if data.get("type") == "message":
                text = data.get("text", "").strip()
                if not text:
                    continue
                await chat_service.handle_message(username, text, channel_name)

    except WebSocketDisconnect:
        manager.remove(channel_name, username)
        await chat_service.handle_leave(username, channel_name)
