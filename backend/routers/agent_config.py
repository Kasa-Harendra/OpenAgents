from backend.db.database import engine, Base, get_db
from backend.models.models import AgentConfig, agent_config_create, agent_config_response, websocket_message
from backend.websocket_manager import manager
from backend.agent_flow import execute

from typing import List, Dict, Any
import os
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session

# Initialize database with config from JSON if empty
def init_db():
    db = next(get_db())
    if db.query(AgentConfig).count() == 0:
        config_path = os.environ.get('AGENT_CONFIG_PATH', 'backend/config/agents_config.json')
        if not os.path.exists(config_path):
            config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'config', 'agents_config.json'))
        
        try:
            with open(config_path, "r") as f:
                config_data = json.load(f)
                for agent_name, config in config_data["agents"].items():
                    db_config = AgentConfig(
                        agent_name=agent_name,
                        llm_provider=config["llm_provider"],
                        agent_type=config["type"],
                        llm_config=config["llm_config"]
                    )
                    db.add(db_config)
                db.commit()
        except FileNotFoundError:
            print("initial config file not found. skipping database initialization.")
    db.close()

init_db()

router = APIRouter()

@router.get("/config", response_model=List[agent_config_response])
def get_all_configs(db: Session = Depends(get_db)):
    return db.query(AgentConfig).all()

@router.get("/config/{agent_name}", response_model=agent_config_response)
def get_config(agent_name: str, db: Session = Depends(get_db)):
    config = db.query(AgentConfig).filter(AgentConfig.agent_name == agent_name).first()
    if not config:
        raise HTTPException(status_status=404, detail="Agent configuration not found")
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
    return db_config