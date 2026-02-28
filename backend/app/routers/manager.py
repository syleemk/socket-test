import asyncio

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self._connections: dict[str, WebSocket] = {}

    def add(self, username: str, ws: WebSocket):
        self._connections[username] = ws

    def remove(self, username: str):
        self._connections.pop(username, None)

    async def broadcast(self, data: str):
        async def send(username: str, ws: WebSocket):
            try:
                await ws.send_text(data)
            except Exception:
                self.remove(username)

        await asyncio.gather(*[
            send(username, ws) for username, ws in list(self._connections.items())
        ])

    def count(self) -> int:
        return len(self._connections)


manager = ConnectionManager()
