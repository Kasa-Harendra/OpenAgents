from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from pydantic import BaseModel

from backend.mods.mod_manager import ModManager

router = APIRouter(prefix="/mods")

class ToggleResponse(BaseModel):
    mod_id: str
    enabled: bool

@router.get("", response_model=List[Dict[str, Any]])
def list_mods():
    mgr = ModManager.get_instance()
    return mgr.get_mods_metadata()

@router.get("/active")
def get_active_mods():
    mgr = ModManager.get_instance()
    all_mods = mgr.get_mods_metadata()
    active = [m for m in all_mods if m.get("enabled")]
    return {
        "total_installed": len(all_mods),
        "total_active": len(active),
        "active_mods": active
    }

@router.post("/{mod_id}/toggle", response_model=ToggleResponse)
def toggle_mod(mod_id: str):
    mgr = ModManager.get_instance()
    new_state = mgr.toggle_mod(mod_id)
    if new_state is None:
        raise HTTPException(status_code=404, detail=f"Mod '{mod_id}' not found")
    return ToggleResponse(mod_id=mod_id, enabled=new_state)

@router.post("/{mod_id}/enable", response_model=ToggleResponse)
def enable_mod(mod_id: str):
    mgr = ModManager.get_instance()
    success = mgr.set_mod_enabled(mod_id, True)
    if not success:
        raise HTTPException(status_code=404, detail=f"Mod '{mod_id}' not found")
    return ToggleResponse(mod_id=mod_id, enabled=True)

@router.post("/{mod_id}/disable", response_model=ToggleResponse)
def disable_mod(mod_id: str):
    mgr = ModManager.get_instance()
    success = mgr.set_mod_enabled(mod_id, False)
    if not success:
        raise HTTPException(status_code=404, detail=f"Mod '{mod_id}' not found")
    return ToggleResponse(mod_id=mod_id, enabled=False)

@router.post("/reload")
def reload_mods():
    mgr = ModManager.get_instance()
    mgr.mods.clear()
    mgr.discover_and_load_all()
    return {
        "status": "success",
        "loaded_mods": mgr.get_mods_metadata()
    }
