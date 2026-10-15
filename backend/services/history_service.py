import os
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

from backend.config.openagents_dir import get_history_dir


class HistoryService:
    @staticmethod
    def _get_index_path() -> Path:
        return get_history_dir() / "sessions.json"

    @staticmethod
    def _read_index() -> List[Dict[str, Any]]:
        index_file = HistoryService._get_index_path()
        if not index_file.exists():
            return []
        try:
            with open(index_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    @staticmethod
    def _write_index(sessions: List[Dict[str, Any]]):
        index_file = HistoryService._get_index_path()
        temp_file = index_file.with_suffix(".tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(sessions, f, indent=2)
        temp_file.replace(index_file)

    @staticmethod
    def list_sessions() -> List[Dict[str, Any]]:
        """
        Lists all conversation sessions ordered by most recently updated.
        """
        sessions = HistoryService._read_index()
        return sorted(sessions, key=lambda s: s.get("updated_at", 0), reverse=True)

    @staticmethod
    def get_session(session_id: str) -> Optional[Dict[str, Any]]:
        """
        Loads full conversation history for a given session.
        """
        session_file = get_history_dir() / f"{session_id}.json"
        if not session_file.exists():
            return None
        try:
            with open(session_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[openagents] Error loading session {session_id}: {e}")
            return None

    @staticmethod
    def save_session(
        session_id: str,
        title: Optional[str] = None,
        messages: Optional[List[Dict[str, Any]]] = None,
        base_directory: Optional[str] = None,
        tasks: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Persists a full session or updates an existing one in ~/.openagents/history/.
        """
        now = int(time.time() * 1000)
        session_file = get_history_dir() / f"{session_id}.json"

        existing = {}
        if session_file.exists():
            try:
                with open(session_file, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            except Exception:
                existing = {}

        updated_session = {
            "id": session_id,
            "title": title or existing.get("title") or "New Chat",
            "messages": messages if messages is not None else existing.get("messages", []),
            "tasks": tasks if tasks is not None else existing.get("tasks", []),
            "base_directory": base_directory if base_directory is not None else existing.get("base_directory"),
            "created_at": existing.get("created_at", now),
            "updated_at": now,
        }

        # Atomically write session file
        temp_file = session_file.with_suffix(".tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(updated_session, f, indent=2)
        temp_file.replace(session_file)

        # Update index
        index = HistoryService._read_index()
        found = False
        summary = {
            "id": session_id,
            "title": updated_session["title"],
            "message_count": len(updated_session["messages"]),
            "base_directory": updated_session["base_directory"],
            "created_at": updated_session["created_at"],
            "updated_at": now,
        }

        for i, s in enumerate(index):
            if s.get("id") == session_id:
                index[i] = summary
                found = True
                break

        if not found:
            index.insert(0, summary)

        HistoryService._write_index(index)
        return updated_session

    @staticmethod
    def delete_session(session_id: str) -> bool:
        """
        Deletes a session from ~/.openagents/history/.
        """
        session_file = get_history_dir() / f"{session_id}.json"
        if session_file.exists():
            try:
                session_file.unlink()
            except Exception:
                pass

        index = HistoryService._read_index()
        new_index = [s for s in index if s.get("id") != session_id]
        HistoryService._write_index(new_index)
        return True
