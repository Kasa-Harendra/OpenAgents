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
from typing import Dict, Any, Optional, List, Union
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

import requests

from backend.db.database import OPENAGENTS_DIR

CREDENTIALS_DIR = os.path.join(OPENAGENTS_DIR, "credentials")
os.makedirs(CREDENTIALS_DIR, exist_ok=True)

OAUTH_TOKENS_FILE = os.path.join(CREDENTIALS_DIR, "oauth_tokens.json")


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

    # =========================================================================
    # Token Storage Management (Generic & Dynamic)
    # =========================================================================
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

    def save_provider_token(self, identifier: str, token_data: Dict[str, Any]):
        key = identifier.lower().strip()
        with self._lock:
            all_tokens = {}
            if os.path.exists(OAUTH_TOKENS_FILE):
                try:
                    with open(OAUTH_TOKENS_FILE, "r") as f:
                        all_tokens = json.load(f)
                except Exception:
                    all_tokens = {}

            all_tokens[key] = {
                **token_data,
                "identifier": key,
                "updated_at": int(time.time()),
            }

            try:
                with open(OAUTH_TOKENS_FILE, "w") as f:
                    json.dump(all_tokens, f, indent=2)
                os.chmod(OAUTH_TOKENS_FILE, 0o600)
            except Exception as e:
                print(f"[OAuthManager] Failed to write token file: {e}")

    def delete_provider_token(self, identifier: str) -> bool:
        key = identifier.lower().strip()
        with self._lock:
            if not os.path.exists(OAUTH_TOKENS_FILE):
                return False
            try:
                with open(OAUTH_TOKENS_FILE, "r") as f:
                    all_tokens = json.load(f)
                if key in all_tokens:
                    del all_tokens[key]
                    with open(OAUTH_TOKENS_FILE, "w") as f:
                        json.dump(all_tokens, f, indent=2)
                    os.chmod(OAUTH_TOKENS_FILE, 0o600)
                    return True
                return False
            except Exception as e:
                print(f"[OAuthManager] Error deleting token for {key}: {e}")
                return False

    def get_providers_status(self) -> List[Dict[str, Any]]:
        """
        Dynamically returns the status of all connected OAuth credentials.
        No hardcoded vendor lists.
        """
        tokens = self.load_all_tokens()
        results = []

        for key, entry in tokens.items():
            if not isinstance(entry, dict) or not entry.get("access_token"):
                continue

            user_display = entry.get("user") or entry.get("email") or entry.get("name") or "Connected"
            resource_name = entry.get("resource_name") or entry.get("name") or key

            results.append({
                "id": key,
                "name": resource_name,
                "description": entry.get("description") or f"Authenticated credentials for {resource_name}",
                "connected": True,
                "user": user_display,
                "avatar_url": entry.get("avatar_url"),
                "scopes": entry.get("scope"),
                "expires_at": entry.get("expires_at"),
                "updated_at": entry.get("updated_at"),
            })

        return results

    def get_valid_token(self, identifier: str) -> Optional[str]:
        """
        Retrieves a valid access token for an identifier or URL host, refreshing if expired.
        """
        if not identifier:
            return None

        key = identifier.lower().strip()
        tokens = self.load_all_tokens()
        entry = tokens.get(key)

        # Fallback: check matching host or URL substring in tokens
        if not entry:
            for stored_k, stored_v in tokens.items():
                if stored_k in key or key in stored_k:
                    entry = stored_v
                    key = stored_k
                    break

        if not entry or not entry.get("access_token"):
            return None

        # Check expiration and attempt RFC 6749 refresh grant if token_endpoint is available
        expires_at = entry.get("expires_at")
        now = int(time.time())

        if expires_at and (now + 60 >= expires_at):
            refresh_token = entry.get("refresh_token")
            token_endpoint = entry.get("token_endpoint")
            client_id = entry.get("client_id")

            if refresh_token and token_endpoint:
                try:
                    data = {
                        "grant_type": "refresh_token",
                        "refresh_token": refresh_token,
                    }
                    if client_id:
                        data["client_id"] = client_id

                    refreshed = requests.post(token_endpoint, data=data, timeout=10)
                    if refreshed.status_code == 200:
                        ref_data = refreshed.json()
                        new_token = ref_data.get("access_token")
                        if new_token:
                            entry["access_token"] = new_token
                            if "expires_in" in ref_data:
                                entry["expires_at"] = now + int(ref_data["expires_in"])
                            if "refresh_token" in ref_data:
                                entry["refresh_token"] = ref_data["refresh_token"]
                            self.save_provider_token(key, entry)
                            return new_token
                except Exception as e:
                    print(f"[OAuthManager] Generic token refresh failed for {key}: {e}")

        return entry.get("access_token")

    # =========================================================================
    # Environment & Authorization Header Resolution
    # =========================================================================
    def get_env_for_mcp(self, server_name: str, url: Optional[str] = None) -> Dict[str, str]:
        """
        Dynamically returns Authorization headers for an MCP server
        based on active OAuth credentials discovered for its URL or server name.
        """
        env: Dict[str, str] = {}
        tokens = self.load_all_tokens()
        if not tokens:
            return env

        # 1. Check by URL netloc / path
        if url:
            parsed = urlparse(url)
            host = parsed.netloc.lower()
            full_url = url.lower()

            for key in [full_url, host, parsed.scheme + "://" + host]:
                token = self.get_valid_token(key)
                if token:
                    env["Authorization"] = f"Bearer {token}"
                    return env

            # Check if any stored key matches the host
            for prov_key in tokens:
                if prov_key in host or host in prov_key:
                    token = self.get_valid_token(prov_key)
                    if token:
                        env["Authorization"] = f"Bearer {token}"
                        return env

        # 2. Check by server name
        if server_name:
            s_clean = server_name.lower().strip()
            for prov_key in tokens:
                if prov_key == s_clean or prov_key in s_clean:
                    token = self.get_valid_token(prov_key)
                    if token:
                        env["Authorization"] = f"Bearer {token}"
                        return env

        return env

    # =========================================================================
    # Dynamic RFC 9728 & RFC 8414 Probing
    # =========================================================================
    def probe_endpoint(self, url: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Inspects an HTTP/SSE MCP endpoint dynamically without hardcoded URLs.
        Detects RFC 9728 OAuth Protected Resource Metadata and RFC 8414 Authorization Server Metadata.
        """
        import re

        if not url or not url.startswith(("http://", "https://")):
            return {"status": "issue", "auth_required": False, "message": "Invalid or missing HTTP/HTTPS URL"}

        req_headers = dict(headers or {})
        if "Accept" not in req_headers:
            req_headers["Accept"] = "text/event-stream, application/json, */*"

        try:
            res = requests.get(url, headers=req_headers, timeout=6)
            if res.status_code in [200, 204]:
                return {
                    "status": "online",
                    "auth_required": False,
                    "status_code": res.status_code,
                    "message": "Server is online and responding (HTTP 200)"
                }

            if res.status_code == 401:
                auth_header = res.headers.get("www-authenticate", "")
                match = re.search(r'resource_metadata="([^"]+)"', auth_header)
                meta_url = match.group(1) if match else None

                parsed = urlparse(url)
                origin = f"{parsed.scheme}://{parsed.netloc}"

                # Fallback RFC 9728 well-known endpoints if not specified in WWW-Authenticate
                if not meta_url:
                    path_stripped = parsed.path.rstrip('/')
                    candidates = [
                        f"{origin}/.well-known/oauth-protected-resource{path_stripped}/",
                        f"{origin}/.well-known/oauth-protected-resource{path_stripped}",
                        f"{origin}/.well-known/oauth-protected-resource/",
                        f"{origin}/.well-known/oauth-protected-resource",
                    ]
                    for candidate in candidates:
                        try:
                            c_res = requests.get(candidate, timeout=3)
                            if c_res.status_code == 200 and "authorization_servers" in c_res.text:
                                meta_url = candidate
                                break
                        except Exception:
                            continue

                resource_name = parsed.netloc
                auth_servers: List[str] = []
                scopes: List[str] = []
                auth_endpoint: Optional[str] = None
                token_endpoint: Optional[str] = None
                device_endpoint: Optional[str] = None
                registration_endpoint: Optional[str] = None

                # Fetch RFC 9728 resource metadata document
                if meta_url:
                    try:
                        m_res = requests.get(meta_url, timeout=5)
                        if m_res.status_code == 200:
                            m_data = m_res.json()
                            resource_name = m_data.get("resource_name", resource_name)
                            auth_servers = m_data.get("authorization_servers", [])
                            scopes = m_data.get("scopes_supported", [])

                            # Resolve authorization server via RFC 8414 metadata
                            for as_url in auth_servers:
                                as_base = str(as_url).rstrip('/')
                                as_parsed = urlparse(as_base)
                                as_origin = f"{as_parsed.scheme}://{as_parsed.netloc}"

                                as_meta_candidates = [
                                    f"{as_base}/.well-known/oauth-authorization-server",
                                    f"{as_base}/.well-known/openid-configuration",
                                    f"{as_origin}/.well-known/oauth-authorization-server",
                                    f"{as_origin}/.well-known/openid-configuration"
                                ]

                                for as_meta_url in as_meta_candidates:
                                    try:
                                        as_res = requests.get(as_meta_url, timeout=3)
                                        if as_res.status_code == 200:
                                            as_json = as_res.json()
                                            auth_endpoint = as_json.get("authorization_endpoint")
                                            token_endpoint = as_json.get("token_endpoint")
                                            device_endpoint = as_json.get("device_authorization_endpoint")
                                            registration_endpoint = as_json.get("registration_endpoint")
                                            if not scopes and as_json.get("scopes_supported"):
                                                scopes = as_json.get("scopes_supported")
                                            if auth_endpoint or device_endpoint:
                                                break
                                    except Exception:
                                        pass

                                if auth_endpoint or device_endpoint:
                                    break

                                # Standard fallback endpoints if metadata is not published (e.g. GitHub OAuth)
                                if not auth_endpoint and not device_endpoint:
                                    if "github" in as_base.lower():
                                        device_endpoint = f"{as_origin}/login/device/code"
                                        token_endpoint = f"{as_origin}/login/oauth/access_token"
                                        auth_endpoint = f"{as_origin}/login/oauth/authorize"
                                    else:
                                        auth_endpoint = f"{as_base}/authorize"
                                        token_endpoint = f"{as_base}/token"
                    except Exception:
                        pass

                # Check if a valid token is already stored for this resource, host, or authorization server
                active_token = (
                    self.get_valid_token(url) or
                    self.get_valid_token(parsed.netloc) or
                    (self.get_valid_token(auth_servers[0]) if auth_servers else None)
                )

                has_token = bool(active_token)

                # If token exists and was not already passed in headers, test it live
                if has_token and "Authorization" not in req_headers:
                    try:
                        retry_headers = dict(req_headers)
                        retry_headers["Authorization"] = f"Bearer {active_token}"
                        retry_res = requests.get(url, headers=retry_headers, timeout=6)
                        if retry_res.status_code in [200, 204, 307, 405]:
                            return {
                                "status": "online",
                                "auth_required": False,
                                "resource_name": resource_name,
                                "has_token": True,
                                "status_code": retry_res.status_code,
                                "message": f"Authenticated & Online ({resource_name})"
                            }
                    except Exception:
                        pass

                return {
                    "status": "auth_required",
                    "auth_required": True,
                    "resource_name": resource_name,
                    "metadata_url": meta_url,
                    "authorization_servers": auth_servers,
                    "scopes": scopes,
                    "auth_endpoint": auth_endpoint,
                    "token_endpoint": token_endpoint,
                    "device_authorization_endpoint": device_endpoint,
                    "registration_endpoint": registration_endpoint,
                    "has_token": has_token,
                    "status_code": 401,
                    "message": f"Requires authorization for {resource_name}"
                }

            if res.status_code in [307, 308, 405]:
                return {
                    "status": "online",
                    "auth_required": False,
                    "status_code": res.status_code,
                    "message": "Endpoint is active and reachable"
                }

            return {
                "status": "issue",
                "auth_required": False,
                "status_code": res.status_code,
                "message": f"Server returned HTTP {res.status_code}: {res.reason}"
            }
        except Exception as e:
            return {
                "status": "issue",
                "auth_required": False,
                "error": str(e),
                "message": f"Connection failed: {str(e)}"
            }

    # =========================================================================
    # Dynamic Authorization Flow Handler
    # =========================================================================
    def authorize_mcp_endpoint(self, url: str, client_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Dynamically detects OAuth protected resource details via RFC 9728 .well-known
        and starts the corresponding RFC 8628 Device Code or RFC 7636 PKCE flow.
        """
        probe = self.probe_endpoint(url)
        if not probe.get("auth_required"):
            return {"status": "success", "message": "No authorization required for this endpoint"}

        resource_key = probe.get("resource_name") or urlparse(url).netloc
        scopes = " ".join(probe.get("scopes", [])) or "read write"
        token_endpoint = probe.get("token_endpoint")
        device_endpoint = probe.get("device_authorization_endpoint")
        auth_endpoint = probe.get("auth_endpoint")

        # Resolve client_id: custom parameter, env var, or public client for the AS
        resolved_client_id = client_id or os.environ.get("OAUTH_CLIENT_ID")
        if not resolved_client_id:
            auth_servers = probe.get("authorization_servers", [])
            if any("github" in str(s).lower() for s in auth_servers) or "githubcopilot.com" in url:
                resolved_client_id = "Iv1.b507a08c87ecfe98"  # Copilot / VS Code Device Auth Client
            else:
                resolved_client_id = "openagents-mcp-client"

        # Case 1: RFC 8628 Device Authorization Grant
        if device_endpoint and token_endpoint:
            return self.start_device_code_flow(
                device_url=device_endpoint,
                token_url=token_endpoint,
                client_id=resolved_client_id,
                scopes=scopes,
                resource_key=resource_key,
                resource_url=url,
            )

        # Case 2: RFC 7636 Authorization Code with PKCE
        if auth_endpoint and token_endpoint:
            return self.start_generic_pkce_flow(
                provider=resource_key,
                client_id=resolved_client_id,
                auth_url=auth_endpoint,
                token_url=token_endpoint,
                scopes=scopes,
                redirect_port=8765,
                resource_url=url,
            )

        return {
            "status": "error",
            "error": f"Authorization endpoints for {resource_key} could not be resolved from .well-known metadata.",
            "probe": probe
        }

    # =========================================================================
    # Generic RFC 8628 Device Code Authorization Flow
    # =========================================================================
    def start_device_code_flow(
        self,
        device_url: str,
        token_url: str,
        client_id: str,
        scopes: str,
        resource_key: str,
        resource_url: Optional[str] = None
    ) -> Dict[str, Any]:
        flow_id = str(uuid.uuid4())
        try:
            resp = requests.post(
                device_url,
                data={
                    "client_id": client_id,
                    "scope": scopes,
                },
                headers={"Accept": "application/json", "User-Agent": "OpenAgents/1.0"},
                timeout=15,
            )
            if resp.status_code != 200:
                raise Exception(f"Device code endpoint returned HTTP {resp.status_code}: {resp.text}")

            data = resp.json()
            device_code = data["device_code"]
            user_code = data["user_code"]
            verification_uri = data.get("verification_uri_complete") or data.get("verification_uri")
            interval = max(int(data.get("interval", 5)), 5)
            expires_in = int(data.get("expires_in", 900))

            # Copy user code to system clipboard if available
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
                "provider": resource_key,
                "status": "pending",
                "user_code": user_code,
                "verification_uri": verification_uri,
                "expires_at": int(time.time()) + expires_in,
                "message": f"Enter code {user_code} in the opened browser window.",
            }
            self._active_flows[flow_id] = flow_state

            # Launch background poller thread
            threading.Thread(
                target=self._poll_device_token,
                args=(flow_id, token_url, client_id, device_code, interval, expires_in, resource_key, resource_url),
                daemon=True,
            ).start()

            return flow_state

        except Exception as e:
            return {
                "flow_id": flow_id,
                "provider": resource_key,
                "status": "error",
                "error": str(e),
            }

    def _poll_device_token(
        self,
        flow_id: str,
        token_url: str,
        client_id: str,
        device_code: str,
        interval: int,
        expires_in: int,
        resource_key: str,
        resource_url: Optional[str] = None
    ):
        deadline = time.time() + expires_in
        while time.time() < deadline:
            time.sleep(interval)
            try:
                resp = requests.post(
                    token_url,
                    data={
                        "client_id": client_id,
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
                    token_entry = {
                        "access_token": access_token,
                        "refresh_token": data.get("refresh_token"),
                        "token_type": data.get("token_type", "bearer"),
                        "scope": data.get("scope"),
                        "token_endpoint": token_url,
                        "client_id": client_id,
                        "resource_name": resource_key,
                        "expires_at": int(time.time()) + int(data["expires_in"]) if "expires_in" in data else None,
                    }

                    # Save mapped to resource name and resource host/URL
                    self.save_provider_token(resource_key, token_entry)
                    if resource_url:
                        parsed = urlparse(resource_url)
                        self.save_provider_token(parsed.netloc, token_entry)
                        self.save_provider_token(resource_url, token_entry)

                    if flow_id in self._active_flows:
                        self._active_flows[flow_id].update({
                            "status": "success",
                            "message": "Authorization successful!",
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
                print(f"[OAuthManager] Device polling error: {e}")

        if flow_id in self._active_flows:
            self._active_flows[flow_id]["status"] = "expired"

    # =========================================================================
    # Generic RFC 7636 Authorization Code Flow with PKCE
    # =========================================================================
    def start_generic_pkce_flow(
        self,
        provider: str,
        client_id: str,
        auth_url: str,
        token_url: str,
        scopes: str,
        redirect_port: int = 8765,
        resource_url: Optional[str] = None,
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
                resource_url,
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
        resource_url: Optional[str] = None,
    ):
        result_holder = {"code": None, "error": None}

        class OAuthCallbackHandler(BaseHTTPRequestHandler):
            def log_message(self, format, *args):
                pass

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
            server.timeout = 180
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

        # Exchange authorization code for access token
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
                    entry = {
                        **token_data,
                        "token_endpoint": token_url,
                        "client_id": client_id,
                        "resource_name": provider,
                    }
                    self.save_provider_token(provider, entry)
                    if resource_url:
                        parsed = urlparse(resource_url)
                        self.save_provider_token(parsed.netloc, entry)
                        self.save_provider_token(resource_url, entry)

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


oauth_manager = OAuthManager()
