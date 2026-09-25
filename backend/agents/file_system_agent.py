"""
Agentic file system agent using LangChain's FileManagementToolkit and a real LLM.
This agent receives instructions and uses all available file system tools as needed.
"""
import sys
import os
import shutil
import pathlib
from datetime import datetime
from typing import List, Optional, Union, Dict
import send2trash

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from langchain.tools import tool
from langchain.agents import create_agent
from backend.agents.model_providers.agent_llms import get_agent_llm
from backend.agents.prompts.prompts import FILE_SYSTEM_PROMPT, get_structured_prompt, get_agent_system_prompt

# --- Markdown conversion tool imports ---
import pypandoc

model = get_agent_llm('FileSystemAgent')

from backend.agents.toolkits.file_system_toolkit import FileSystemToolkit

toolkit = FileSystemToolkit()
tools = toolkit.get_tools()

def get_agent():
    model = get_agent_llm('FileSystemAgent')
    if not model:
        return None
    
    prompt_str = get_agent_system_prompt('FileSystemAgent', FILE_SYSTEM_PROMPT)
    structured_system_prompt = get_structured_prompt(model, prompt_str)
    
    return create_agent(
        model,
        tools,
        system_prompt=structured_system_prompt,
        name="FileSystemAgent"
    )

agent = None # Deprecated, use get_agent()


def run_agentic_filesystem_demo():
    """
    Run a scripted demo of the file system agent.
    Returns:
        None
    """
    instructions = [
        ("user", "Write 'Hello World!' to a file named example.txt."),
        ("user", "List all files in the directory."),
        ("user", "Read the contents of example.txt."),
        ("user", "Move example.txt to example2.txt."),
        ("user", "Copy example2.txt to example3.txt."),
        ("user", "Search for all .txt files."),
        ("user", "Delete example2.txt."),
        ("user", "List all files in the directory again."),
    ]
    events = agent.stream({"messages": instructions}, stream_mode="values")
    for event in events:
        event["messages"][-1].pretty_print()

if __name__ == "__main__":
    run_agentic_filesystem_demo()
