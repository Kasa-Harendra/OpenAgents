from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class ModHookType(str, Enum):
    BEFORE_PROMPT = "on_before_prompt"
    AFTER_PROMPT = "on_after_prompt"
    BEFORE_TOOL_EXECUTION = "on_before_tool_execution"
    AFTER_TOOL_EXECUTION = "on_after_tool_execution"
    CUSTOM_COMMAND = "on_custom_command"

class ModContext(BaseModel):
    event_type: str
    session_id: Optional[str] = None
    prompt: Optional[str] = None
    agent_name: Optional[str] = None
    tool_name: Optional[str] = None
    tool_args: Optional[Dict[str, Any]] = None
    tool_result: Optional[Any] = None
    cancelled: bool = False
    cancel_reason: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    logs: List[str] = Field(default_factory=list)

    def log(self, message: str) -> None:
        self.logs.append(message)

    def abort(self, reason: str) -> None:
        self.cancelled = True
        self.cancel_reason = reason
        self.log(f"[ABORTED] {reason}")

class ModMetadata(BaseModel):
    id: str
    name: str
    version: str = "1.0.0"
    description: str = ""
    author: str = "OpenAgents"
    enabled: bool = True
    hooks: List[str] = Field(default_factory=list)
    entry: str = "mod.py"

class BaseMod:
    def __init__(self, metadata: ModMetadata):
        self.metadata = metadata

    async def on_init(self) -> None:
        """Called when the mod is loaded and initialized."""
        pass

    async def on_before_prompt(self, ctx: ModContext) -> None:
        """Called before a prompt is dispatched to the agent model."""
        pass

    async def on_after_prompt(self, ctx: ModContext) -> None:
        """Called after the agent model returns a response."""
        pass

    async def on_before_tool_execution(self, ctx: ModContext) -> None:
        """Called before a tool is executed. Can block or sanitize tool args."""
        pass

    async def on_after_tool_execution(self, ctx: ModContext) -> None:
        """Called after a tool is executed. Can inspect or redact results."""
        pass

    async def on_custom_command(self, ctx: ModContext) -> None:
        """Called when a user invokes a custom slash command."""
        pass

    async def on_shutdown(self) -> None:
        """Called when the mod manager shuts down."""
        pass
