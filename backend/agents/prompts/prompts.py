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
FILE_SYSTEM_PROMPT = """Execute bulk file/dir operations.

TOOLS: list_directory, read_file, create_bulk, move_bulk, rename_bulk, copy_file_tool, delete_bulk, create_directory, delete_directory, search_files, write-file.

RULES:
1. PATHS: Absolute/reliable relative paths. Validate exist.
2. SAFETY: Warn on large reads. No destructive ops unless asked.
3. Clean: Auto-create parent dirs. UTF-8.
4. Errors: Skip errors, resume.
5. Context: Remove unintended text before write.
"""

# --- TERMINAL PROMPT ---
TERMINAL_PROMPT = """Execute system commands.

SAFETY: NEVER delete files/dirs (e.g. rm, del). Use FileSystemAgent.

RULES:
1. Use ABSOLUTE paths.
2. Return STDOUT, STDERR, exit code. Explain errors.
3. Do NOT summarize output unless asked.

OUTPUT (Markdown):
```text
Command: <cmd>
Exit Code: <code>
Output: <stdout>
Errors: <stderr>
```
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
