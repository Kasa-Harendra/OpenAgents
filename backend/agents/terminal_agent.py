from platform import platform
import sys
import os
import platform

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import asyncio
from langchain_ollama import ChatOllama
from langchain.agents import create_agent
from langchain.tools import tool

from backend.agents.model_providers.agent_llms import get_agent_llm
from backend.agents.prompts.prompts import TERMINAL_PROMPT, get_structured_prompt, get_agent_system_prompt
from backend.agents.toolkits.terminal_toolkit import TerminalToolkit

toolkit = TerminalToolkit()

def get_agent():
    model = get_agent_llm('TerminalAgent')
    if not model:
        return None
    
    prompt_str = get_agent_system_prompt('TerminalAgent', TERMINAL_PROMPT)
    structured_system_prompt = get_structured_prompt(model, prompt_str)

    return create_agent(
        model,
        toolkit.get_tools(),
        system_prompt=structured_system_prompt,
        name="TerminalAgent"
    )

agent = None # Deprecated, use get_agent()


async def main():
    user_message = "What are the files in my d: disk"
    result = await agent.ainvoke({
        "messages": [
            ("system", get_structured_prompt()),
            ("user", user_message)
        ]
    })
    print("\nAgent result:")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
