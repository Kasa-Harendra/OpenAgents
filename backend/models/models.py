import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from sqlalchemy import Column, String, JSON, DateTime, Integer
from sqlalchemy.sql import func
from backend.db.database import Base
from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any, List
import datetime

# SQLAlchemy Model
class AgentConfig(Base):
    __tablename__ = "agent_configs"

    id = Column(Integer, primary_key=True, index=True)
    agent_name = Column(String, unique=True, index=True)
    llm_provider = Column(String)  # ollama, openai, gemini, anthropic, groq, others, none
    agent_type = Column(String)  # chat, code, research, etc.
    llm_config = Column(JSON)  # {model: str, api_key: str, base_url: str}
    description = Column(String, nullable=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc), onupdate=lambda: datetime.datetime.now(datetime.timezone.utc))

class AgentPrompt(Base):
    __tablename__ = "agent_prompts"

    id = Column(Integer, primary_key=True, index=True)
    agent_name = Column(String, unique=True, index=True)
    system_prompt = Column(String)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc), onupdate=lambda: datetime.datetime.now(datetime.timezone.utc))

class MCPServer(Base):
    __tablename__ = "mcp_servers"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    type = Column(String)  # 'stdio' or 'sse'
    command = Column(String, nullable=True)
    args = Column(JSON, nullable=True)
    env = Column(JSON, nullable=True)
    url = Column(String, nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), default=func.now())

# Pydantic Models
class agent_config_base(BaseModel):
    llm_provider: str
    agent_type: str
    llm_config: Dict[str, Any]
    description: Optional[str] = None

class agent_config_create(BaseModel):
    agent_name: str
    llm_provider: str
    agent_type: str
    llm_config: Dict[str, Any]
    description: Optional[str] = None

class agent_config_response(BaseModel):
    agent_name: str
    llm_provider: str
    agent_type: str
    llm_config: Dict[str, Any]
    description: Optional[str] = None
    
    class Config:
        from_attributes = True

class agent_prompt_base(BaseModel):
    system_prompt: str

class agent_prompt_create(agent_prompt_base):
    agent_name: str

class agent_prompt_response(agent_prompt_base):
    agent_name: str
    updated_at: datetime.datetime

    class Config:
        from_attributes = True

class websocket_message(BaseModel):
    type: str # 'prompt', 'tool_start', 'tool_output', 'agent_response', 'error', 'complete', 'status', 'tasks_decomposed', 'agent_start', 'content_chunk', 'agent_error', 'tool_error'
    agent_name: Optional[str] = None
    content: Any = None
    chunk: Optional[str] = None
    step: Optional[int] = None

class UserRequest(BaseModel):
    prompt: str
    session_id: str
    history: List[Dict[str, Any]] = []
    base_directory: str
    chat_mode: str = "multiagent"
    model_config = {
        "extra": "ignore"
    }

# MCP Server Models
class mcp_server_base(BaseModel):
    name: str
    type: str
    command: Optional[str] = None
    args: Optional[List[str]] = None
    env: Optional[Dict[str, str]] = None
    url: Optional[str] = None

class mcp_server_create(mcp_server_base):
    id: str

class mcp_server_response(mcp_server_base):
    id: str
    updated_at: datetime.datetime

    class Config:
        from_attributes = True
