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
import subprocess

from backend.agents.model_providers.agent_llms import get_agent_llm
from backend.agents.prompts.prompts import TERMINAL_PROMPT, get_structured_prompt, get_agent_system_prompt

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

@tool
def run_linux_command(commands: list):
    """
    Executes one or more Linux/MacOS shell commands and returns their combined output.

    - Use `pip3` for python 
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

if platform.system() == "Windows":
    tools = [run_windows_command, read_file]
else:
    tools = [run_linux_command, read_file]

def get_agent():
    model = get_agent_llm('TerminalAgent')
    if not model:
        return None
    
    prompt_str = get_agent_system_prompt('TerminalAgent', TERMINAL_PROMPT)
    structured_system_prompt = get_structured_prompt(model, prompt_str)

    return create_agent(
        model,
        tools,
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
