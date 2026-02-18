# Multi-Agent AI Desktop Assistant (with MCP Support)

## 1. System Architecture Diagram

The application follows a **Sidecar Architecture** to bridge high-performance UI with deep system-level AI orchestration, extended with **Model Context Protocol (MCP)** support.

### Core Layers

- **Frontend Layer (Electron + React)**  
  The "Visual Shell." Manages the desktop window, user input, permission prompts, MCP server management UI, and real-time streaming of agent thoughts.

- **API Bridge (Localhost)**  
  High-speed communication using FastAPI:
  - REST → commands and task dispatch
  - WebSockets → live reasoning / thought streaming

- **Backend Layer (FastAPI Sidecar)**  
  The "Agent Controller" and **MCP Host**. A standalone Python executable that orchestrates:
  - Multi-agent execution
  - MCP client connections
  - Tool discovery and execution

- **Persistence Layer**
  - SQLite → task history and state
  - Windows Credential Manager → API keys and OAuth tokens

---

## 2. Multi-Agent Hierarchy

The system uses a **Router–Worker Pattern** orchestrated by the **Google Agent Development Kit (ADK)**.

### A. Coordinator (Orchestrator)

- **Framework**: `google.adk.agents.LlmAgent`
- **Role**:
  - Analyzes user intent
  - Decomposes tasks
  - Routes subtasks to local agents or MCP tools
  - Maintains global State and reasoning history

---

### B. Specialized Worker Agents

| Agent Name       | Tech Stack                           | Capability                                                            |
| ---------------- | ------------------------------------ | --------------------------------------------------------------------- |
| Coordinator      | google-adk                           | High-level orchestration across local tools, web, and MCP services    |
| IntegrationAgent | mcp-python-sdk                       | Handles Google Sheets, Gmail, Slack, and other MCP-based integrations |
| FileSystemAgent  | LangChain FileManagementToolkit / OS | CRUD operations, directory cleanup, batch renaming                    |
| BrowserAgent     | browser-use + Playwright             | Visual navigation, form filling, automated web interaction            |
| ScrapingAgent    | Crawl4AI                             | Converts JS-heavy websites into clean, LLM-ready Markdown             |
| TerminalAgent    | Python subprocess                    | Executes PowerShell / CMD commands in a sandbox                       |
| RAGAgent         | LangChain + ChromaDB                 | Semantic search over local folders or project directories             |
| ResearchAgent    | ADK + Web Search APIs                | Multi-step reasoning to synthesize web data into reports              |

---

## 3. Workflow Pattern: The Reasoning Loop

### Example User Input

User selects a "Brain" (e.g., **Gemini 2.0**) and enters:

> “Find the latest Nvidia stock price and save a summary in a new folder on my desktop.”

### Execution Flow

1. **Dispatch**  
   The Coordinator identifies:
   - Web access requirement
   - Local file system access
   - No MCP tools required

2. **Action 1 – BrowserAgent**  
   Uses `browser-use` to navigate to a financial website and extract the price.

3. **Action 2 – FileSystemAgent**  
    Creates:
   `C:\Users\Name\Desktop\Stocks`

4. **Observation**  
   Each agent reports progress back to the global State.

5. **Streaming**  
   FastAPI streams intermediate thoughts (e.g., _“Navigating to Yahoo Finance…”_) to React via WebSockets.

---

## 4. MCP-Enabled Architecture

### MCP Role in the System

The FastAPI backend acts as the **MCP Host**, managing persistent connections to external MCP Servers and exposing their tools to agents.

### MCP Connection Types

- **Stdio MCP Servers**  
  Local command-line processes  
  Example:
  `npx @modelcontextprotocol/server-google-sheets`

- **SSE / HTTP MCP Servers**  
  Remote MCP servers accessed via Server-Sent Events

---

## 5. MCP Tool Discovery & Execution

### Tool Lifecycle

1. **Discovery**  
   On startup, FastAPI connects to configured MCP servers and retrieves available tools  
   (e.g., `gmail_send_message`, `sheets_append_row`).

2. **Exposure**  
   Tools are converted into **JSON Schema** compatible with:

- Google ADK
- LangChain tool calling

3. **Execution**  
   When an agent invokes a tool:

- Request → MCP Host
- MCP Host → specific MCP Server
- Result → mapped back into agent State

---

## 6. Key Capability Requirements

### Google Sheets & Gmail (via MCP)

- **Setup**  
  Use pre-built Google Sheets / Gmail MCP servers.

- **Workflow**  
  ResearchAgent or ScrapingAgent →  
  calls MCP tool `append_to_sheet` to log structured data.

---

### Flexible “Brain” (LLM) Support

- **Local**  
  Ollama (e.g., Llama 3, Mistral) via user-provided base URL.

- **Cloud**  
  Native SDK support for:
- Gemini (Google)
- OpenAI
- xAI (Grok)
- Groq (LPU)

- **Configuration Rule**  
  Gemini-based agents must always use: `temperature = 1.0`

- **Dynamic Tool Binding**  
  MCP-discovered tools are injected into the LLM context regardless of provider.

---

## 7. Security & User Control

- **Permission Guard UI**  
  Any destructive or external action requires explicit user approval:
- File deletion
- Terminal execution
- MCP actions (e.g., _“Send email to boss@company.com”_)

- **MCP Sandbox**  
  MCP servers run as isolated processes. Crashes do not affect the main app.

- **Credential Management**
- OAuth handled by MCP servers or
- Stored securely in Windows Credential Manager
- No plaintext API keys on disk

---

## 8. Technical Stack

- **Backend**: Python 3.10+, FastAPI
- **Frontend**: Electron + React, Node.js 20+
- **Agent Frameworks**: google-adk, langchain
- **Automation**: browser-use, Playwright, crawl4ai
- **Vector Store**: ChromaDB
- **Security**: keyring (Windows Credential Manager)

---

## 9. Implementation Roadmap

### Phase 1 – Model Provider Factory

- Unified LLM loader supporting:
- Ollama
- Gemini
- OpenAI
- xAI
- Groq

---

### Phase 2 – Windows System Integration

- Use `pathlib` for all filesystem paths
- Map LangChain FileManagement tools to Windows directories
- Enforce Permission Guard confirmations

---

### Phase 3 – MCP Host Integration

- Implement MCP Client Manager inside FastAPI
- Support Stdio and SSE MCP servers
- Convert MCP tools to ADK / LangChain schemas

---

### Phase 4 – Packaging (.exe)

- Bundle FastAPI backend using PyInstaller → `backend.exe`
- Electron spawns backend as child process
- Ensure `will-quit` kills backend to avoid ghost APIs

---

## 10. Development Instructions

- Create Python virtual environment
- Install:

```
fastapi
mcp
browser-use
langchain
chromadb
```

- Implement MCP manager in:
  `backend/mcp_manager.py`

- Use `asyncio.create_subprocess_exec` for Stdio MCP servers
- Map MCP CallToolResult → agent State history

---

## 11. Critical Challenges & Mitigations

### Playwright Installation

- **Issue**: Missing browser drivers
- **Solution**: UI-triggered setup script:
  `playwright install chromium`

### Windows Pathing

- **Issue**: Slash vs backslash inconsistencies
- **Solution**: Enforce `pathlib` everywhere

### Node.js & MCP Dependencies

- **Issue**: MCP servers require npm / npx
- **Solution**:
- Detect local Node.js
- Or bundle portable Node.js (Openwork-style)

### API Key Privacy

- **Solution**: Native OS keychain only

Ensure setting up a vrtual environment to prevent dependany conflicts.


Orchestrator Agent Implementation Plan
Goal
Create an intelligent orchestrator agent that:

Receives generalized user prompts
Analyzes available specialized agents and their capabilities
Decomposes the prompt into subtasks
Routes each subtask to the appropriate agent
Returns a sequential execution plan as a list of (agent_name, detailed_subtask)
Available Agents
1. BrowserAgent
Capabilities:

Web navigation and automation
Form filling and interaction
Web page screenshots
Data extraction from web pages
Multi-step browser workflows
Use Cases:

