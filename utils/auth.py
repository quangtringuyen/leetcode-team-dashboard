# Updated auth.py to use SQLite database
from .database import register_user, login_user

def register(username: str, password: str) -> bool:
    """Register a new user"""
    return register_user(username, password)

def login(username: str, password: str) -> bool:
    """Authenticate user login"""
    return login_user(username, password)

def get_current_user(session_state):
    """Get current user from session state"""
    return session_state.get("user", None)