# OpenAgents: Core System Requirements & Architectural Blueprint

This document records the foundational product and architecture requirements for OpenAgents. All development across backend, frontend, database schemas, and agent orchestration must adhere to these specifications.

---

## 1. User-Created Custom Agents (Interface & Database)

### 1.1 Objective
Users must be able to define, configure, activate/deactivate, and manage custom specialized agents directly from the graphical user interface without modifying source code.

### 1.2 Required Agent Attributes
Every user-created agent consists of:
- **Agent Name (`name` / `agent_name`)**: Unique identifier / display name for the agent.
- **Description (`description`)**: Detailed explanation of the agent's purpose, domain expertise, and operational instructions.
- **MCP Servers & Tools (`mcp_servers` / `tools`)**: Assigned Model Context Protocol (MCP) servers and tools available to this agent.
- **Skills (`skills`)**: Associated skills, prompt modules, or specialized execution procedures.
- **Active Status (`is_active` / `active`)**: Boolean flag controlling whether the agent is currently enabled and exposed to the orchestration system.
- **LLM Configuration (`llm_provider`, `model`, `temperature`, etc.)**: The specific model routing parameters for this agent.

### 1.3 Database Specification: `agents` Table
Agents are persisted in `openagents.db` under the dedicated `agents` table.

```sql
CREATE TABLE agents (
    id VARCHAR(36) PRIMARY KEY,              -- UUID
    name VARCHAR(255) NOT NULL UNIQUE,       -- Agent name
    description TEXT,                        -- Capabilities & role prompt
    system_prompt TEXT,                      -- Custom base system prompt
    llm_provider VARCHAR(50) DEFAULT 'ollama', -- openai, anthropic, gemini, ollama, groq
    model_name VARCHAR(100),                 -- e.g., gpt-4o, claude-3-5-sonnet, llama3.1
    mcp_servers JSON DEFAULT '[]',           -- List of MCP server IDs / configurations
    skills JSON DEFAULT '[]',                -- List of skill names / paths / configurations
    is_active BOOLEAN DEFAULT TRUE,          -- Dynamic availability toggle
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 1.4 Frontend Interface Requirements
- Dedicated **Agent Management Hub / Studio** in the UI to:
  - Create new agents with a structured form (Name, Description, System Prompt, Provider/Model, Tool/MCP selection, Skill assignment, Active toggle).
  - Edit existing agents.
  - Toggle `is_active` on/off with an instant switch.
  - Delete or clone agents.

---

## 2. Conversation Persistence Architecture

### 2.1 Storage Directory Structure
All conversation payloads are saved to the user's home directory:
```
~/.openagents/
├── conversations/
│   ├── <convo_id_1>.json
│   ├── <convo_id_2>.json
│   └── ...
└── openagents.db (or database index)
```

### 2.2 Dual-Layer Persistence Strategy

1. **Detailed JSON Payload (`~/.openagents/conversations/<convo_id>.json`)**:
   - Each conversation is saved as an individual JSON file identified by its `convo_id` (UUID).
   - Structure:
     ```json
     {
       "convo_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
       "title": "Build a React component for user settings",
       "created_at": "2026-10-18T14:45:00Z",
       "updated_at": "2026-10-18T14:48:30Z",
       "base_directory": "/path/to/project",
       "chat_mode": "multiagent",
       "messages": [
         {
           "id": "msg-001",
           "role": "user",
           "content": "Create a new agent for Docker deployment",
           "timestamp": 1729241100000
         },
         {
           "id": "msg-002",
           "role": "assistant",
           "agent_name": "IntegratorAgent",
           "content": "I am initiating the Docker deployment agent...",
           "timestamp": 1729241105000,
           "type": "agent_response"
         }
       ]
     }
     ```

2. **Metadata Tracking Table (`conversations`) in `openagents.db`**:
   - Maintains fast index and queryable metadata for sidebar listings, search, and sorting.
   ```sql
   CREATE TABLE conversations (
       convo_id VARCHAR(36) PRIMARY KEY,       -- UUID matching JSON filename
       title VARCHAR(255) NOT NULL,            -- Conversation title
       file_path TEXT NOT NULL,                -- Absolute path: ~/.openagents/conversations/<convo_id>.json
       message_count INTEGER DEFAULT 0,        -- Total messages in conversation
       last_message_preview TEXT,              -- Snippet for sidebar display
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
       updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );
   ```

### 2.3 Synchronization & Operations
- **Creation**: When a user creates a new chat, generate a UUID `convo_id`, insert the record into `conversations`, and initialize `~/.openagents/conversations/<convo_id>.json`.
- **Append**: Every incoming user prompt and outgoing assistant message/stream update commits atomically to the JSON file and updates `updated_at` + `message_count` in the DB.
- **Deletion**: Deleting a chat removes the database record and removes `<convo_id>.json` from disk.
- **Listing**: Sidebar fetches the conversation list from the fast `conversations` table, and loads the full JSON payload on demand when clicked.

---

## 3. Integrator Agent as Dynamic Deep Agent & Meta-Orchestrator

### 3.1 Role & Responsibility
The **Integrator Agent** acts as a deep agent responsible for:
- Receiving all miscellaneous, unassigned, or complex cross-domain tasks from the user or orchestrator.
- Serving as the meta-layer that manages and coordinates all **user-created agents**.

### 3.2 Dynamic Active-Agent Injection
- The Integrator Agent **must not** rely on static hardcoded agent lists.
- At runtime (or per conversation turn), the Integrator queries the database:
  ```sql
  SELECT * FROM agents WHERE is_active = TRUE;
  ```
- The active agents' metadata—including their **Name**, **Description**, **Assigned MCP Tools**, and **Skills**—is dynamically compiled into the Integrator Agent's system prompt and tool dispatch context.
- **Dynamic Awareness**:
  - If a user creates a new agent named "KubernetesDeployer" and sets it to `active`, the Integrator immediately learns about its existence, role, tools, and triggers without requiring a backend restart.
  - If an agent is marked inactive (`is_active = FALSE`), it is instantly excluded from the Integrator's context.

### 3.3 Execution & Routing Logic
1. User prompt is submitted.
2. If the task matches a specific dedicated specialist or is classified as general/miscellaneous, it is handed to the Integrator Agent.
3. The Integrator Agent evaluates the task against the dynamically loaded list of active user-created agents.
4. The Integrator delegates execution steps to the relevant user agents, invokes their tools/MCPs, synthesizes results, and streams the final outcome back to the user.

---

## 4. Implementation Roadmap

| Phase | Component | Key Deliverables |
|---|---|---|
| **Phase 1** | **Database & Storage Foundation** | Create `agents` table and `conversations` table in SQLAlchemy; implement `~/.openagents/conversations/` JSON storage service with atomic read/write/delete. |
| **Phase 2** | **Integrator Agent Dynamic Registry** | Implement dynamic fetching of active agents (`is_active=True`), dynamic prompt generation, and sub-agent invocation in `integrator_agent.py`. |
| **Phase 3** | **API Routers & WebSocket Sync** | Expose REST endpoints for CRUD on `agents` and `conversations`; ensure WebSocket streaming automatically persists messages to `<convo_id>.json`. |
| **Phase 4** | **Frontend UI & Integration** | Build Agent Creator & Manager UI (create, edit, MCP/skills assignment, active toggle); integrate conversation sidebar with DB + JSON persistence. |