Login to websites
Extract pricing information
Fill forms
Click buttons and navigate pages
Download files from web
Skill Reference: 
backend/skills/browser-automation/SKILL.md

2. TerminalAgent
Capabilities:

Execute PowerShell/CMD commands
System operations
Development tool execution
File system operations via CLI
Use Cases:

Run build scripts
Execute system commands
Install packages
Git operations
Process management
Skill Reference: 
backend/skills/terminal-execution/SKILL.md

3. FileSystemAgent
Capabilities:

List files and directories
Read file contents
Write/create files
Move/rename files
Delete files
Use Cases:

File organization
Reading configuration files
Creating/updating files
Directory exploration
File management
Skill Reference: 
backend/skills/filesystem-management/SKILL.md

4. RAGAgent
Capabilities:

Search indexed documents
Provide answers with source citations
Query vector store
Knowledge retrieval
Use Cases:

Answer questions from documentation
Search indexed knowledge base
Retrieve specific information from docs
Skill Reference: 
backend/skills/knowledge-retrieval/SKILL.md

5. ResearchAgent
Capabilities:

Web search
Information gathering
Answer questions with web research
Summarize findings
Use Cases:

Research topics
Find latest information
Gather data from multiple sources
Fact-checking
Currently Implemented: Yes (as web_search_agent.py)

6. ScrapingAgent
Capabilities:

Fast data extraction from web pages
Scrape pricing tables
Extract structured content
Convert HTML to Markdown
Use Cases:

Extract product catalogs
Scrape pricing information
Get documentation content
Extract table data
Skill Reference: 
backend/skills/web-scraping/SKILL.md
 Currently Implemented: No (skill defined, agent not implemented)

7. IntegratorAgent (MCP)
Capabilities:

Gmail operations (send, read, search)
Google Drive operations (upload, download, list)
Google Calendar operations (create, list events)
Slack integration (future)
Use Cases:

Send emails
Upload files to Drive
Manage calendar events
External API integrations
Skill Reference: 
backend/skills/mcp-integration/SKILL.md
 Currently Implemented: No (skill defined, agent not implemented)

Orchestrator Design
Architecture
User Prompt
     ↓
[Orchestrator Agent]
     ↓
Task Decomposition (using LLM)
     ↓
Agent Routing (match subtasks to agents)
     ↓
Execution Plan: [(agent_name, detailed_subtask), ...]
     ↓
Sequential Execution (by caller)
Agent Registry Structure
AGENT_REGISTRY = {
    "BrowserAgent": {
        "description": "Web automation and browser interactions",
        "capabilities": [
            "Navigate to URLs",
            "Click elements and fill forms",
            "Login to websites",
            "Extract data from web pages",
            "Take screenshots",
            "Multi-step browser workflows"
        ],
        "skill_path": "backend/skills/browser-automation/SKILL.md",
        "implemented": True
    },
    "TerminalAgent": {
        "description": "Command-line execution and system operations",
        "capabilities": [
            "Execute PowerShell/CMD commands",
            "Run scripts and build tools",
            "Install packages",
            "Git operations",
            "File operations via CLI"
        ],
        "skill_path": "backend/skills/terminal-execution/SKILL.md",
        "implemented": True
    },
    # ... other agents
}
Implementation Approach
1. Create Orchestrator Agent Class
File: backend/agents/orchestrator_agent.py

Key Components:

Agent registry with capabilities
LLM-based task decomposition
Agent routing logic
Execution plan generation
2. Task Decomposition Prompt
The orchestrator uses an LLM to:

Analyze user prompt
Identify required capabilities
Break down into sequential subtasks
Match each subtask to best agent
Example Decomposition:

