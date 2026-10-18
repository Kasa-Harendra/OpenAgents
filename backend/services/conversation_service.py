import os
import json
import uuid
import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from backend.models.models import Conversation
from backend.db.database import OPENAGENTS_DIR

CONVERSATIONS_DIR = os.path.join(OPENAGENTS_DIR, "conversations")


def get_conversations_dir() -> str:
    """Ensure ~/.openagents/conversations directory exists and return its path."""
    os.makedirs(CONVERSATIONS_DIR, exist_ok=True)
    return CONVERSATIONS_DIR


def get_conversation_file_path(convo_id: str) -> str:
    """Return the absolute path for a conversation JSON file."""
    return os.path.join(get_conversations_dir(), f"{convo_id}.json")


def _read_json_file(file_path: str) -> Optional[Dict[str, Any]]:
    if not os.path.exists(file_path):
        return None
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error reading conversation file {file_path}: {e}")
        return None


def _write_json_file(file_path: str, data: Dict[str, Any]) -> bool:
    try:
        temp_file = f"{file_path}.tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(temp_file, file_path)
        return True
    except Exception as e:
        print(f"Error writing conversation file {file_path}: {e}")
        return False


def create_conversation(
    db: Session,
    convo_id: Optional[str] = None,
    title: str = "New Chat",
    base_directory: Optional[str] = None,
    chat_mode: str = "multiagent"
) -> Dict[str, Any]:
    """Create a new conversation both as a JSON file and a DB record."""
    if not convo_id:
        convo_id = str(uuid.uuid4())
    
    file_path = get_conversation_file_path(convo_id)
    now_dt = datetime.datetime.now(datetime.timezone.utc)
    now_iso = now_dt.isoformat()

    convo_data = {
        "convo_id": convo_id,
        "title": title or "New Chat",
        "created_at": now_iso,
        "updated_at": now_iso,
        "base_directory": base_directory,
        "chat_mode": chat_mode or "multiagent",
        "messages": []
    }

    _write_json_file(file_path, convo_data)

    # Upsert in database
    db_convo = db.query(Conversation).filter(Conversation.convo_id == convo_id).first()
    if not db_convo:
        db_convo = Conversation(
            convo_id=convo_id,
            title=convo_data["title"],
            file_path=file_path,
            message_count=0,
            last_message_preview=None,
            created_at=now_dt,
            updated_at=now_dt
        )
        db.add(db_convo)
    else:
        db_convo.title = convo_data["title"]
        db_convo.file_path = file_path
        db_convo.updated_at = now_dt

    db.commit()
    db.refresh(db_convo)

    return convo_data


