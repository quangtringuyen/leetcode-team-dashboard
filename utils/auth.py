# utils/auth.py
import json
import os
import io
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

import bcrypt

# Optional: use Streamlit secrets for S3 if available
try:
    import streamlit as st
    HAS_ST = True
except Exception:
    HAS_ST = False

# -----------------------------
# Storage (S3-or-local), same behavior as app.py
# -----------------------------
def _use_s3() -> bool:
    if not HAS_ST:
        return False
    try:
        return "aws" in st.secrets and all(
            k in st.secrets["aws"]
            for k in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_DEFAULT_REGION", "S3_BUCKET", "S3_PREFIX")
        )
    except Exception:
        return False

_s3_client_cached = None
def _s3_client():
    global _s3_client_cached
    if _s3_client_cached is None:
        import boto3
        _s3_client_cached = boto3.client(
            "s3",
            aws_access_key_id=st.secrets["aws"]["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=st.secrets["aws"]["AWS_SECRET_ACCESS_KEY"],
            region_name=st.secrets["aws"]["AWS_DEFAULT_REGION"],
        )
    return _s3_client_cached

def _s3_bucket_key(local_path: str) -> Tuple[str, str]:
    bucket = st.secrets["aws"]["S3_BUCKET"]
    prefix = st.secrets["aws"]["S3_PREFIX"].rstrip("/")
    key = f"{prefix}/{local_path.lstrip('/')}"
    return bucket, key

def _read_json(local_path: str, default):
    if _use_s3():
        try:
            bucket, key = _s3_bucket_key(local_path)
            obj = _s3_client().get_object(Bucket=bucket, Key=key)
            return json.loads(obj["Body"].read().decode("utf-8"))
        except Exception:
            return default
    else:
        if not os.path.exists(local_path):
            return default
        with open(local_path, "r", encoding="utf-8") as f:
            return json.load(f)

def _write_json(local_path: str, payload):
    if _use_s3():
        bucket, key = _s3_bucket_key(local_path)
        buf = io.BytesIO(json.dumps(payload, indent=2).encode("utf-8"))
        _s3_client().upload_fileobj(buf, bucket, key)
    else:
        Path(os.path.dirname(local_path)).mkdir(parents=True, exist_ok=True)
        with open(local_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

# -----------------------------
# Users DB
# -----------------------------
USERS_PATH = "data/users.json"

def load_users() -> Dict[str, Any]:
    """
    Returns:
    {
      "users": {
        "alice": {"name": "Alice", "email": "alice@example.com", "password": "<hash or plaintext>"},
        ...
      }
    }
    """
    return _read_json(USERS_PATH, {"users": {}})

def save_users(db: Dict[str, Any]):
    _write_json(USERS_PATH, db)

def _is_bcrypt_hash(value: str) -> bool:
    if not isinstance(value, str):
        return False
    # bcrypt hashes typically start with $2a$, $2b$, or $2y$
    return value.startswith("$2a$") or value.startswith("$2b$") or value.startswith("$2y$")

def register(username: str, password: str, name: Optional[str] = None, email: Optional[str] = None) -> bool:
    """
    Create a new user with a bcrypt-hashed password. Returns False if user exists.
    """
    db = load_users()
    if username in db["users"]:
        return False
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    db["users"][username] = {"name": name or username, "email": email or "", "password": hashed}
    save_users(db)
    return True

def verify_login(username: str, password: str) -> bool:
    """
    Verify a username/password. If the stored password is plaintext and matches,
    it will be transparently migrated to bcrypt.
    """
    db = load_users()
    rec = db.get("users", {}).get(username)
    if not rec:
        return False

    stored = rec.get("password", "")
    if _is_bcrypt_hash(stored):
        try:
            return bcrypt.checkpw(password.encode("utf-8"), stored.encode("utf-8"))
        except Exception:
            return False
    else:
        # Legacy plaintext: if it matches exactly, migrate to bcrypt
        if password == stored:
            new_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            rec["password"] = new_hash
            db["users"][username] = rec
            save_users(db)
            return True
        return False

def migrate_plaintext_passwords() -> int:
    """
    One-shot migration: convert any plaintext passwords to bcrypt.
    Returns the number of accounts migrated.
    """
    db = load_users()
    users = db.get("users", {})
    changed = 0
    for uname, rec in users.items():
        pwd = rec.get("password", "")
        if pwd and not _is_bcrypt_hash(pwd):
            # treat current stored pwd as plaintext and re-hash
            new_hash = bcrypt.hashpw(pwd.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            rec["password"] = new_hash
            users[uname] = rec
            changed += 1
    if changed:
        db["users"] = users
        save_users(db)
    return changed

def credentials_for_authenticator() -> Dict[str, Any]:
    """
    Transform our users DB into streamlit-authenticator credentials dict:
    {
      "usernames": {
        "alice": {"email": "alice@example.com", "name": "Alice", "password": "<bcrypt hash>"},
        ...
      }
    }
    NOTE: streamlit-authenticator REQUIRES bcrypt hashes here.
    If legacy plaintext exists, run migrate_plaintext_passwords() first.
    """
    db = load_users()
    users = db.get("users", {})
    return {
        "usernames": {
            uname: {
                "name": urec.get("name", uname),
                "email": urec.get("email", ""),
                "password": urec.get("password", ""),  # should be bcrypt
            }
            for uname, urec in users.items()
        }
    }