User: "Research Python packaging, create a requirements.txt file, and send it via email"
Decomposition:
1. ResearchAgent: "Research Python packaging best practices and tools"
2. FileSystemAgent: "Create requirements.txt file with content: [packages]"
3. IntegratorAgent: "Send email with requirements.txt as attachment to [email]"
3. Output Format
[
    ("ResearchAgent", "Research Python packaging best practices and common tools used in 2026"),
    ("FileSystemAgent", "Create a file named 'requirements.txt' with the following packages: [list]"),
    ("IntegratorAgent", "Send an email to user@example.com with subject 'Requirements File' and attach requirements.txt")
]
Proposed Changes
New File: orchestrator_agent.py
from typing import List, Tuple, Dict
from langchain_ollama import ChatOllama
from langchain.prompts import ChatPromptTemplate
import json
class OrchestratorAgent:
    def __init__(self, llm_model: str = "gpt-oss:20b"):
        """Initialize orchestrator with LLM and agent registry"""
        
    def decompose_task(self, user_prompt: str) -> List[Tuple[str, str]]:
        """
        Decompose user prompt into sequential subtasks.
        
        Returns:
            List of (agent_name, detailed_subtask_prompt) tuples
        """
        
    def get_agent_capabilities(self) -> Dict:
        """Return agent registry with capabilities"""
Agent Registry Format
Stored in backend/config/agent_registry.json:

{
  "agents": {
    "BrowserAgent": {
      "description": "...",
      "capabilities": [...],
      "skill_path": "...",
      "implemented": true
    },
    ...
  }
}
System Prompt for Orchestrator
The orchestrator LLM will receive:

Agent Registry: List of available agents with capabilities
User Prompt: The task to decompose
Instructions: How to decompose and route tasks
Prompt Template:

You are an intelligent task orchestrator. Your job is to:
1. Analyze the user's request
2. Break it down into sequential subtasks
3. Route each subtask to the most appropriate agent
Available Agents:
{agent_registry}
User Request:
{user_prompt}
Rules:
- Each subtask should be self-contained and detailed
- Subtasks should execute sequentially (output of one feeds to next)
- Choose the most appropriate agent for each subtask
- Make subtask prompts detailed and actionable
Output Format (JSON):
[
  {
    "agent": "AgentName",
    "subtask": "Detailed description of what this agent should do"
  },
  ...
]
Example Scenarios
Example 1: Simple Single-Agent Task
User Prompt: "Get the list of files in the current directory"

Orchestrator Output:

[
    ("FileSystemAgent", "List all files and directories in the current working directory with details")
]
Example 2: Multi-Agent Workflow
User Prompt: "Research the latest Python web frameworks, create a comparison document, and save it to my Drive"

Orchestrator Output:

[
    ("ResearchAgent", "Research the latest Python web frameworks in 2026, including FastAPI, Django, Flask. Compare features, performance, and use cases."),
    ("FileSystemAgent", "Create a file named 'python-frameworks-comparison.md' with the research findings in markdown format with sections for each framework."),
    ("IntegratorAgent", "Upload the file 'python-frameworks-comparison.md' to Google Drive in the 'Documents' folder")
]
Example 3: Complex Browser + Data Task
User Prompt: "Login to OpenAI pricing page and extract pricing, then save to a JSON file"

Orchestrator Output:

[
    ("BrowserAgent", "Navigate to https://openai.com/pricing and extract all pricing plan details including plan names, prices, and features in structured format"),
    ("FileSystemAgent", "Create a file named 'openai-pricing.json' with the extracted pricing data in JSON format")
]
Implementation Steps
Phase 1: Core Structure
Create orchestrator_agent.py
Define agent registry (inline or JSON)
Initialize LLM with system prompt
Phase 2: Decomposition Logic
Create orchestrator system prompt template
Implement decompose_task() method
Parse LLM output into structured format
Phase 3: Testing
Test with single-agent tasks
Test with multi-agent workflows
Validate output format
Test edge cases
Success Criteria
✅ Orchestrator can decompose simple single-agent tasks
✅ Orchestrator can handle multi-agent workflows
✅ Output format is correct: List[(agent_name, subtask)]
✅ Subtasks are detailed and actionable
✅ Agent routing is appropriate for each subtask
✅ Sequential execution order makes logical sense
✅ Works with existing and planned agents

Notes
Orchestrator does NOT execute tasks, only creates execution plan
Execution will be handled by a separate runner/executor
Agent registry should be easily extensible
Consider fallback logic if no suitable agent found
Future: Add parallel execution support for independent tasks