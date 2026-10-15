from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any

from backend.config.openagents_dir import load_config, update_config, get_openagents_dir

router = APIRouter(prefix="/config", tags=["config"])


class UpdateConfigRequest(BaseModel):
    settings: Dict[str, Any]


@router.get("")
async def get_config():
    """Retrieve global configuration from ~/.openagents/config.json."""
    return {
        "home": str(get_openagents_dir()),
        "config": load_config()
    }


@router.post("")
async def save_config(req: UpdateConfigRequest):
    """Update global configuration in ~/.openagents/config.json."""
    updated = update_config(req.settings)
    return {
        "status": "success",
        "config": updated
    }
