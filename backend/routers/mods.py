from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from backend.mods.mod_manager import ModManager

router = APIRouter(prefix="/mods")

class ToggleResponse(BaseModel):
    mod_id: str
    enabled: bool

class GenerateModRequest(BaseModel):
    prompt: str

class CommandRequest(BaseModel):
    command: str

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

@router.get("/hud", response_model=List[Dict[str, Any]])
def get_hud_widgets():
    mgr = ModManager.get_instance()
    return mgr.get_hud_widgets()

@router.post("/generate")
async def generate_mod(req: GenerateModRequest):
    mgr = ModManager.get_instance()
    res = await mgr.generate_mod(req.prompt)
    if res.get("status") == "error":
        raise HTTPException(status_code=400, detail=res.get("error"))
    return res

@router.post("/command")
async def run_command(req: CommandRequest):
    mgr = ModManager.get_instance()
    ctx = await mgr.trigger_custom_command(req.command)
    if ctx and ctx.command_output is not None:
        return {
            "handled": True,
            "output": ctx.command_output
        }
    return {
        "handled": False,
        "output": None
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
