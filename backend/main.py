import asyncio
import json
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

import redis.asyncio as aioredis

from database import init_db, AsyncSessionLocal
from models import Message
from redis_client import get_redis, CHANNEL, ONLINE_USERS_KEY
from config import CORS_ORIGINS, MESSAGE_HISTORY_LIMIT


class ConnectionManager:
    def __init__(self):
        self._connections: dict[str, WebSocket] = {}

    def add(self, username: str, ws: WebSocket):
        self._connections[username] = ws

    def remove(self, username: str):
        self._connections.pop(username, None)

    async def broadcast(self, data: str):
        dead = []
        for username, ws in self._connections.items():
            try:
                await ws.send_text(data)
            except Exception:
                dead.append(username)
        for username in dead:
            self.remove(username)

    def count(self) -> int:
        return len(self._connections)


manager = ConnectionManager()


async def redis_subscriber():
    """Dedicated asyncio task that listens to Redis pub/sub and broadcasts to all WS clients."""
    r: aioredis.Redis = get_redis()
    pubsub = r.pubsub()
    await pubsub.subscribe(CHANNEL)
    try:
        async for raw in pubsub.listen():
            if raw["type"] != "message":
                continue
            await manager.broadcast(raw["data"])
    finally:
        await pubsub.unsubscribe(CHANNEL)
        await pubsub.aclose()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    task = asyncio.create_task(redis_subscriber())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    redis = get_redis()
    await redis.aclose()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


def now_str() -> str:
    return datetime.now(timezone.utc).astimezone().strftime("%H:%M")


@app.websocket("/ws/{username}")
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
