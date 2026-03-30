from  pydantic import BaseModel
from typing import Optional

class AgentConfig(BaseModel):
    agent_name: str
    type: str
    provider: str
    model_name: str
    api_key: Optional[str]
    base_url: Optional[str]