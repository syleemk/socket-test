from fastapi import WebSocket


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
