from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any

from backend.config.openagents_dir import load_config, update_config, get_openagents_dir

from backend.config.openagents_dir import (
    load_config, update_config, get_openagents_dir,
    get_credentials_dir, get_skills_dir, get_mods_dir,
    get_history_dir, get_audit_dir, get_database_path
)

router = APIRouter(prefix="/system", tags=["system"])


class UpdateConfigRequest(BaseModel):
    settings: Dict[str, Any]


@router.get("/config")
async def get_system_config():
    """Retrieve global configuration from ~/.openagents/config.json."""
    return {
        "home": str(get_openagents_dir()),
        "config": load_config()
    }


@router.post("/config")
async def save_system_config(req: UpdateConfigRequest):
    """Update global configuration in ~/.openagents/config.json."""
    updated = update_config(req.settings)
    return {
        "status": "success",
        "config": updated
    }


@router.get("/storage")
async def get_storage_overview():
    """Overview of ~/.openagents directory storage, paths, and stats."""
    home = get_openagents_dir()
    history_dir = get_history_dir()
    skills_dir = get_skills_dir()
    mods_dir = get_mods_dir()

    history_count = len(list(history_dir.glob("*.json"))) - (1 if (history_dir / "sessions.json").exists() else 0)
    skills_count = len([d for d in skills_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]) if skills_dir.exists() else 0
    mods_count = len([d for d in mods_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]) if mods_dir.exists() else 0

    return {
        "home": str(home),
        "database": str(get_database_path()),
        "database_exists": get_database_path().exists(),
        "credentials_dir": str(get_credentials_dir()),
        "credentials_secured": True,
        "skills_dir": str(skills_dir),
        "skills_count": max(0, skills_count),
        "mods_dir": str(mods_dir),
        "mods_count": max(0, mods_count),
        "history_dir": str(history_dir),
        "history_sessions_count": max(0, history_count),
        "audit_dir": str(get_audit_dir()),
    }
