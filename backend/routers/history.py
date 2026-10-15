from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from backend.services.history_service import HistoryService

router = APIRouter(prefix="/history", tags=["history"])


class SaveSessionRequest(BaseModel):
    title: Optional[str] = None
    messages: Optional[List[Dict[str, Any]]] = None
    base_directory: Optional[str] = None
    tasks: Optional[List[Dict[str, Any]]] = None


@router.get("/sessions")
async def list_sessions():
    """List all indexed conversation sessions from ~/.openagents/history/."""
    return HistoryService.list_sessions()


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Retrieve full message history for a session."""
    session = HistoryService.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")
    return session


@router.post("/sessions/{session_id}")
async def save_session(session_id: str, req: SaveSessionRequest):
    """Save or update a conversation session in ~/.openagents/history/."""
    try:
        saved = HistoryService.save_session(
            session_id=session_id,
            title=req.title,
            messages=req.messages,
            base_directory=req.base_directory,
            tasks=req.tasks
        )
        return {"status": "success", "session": saved}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a conversation session from ~/.openagents/history/."""
    HistoryService.delete_session(session_id)
    return {"status": "success", "deleted": session_id}
