from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from backend.db.database import get_db
from backend.models.models import (
    ConversationSummary,
    ConversationCreate,
    ConversationUpdate,
    ConversationDetail
)
from backend.services import conversation_service

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.get("", response_model=List[ConversationSummary])
def list_all_conversations(db: Session = Depends(get_db)):
    """List all conversations ordered by recent activity."""
    return conversation_service.list_conversations(db)


@router.post("", response_model=ConversationDetail)
def create_new_conversation(data: ConversationCreate, db: Session = Depends(get_db)):
    """Create a new conversation, initializing both DB record and ~/.openagents/conversations/<convo_id>.json file."""
    return conversation_service.create_conversation(
        db=db,
        convo_id=data.convo_id,
        title=data.title or "New Chat",
        base_directory=data.base_directory,
        chat_mode=data.chat_mode or "multiagent"
    )


@router.get("/{convo_id}", response_model=ConversationDetail)
def get_conversation_details(convo_id: str, db: Session = Depends(get_db)):
    """Retrieve full conversation details and message history from JSON storage."""
    convo = conversation_service.get_conversation(db, convo_id)
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return convo


@router.put("/{convo_id}", response_model=ConversationDetail)
def update_conversation(convo_id: str, data: ConversationUpdate, db: Session = Depends(get_db)):
    """Update conversation title or base directory."""
    updated = conversation_service.update_conversation(
        db=db,
        convo_id=convo_id,
        title=data.title,
        base_directory=data.base_directory
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return updated


@router.delete("/{convo_id}")
def delete_conversation(convo_id: str, db: Session = Depends(get_db)):
    """Delete conversation from DB and remove JSON file from ~/.openagents/conversations/."""
    deleted = conversation_service.delete_conversation(db, convo_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "deleted", "convo_id": convo_id}
