import shlex
import subprocess
import platform
from pydantic import BaseModel, Field
from langchain.tools import BaseTool

class CommandSchema(BaseModel):
    commands: list = Field(..., description="A list of shell commands to execute.")

class RunWindowsCommandTool(BaseTool):
    name: str = "run_windows_command"
    description: str = "Executes one or more Windows shell commands (PowerShell or CMD) and returns their combined output."
    args_schema: type[BaseModel] = CommandSchema

    def _run(self, commands: list) -> str:
        print(commands)
        results = []
        for cmd in commands:
            try:
                if isinstance(cmd, str):
                    cmd = shlex.split(cmd, posix=False)
                completed = subprocess.run(cmd, shell=False, capture_output=True, text=True)
                output = completed.stdout + completed.stderr
                print(output)
            except Exception as e:
                output = str(e)
            results.append(output)
        return "\n".join(results)

class RunLinuxCommandTool(BaseTool):
    name: str = "run_linux_command"
    description: str = "Executes one or more Linux/MacOS shell commands and returns their combined output.\n- Use `pip3` for python"
    args_schema: type[BaseModel] = CommandSchema

    def _run(self, commands: list) -> str:
        print(commands)
        results = []
        for cmd in commands:
            try:
                if isinstance(cmd, str):
                    cmd = shlex.split(cmd)
                completed = subprocess.run(cmd, shell=False, capture_output=True, text=True)
                output = completed.stdout + completed.stderr
                print(output)
            except Exception as e:
                output = str(e)
            results.append(output)
        return "\n".join(results)

class ReadFileSchema(BaseModel):
    file_name: str = Field(..., description="The name of the file to read.")

class ReadFileTool(BaseTool):
    name: str = "read_file"
    description: str = "Reads the contents of a file and returns it as a string."
    args_schema: type[BaseModel] = ReadFileSchema

    def _run(self, file_name: str) -> str:
        with open(file_name, 'r') as f:
            return f.read()

from langchain_core.tools import BaseToolkit
from typing import List

class TerminalToolkit(BaseToolkit):
    def get_tools(self) -> List[BaseTool]:
        if platform.system() == "Windows":
            return [RunWindowsCommandTool(), ReadFileTool()]
        else:
            return [RunLinuxCommandTool(), ReadFileTool()]
