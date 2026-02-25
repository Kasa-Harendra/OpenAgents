import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import os

from backend.db.database import engine, Base, get_db
from backend.models.models import AgentConfig, agent_config_create, agent_config_response, websocket_message, UserRequest
from backend.websocket_manager import manager
from backend.agent_flow import execute
from backend.routers.agent_config import router as config_router

# Create database tables
Base.metadata.create_all(bind=engine)

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="OpenAgents Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(config_router, tags=["config"])

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                try:
                    request = UserRequest.model_validate_json(data)
                except Exception as e:
                     await manager.send_json_safe(websocket_message(type="error", content=f"Invalid request format: {str(e)}"), websocket)
                     continue

                prompt = request.prompt
                session_id = request.session_id
                # History is available in request.history if needed for context
                history = request.history or []
                base_directory = request.base_directory

                async def streaming_callback(event: websocket_message):
                    await manager.send_json_safe(event, websocket)

                await execute(prompt, base_directory=base_directory, history=history, callback=streaming_callback)

            except json.JSONDecodeError:
                await manager.send_json_safe(websocket_message(type="error", content="Invalid JSON format"), websocket)
            except WebSocketDisconnect:
                raise
            except Exception as e:
                await manager.send_json_safe(websocket_message(type="error", content=str(e)), websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
