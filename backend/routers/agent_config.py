import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.db.database import engine, Base, get_db
from backend.models.models import (
    AgentConfig, agent_config_create, agent_config_response, websocket_message,
    MCPServer, mcp_server_create, mcp_server_response, AgentPrompt, agent_prompt_create, agent_prompt_response
)
from backend.agents.prompts.prompts import (
    ORCHESTRATOR_PROMPT_BASE, FILE_SYSTEM_PROMPT, TERMINAL_PROMPT,
    RESEARCH_PROMPT, INTEGRATOR_AGENT_PROMPT, RAG_PROMPT_BASE,
    CODE_EXPLAINER_PROMPT_BASE, YT_PROMPT_BASE
)
from backend.services.websocket_manager import manager
from backend.agent_flow import execute
from backend.agents.model_providers.agent_llms import load_agent_llms

from typing import List, Dict, Any
import os
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session

# Initialize database with config from registry if empty
def init_db():
    db = next(get_db())
    
    # Specified order
    ordered_agent_names = [
        "Coordinator", 
        "FileSystemAgent", 
        "ResearchAgent", 
        "TerminalAgent", 
        "BrowserAgent", 
        "RAGAgent", 
        "EmbeddingModel", 
        "IntegratorAgent", 
        "GuardianAgent"
    ]
    
    # Load all agents from registry
    registry_path = os.environ.get('AGENT_REGISTRY_PATH', 'backend/config/agent_registry.json')
    if not os.path.exists(registry_path):
        registry_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config', 'agent_registry.json'))
    
    registry_agents = []
    try:
        if os.path.exists(registry_path):
            with open(registry_path, "r") as f:
                registry_data = json.load(f)
                registry_agents = list(registry_data["agents"].keys())
    except Exception as e:
        print(f"Error loading registry: {e}")

    # Combine and deduplicate while preserving order
    all_agents = ordered_agent_names.copy()
    for ra in registry_agents:
        if ra not in all_agents:
            all_agents.append(ra)

    # System agents descriptions
    system_descriptions = {
        "Coordinator": "Main orchestrator that decomposes tasks and routes them to specialized agents",
        "EmbeddingModel": "Model used for generating vector embeddings for RAG and search",
        "GuardianAgent": "Strict evaluation agent that judges response quality and safety"
    }

    for agent_name in all_agents:
        # Get description from registry or system descriptions
        description = None
        if os.path.exists(registry_path):
            try:
                with open(registry_path, "r") as f:
                    registry_data = json.load(f)
                    agent_info = registry_data.get("agents", {}).get(agent_name)
                    if agent_info:
                        description = agent_info.get("description")
            except:
                pass
        
        if not description:
            description = system_descriptions.get(agent_name)

        db_config = db.query(AgentConfig).filter(AgentConfig.agent_name == agent_name).first()
        if not db_config:
            # Create new entry with default unconfigured state
            db_config = AgentConfig(
                agent_name=agent_name,
                llm_provider="none",
                agent_type="embed" if agent_name == "EmbeddingModel" else "chat",
                llm_config={
                    "api_key": None,
                    "model": "",
                    "base_url": ""
                },
                description=description
            )
            db.add(db_config)
        else:
            # Update description if it changed in registry
            if description and db_config.description != description:
                db_config.description = description
    
    # Initialize default prompts
    default_prompts = {
        "Coordinator": ORCHESTRATOR_PROMPT_BASE,
        "FileSystemAgent": FILE_SYSTEM_PROMPT,
        "TerminalAgent": TERMINAL_PROMPT,
        "ResearchAgent": RESEARCH_PROMPT,
        "IntegratorAgent": INTEGRATOR_AGENT_PROMPT,
        "RAGAgent": RAG_PROMPT_BASE,
        "CodeExplainerAgent": CODE_EXPLAINER_PROMPT_BASE,
        "YTAgent": YT_PROMPT_BASE,
        "ChatMode": "You are helpful assistant"
    }

    for p_agent_name, default_prompt in default_prompts.items():
        db_prompt = db.query(AgentPrompt).filter(AgentPrompt.agent_name == p_agent_name).first()
        if not db_prompt:
            db_prompt = AgentPrompt(
                agent_name=p_agent_name,
                system_prompt=default_prompt
            )
            db.add(db_prompt)
    
    db.commit()
    db.close()

router = APIRouter()

@router.get("/config", response_model=List[agent_config_response])
def get_all_configs(db: Session = Depends(get_db)):
    return db.query(AgentConfig).all()

@router.get("/config/{agent_name}", response_model=agent_config_response)
def get_config(agent_name: str, db: Session = Depends(get_db)):
    config = db.query(AgentConfig).filter(AgentConfig.agent_name == agent_name).first()
    if not config:
        raise HTTPException(status_code=404, detail="Agent configuration not found")
    return config

@router.put("/config/{agent_name}", response_model=agent_config_response)
def update_config(agent_name: str, config_update: agent_config_create, db: Session = Depends(get_db)):
    db_config = db.query(AgentConfig).filter(AgentConfig.agent_name == agent_name).first()
    if not db_config:
        db_config = AgentConfig(agent_name=agent_name)
        db.add(db_config)
    
    db_config.llm_provider = config_update.llm_provider
    db_config.agent_type = config_update.agent_type
    db_config.llm_config = config_update.llm_config
    
    db.commit()
    db.refresh(db_config)
    
    # Reload LLMs in the live system
    load_agent_llms()
    
    return db_config

@router.get("/prompts", response_model=List[agent_prompt_response])
def get_all_prompts(db: Session = Depends(get_db)):
    return db.query(AgentPrompt).all()

@router.get("/prompts/{agent_name}", response_model=agent_prompt_response)
def get_prompt(agent_name: str, db: Session = Depends(get_db)):
    prompt = db.query(AgentPrompt).filter(AgentPrompt.agent_name == agent_name).first()
    if not prompt:
        raise HTTPException(status_code=404, detail="Agent prompt not found")
    return prompt

@router.put("/prompts/{agent_name}", response_model=agent_prompt_response)
def update_prompt(agent_name: str, prompt_update: agent_prompt_create, db: Session = Depends(get_db)):
    db_prompt = db.query(AgentPrompt).filter(AgentPrompt.agent_name == agent_name).first()
    if not db_prompt:
        db_prompt = AgentPrompt(agent_name=agent_name)
        db.add(db_prompt)
    
    db_prompt.system_prompt = prompt_update.system_prompt
    
    db.commit()
    db.refresh(db_prompt)
    
    return db_prompt
