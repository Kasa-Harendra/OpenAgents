import os
import sys
import json
import shutil
import stat
from pathlib import Path
from typing import Dict, Any, Optional

# Root directory resolution
DEFAULT_OPENAGENTS_DIR = Path.home() / ".openagents"
OPENAGENTS_DIR = Path(os.environ.get("OPENAGENTS_HOME", DEFAULT_OPENAGENTS_DIR)).resolve()

# Subdirectories
CREDENTIALS_DIR = OPENAGENTS_DIR / "credentials"
SKILLS_DIR = OPENAGENTS_DIR / "skills"
MODS_DIR = OPENAGENTS_DIR / "mods"
HISTORY_DIR = OPENAGENTS_DIR / "history"
AUDIT_DIR = OPENAGENTS_DIR / "audit"
CONFIG_FILE = OPENAGENTS_DIR / "config.json"
DB_FILE = OPENAGENTS_DIR / "openagents.db"

DEFAULT_CONFIG: Dict[str, Any] = {
    "version": "1.0.0",
    "theme": "dark",
    "telemetry": False,
    "default_model_provider": "gemini",
    "default_chat_mode": "multiagent",
    "server": {
        "host": "127.0.0.1",
        "port": 8000
    },
    "features": {
        "claude_mods": True,
        "self_healing": True,
        "context_compaction": True,
        "human_in_the_loop": True
    }
}


def get_openagents_dir() -> Path:
    """Returns the central ~/.openagents home directory."""
    return OPENAGENTS_DIR


def get_credentials_dir() -> Path:
    """Returns ~/.openagents/credentials with 0o700 secure permission."""
    return CREDENTIALS_DIR


def get_skills_dir() -> Path:
    """Returns ~/.openagents/skills directory."""
    return SKILLS_DIR


def get_mods_dir() -> Path:
    """Returns ~/.openagents/mods directory for user mods."""
    return MODS_DIR


def get_history_dir() -> Path:
    """Returns ~/.openagents/history directory."""
    return HISTORY_DIR


def get_audit_dir() -> Path:
    """Returns ~/.openagents/audit directory."""
    return AUDIT_DIR


def get_config_path() -> Path:
    """Returns ~/.openagents/config.json path."""
    return CONFIG_FILE


def get_database_path() -> Path:
    """Returns ~/.openagents/openagents.db path."""
    return DB_FILE


def load_config() -> Dict[str, Any]:
    """Loads ~/.openagents/config.json or returns default configuration."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return {**DEFAULT_CONFIG, **json.load(f)}
        except Exception:
            return DEFAULT_CONFIG
    return DEFAULT_CONFIG


def update_config(updates: Dict[str, Any]) -> Dict[str, Any]:
    """Updates and saves ~/.openagents/config.json."""
    current = load_config()
    current.update(updates)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(current, f, indent=2)
    return current


def ensure_openagents_dirs(project_root: Optional[Path] = None):
    """
    Initializes ~/.openagents and its subdirectories.
    Migrates any existing project-local artifacts (openagents.db, credentials, skills).
    """
    # 1. Create main directories
    OPENAGENTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Secure credentials directory (owner only)
    CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(CREDENTIALS_DIR, stat.S_IRWXU)  # 0o700
    except Exception:
        pass

    SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    MODS_DIR.mkdir(parents=True, exist_ok=True)
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)

    # 2. Initialize default config if not present
    if not CONFIG_FILE.exists():
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)

    # 3. Initialize sessions.json if not present
    sessions_index = HISTORY_DIR / "sessions.json"
    if not sessions_index.exists():
        with open(sessions_index, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2)

    if project_root is None:
        # Resolve repo root relative to this file
        project_root = Path(__file__).resolve().parent.parent.parent

    # 4. Migrate database if it exists in project root but not in ~/.openagents
    legacy_db = project_root / "openagents.db"
    if legacy_db.exists() and not DB_FILE.exists():
        try:
            shutil.copy2(legacy_db, DB_FILE)
            print(f"[openagents] Migrated database from {legacy_db} to {DB_FILE}")
        except Exception as e:
            print(f"[openagents] Warning: Failed to migrate legacy DB: {e}")

    # 5. Migrate project-local credentials if present
    legacy_creds_dir = project_root / "backend" / "credentials"
    if legacy_creds_dir.exists():
        for filename in ["credentials.json", "token.json"]:
            src = legacy_creds_dir / filename
            dst = CREDENTIALS_DIR / filename
            if src.exists() and not dst.exists():
                try:
                    shutil.copy2(src, dst)
                    os.chmod(dst, stat.S_IRUSR | stat.S_IWUSR)  # 0o600
                    print(f"[openagents] Migrated credential {filename} to {dst}")
                except Exception as e:
                    print(f"[openagents] Warning: Failed to migrate {filename}: {e}")

    # 6. Seed default system skills from project backend/skills to ~/.openagents/skills
    legacy_skills_dir = project_root / "backend" / "skills"
    if legacy_skills_dir.exists():
        for skill_dir in legacy_skills_dir.iterdir():
            if skill_dir.is_dir() and not skill_dir.name.startswith("."):
                target_skill_dir = SKILLS_DIR / skill_dir.name
                if not target_skill_dir.exists():
                    try:
                        shutil.copytree(skill_dir, target_skill_dir)
                    except Exception:
                        pass


# Automatically ensure dirs on import
ensure_openagents_dirs()
