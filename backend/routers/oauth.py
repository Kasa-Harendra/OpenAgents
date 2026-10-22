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
    client_id: str
    auth_url: str
    token_url: str
    scopes: str = "read"
    redirect_port: int = 8765


@router.get("/providers")
async def get_providers():
    """
    List all supported OAuth providers and their current connection status.
    """
    try:
        return oauth_manager.get_providers_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/authorize/{provider}")
async def authorize_provider(provider: str, generic_req: Optional[GenericOAuthRequest] = None):
    """
    Start OAuth flow for a provider.
    - 'github': Initiates zero-config GitHub Device Flow, copies code, opens browser.
    - 'google': Initiates Google InstalledAppFlow with loopback redirect.
    - other: Uses generic PKCE loopback flow if config provided.
    """
    provider_clean = provider.lower()

    if provider_clean == "github":
        res = oauth_manager.start_github_device_flow()
        if res.get("status") == "error":
            raise HTTPException(status_code=500, detail=res.get("error", "Failed to initiate GitHub authorization"))
        return res

    elif provider_clean == "google":
        res = oauth_manager.start_google_flow()
        if res.get("status") == "error":
            raise HTTPException(status_code=500, detail=res.get("error", "Failed to initiate Google authorization"))
        return res

    elif generic_req:
        res = oauth_manager.start_generic_pkce_flow(
            provider=provider_clean,
            client_id=generic_req.client_id,
            auth_url=generic_req.auth_url,
            token_url=generic_req.token_url,
            scopes=generic_req.scopes,
            redirect_port=generic_req.redirect_port,
        )
        return res

    else:
        raise HTTPException(
            status_code=400,
            detail=f"Provider '{provider}' is not natively pre-configured. Please provide OAuth endpoints.",
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
    Disconnect a provider and remove stored OAuth tokens.
    """
    success = oauth_manager.delete_provider_token(provider)
    if success:
        return {"message": f"Successfully disconnected {provider}", "provider": provider}
    return {"message": f"{provider} was not connected", "provider": provider}


@router.get("/env/{server_name}")
async def get_mcp_env(server_name: str):
    """
    Retrieve auto-injected environment variables for an MCP server from active OAuth tokens.
    """
    return oauth_manager.get_env_for_mcp(server_name)
