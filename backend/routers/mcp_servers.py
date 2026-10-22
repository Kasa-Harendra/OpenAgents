import uuid
import datetime
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
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

class ProbeRequest(BaseModel):
    url: str

class AuthorizeServerRequest(BaseModel):
    url: str

POPULAR_MCP_PRESETS = [
    {
        "id": "preset-filesystem",
        "name": "Filesystem",
        "type": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "./workspace"],
        "env": {},
        "description": "Local filesystem operations, directory traversal, and editing"
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
        "id": "preset-sqlite",
        "name": "SQLite",
        "type": "stdio",
        "command": "uvx",
        "args": ["mcp-server-sqlite", "--db-path", "./test.db"],
        "env": {},
        "description": "Local SQLite database querying and schema inspection"
    },
    {
        "id": "preset-memory",
        "name": "Memory",
        "type": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-memory"],
        "env": {},
        "description": "Persistent knowledge graph memory across agent turns"
    }
]

@router.get("/presets")
def get_mcp_presets():
    """Returns 4 standard utility MCP server presets."""
    return POPULAR_MCP_PRESETS

@router.post("/authorize")
def authorize_mcp_server(data: AuthorizeServerRequest):
    """
    Dynamically inspects a remote MCP server via .well-known/oauth-protected-resource,
    identifies the authorization server, and triggers the OAuth authorization flow.
    """
    return oauth_manager.authorize_mcp_endpoint(data.url)

class CheckServerRequest(BaseModel):
    server_id: Optional[str] = None
    name: Optional[str] = "MCP Server"
    type: str = "sse"  # 'stdio' or 'sse'
    url: Optional[str] = None
    command: Optional[str] = None
    args: Optional[List[str]] = None
    env: Optional[Dict[str, str]] = None

@router.post("/probe")
def probe_mcp_server(data: ProbeRequest):
    """Probe an SSE/HTTP MCP endpoint dynamically to detect if OAuth authorization is required."""
    return oauth_manager.probe_endpoint(data.url)

@router.post("/check")
def check_mcp_server(data: CheckServerRequest, db: Session = Depends(get_db)):
    """Dynamically tests if an MCP server is working, detects if auth is required, and reports online / issue status."""
    server_id = data.server_id
    server_type = data.type.lower()
    
    server_record = None
    if server_id:
        server_record = db.query(MCPServer).filter(MCPServer.id == server_id).first()
        if server_record:
            if not data.url and server_record.url:
                data.url = server_record.url
            if not data.command and server_record.command:
                data.command = server_record.command
            if not data.env and server_record.env:
                data.env = server_record.env
            server_type = server_record.type
    
    status_result = "issue"
    message = "Unknown error"
    probe_details = {}

    if server_type == "sse":
        if not data.url:
            return {"status": "issue", "message": "Server SSE URL is required"}
        
        # Prepare headers
        req_headers = {}
        for k, v in (data.env or {}).items():
            if not v:
                continue
            if k.lower() == "authorization":
                req_headers["Authorization"] = v
            elif k.upper().endswith("_TOKEN") or k.upper().endswith("_KEY") or k.upper() in ["TOKEN", "API_KEY", "BEARER_TOKEN", "ACCESS_TOKEN"]:
                if "Authorization" not in req_headers:
                    req_headers["Authorization"] = f"Bearer {v}"
        
        probe_res = oauth_manager.probe_endpoint(data.url, headers=req_headers)
        probe_details = probe_res
        status_result = probe_res.get("status", "issue")
        message = probe_res.get("message", "Checked")
    else:
        # stdio
        cmd = data.command
        if not cmd:
            return {"status": "issue", "message": "Command is required for stdio server"}
        
        import shutil, subprocess
        bin_path = shutil.which(cmd.strip())
        if not bin_path:
            status_result = "issue"
            message = f"Command '{cmd}' not found on system PATH"
        else:
            try:
                subprocess.run([bin_path, "--version"], capture_output=True, text=True, timeout=3)
                status_result = "online"
                message = f"Executable '{cmd}' is available and ready"
            except subprocess.TimeoutExpired:
                status_result = "online"
                message = f"Executable '{cmd}' started successfully"
            except Exception as e:
                status_result = "issue"
                message = f"Failed to execute command: {str(e)}"
    
    if server_record:
        server_record.status = status_result
        server_record.status_message = message
        db.commit()
    
    return {
        "status": status_result,
        "message": message,
        **probe_details
    }

@router.post("/{server_id}/check")
def check_registered_server(server_id: str, db: Session = Depends(get_db)):
    """Run live connection check for a specific registered MCP server."""
    server = db.query(MCPServer).filter(MCPServer.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="MCP server not found.")
    
    req = CheckServerRequest(
        server_id=server.id,
        name=server.name,
        type=server.type,
        url=server.url,
        command=server.command,
        args=server.args,
        env=server.env
    )
    return check_mcp_server(req, db)

@router.get("", response_model=List[mcp_server_response])
def list_mcp_servers(db: Session = Depends(get_db)):
    """List all registered MCP servers in the registry with auto-injected OAuth envs and Bearer headers."""
    servers = db.query(MCPServer).order_by(MCPServer.updated_at.desc()).all()
    # Enrich with active OAuth env variables / Bearer header if env token is empty
    for s in servers:
        oauth_env = oauth_manager.get_env_for_mcp(s.name, s.url)
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
    
    # Auto-inject OAuth environment / Bearer token if not explicitly provided
    initial_env = dict(data.env or {})
    oauth_env = oauth_manager.get_env_for_mcp(name_clean, data.url)
    for k, v in oauth_env.items():
        if not initial_env.get(k):
            initial_env[k] = v
    
    new_server = MCPServer(
        id=server_id,
        name=name_clean,
        type=server_type,
        command=data.command.strip() if data.command else None,
        args=data.args or [],
        env=initial_env,
        url=data.url.strip() if data.url else None,
        status=data.status or "online",
        status_message=data.status_message or "Registered"
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
    oauth_env = oauth_manager.get_env_for_mcp(server.name, server.url)
    if oauth_env:
        merged_env = dict(server.env or {})
        for k, v in oauth_env.items():
            if not merged_env.get(k):
                merged_env[k] = v
        server.env = merged_env
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
    if update_data.status is not None:
        server.status = update_data.status
    if update_data.status_message is not None:
        server.status_message = update_data.status_message
        
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