def get_conversation(db: Session, convo_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve full conversation details from JSON file, falling back to DB record."""
    file_path = get_conversation_file_path(convo_id)
    data = _read_json_file(file_path)
    
    if data:
        return data

    # Check if DB has it
    db_convo = db.query(Conversation).filter(Conversation.convo_id == convo_id).first()
    if db_convo:
        # Re-create empty JSON payload
        now_iso = db_convo.created_at.isoformat() if db_convo.created_at else datetime.datetime.now(datetime.timezone.utc).isoformat()
        convo_data = {
            "convo_id": convo_id,
            "title": db_convo.title,
            "created_at": now_iso,
            "updated_at": db_convo.updated_at.isoformat() if db_convo.updated_at else now_iso,
            "base_directory": None,
            "chat_mode": "multiagent",
            "messages": []
        }
        _write_json_file(file_path, convo_data)
        return convo_data

    return None


def list_conversations(db: Session) -> List[Conversation]:
    """List all conversations tracked in the conversations table, ordered by updated_at descending."""
    return db.query(Conversation).order_by(Conversation.updated_at.desc()).all()


def update_conversation(
    db: Session,
    convo_id: str,
    title: Optional[str] = None,
    base_directory: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Update title or base_directory in both JSON file and DB."""
    data = get_conversation(db, convo_id)
    if not data:
        return None

    now_dt = datetime.datetime.now(datetime.timezone.utc)
    data["updated_at"] = now_dt.isoformat()

    if title is not None:
        data["title"] = title
    if base_directory is not None:
        data["base_directory"] = base_directory

    file_path = get_conversation_file_path(convo_id)
    _write_json_file(file_path, data)

    db_convo = db.query(Conversation).filter(Conversation.convo_id == convo_id).first()
    if db_convo:
        if title is not None:
            db_convo.title = title
        db_convo.updated_at = now_dt
        db.commit()

    return data


def delete_conversation(db: Session, convo_id: str) -> bool:
    """Delete a conversation from both DB and the ~/.openagents/conversations directory."""
    deleted = False

    # 1. Remove DB record
    db_convo = db.query(Conversation).filter(Conversation.convo_id == convo_id).first()
    if db_convo:
        db.delete(db_convo)
        db.commit()
        deleted = True

    # 2. Delete JSON file from disk
    file_path = get_conversation_file_path(convo_id)
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            deleted = True
        except Exception as e:
            print(f"Error deleting conversation file {file_path}: {e}")

    return deleted


def append_message_to_conversation(
    db: Session,
    convo_id: str,
    message: Dict[str, Any],
    auto_title: bool = True
) -> Dict[str, Any]:
    """Append a message to the conversation JSON and update DB tracking."""
    data = get_conversation(db, convo_id)
    if not data:
        data = create_conversation(db, convo_id=convo_id)

    # Ensure message has an ID and timestamp
    if "id" not in message:
        message["id"] = str(uuid.uuid4())[:8]
    if "timestamp" not in message:
        message["timestamp"] = int(datetime.datetime.now().timestamp() * 1000)

    data.setdefault("messages", []).append(message)

    now_dt = datetime.datetime.now(datetime.timezone.utc)
    data["updated_at"] = now_dt.isoformat()

    # Auto-generate title from first user prompt if still default
    new_title = None
    if auto_title and data.get("title") in ("New Chat", "", None) and message.get("role") == "user":
        content_str = message.get("content", "")
        if isinstance(content_str, str) and content_str.strip():
            # Clean single line title up to 45 chars
            first_line = content_str.strip().split("\n")[0]
            clean_title = (first_line[:42] + "...") if len(first_line) > 42 else first_line
            data["title"] = clean_title
            new_title = clean_title

    file_path = get_conversation_file_path(convo_id)
    _write_json_file(file_path, data)

    # Update DB metadata
    db_convo = db.query(Conversation).filter(Conversation.convo_id == convo_id).first()
    content_preview = str(message.get("content", ""))[:120] if message.get("content") else None
    if db_convo:
        if new_title:
            db_convo.title = new_title
        db_convo.message_count = len(data["messages"])
        db_convo.last_message_preview = content_preview
        db_convo.updated_at = now_dt
        db.commit()
    else:
        db_convo = Conversation(
            convo_id=convo_id,
            title=data.get("title", "New Chat"),
            file_path=file_path,
            message_count=len(data["messages"]),
            last_message_preview=content_preview,
            created_at=now_dt,
            updated_at=now_dt
        )
        db.add(db_convo)
        db.commit()

    return data


def update_last_message(
    db: Session,
    convo_id: str,
    content: Any,
    msg_type: Optional[str] = None,
    is_append: bool = False,
    agent_name: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Update or append to the last message in the conversation (useful for streaming chunks)."""
    data = get_conversation(db, convo_id)
    if not data or not data.get("messages"):
        return None

    last_msg = data["messages"][-1]
    if is_append:
        existing_content = last_msg.get("content", "") or ""
        last_msg["content"] = str(existing_content) + str(content)
    else:
        last_msg["content"] = content

    if msg_type:
        last_msg["type"] = msg_type
    if agent_name:
        last_msg["agentName"] = agent_name

    now_dt = datetime.datetime.now(datetime.timezone.utc)
    data["updated_at"] = now_dt.isoformat()

    file_path = get_conversation_file_path(convo_id)
    _write_json_file(file_path, data)

    db_convo = db.query(Conversation).filter(Conversation.convo_id == convo_id).first()
    if db_convo:
        content_preview = str(last_msg.get("content", ""))[:120]
        db_convo.last_message_preview = content_preview
        db_convo.updated_at = now_dt
        db.commit()

    return data
