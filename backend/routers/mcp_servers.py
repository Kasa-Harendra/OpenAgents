import uuid
import datetime
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.models.models import (
    MCPServer,
    mcp_server_create,
    mcp_server_update,
    mcp_server_response
)
from backend.services.oauth_manager import oauth_manager

router = APIRouter(prefix="/mcp-servers")

POPULAR_MCP_PRESETS = [
    {
        "id": "preset-github",
        "name": "GitHub",
        "type": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-github"],
        "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": ""},
        "description": "Repository management, issues, pull requests, and git search",
        "oauth_provider": "github"
    },
    {
        "id": "preset-google-drive",
        "name": "Google Drive",
        "type": "stdio",
        "command": "npx",
        "args": ["-y", "@piotr-agier/google-drive-mcp"],
        "env": {},
        "description": "Read, search, upload, and organize Google Drive files and folders",
        "oauth_provider": "google"
    },
    {
        "id": "preset-gmail",
        "name": "Gmail",
        "type": "stdio",
        "command": "npx",
        "args": ["-y", "@shinzolabs/gmail-mcp"],
        "env": {},
        "description": "Send emails, search messages, and manage Gmail inbox with OAuth",
        "oauth_provider": "google"
    },
    {
        "id": "preset-filesystem",
        "name": "Filesystem",
        "type": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "./workspace"],
        "env": {},
        "description": "Secure local filesystem operations, directory traversal, and editing"
    },
    {
        "id": "preset-postgres",
        "name": "PostgreSQL",
        "type": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-postgres", "postgresql://user:password@localhost:5432/mydb"],
        "env": {},
        "description": "PostgreSQL database querying, schema inspection, and table analysis"
    },
    {
        "id": "preset-sqlite",
        "name": "SQLite",
        "type": "stdio",
        "command": "uvx",
        "args": ["mcp-server-sqlite", "--db-path", "./test.db"],
        "env": {},
        "description": "Local SQLite database querying and schema inspection"
    },
    {
        "id": "preset-fetch",
        "name": "Fetch / Web",
        "type": "stdio",
        "command": "uvx",
        "args": ["mcp-server-fetch"],
        "env": {},
        "description": "HTTP web page scraping and content conversion"
    },
    {
        "id": "preset-brave-search",
        "name": "Brave Search",
        "type": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-brave-search"],
        "env": {"BRAVE_API_KEY": ""},
        "description": "Real-time internet web search and news search API"
    },
    {
        "id": "preset-memory",
        "name": "Memory",
        "type": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-memory"],
        "env": {},
        "description": "Persistent knowledge graph memory across agent turns"
    },
    {
        "id": "preset-slack",
        "name": "Slack",
        "type": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-slack"],
        "env": {"SLACK_BOT_TOKEN": "", "SLACK_TEAM_ID": ""},
        "description": "Slack channel management and message posting",
        "oauth_provider": "slack"
    }
]

@router.get("/presets")
def get_mcp_presets():
    """Returns curated popular MCP server presets for quick registration enriched with OAuth connection status."""
    providers_status = {p["id"]: p for p in oauth_manager.get_providers_status()}
    enriched = []
    for preset in POPULAR_MCP_PRESETS:
        p_copy = dict(preset)
        oauth_pid = preset.get("oauth_provider")
        if oauth_pid and oauth_pid in providers_status:
            p_status = providers_status[oauth_pid]
            p_copy["oauth_connected"] = p_status.get("connected", False)
            p_copy["oauth_user"] = p_status.get("user")
        else:
            p_copy["oauth_connected"] = False
            p_copy["oauth_user"] = None
        enriched.append(p_copy)
    return enriched

