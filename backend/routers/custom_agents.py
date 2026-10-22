import os
import sys
import uuid
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.models.models import (
    CustomAgent,
    MCPServer,
    CustomAgentCreate,
    CustomAgentUpdate,
    CustomAgentResponse
)

router = APIRouter(prefix="/custom-agents")

DEFAULT_MCP_PRESETS = [
    {"name": "Filesystem", "type": "stdio", "description": "Local filesystem operations, file inspection, and editing"},
    {"name": "Fetch / Web", "type": "stdio", "description": "Direct HTTP fetching, web content extraction, and conversion"},
    {"name": "SQLite", "type": "stdio", "description": "Local SQLite database querying and schema manipulation"},
    {"name": "Memory", "type": "stdio", "description": "Knowledge graph and long-term memory persistence across sessions"}
]

def get_installed_skills() -> List[Dict[str, Any]]:
    skills_dir = Path.home() / ".openagents" / "skills"
    skills = []
    
    if skills_dir.exists() and skills_dir.is_dir():
        for item in sorted(skills_dir.iterdir()):
            if item.is_dir():
                skill_file = item / "SKILL.md"
                description = ""
                name = item.name
                
                if skill_file.exists():
                    try:
                        content = skill_file.read_text(encoding="utf-8")
                        # Basic YAML frontmatter parser
                        if content.startswith("---"):
                            parts = content.split("---", 2)
                            if len(parts) >= 3:
                                frontmatter = parts[1]
                                for line in frontmatter.splitlines():
                                    if line.startswith("name:"):
                                        name = line.split("name:", 1)[1].strip().strip('"\'')
                                    elif line.startswith("description:"):
                                        description = line.split("description:", 1)[1].strip().strip('"\'')
                    except Exception as e:
                        print(f"Error parsing skill {item.name}: {e}")
                
                skills.append({
                    "id": item.name,
                    "name": name,
                    "description": description or f"Specialized skill for {item.name}",
                    "path": str(item)
                })

    # If no local skills folder or empty, provide curated built-in skills
    if not skills:
        fallback_skills = [
            {"id": "browser-automation", "name": "browser-automation", "description": "Automated web browsing and interaction"},
            {"id": "filesystem-management", "name": "filesystem-management", "description": "File manipulation and document management"},
            {"id": "knowledge-retrieval", "name": "knowledge-retrieval", "description": "Documentation search and knowledge synthesis"},
            {"id": "terminal-execution", "name": "terminal-execution", "description": "Shell command running and process monitoring"},
            {"id": "web-scraping", "name": "web-scraping", "description": "Web scraping and content aggregation"},
            {"id": "mcp-integration", "name": "mcp-integration", "description": "Model Context Protocol tools and lifecycle handling"}
        ]
        return fallback_skills

    return skills

@router.get("/available-options")
def get_available_options(db: Session = Depends(get_db)):
    """Returns available skills and MCP server options for custom agent creation."""
    skills = get_installed_skills()
    
    # Query configured MCP servers in DB
    db_mcp_servers = db.query(MCPServer).all()
    db_mcp_list = [
        {"name": s.name, "type": s.type, "description": f"Configured {s.type} MCP Server", "id": s.id}
        for s in db_mcp_servers
    ]
    
    # Merge with presets (ensuring unique by name)
    existing_names = {s["name"].lower() for s in db_mcp_list}
    merged_mcps = list(db_mcp_list)
    for preset in DEFAULT_MCP_PRESETS:
        if preset["name"].lower() not in existing_names:
            merged_mcps.append(preset)
            
    return {
        "skills": skills,
        "mcp_servers": merged_mcps
    }

@router.get("", response_model=List[CustomAgentResponse])
def list_custom_agents(db: Session = Depends(get_db)):
    """List all user-created custom agents."""
    agents = db.query(CustomAgent).order_by(CustomAgent.created_at.desc()).all()
    return agents

