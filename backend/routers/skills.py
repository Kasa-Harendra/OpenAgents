from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from backend.services.skills_service import SkillsService

router = APIRouter(prefix="/skills", tags=["skills"])


class CreateSkillRequest(BaseModel):
    id: str
    content: str
    metadata: Optional[Dict[str, Any]] = None


@router.get("")
async def list_skills():
    """List all standardized skills in ~/.openagents/skills/."""
    return SkillsService.list_skills()


@router.get("/{skill_id}")
async def get_skill(skill_id: str):
    """Get full details of a specific skill."""
    skill = SkillsService.get_skill(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill '{skill_id}' not found.")
    return skill


@router.post("")
async def save_skill(req: CreateSkillRequest):
    """Create or update a skill in ~/.openagents/skills/."""
    try:
        saved = SkillsService.save_skill(req.id, req.content, req.metadata)
        return {"status": "success", "skill": saved}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{skill_id}")
async def delete_skill(skill_id: str):
    """Delete a custom skill from ~/.openagents/skills/."""
    success = SkillsService.delete_skill(skill_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Skill '{skill_id}' not found.")
    return {"status": "success", "deleted": skill_id}
