import json
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from app.routers.manager import manager
from app.database import AsyncSessionLocal
from app.models import Message
from app.core.redis import get_redis, CHANNEL, ONLINE_USERS_KEY
from app.config import MESSAGE_HISTORY_LIMIT

router = APIRouter()


def now_str() -> str:
    return datetime.now(timezone.utc).astimezone().strftime("%H:%M")


@router.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    await websocket.accept()

    r = get_redis()

    # Send message history from PostgreSQL
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Message).order_by(Message.created_at.desc()).limit(MESSAGE_HISTORY_LIMIT)
        )
        messages = result.scalars().all()
        history = [
            {
                "username": m.username,
                "text": m.text,
                "time": m.created_at.strftime("%H:%M") if m.created_at else "",
            }
            for m in reversed(messages)
        ]
    await websocket.send_text(json.dumps({"type": "history", "messages": history}))

    # Register connection and add to online users
    manager.add(username, websocket)
    await r.sadd(ONLINE_USERS_KEY, username)
    online_count = await r.scard(ONLINE_USERS_KEY)

    # Broadcast join system message via Redis
    join_msg = json.dumps(
        {
            "type": "system",
            "text": f"{username}님이 입장했습니다.",
            "count": online_count,
        }
    )
    await r.publish(CHANNEL, join_msg)

    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)

            if data.get("type") == "message":
                text = data.get("text", "").strip()
                if not text:
                    continue

                time_str = now_str()

                # Persist to PostgreSQL
                async with AsyncSessionLocal() as session:
                    msg = Message(username=username, text=text)
                    session.add(msg)
                    await session.commit()

                # Publish to Redis → subscriber will broadcast
                out = json.dumps(
                    {
                        "type": "message",
                        "username": username,
                        "text": text,
                        "time": time_str,
                    }
                )
                await r.publish(CHANNEL, out)

    except WebSocketDisconnect:
        manager.remove(username)
        await r.srem(ONLINE_USERS_KEY, username)
        online_count = await r.scard(ONLINE_USERS_KEY)

        leave_msg = json.dumps(
            {
                "type": "system",
                "text": f"{username}님이 퇴장했습니다.",
                "count": online_count,
            }
        )
        await r.publish(CHANNEL, leave_msg)