@router.post("", response_model=CustomAgentResponse, status_code=status.HTTP_201_CREATED)
def create_custom_agent(agent_data: CustomAgentCreate, db: Session = Depends(get_db)):
    """Create a new user-defined custom agent."""
    name_clean = agent_data.name.strip()
    if not name_clean:
        raise HTTPException(status_code=400, detail="Agent name cannot be empty.")
    
    # Validate unique name
    existing = db.query(CustomAgent).filter(CustomAgent.name == name_clean).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"An agent with name '{name_clean}' already exists.")
    
    # Validation requirement: Agent must have an MCP or Skill or both
    has_mcp = bool(agent_data.mcp_servers and len(agent_data.mcp_servers) > 0)
    has_skill = bool(agent_data.skills and len(agent_data.skills) > 0)
    if not has_mcp and not has_skill:
        raise HTTPException(
            status_code=400, 
            detail="An agent must have at least one MCP server or Skill (or both)."
        )
    
    new_agent = CustomAgent(
        id=str(uuid.uuid4()),
        name=name_clean,
        description=agent_data.description or "",
        system_prompt=agent_data.system_prompt or "",
        llm_provider=agent_data.llm_provider or "ollama",
        model_name=agent_data.model_name or "llama3.1",
        mcp_servers=agent_data.mcp_servers or [],
        skills=agent_data.skills or [],
        is_active=agent_data.is_active if agent_data.is_active is not None else True
    )
    
    db.add(new_agent)
    db.commit()
    db.refresh(new_agent)
    return new_agent

@router.get("/{agent_id}", response_model=CustomAgentResponse)
def get_custom_agent(agent_id: str, db: Session = Depends(get_db)):
    """Get single custom agent details."""
    agent = db.query(CustomAgent).filter(CustomAgent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found.")
    return agent

@router.put("/{agent_id}", response_model=CustomAgentResponse)
def update_custom_agent(agent_id: str, update_data: CustomAgentUpdate, db: Session = Depends(get_db)):
    """Update custom agent configuration."""
    agent = db.query(CustomAgent).filter(CustomAgent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found.")
    
    # Check name uniqueness if name is changed
    if update_data.name is not None:
        name_clean = update_data.name.strip()
        if not name_clean:
            raise HTTPException(status_code=400, detail="Agent name cannot be empty.")
        if name_clean != agent.name:
            existing = db.query(CustomAgent).filter(CustomAgent.name == name_clean).first()
            if existing:
                raise HTTPException(status_code=400, detail=f"An agent with name '{name_clean}' already exists.")
            agent.name = name_clean
            
    # Capabilities validation
    new_mcps = update_data.mcp_servers if update_data.mcp_servers is not None else agent.mcp_servers
    new_skills = update_data.skills if update_data.skills is not None else agent.skills
    if len(new_mcps) == 0 and len(new_skills) == 0:
        raise HTTPException(
            status_code=400,
            detail="An agent must have at least one MCP server or Skill (or both)."
        )

    if update_data.description is not None:
        agent.description = update_data.description
    if update_data.system_prompt is not None:
        agent.system_prompt = update_data.system_prompt
    if update_data.llm_provider is not None:
        agent.llm_provider = update_data.llm_provider
    if update_data.model_name is not None:
        agent.model_name = update_data.model_name
    if update_data.mcp_servers is not None:
        agent.mcp_servers = update_data.mcp_servers
    if update_data.skills is not None:
        agent.skills = update_data.skills
    if update_data.is_active is not None:
        agent.is_active = update_data.is_active
        
    db.commit()
    db.refresh(agent)
    return agent

@router.delete("/{agent_id}")
def delete_custom_agent(agent_id: str, db: Session = Depends(get_db)):
    """Delete a custom agent."""
    agent = db.query(CustomAgent).filter(CustomAgent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found.")
    
    db.delete(agent)
    db.commit()
    return {"success": True, "message": f"Agent '{agent.name}' deleted successfully."}

@router.patch("/{agent_id}/toggle")
def toggle_custom_agent(agent_id: str, db: Session = Depends(get_db)):
    """Toggle active status of a custom agent."""
    agent = db.query(CustomAgent).filter(CustomAgent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found.")
    
    agent.is_active = not agent.is_active
    db.commit()
    db.refresh(agent)
    return {"id": agent.id, "name": agent.name, "is_active": agent.is_active}
