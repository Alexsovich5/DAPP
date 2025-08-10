from __future__ import annotations

from typing import List, Dict, Optional
from fastapi import WebSocket, WebSocketDisconnect
import asyncio
import json


class ConnectionManager:
    """
    Minimal WebSocket connection manager for real-time features (chat, typing, status).
    Tracks active connections and supports broadcast utilities.
    """

    def __init__(self) -> None:
        self.active_connections: List[WebSocket] = []
        # Optional: map of websocket id to user id (if passed as query param)
        self.connection_user: Dict[int, str] = {}
        # Broadcast lock to avoid concurrent writes to same socket
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)

        # Try to capture user id from query params (optional)
        try:
            user_id = websocket.query_params.get("user_id")
            if user_id:
                self.connection_user[id(websocket)] = str(user_id)
        except Exception:
            pass

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        self.connection_user.pop(id(websocket), None)

    async def broadcast(self, message: dict) -> None:
        data = json.dumps(message)
        async with self._lock:
            send_tasks = []
            for connection in list(self.active_connections):
                send_tasks.append(self._safe_send_text(connection, data))
            if send_tasks:
                await asyncio.gather(*send_tasks, return_exceptions=True)

    async def send_to_all_except(self, message: dict, except_ws: Optional[WebSocket]) -> None:
        data = json.dumps(message)
        async with self._lock:
            send_tasks = []
            for connection in list(self.active_connections):
                if except_ws is not None and connection is except_ws:
                    continue
                send_tasks.append(self._safe_send_text(connection, data))
            if send_tasks:
                await asyncio.gather(*send_tasks, return_exceptions=True)

    async def _safe_send_text(self, websocket: WebSocket, data: str) -> None:
        try:
            await websocket.send_text(data)
        except WebSocketDisconnect:
            self.disconnect(websocket)
        except Exception:
            # Best-effort; disconnect on persistent failures
            self.disconnect(websocket)


# Global connection manager instance reused by routers/endpoints
manager = ConnectionManager()


