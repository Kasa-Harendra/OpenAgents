import os
import sys

# Add project root to path to support both backend.main and main imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.db.database import engine, Base, get_db
from backend.models.models import AgentConfig, agent_config_create, agent_config_response, websocket_message, UserRequest
from backend.services.websocket_manager import manager
from backend.chat_flow import handle_general_chat
from backend.agent_flow import execute
from backend.routers.agent_config import router as config_router, init_db
from backend.routers.auth import router as auth_router

import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize database with default configs
init_db()

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
app.include_router(auth_router, tags=["auth"])

active_tasks: Dict[str, asyncio.Task] = {}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg_data = json.loads(data)
                if msg_data.get("action") == "cancel":
                    session_id = msg_data.get("session_id")
                    if session_id in active_tasks:
                        active_tasks[session_id].cancel()
                        await manager.send_json_safe(websocket_message(type="status", content="Execution cancelled by user.", session_id=session_id), websocket)
                    continue

                try:
                    request = UserRequest.model_validate(msg_data)
                except Exception as e:
                     await manager.send_json_safe(websocket_message(type="error", content=f"Invalid request format: {str(e)}"), websocket)
                     continue

                prompt = request.prompt
                session_id = request.session_id
                # History is available in request.history if needed for context
                history = request.history or []
                base_directory = request.base_directory
                chat_mode = getattr(request, 'chat_mode', 'multiagent')

                async def streaming_callback(event: websocket_message):
                    event.session_id = session_id
                    await manager.send_json_safe(event, websocket)

                async def run_task():
                    try:
                        if chat_mode == "chat":
                            await handle_general_chat(prompt, history, streaming_callback)
                        else:
                            await execute(prompt, base_directory=base_directory, history=history, callback=streaming_callback)
                    except asyncio.CancelledError:
                        print(f"Task for session {session_id} was cancelled")
                        await streaming_callback(websocket_message(type="error", content="Task execution stopped.", session_id=session_id))
                    finally:
                        if session_id in active_tasks:
                            del active_tasks[session_id]

                task = asyncio.create_task(run_task())
                active_tasks[session_id] = task


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
