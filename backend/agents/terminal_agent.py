import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import asyncio
from langchain_ollama import ChatOllama
from langchain.agents import create_agent
from langchain.tools import tool
import subprocess

from backend.agents.model_providers.agent_llms import get_agent_llm
from backend.agents.prompts import TERMINAL_PROMPT, get_structured_prompt

@tool
def run_windows_command(commands: list):
    """
    Executes one or more Windows shell commands (PowerShell or CMD) and returns their combined output.
    """
    print(commands)
    results = []
    for cmd in commands:
        try:
            completed = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            output = completed.stdout + completed.stderr
            print(output)
        except Exception as e:
            output = str(e)
        results.append(output)
    return "\n".join(results)

def read_file(file_name: str): 
    """
    Reads the contents of a file and returns it as a string.
    """
    with open(file_name, 'r') as f:
        return f.read()

tools = [run_windows_command, read_file]

model = get_agent_llm('TerminalAgent')
if model:
    # Use centralized prompt helper for caching
    structured_system_prompt = get_structured_prompt(model, TERMINAL_PROMPT)

    agent = create_agent(
        model,
        tools,
        system_prompt=structured_system_prompt,
        name="TerminalAgent"
    )
else:
    agent = None

async def main():
    user_message = "What are the files in my d: disk"
    result = await agent.ainvoke({
        "messages": [
            ("system", system_prompt),
            ("user", user_message)
        ]
    })
    print("\nAgent result:")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
