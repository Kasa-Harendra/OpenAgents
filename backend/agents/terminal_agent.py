import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import asyncio
from langchain_ollama import ChatOllama
from langchain.agents import create_agent
from langchain.tools import tool
import subprocess

from backend.agents.model_providers.agent_llms import agent_llms

@tool
def run_windows_command(commands: list):
    """
    Executes one or more Windows shell commands (PowerShell or CMD) and returns their combined output.

    Args:
        commands (list[str]):
            A list of command strings to execute. Each string should be a complete command as you would type in PowerShell or CMD.
            Example:
                [
                    'Get-ChildItem -Path C:\\Users\\Public',
                    'python --version',
                    'git status'
                ]

            - Use PowerShell syntax by default (preferred over CMD).
            - Use absolute paths when possible.
            - Each command is run independently; output is collected for each.
            - Destructive commands (e.g., Remove-Item, del, rmdir) should be clearly indicated and require user confirmation.

    Returns:
        str: Combined output of all commands, including STDOUT and STDERR for each command, separated by newlines.

    Output Format:
        For each command, output should be formatted as:
            Command: <command>
            Exit Code: <code>
            Output: <stdout>
            Errors: <stderr>

    Notes:
        - Do not explain or summarize the output unless explicitly asked.
        - Always run the command exactly as provided.
        - If a command is destructive, note the risk in the output.
        - If an error occurs, include the error message in the output.
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

tools = [run_windows_command]

model = agent_llms['TerminalAgent']
system_prompt = """You are a Windows Terminal Agent specializing in PowerShell and CMD command execution.

CAPABILITIES:
- Execute PowerShell/CMD commands
- Navigate directories
- Manage processes
- Run development tools (git, npm, python, etc.)
- System inspection and automation

SAFETY PROTOCOLS:
⚠️ DESTRUCTIVE COMMANDS require user confirmation:
- File deletion: rm, del, Remove-Item
- Directory deletion: rmdir, Remove-Item -Recurse
- System operations: shutdown, restart, format
- Bulk operations: wildcards with delete commands

EXECUTION GUIDELINES:
1. Use PowerShell by default (more reliable than CMD)
2. Use ABSOLUTE paths when provided or working directory is unclear
3. Validate command exists before execution
4. Return: STDOUT, STDERR, and exit code
5. Explain errors in user-friendly terms
6. Suggest fixes for common errors
7. Never include `cmd /c` in your commands.

OUTPUT FORMAT:
```
Command: <command>
Exit Code: <code>
Output: <stdout>
Errors: <stderr>
```

EXAMPLES:
- List files: `Get-ChildItem -Path C:\\Users\\Public`
- Check Python: `python --version`
- Git clone: `git clone https://github.com/example/repo.git`
- Process list: `Get-Process | Select-Object -First 10`

CRITICAL: Always run the command requested by the user and return the output directly. Do not explain or summarize unless explicitly asked.
For destructive commands, execute but note the risk in the output.
"""
agent = create_agent(
    model, 
    tools, 
    system_prompt=system_prompt,
    name="TerminalAgent"
)

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
