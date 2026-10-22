import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from sqlalchemy import Column, String, JSON, DateTime, Integer, Boolean
from sqlalchemy.sql import func
from backend.db.database import Base
from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any, List
import datetime
import uuid

# SQLAlchemy Model
class CustomAgent(Base):
    __tablename__ = "agents"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    system_prompt = Column(String, nullable=True)
    llm_provider = Column(String(50), default="ollama")
    model_name = Column(String(100), default="llama3.1")
    mcp_servers = Column(JSON, default=list)
    skills = Column(JSON, default=list)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc), onupdate=lambda: datetime.datetime.now(datetime.timezone.utc))
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

class Conversation(Base):
    __tablename__ = "conversations"

    convo_id = Column(String, primary_key=True, index=True)
    title = Column(String, default="New Chat")
    file_path = Column(String)
    message_count = Column(Integer, default=0)
    last_message_preview = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc), onupdate=lambda: datetime.datetime.now(datetime.timezone.utc))

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
    system_prompt: str

class agent_prompt_response(agent_prompt_base):
    agent_name: str
    updated_at: datetime.datetime

    class Config:
        from_attributes = True

class websocket_message(BaseModel):
    type: str # 'prompt', 'tool_start', 'tool_output', 'agent_response', 'error', 'complete', 'status', 'tasks_decomposed', 'agent_start', 'content_chunk', 'agent_error', 'tool_error'
    session_id: Optional[str] = None
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
    type: str = "stdio" # 'stdio' or 'sse'
    command: Optional[str] = None
    args: Optional[List[str]] = None
    env: Optional[Dict[str, str]] = None
    url: Optional[str] = None

class mcp_server_create(mcp_server_base):
    id: Optional[str] = None

class mcp_server_update(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    command: Optional[str] = None
    args: Optional[List[str]] = None
    env: Optional[Dict[str, str]] = None
    url: Optional[str] = None

class mcp_server_response(mcp_server_base):
    id: str
    updated_at: Optional[datetime.datetime] = None

    class Config:
        from_attributes = True

# Conversation Models
class ConversationSummary(BaseModel):
    convo_id: str
    title: str
    message_count: int
    last_message_preview: Optional[str] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True

class ConversationCreate(BaseModel):
    convo_id: Optional[str] = None
    title: Optional[str] = "New Chat"
    base_directory: Optional[str] = None
    chat_mode: Optional[str] = "multiagent"

class ConversationUpdate(BaseModel):
    title: Optional[str] = None
    base_directory: Optional[str] = None

class ConversationDetail(BaseModel):
    convo_id: str
    title: str
    created_at: str
    updated_at: str
    base_directory: Optional[str] = None
    chat_mode: Optional[str] = "multiagent"
    messages: List[Dict[str, Any]] = []

# Custom Agent Models
class CustomAgentBase(BaseModel):
    name: str
    description: Optional[str] = ""
    system_prompt: Optional[str] = ""
    llm_provider: str = "ollama"
    model_name: str = "llama3.1"
    mcp_servers: List[Any] = []
    skills: List[Any] = []
    is_active: bool = True

class CustomAgentCreate(CustomAgentBase):
    pass

class CustomAgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    llm_provider: Optional[str] = None
    model_name: Optional[str] = None
    mcp_servers: Optional[List[Any]] = None
    skills: Optional[List[Any]] = None
    is_active: Optional[bool] = None

class CustomAgentResponse(CustomAgentBase):
    id: str
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None

    class Config:
        from_attributes = True
