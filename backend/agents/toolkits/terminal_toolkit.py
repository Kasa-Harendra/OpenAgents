import os
import sys
import subprocess
import platform
import shlex
import time
from typing import Optional, List, Dict
from pydantic import BaseModel, Field
from langchain.tools import BaseTool

DANGEROUS_PATTERNS = [
    "rm -rf /",
    ":(){ :|:& };:",
    "mkfs",
    "dd if=/dev/zero",
    "> /dev/sda",
    "format c:",
]

class CommandExecutionSchema(BaseModel):
    command: str = Field(..., description="The shell command to execute.")
    cwd: Optional[str] = Field(None, description="Working directory to run the command in. Defaults to current workspace.")
    timeout_seconds: Optional[int] = Field(60, description="Max execution time before terminating the process (default: 60s).")

class RunTerminalCommandTool(BaseTool):
    name: str = "run_command"
    description: str = (
        "Execute a shell command with timeout protection, directory tracking, and structured output. "
        "Returns Exit Code, STDOUT, and STDERR."
    )
    args_schema: type[BaseModel] = CommandExecutionSchema
    _current_cwd: str = os.getcwd()

    def _run(self, command: str, cwd: Optional[str] = None, timeout_seconds: int = 60) -> str:
        # 1. Zero-trust safety verification
        cmd_lower = command.lower().strip()
        for dangerous in DANGEROUS_PATTERNS:
            if dangerous in cmd_lower:
                return (
                    f"⛔ BLOCKED BY SECURITY GATEWAY\n"
                    f"Command '{command}' matches restricted destructive pattern '{dangerous}'.\n"
                    f"If this operation is intended, request Human-in-the-Loop authorization."
                )

        # 2. Determine working directory
        target_cwd = cwd if cwd else self._current_cwd
        if not os.path.exists(target_cwd):
            return f"❌ Target directory not found: {target_cwd}"

        # 3. Handle 'cd' commands directly to maintain state
        if cmd_lower.startswith("cd "):
            target_path = command[3:].strip().strip('"').strip("'")
            new_path = os.path.abspath(os.path.join(target_cwd, target_path))
            if os.path.isdir(new_path):
                self._current_cwd = new_path
                return f"✅ Working directory changed to: {new_path}"
            return f"❌ Directory does not exist: {target_path}"

        # 4. Execute command
        is_windows = platform.system() == "Windows"
        shell_cmd = command
        start_time = time.time()

        try:
            process = subprocess.run(
                shell_cmd,
                shell=True,
                cwd=target_cwd,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                env=os.environ.copy()
            )
            duration = round(time.time() - start_time, 2)
            stdout = process.stdout.strip()
            stderr = process.stderr.strip()
            exit_code = process.returncode

            # Format structured output like Claude Code
            output_parts = [
                f"Command: {command}",
                f"Directory: {target_cwd}",
                f"Exit Code: {exit_code} (took {duration}s)",
            ]

            if stdout:
                # Limit oversized stdout to avoid flooding context window
                if len(stdout) > 20000:
                    truncated_stdout = stdout[:20000] + f"\n...[Truncated: {len(stdout) - 20000} characters omitted]"
                    output_parts.append(f"STDOUT:\n```text\n{truncated_stdout}\n```")
                else:
                    output_parts.append(f"STDOUT:\n```text\n{stdout}\n```")

            if stderr:
                output_parts.append(f"STDERR:\n```text\n{stderr}\n```")

            if not stdout and not stderr:
                output_parts.append("Output: (Command executed with no terminal output)")

            return "\n\n".join(output_parts)

        except subprocess.TimeoutExpired:
            return (
                f"⏱️ COMMAND TIMEOUT\n"
                f"Command '{command}' exceeded maximum limit of {timeout_seconds} seconds and was terminated.\n"
                f"Check for hanging processes or interactive prompts."
            )
        except Exception as e:
            return f"❌ Execution error: {str(e)}"

from langchain_core.tools import BaseToolkit

class TerminalToolkit(BaseToolkit):
    working_dir: Optional[str] = None

    def get_tools(self) -> List[BaseTool]:
        tool = RunTerminalCommandTool()
        if self.working_dir:
            tool._current_cwd = os.path.abspath(self.working_dir)
        return [tool]

RunCommandTool = RunTerminalCommandTool

