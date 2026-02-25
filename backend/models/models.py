from sqlalchemy import Column, String, JSON, DateTime
from sqlalchemy.sql import func
from backend.db.database import Base
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

# SQLAlchemy Model
class AgentConfig(Base):
    __tablename__ = "agent_configs"

    agent_name = Column(String, primary_key=True, index=True)
    llm_provider = Column(String)
    agent_type = Column(String) # 'chat' or 'embed'
    llm_config = Column(JSON)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), default=func.now())

# Pydantic Models
class agent_config_base(BaseModel):
    llm_provider: str
    agent_type: str
    llm_config: Dict[str, Any]

class agent_config_create(agent_config_base):
    agent_name: str

class agent_config_response(agent_config_base):
    agent_name: str
    
    class Config:
        from_attributes = True

class websocket_message(BaseModel):
    type: str # 'prompt', 'tool_start', 'tool_output', 'agent_response', 'error', 'complete', 'status', 'tasks_decomposed', 'agent_start', 'content_chunk'
    agent_name: Optional[str] = None
    content: Any = None
    chunk: Optional[str] = None
    step: Optional[int] = None

class UserRequest(BaseModel):
    prompt: str
    session_id: str
    history: List[Dict[str, Any]] = []
<<<<<<< HEAD
    base_directory: str
=======
>>>>>>> b77603ccca528f233f6ce3688c4be5faf77979b3
    model_config = {
        "extra": "ignore"
    }
