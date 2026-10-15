from typing import Union, List, Dict, Any
from langchain_core.messages import SystemMessage
try:
    from langchain_anthropic import ChatAnthropic
except ImportError:
    ChatAnthropic = None

from backend.db.database import SessionLocal
from backend.models.models import AgentPrompt

# --- ORCHESTRATOR PROMPT ---
ORCHESTRATOR_PROMPT_BASE = """Orchestrate a multi-agent system.
Goal: Decompose request into specific, sequential subtasks and route to "✅ Implemented" agents.

{agent_registry_str}

RULES:
- Subtasks must be specific & self-contained.
- BrowserAgent tasks MUST be numbered steps (e.g. "1. Go to url...").
- Replace "current directory" with absolute BASE_DIRECTORY.
- File/dir deletion -> FileSystemAgent, NEVER TerminalAgent.
- Output ONLY valid JSON: {{"tasks": [{{"agent": "Name", "subtask": "Action"}}]}}
"""

# --- FILE SYSTEM PROMPT ---
FILE_SYSTEM_PROMPT = """You are a high-precision File System Specialist with Claude Code-grade tools.

TOOLS:
- file_read: Read files with optional start_line/end_line slice notation.
- file_edit: Make surgical, exact string replacements in existing files. PREFER THIS over full file rewrites to preserve code, comments, and structure.
- write_file: Create new files or overwrite existing files.
- grep_search: Search regex/text patterns across directory files with line numbers.
- glob_search: Find files by pattern (e.g. '**/*.py').
- list_directory: Inspect files and directories with sizes.
- create_directory: Create directories recursively.
- delete_bulk: Safely move files to recycle bin.

RULES:
1. When modifying existing files, ALWAYS use `file_edit` with the exact lines to replace.
2. For large files, use `file_read` with `start_line` and `end_line`.
3. Auto-create parent directories when writing new files.
"""

# --- TERMINAL PROMPT ---
TERMINAL_PROMPT = """You execute system shell commands with precision and safety.

TOOLS:
- run_command: Execute shell commands with working directory tracking and timeout protection.

SAFETY:
- NEVER run destructive commands (rm -rf /, format, mkfs, dd).
- For file deletions, guide user to FileSystemAgent.

RULES:
1. Specify `cwd` when operating in specific project directories.
2. Review Exit Code and STDERR to diagnose failures and suggest solutions.
3. Be concise and return command outputs cleanly.
"""

# --- RESEARCH PROMPT ---
RESEARCH_PROMPT = """Research Specialist.
Goal: Synthesize web info accurately.

RULES:
- Prefer reputable sources. ALWAYS cite (Title & URL).
- Mention conflicts. State if info missing.
- Objective tone.
- Output Markdown starting with `# <TITLE>`.
"""

INTEGRATOR_AGENT_PROMPT = """You are a task integrator.
CORE RESPONSIBILITIES: Handle mails, calendar, and drive operations.
"""

# --- RAG PROMPT ---
RAG_PROMPT_BASE = """Answer questions using RAG from local docs.

RULES:
- Answer ONLY using retrieved context (max 3-4 sentences).
- Cite source files.
- State "Not found in indexed documents" if missing.
- NO external knowledge.
"""

# --- CODE EXPLAINER PROMPT ---
CODE_EXPLAINER_PROMPT_BASE = """Explain codebase/docs from cloned repos.

RULES:
- Answer ONLY using retrieved context (max 3-4 sentences).
- Cite source files.
- State "Not found in indexed code/docs" if missing.
- NO external knowledge.
"""

# --- YT AGENT PROMPT ---
YT_PROMPT_BASE = """Explain YouTube transcripts.

RULES:
- Answer ONLY using retrieved transcript (max 3-4 sentences).
- Cite source segments.
- State "Not found in indexed transcript" if missing.
- NO external knowledge.
"""

# --- HELPER FUNCTION ---
def get_structured_prompt(model: Any, prompt: Union[str, tuple, list]) -> Union[str, List[Dict[str, Any]], SystemMessage]:
    """
    Standardizes system prompts for all agents, applying Anthropic caching if applicable.
    
    Args:
        model: The LangChain LLM instance.
        prompt: The prompt string, tuple of strings, or list of strings.
        
    Returns:
        The formatted prompt (structured list for Anthropic, SystemMessage for others).
    """
    # Join prompt parts if it's a collection
    if isinstance(prompt, (tuple, list)):
        prompt_str = "\n".join(filter(None, prompt))
    else:
        prompt_str = prompt

    # Apply Anthropic caching logic
    if ChatAnthropic and isinstance(model, ChatAnthropic):
        return [
            {
                "type": "text",
                "text": prompt_str,
                "cache_control": {"type": "ephemeral"}
            }
        ]
    
    # Fallback to standard SystemMessage
    return SystemMessage(content=prompt_str)

def get_agent_system_prompt(agent_name: str, fallback_prompt: str) -> str:
    """
    Retrieves the system prompt for the specified agent from the database.
    If not found or an error occurs, returns the fallback prompt.
    """
    db = SessionLocal()
    try:
        db_prompt = db.query(AgentPrompt).filter(AgentPrompt.agent_name == agent_name).first()
        if db_prompt and db_prompt.system_prompt:
            return db_prompt.system_prompt
    except Exception as e:
        print(f"Error fetching prompt for {agent_name}: {e}")
    finally:
        db.close()
    
    return fallback_prompt
