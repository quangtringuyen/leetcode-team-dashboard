# utils/auth.py
import json
import os
from typing import Dict, Any
from pathlib import Path
import bcrypt

USERS_PATH = "data/users.json"

def _ensure_dir():
    Path("data").mkdir(parents=True, exist_ok=True)

def _read_json(path: str, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _write_json(path: str, payload):
    _ensure_dir()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

def load_users() -> Dict[str, Any]:
    """
    Returns:
    {
      "users": {
        "alice": {"name": "Alice", "email": "alice@example.com", "password": "<bcrypt hash>"},
        ...
      }
    }
    """
    return _read_json(USERS_PATH, {"users": {}})

def save_users(db: Dict[str, Any]):
    _write_json(USERS_PATH, db)

def register(username: str, password: str, name: str | None = None, email: str | None = None) -> bool:
    """
    Registers a new user with a bcrypt-hashed password.
    Returns True if created, False if username exists.
    """
    db = load_users()
    if username in db["users"]:
        return False
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    db["users"][username] = {"name": name or username, "email": email or "", "password": hashed}
    save_users(db)
    return True

def credentials_for_authenticator() -> Dict[str, Any]:
    """
    Transform our users DB into streamlit-authenticator credential dict:
    {
      "usernames": {
        "alice": {"email": "alice@example.com", "name": "Alice", "password": "<bcrypt hash>"},
        ...
      }
    }
    """
    db = load_users()
    users = db.get("users", {})
    return {
        "usernames": {
            uname: {
                "name": urec.get("name", uname),
                "email": urec.get("email", ""),
                "password": urec.get("password", ""),
            }
            for uname, urec in users.items()
        }
    }
