import os
import json
import hashlib

USER_PATH = "data/users.json"

def load_users():
    if not os.path.exists(USER_PATH):
        return {}
    with open(USER_PATH, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USER_PATH, "w") as f:
        json.dump(users, f, indent=4)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register(username, password):
    users = load_users()
    if username in users:
        return False
    users[username] = hash_password(password)
    save_users(users)
    return True

def login(username, password):
    users = load_users()
    return users.get(username) == hash_password(password)

def get_current_user(session_state):
    return session_state.get("user", None)
