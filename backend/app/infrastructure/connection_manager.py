import asyncio

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        # { channel_name: { username: WebSocket } }
        self._connections: dict[str, dict[str, WebSocket]] = {}

    def add(self, channel: str, username: str, ws: WebSocket) -> None:
        self._connections.setdefault(channel, {})[username] = ws

    def remove(self, channel: str, username: str) -> None:
        self._connections.get(channel, {}).pop(username, None)
        # clean up empty channel dicts
        if not self._connections.get(channel):
            self._connections.pop(channel, None)

    async def broadcast_to_channel(self, channel: str, data: str) -> None:
        connections = self._connections.get(channel, {})

        async def send(username: str, ws: WebSocket) -> None:
            try:
                await ws.send_text(data)
            except Exception:
                self.remove(channel, username)

        await asyncio.gather(*[
            send(username, ws) for username, ws in list(connections.items())
        ])

    def count(self, channel: str) -> int:
        return len(self._connections.get(channel, {}))


manager = ConnectionManager()
