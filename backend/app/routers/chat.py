import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.routers.manager import manager
from app.core.redis import get_redis
from app.repositories import make_repo_factory
from app.repositories.message_repository import MessageRepository
from app.services.chat_service import ChatService

router = APIRouter()


@router.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    await websocket.accept()

    chat_service = ChatService(
        redis=get_redis(),
        message_repo_factory=make_repo_factory(MessageRepository),
    )

    history = await chat_service.get_history()
    await websocket.send_text(json.dumps({"type": "history", "messages": history}))

    manager.add(username, websocket)
    await chat_service.handle_join(username)

    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)

            if data.get("type") == "message":
                text = data.get("text", "").strip()
                if not text:
                    continue
                await chat_service.handle_message(username, text)

    except WebSocketDisconnect:
        manager.remove(username)
        await chat_service.handle_leave(username)
