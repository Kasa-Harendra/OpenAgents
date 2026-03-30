import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from fastapi import APIRouter, HTTPException
from backend.services.auth_service import AuthService

router = APIRouter(prefix="/auth")

@router.get("/status")
async def get_auth_status():
    """Check if the user is authenticated."""
    is_auth = AuthService.is_authenticated()
    if is_auth:
        return {"authenticated": True, "user": AuthService.get_user_info()}
    return {"authenticated": False}

@router.post("/login")
async def login():
    """Start the OAuth login flow."""
    try:
        # Note: In a real production app, this would redirect the browser.
        # Here we follow the user's request to 'open the browser for oauth'.
        AuthService.start_auth_flow()
        return {"message": "Login successful"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/logout")
async def logout():
    """Delete the token and logout the user."""
    success = AuthService.logout()
    if success:
        return {"message": "Logged out successfully"}
    return {"message": "No active session found"}
