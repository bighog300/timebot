import json
import logging
from typing import Dict, Set

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self._connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, channel: str):
        await websocket.accept()
        self._connections.setdefault(channel, set()).add(websocket)

    def disconnect(self, websocket: WebSocket, channel: str):
        if channel in self._connections:
            self._connections[channel].discard(websocket)
            if not self._connections[channel]:
                del self._connections[channel]

    async def send(self, channel: str, data: dict):
        if channel not in self._connections:
            return
        dead: Set[WebSocket] = set()
        for ws in self._connections[channel]:
            try:
                await ws.send_text(json.dumps(data))
            except Exception:
                dead.add(ws)
        for ws in dead:
            self._connections[channel].discard(ws)

    async def broadcast(self, data: dict):
        for channel in list(self._connections):
            await self.send(channel, data)

    @property
    def active_channels(self) -> int:
        return len(self._connections)

    @property
    def active_connections(self) -> int:
        return sum(len(v) for v in self._connections.values())


manager = ConnectionManager()
