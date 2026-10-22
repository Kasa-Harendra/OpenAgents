import os
import sys
import json
import time
import uuid
import base64
import hashlib
import secrets
import threading
import subprocess
import webbrowser
from typing import Dict, Any, Optional, List
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

import requests

from backend.db.database import OPENAGENTS_DIR

CREDENTIALS_DIR = os.path.join(OPENAGENTS_DIR, "credentials")
os.makedirs(CREDENTIALS_DIR, exist_ok=True)

OAUTH_TOKENS_FILE = os.path.join(CREDENTIALS_DIR, "oauth_tokens.json")
GOOGLE_CREDENTIALS_FILE = os.path.join(CREDENTIALS_DIR, "credentials.json")
GOOGLE_TOKEN_FILE = os.path.join(CREDENTIALS_DIR, "token.json")

# Public Client IDs (No client secret required)
GITHUB_PUBLIC_CLIENT_ID = "Iv1.b507a08c87ecfe98"  # Copilot / VS Code Device Auth Client
GITHUB_DEFAULT_SCOPES = "repo,read:org,read:user,user:email"

GOOGLE_SCOPES = [
    "https://mail.google.com/",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email",
]


class OAuthManager:
    _instance = None
    _lock = threading.Lock()
    _active_flows: Dict[str, Dict[str, Any]] = {}

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(OAuthManager, cls).__new__(cls)
                cls._instance._init_manager()
            return cls._instance

    def _init_manager(self):
        self._ensure_storage()

    def _ensure_storage(self):
        if not os.path.exists(OAUTH_TOKENS_FILE):
            try:
                with open(OAUTH_TOKENS_FILE, "w") as f:
                    json.dump({}, f, indent=2)
                os.chmod(OAUTH_TOKENS_FILE, 0o600)
            except Exception as e:
                print(f"[OAuthManager] Error creating tokens file: {e}")

    def load_all_tokens(self) -> Dict[str, Any]:
        with self._lock:
            if not os.path.exists(OAUTH_TOKENS_FILE):
                return {}
            try:
                with open(OAUTH_TOKENS_FILE, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[OAuthManager] Error loading tokens: {e}")
                return {}

    def save_provider_token(self, provider: str, token_data: Dict[str, Any]):
        with self._lock:
            all_tokens = {}
            if os.path.exists(OAUTH_TOKENS_FILE):
                try:
                    with open(OAUTH_TOKENS_FILE, "r") as f:
                        all_tokens = json.load(f)
                except Exception:
                    all_tokens = {}

            all_tokens[provider.lower()] = {
                **token_data,
                "provider": provider.lower(),
                "updated_at": int(time.time()),
            }

            try:
                with open(OAUTH_TOKENS_FILE, "w") as f:
                    json.dump(all_tokens, f, indent=2)
                os.chmod(OAUTH_TOKENS_FILE, 0o600)
            except Exception as e:
                print(f"[OAuthManager] Failed to write token file: {e}")

    def delete_provider_token(self, provider: str) -> bool:
        provider = provider.lower()
        with self._lock:
            if not os.path.exists(OAUTH_TOKENS_FILE):
                return False
            try:
                with open(OAUTH_TOKENS_FILE, "r") as f:
                    all_tokens = json.load(f)
                if provider in all_tokens:
                    del all_tokens[provider]
                    with open(OAUTH_TOKENS_FILE, "w") as f:
                        json.dump(all_tokens, f, indent=2)
                    os.chmod(OAUTH_TOKENS_FILE, 0o600)

                    # Also clean up provider-specific legacy files if needed
                    if provider == "google" and os.path.exists(GOOGLE_TOKEN_FILE):
                        try:
                            os.remove(GOOGLE_TOKEN_FILE)
                        except Exception:
                            pass
                    return True
                return False
            except Exception as e:
                print(f"[OAuthManager] Error deleting token for {provider}: {e}")
                return False

    def get_providers_status(self) -> List[Dict[str, Any]]:
        tokens = self.load_all_tokens()
        results = []

        # Supported preset providers
        known_providers = [
            {
                "id": "github",
                "name": "GitHub",
                "description": "Authenticate for Git repositories, PRs, issues, and search tools",
                "icon": "github",
                "type": "device_code",
                "category": "Code & Development",
            },
            {
                "id": "google",
                "name": "Google (Workspace & Drive)",
                "description": "Connect Gmail, Google Drive, Google Calendar, and Docs MCPs",
                "icon": "google",
                "type": "pkce_loopback",
                "category": "Productivity & Workspace",
            },
            {
                "id": "slack",
                "name": "Slack",
                "description": "Connect Slack channels, direct messages, and team notifications",
                "icon": "slack",
                "type": "pkce_loopback",
                "category": "Communication",
            },
        ]

        for p in known_providers:
            pid = p["id"]
            token_entry = tokens.get(pid)
            is_connected = False
            user_display = None
            expires_at = None

            if token_entry and token_entry.get("access_token"):
                is_connected = True
                user_display = token_entry.get("user") or token_entry.get("email") or token_entry.get("name")
                expires_at = token_entry.get("expires_at")

            results.append({
                **p,
                "connected": is_connected,
                "user": user_display,
                "avatar_url": token_entry.get("avatar_url") if token_entry else None,
                "scopes": token_entry.get("scope") if token_entry else None,
                "expires_at": expires_at,
                "updated_at": token_entry.get("updated_at") if token_entry else None,
            })

        return results

    def get_valid_token(self, provider: str) -> Optional[str]:
        provider = provider.lower()
        tokens = self.load_all_tokens()
        entry = tokens.get(provider)
        if not entry or not entry.get("access_token"):
            return None

        # Check expiration
        expires_at = entry.get("expires_at")
        now = int(time.time())

        # If expires in next 60s and we have a refresh token, refresh it
        if expires_at and (now + 60 >= expires_at):
            refresh_token = entry.get("refresh_token")
            if refresh_token:
                try:
                    refreshed = self._refresh_token(provider, refresh_token, entry)
                    if refreshed:
                        return refreshed
                except Exception as e:
                    print(f"[OAuthManager] Token refresh failed for {provider}: {e}")

        return entry.get("access_token")

    def _refresh_token(self, provider: str, refresh_token: str, entry: Dict[str, Any]) -> Optional[str]:
        if provider == "google":
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request

            if os.path.exists(GOOGLE_TOKEN_FILE):
                try:
                    creds = Credentials.from_authorized_user_file(GOOGLE_TOKEN_FILE, GOOGLE_SCOPES)
                    creds.refresh(Request())
                    new_token = creds.token
                    entry["access_token"] = new_token
                    if creds.expiry:
                        entry["expires_at"] = int(creds.expiry.timestamp())
                    self.save_provider_token("google", entry)
                    with open(GOOGLE_TOKEN_FILE, "w") as f:
                        f.write(creds.to_json())
                    return new_token
                except Exception as e:
                    print(f"[OAuthManager] Google refresh via creds failed: {e}")

        elif provider == "github":
            # GitHub tokens generated via device flow typically don't expire unless revoked
            return entry.get("access_token")

        return None

    # =========================================================================
    # GitHub Device Authorization Flow
    # =========================================================================
    def start_github_device_flow(self) -> Dict[str, Any]:
        flow_id = str(uuid.uuid4())
        try:
            resp = requests.post(
                "https://github.com/login/device/code",
                data={
                    "client_id": GITHUB_PUBLIC_CLIENT_ID,
                    "scope": GITHUB_DEFAULT_SCOPES,
                },
                headers={"Accept": "application/json", "User-Agent": "OpenAgents/1.0"},
                timeout=15,
            )
            if resp.status_code != 200:
                raise Exception(f"GitHub returned HTTP {resp.status_code}: {resp.text}")

            data = resp.json()
            device_code = data["device_code"]
            user_code = data["user_code"]
            verification_uri = data.get("verification_uri", "https://github.com/login/device")
            interval = max(int(data.get("interval", 5)), 5)
            expires_in = int(data.get("expires_in", 900))

            # Copy user code to macOS clipboard if available
            try:
                subprocess.run(
                    ["pbcopy"],
                    input=user_code.encode("utf-8"),
                    check=False,
                    timeout=2,
                )
            except Exception:
                pass

            # Open verification URI in default browser
            try:
                webbrowser.open(verification_uri)
            except Exception:
                pass

            flow_state = {
                "flow_id": flow_id,
                "provider": "github",
                "status": "pending",
                "user_code": user_code,
                "verification_uri": verification_uri,
                "expires_at": int(time.time()) + expires_in,
                "message": f"Enter code {user_code} in the opened browser window.",
            }
            self._active_flows[flow_id] = flow_state

            # Launch background poller thread
            threading.Thread(
                target=self._poll_github_device_token,
                args=(flow_id, device_code, interval, expires_in),
                daemon=True,
            ).start()

            return flow_state

        except Exception as e:
            return {
                "flow_id": flow_id,
                "provider": "github",
                "status": "error",
                "error": str(e),
            }

    def _poll_github_device_token(self, flow_id: str, device_code: str, interval: int, expires_in: int):
        deadline = time.time() + expires_in
        while time.time() < deadline:
            time.sleep(interval)
            try:
                resp = requests.post(
                    "https://github.com/login/oauth/access_token",
                    data={
                        "client_id": GITHUB_PUBLIC_CLIENT_ID,
                        "device_code": device_code,
                        "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                    },
                    headers={"Accept": "application/json", "User-Agent": "OpenAgents/1.0"},
                    timeout=15,
                )
                if resp.status_code != 200:
                    continue

                data = resp.json()
                if "access_token" in data:
                    access_token = data["access_token"]
                    # Fetch user info
                    user_info = self._fetch_github_user_profile(access_token)
                    token_entry = {
                        "access_token": access_token,
                        "token_type": data.get("token_type", "bearer"),
                        "scope": data.get("scope", GITHUB_DEFAULT_SCOPES),
                        "user": user_info.get("login"),
                        "name": user_info.get("name"),
                        "avatar_url": user_info.get("avatar_url"),
                        "expires_at": None,
                    }
                    self.save_provider_token("github", token_entry)
                    if flow_id in self._active_flows:
                        self._active_flows[flow_id].update({
                            "status": "success",
                            "user": user_info.get("login"),
                            "name": user_info.get("name"),
                        })
                    return

                err = data.get("error")
                if err == "authorization_pending":
                    continue
                elif err == "slow_down":
                    time.sleep(5)
                    continue
                elif err in ("expired_token", "access_denied"):
                    if flow_id in self._active_flows:
                        self._active_flows[flow_id]["status"] = "error"
                        self._active_flows[flow_id]["error"] = data.get("error_description", err)
                    return
            except Exception as e:
                print(f"[OAuthManager] GitHub device polling error: {e}")

        if flow_id in self._active_flows:
            self._active_flows[flow_id]["status"] = "expired"

    def _fetch_github_user_profile(self, access_token: str) -> Dict[str, Any]:
        try:
            res = requests.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                    "User-Agent": "OpenAgents/1.0",
                },
                timeout=10,
            )
            if res.status_code == 200:
                return res.json()
        except Exception:
            pass
        return {}

    # =========================================================================
    # Google OAuth 2.0 InstalledAppFlow / PKCE
    # =========================================================================
    def start_google_flow(self) -> Dict[str, Any]:
        flow_id = str(uuid.uuid4())
        flow_state = {
            "flow_id": flow_id,
            "provider": "google",
            "status": "pending",
            "message": "Opening browser for Google authorization...",
        }
        self._active_flows[flow_id] = flow_state

        threading.Thread(
            target=self._run_google_auth_worker,
            args=(flow_id,),
            daemon=True,
        ).start()

        return flow_state

    def _run_google_auth_worker(self, flow_id: str):
        try:
            from google_auth_oauthlib.flow import InstalledAppFlow

            if not os.path.exists(GOOGLE_CREDENTIALS_FILE):
                raise FileNotFoundError(
                    f"Google credentials file not found at {GOOGLE_CREDENTIALS_FILE}. "
                    "Place your Google client secrets in ~/.openagents/credentials/credentials.json"
                )

            os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"
            flow = InstalledAppFlow.from_client_secrets_file(
                GOOGLE_CREDENTIALS_FILE,
                GOOGLE_SCOPES,
            )

            # run_local_server automatically binds an ephemeral port, opens the browser,
            # catches the OAuth redirect, exchanges tokens, and shuts down the local server.
            creds = flow.run_local_server(port=0, prompt="consent")

            # Save to standard token.json for legacy tools
            with open(GOOGLE_TOKEN_FILE, "w") as f:
                f.write(creds.to_json())

            # Fetch user email / profile
            user_email = None
            user_name = None
            try:
                user_res = requests.get(
                    "https://www.googleapis.com/oauth2/v2/userinfo",
                    headers={"Authorization": f"Bearer {creds.token}"},
                    timeout=10,
                )
                if user_res.status_code == 200:
                    u_data = user_res.json()
                    user_email = u_data.get("email")
                    user_name = u_data.get("name")
            except Exception:
                pass

            token_entry = {
                "access_token": creds.token,
                "refresh_token": creds.refresh_token,
                "token_type": "Bearer",
                "expires_at": int(creds.expiry.timestamp()) if creds.expiry else None,
                "scope": " ".join(creds.scopes or GOOGLE_SCOPES),
                "email": user_email,
                "user": user_email or user_name,
                "name": user_name,
            }
            self.save_provider_token("google", token_entry)

            if flow_id in self._active_flows:
                self._active_flows[flow_id].update({
                    "status": "success",
                    "user": user_email or user_name,
                    "email": user_email,
                })

        except Exception as e:
            print(f"[OAuthManager] Google auth worker error: {e}")
            if flow_id in self._active_flows:
                self._active_flows[flow_id].update({
                    "status": "error",
                    "error": str(e),
                })

    # =========================================================================
    # Generic PKCE Flow for any OAuth MCP Server (Slack, Linear, etc.)
    # =========================================================================
    def start_generic_pkce_flow(
        self,
        provider: str,
        client_id: str,
        auth_url: str,
        token_url: str,
        scopes: str,
        redirect_port: int = 8765,
    ) -> Dict[str, Any]:
        flow_id = str(uuid.uuid4())

        # Generate PKCE code verifier and code challenge
        code_verifier = secrets.token_urlsafe(64)
        hashed = hashlib.sha256(code_verifier.encode("ascii")).digest()
        code_challenge = base64.urlsafe_b64encode(hashed).decode("ascii").rstrip("=")

        state = secrets.token_urlsafe(32)
        redirect_uri = f"http://127.0.0.1:{redirect_port}/callback"

        full_auth_url = (
            f"{auth_url}?response_type=code"
            f"&client_id={client_id}"
            f"&redirect_uri={redirect_uri}"
            f"&scope={scopes}"
            f"&code_challenge={code_challenge}"
            f"&code_challenge_method=S256"
            f"&state={state}"
        )

        flow_state = {
            "flow_id": flow_id,
            "provider": provider.lower(),
            "status": "pending",
            "auth_url": full_auth_url,
            "message": "Opening browser for authorization...",
        }
        self._active_flows[flow_id] = flow_state

        threading.Thread(
            target=self._run_pkce_server,
            args=(
                flow_id,
                provider,
                client_id,
                code_verifier,
                token_url,
                redirect_uri,
                redirect_port,
                state,
            ),
            daemon=True,
        ).start()

        try:
            webbrowser.open(full_auth_url)
        except Exception:
            pass

        return flow_state

    def _run_pkce_server(
        self,
        flow_id: str,
        provider: str,
        client_id: str,
        code_verifier: str,
        token_url: str,
        redirect_uri: str,
        port: int,
        expected_state: str,
    ):
        result_holder = {"code": None, "error": None}

        class OAuthCallbackHandler(BaseHTTPRequestHandler):
            def log_message(self, format, *args):
                pass  # Silence default stderr logging

            def do_GET(self):
                parsed = urlparse(self.path)
                if parsed.path == "/callback":
                    qs = parse_qs(parsed.query)
                    code = qs.get("code", [None])[0]
                    state = qs.get("state", [None])[0]
                    err = qs.get("error", [None])[0]

                    if err:
                        result_holder["error"] = err
                        self._render_page(False, f"OAuth Error: {err}")
                    elif state != expected_state:
                        result_holder["error"] = "State verification failed"
                        self._render_page(False, "Security check failed (invalid state parameter).")
                    elif code:
                        result_holder["code"] = code
                        self._render_page(True, "Successfully connected to OpenAgents!")
                    else:
                        result_holder["error"] = "No authorization code received"
                        self._render_page(False, "No authorization code returned.")
                else:
                    self.send_response(404)
                    self.end_headers()

            def _render_page(self, success: bool, msg: str):
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                color = "#10b981" if success else "#ef4444"
                icon = "✓" if success else "✕"
                html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>OpenAgents OAuth</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; background: #090d16; color: #f8fafc; }}
    .card {{ text-align: center; padding: 2.5rem; background: #131b2e; border-radius: 1.25rem; border: 1px solid #1e293b; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.5); max-width: 420px; }}
    .badge {{ width: 56px; height: 56px; line-height: 56px; border-radius: 50%; background: {color}20; color: {color}; font-size: 26px; font-weight: bold; margin: 0 auto 1.25rem auto; border: 1px solid {color}40; }}
    h1 {{ font-size: 1.35rem; margin-bottom: 0.5rem; }}
    p {{ color: #94a3b8; font-size: 0.9rem; line-height: 1.5; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="badge">{icon}</div>
    <h1>{msg}</h1>
    <p>You can safely close this tab and return to the OpenAgents desktop app.</p>
  </div>
</body>
</html>"""
                self.wfile.write(html.encode("utf-8"))

        server = None
        try:
            server = HTTPServer(("127.0.0.1", port), OAuthCallbackHandler)
            server.timeout = 180  # 3 minutes timeout
            while result_holder["code"] is None and result_holder["error"] is None:
                server.handle_request()
        except Exception as e:
            result_holder["error"] = str(e)
        finally:
            if server:
                try:
                    server.server_close()
                except Exception:
                    pass

        # Exchange authorization code for token
        if result_holder["code"]:
            try:
                resp = requests.post(
                    token_url,
                    data={
                        "client_id": client_id,
                        "grant_type": "authorization_code",
                        "code": result_holder["code"],
                        "redirect_uri": redirect_uri,
                        "code_verifier": code_verifier,
                    },
                    headers={"Accept": "application/json"},
                    timeout=15,
                )
                if resp.status_code == 200:
                    token_data = resp.json()
                    self.save_provider_token(provider, token_data)
                    if flow_id in self._active_flows:
                        self._active_flows[flow_id]["status"] = "success"
                else:
                    if flow_id in self._active_flows:
                        self._active_flows[flow_id]["status"] = "error"
                        self._active_flows[flow_id]["error"] = f"Token exchange failed: {resp.text}"
            except Exception as e:
                if flow_id in self._active_flows:
                    self._active_flows[flow_id]["status"] = "error"
                    self._active_flows[flow_id]["error"] = str(e)
        else:
            if flow_id in self._active_flows:
                self._active_flows[flow_id]["status"] = "error"
                self._active_flows[flow_id]["error"] = result_holder.get("error") or "Timed out"

    def get_flow_status(self, flow_id: str) -> Optional[Dict[str, Any]]:
        return self._active_flows.get(flow_id)

    # =========================================================================
    # Environment Injection for MCP Servers
    # =========================================================================
    def get_env_for_mcp(self, server_name: str) -> Dict[str, str]:
        """
        Automatically returns environment variables needed for an MCP server
        based on active OAuth connections.
        """
        env: Dict[str, str] = {}
        s_lower = server_name.lower()

        # GitHub
        if "github" in s_lower or "git" in s_lower:
            gh_token = self.get_valid_token("github")
            if gh_token:
                env["GITHUB_PERSONAL_ACCESS_TOKEN"] = gh_token
                env["GITHUB_TOKEN"] = gh_token

        # Google Drive / Gmail / Google Calendar
        if "google" in s_lower or "drive" in s_lower or "gmail" in s_lower or "calendar" in s_lower:
            if os.path.exists(GOOGLE_CREDENTIALS_FILE):
                env["GOOGLE_DRIVE_OAUTH_CREDENTIALS"] = GOOGLE_CREDENTIALS_FILE
                env["GOOGLE_OAUTH_CREDENTIALS"] = GOOGLE_CREDENTIALS_FILE
            if os.path.exists(GOOGLE_TOKEN_FILE):
                env["GMAIL_CREDENTIALS_PATH"] = GOOGLE_TOKEN_FILE
                env["GOOGLE_DRIVE_MCP_TOKEN_PATH"] = GOOGLE_TOKEN_FILE
                env["GOOGLE_CALENDAR_MCP_TOKEN_PATH"] = GOOGLE_TOKEN_FILE

        # Slack
        if "slack" in s_lower:
            slack_token = self.get_valid_token("slack")
            if slack_token:
                env["SLACK_BOT_TOKEN"] = slack_token

        return env


oauth_manager = OAuthManager()
