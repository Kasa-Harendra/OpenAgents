import sys
import os 
from typing import List, Optional, Union, Dict, Any

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from langchain.agents import create_agent
from backend.agents.model_providers.agent_llms import get_agent_llm
from backend.agents.prompts.prompts import INTEGRATOR_AGENT_PROMPT, get_structured_prompt, get_agent_system_prompt
from backend.utils.additional_tools import get_tools

from langgraph.graph.state import CompiledStateGraph
from langchain.agents.middleware.types import (AgentState, _InputAgentState, _OutputAgentState)


async def get_agent() -> CompiledStateGraph[AgentState[Any], Any, _InputAgentState, _OutputAgentState[Any]]:
    """Lazily initialize the IntegratorAgent with Langchain Toolkits."""
    model = get_agent_llm("IntegratorAgent")
    if not model:
        return None
        
    tools = get_tools()
    
    # Use centralized prompt helper for caching
    prompt_str = get_agent_system_prompt("IntegratorAgent", INTEGRATOR_AGENT_PROMPT)
    structured_system_prompt = get_structured_prompt(model, prompt_str)

    return create_agent(
        model,
        tools,
        system_prompt=structured_system_prompt,
        name="IntegratorAgent"
    )

