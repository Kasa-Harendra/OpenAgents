from  pydantic import BaseModel
from typing import Optional

class AgentConfig(BaseModel):
    agent_name: str
    type: str
    provider: str
    model_name: str
    apiKey: Optional[str]
    base_url: Optional[str]