@router.get("", response_model=List[mcp_server_response])
def list_mcp_servers(db: Session = Depends(get_db)):
    """List all registered MCP servers in the registry with auto-injected OAuth envs."""
    servers = db.query(MCPServer).order_by(MCPServer.updated_at.desc()).all()
    # Enrich with active OAuth env variables if env token is empty
    for s in servers:
        oauth_env = oauth_manager.get_env_for_mcp(s.name)
        if oauth_env:
            merged_env = dict(s.env or {})
            for k, v in oauth_env.items():
                if not merged_env.get(k):
                    merged_env[k] = v
            s.env = merged_env
    return servers

@router.post("", response_model=mcp_server_response, status_code=status.HTTP_201_CREATED)
def register_mcp_server(data: mcp_server_create, db: Session = Depends(get_db)):
    """Register a new MCP server in the registry."""
    name_clean = data.name.strip()
    if not name_clean:
        raise HTTPException(status_code=400, detail="Server name cannot be empty.")
    
    # Check uniqueness of name
    existing = db.query(MCPServer).filter(MCPServer.name == name_clean).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"An MCP server named '{name_clean}' already exists in registry.")
    
    server_type = data.type.lower()
    if server_type not in ["stdio", "sse"]:
        raise HTTPException(status_code=400, detail="Server type must be either 'stdio' or 'sse'.")
    
    if server_type == "stdio" and not data.command:
        raise HTTPException(status_code=400, detail="Command is required for stdio MCP servers (e.g., 'npx', 'uvx', 'python').")
    
    if server_type == "sse" and not data.url:
        raise HTTPException(status_code=400, detail="URL is required for SSE MCP servers (e.g., 'http://localhost:3000/sse').")
    
    server_id = data.id.strip() if data.id else str(uuid.uuid4())
    
    new_server = MCPServer(
        id=server_id,
        name=name_clean,
        type=server_type,
        command=data.command.strip() if data.command else None,
        args=data.args or [],
        env=data.env or {},
        url=data.url.strip() if data.url else None
    )
    
    db.add(new_server)
    db.commit()
    db.refresh(new_server)
    return new_server

@router.get("/{server_id}", response_model=mcp_server_response)
def get_mcp_server(server_id: str, db: Session = Depends(get_db)):
    """Get single MCP server details."""
    server = db.query(MCPServer).filter(MCPServer.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="MCP server not found.")
    return server

@router.put("/{server_id}", response_model=mcp_server_response)
def update_mcp_server(server_id: str, update_data: mcp_server_update, db: Session = Depends(get_db)):
    """Update registered MCP server configuration."""
    server = db.query(MCPServer).filter(MCPServer.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="MCP server not found.")
    
    if update_data.name is not None:
        name_clean = update_data.name.strip()
        if not name_clean:
            raise HTTPException(status_code=400, detail="Server name cannot be empty.")
        if name_clean != server.name:
            existing = db.query(MCPServer).filter(MCPServer.name == name_clean).first()
            if existing:
                raise HTTPException(status_code=400, detail=f"An MCP server named '{name_clean}' already exists.")
            server.name = name_clean
            
    if update_data.type is not None:
        stype = update_data.type.lower()
        if stype not in ["stdio", "sse"]:
            raise HTTPException(status_code=400, detail="Server type must be either 'stdio' or 'sse'.")
        server.type = stype
        
    if update_data.command is not None:
        server.command = update_data.command.strip() if update_data.command else None
    if update_data.args is not None:
        server.args = update_data.args
    if update_data.env is not None:
        server.env = update_data.env
    if update_data.url is not None:
        server.url = update_data.url.strip() if update_data.url else None
        
    server.updated_at = datetime.datetime.now(datetime.timezone.utc)
    db.commit()
    db.refresh(server)
    return server

@router.delete("/{server_id}")
def delete_mcp_server(server_id: str, db: Session = Depends(get_db)):
    """Delete an MCP server from registry."""
    server = db.query(MCPServer).filter(MCPServer.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="MCP server not found.")
    
    db.delete(server)
    db.commit()
    return {"success": True, "message": f"MCP server '{server.name}' deleted successfully."}
