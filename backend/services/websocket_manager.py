from typing import List, Dict, Any
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_json_safe(self, message: Any, websocket: WebSocket):
        if websocket.client_state.value == 1: # CONNECTED
            try:
                if hasattr(message, "model_dump"):
                    await websocket.send_json(message.model_dump())
                elif hasattr(message, "dict"):
                     await websocket.send_json(message.dict())
                else:
                    await websocket.send_json(message)
            except Exception:
                pass

    async def broadcast(self, message: Any):
        for connection in self.active_connections:
            await self.send_json_safe(message, connection)

manager = ConnectionManager()
