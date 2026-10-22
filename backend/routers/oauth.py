import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from fastapi import APIRouter, HTTPException, Query, Body
from typing import Optional, Dict, Any
from pydantic import BaseModel

from backend.services.oauth_manager import oauth_manager

router = APIRouter(prefix="/oauth", tags=["oauth"])


class GenericOAuthRequest(BaseModel):
    client_id: Optional[str] = "openagents-mcp-client"
    auth_url: str
    token_url: str
    scopes: str = "read write"
    redirect_port: int = 8765


class AuthorizeUrlRequest(BaseModel):
    url: str
    client_id: Optional[str] = None


@router.get("/providers")
async def get_providers():
    """
    List all active OAuth connections dynamically from stored tokens.
    """
    try:
        return oauth_manager.get_providers_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/authorize")
async def authorize_url(req: AuthorizeUrlRequest):
    """
    Dynamically authorizes any protected MCP server endpoint via RFC 9728 .well-known.
    """
    res = oauth_manager.authorize_mcp_endpoint(req.url, client_id=req.client_id)
    if res.get("status") == "error":
        raise HTTPException(status_code=400, detail=res.get("error", "Failed to initiate authorization"))
    return res


@router.post("/authorize/{provider}")
async def authorize_provider(
    provider: str,
    generic_req: Optional[GenericOAuthRequest] = None,
    url: Optional[str] = None
):
    """
    Start OAuth flow. If URL or endpoints are provided, initiates dynamic flow.
    """
    # If the provider string itself is a URL or url param was provided
    target_url = url or (provider if provider.startswith(("http://", "https://")) else None)
    if target_url:
        res = oauth_manager.authorize_mcp_endpoint(target_url)
        if res.get("status") == "error":
            raise HTTPException(status_code=400, detail=res.get("error", "Failed to initiate authorization"))
        return res

    if generic_req:
        res = oauth_manager.start_generic_pkce_flow(
            provider=provider.lower(),
            client_id=generic_req.client_id or "openagents-mcp-client",
            auth_url=generic_req.auth_url,
            token_url=generic_req.token_url,
            scopes=generic_req.scopes,
            redirect_port=generic_req.redirect_port,
        )
        return res

    raise HTTPException(
        status_code=400,
        detail=f"Please provide an MCP server URL or OAuth endpoints to authorize {provider}.",
    )


@router.get("/flows/{flow_id}")
async def get_flow_status(flow_id: str):
    """
    Poll status of an active authorization flow.
    """
    status = oauth_manager.get_flow_status(flow_id)
    if not status:
        raise HTTPException(status_code=404, detail="Authorization flow not found or expired")
    return status


@router.delete("/providers/{provider}")
async def disconnect_provider(provider: str):
    """
    Disconnect a provider / server and remove stored OAuth tokens.
    """
    success = oauth_manager.delete_provider_token(provider)
    if success:
        return {"message": f"Successfully disconnected {provider}", "provider": provider}
    return {"message": f"{provider} was not connected", "provider": provider}


@router.get("/env/{server_name}")
async def get_mcp_env(server_name: str, url: Optional[str] = None):
    """
    Retrieve auto-injected environment variables for an MCP server from active OAuth tokens.
    """
    return oauth_manager.get_env_for_mcp(server_name, url=url)
