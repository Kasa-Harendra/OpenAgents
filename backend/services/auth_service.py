import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

application_scopes = [
    'drive', 
    'calendar', 
    'gmail.modify', 
    'userinfo.profile', 
    'userinfo.email', 
    'calendar.events', 
    'calendar',
    'documents',
    'spreadsheets',
    'presentations'
]
# Scopes required by the application
# SCOPES = [
#     f'https://www.googleapis.com/auth/{scope}' for scope in application_scopes
# ] + ['openid']

SCOPES = [
    "https://mail.google.com/", 
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email",
]

TOKEN_FILE = os.path.join(os.path.dirname(__file__), '..', 'credentials', 'token.json')
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), '..', 'credentials', 'credentials.json')

class AuthService:
    @staticmethod
    def get_credentials():
        creds = None
        if os.path.exists(TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    with open(TOKEN_FILE, 'w') as token:
                        token.write(creds.to_json())
                except Exception:
                    return None
            else:
                return None
        return creds

    @staticmethod
    def is_authenticated():
        creds = AuthService.get_credentials()
        return creds is not None

    @staticmethod
    def start_auth_flow():
        # This will be called from the router
        if not os.path.exists(CREDENTIALS_FILE):
            raise FileNotFoundError(f"Credentials file not found at {CREDENTIALS_FILE}")
            
        # Allow scopes to change since users might not grant all requested scopes or 
        # the Google app's verification status might change them.
        os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
        
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
        creds = flow.run_local_server(port=0)
        
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
        
        return creds

    @staticmethod
    def logout():
        if os.path.exists(TOKEN_FILE):
            os.remove(TOKEN_FILE)
            return True
        return False

    @staticmethod
    def get_user_info():
        creds = AuthService.get_credentials()
        if not creds:
            return None
            
        # We can extract info from the creds or fetch from Google API
        # For now, let's just return a placeholder or basics if we have them
        return {
            "authenticated": True,
            "scopes": creds.scopes
        }
