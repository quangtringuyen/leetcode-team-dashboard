import sqlite3
import hashlib
import os
from typing import List, Dict, Optional
import json

DATABASE_PATH = "data/leetcode_dashboard.db"

def get_db_connection():
    """Get database connection and ensure tables exist"""
    # Ensure data directory exists
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # This allows dict-like access to rows
    
    # Create tables if they don't exist
    create_tables(conn)
    return conn

def create_tables(conn):
    """Create all necessary tables"""
    cursor = conn.cursor()
    
    # Users table for authentication
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Teams table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            owner_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (owner_id) REFERENCES users (id)
        )
    ''')
    
    # Members table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            leetcode_username TEXT NOT NULL,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (team_id) REFERENCES teams (id),
            UNIQUE(team_id, leetcode_username)
        )
    ''')
    
    # Cache table for LeetCode data (optional - for performance)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leetcode_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            data TEXT NOT NULL,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()

def hash_password(password: str) -> str:
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

# === USER AUTHENTICATION ===
def register_user(username: str, password: str) -> bool:
    """Register a new user"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        password_hash = hash_password(password)
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, password_hash)
        )
        
        # Create default team for user
        user_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO teams (name, owner_id) VALUES (?, ?)",
            (f"{username}'s Team", user_id)
        )
        
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False  # Username already exists

def login_user(username: str, password: str) -> bool:
    """Authenticate user login"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    password_hash = hash_password(password)
    cursor.execute(
        "SELECT id FROM users WHERE username = ? AND password_hash = ?",
        (username, password_hash)
    )
    
    result = cursor.fetchone()
    conn.close()
    return result is not None

def get_user_id(username: str) -> Optional[int]:
    """Get user ID by username"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    
    return result[0] if result else None

def get_user_team_id(username: str) -> Optional[int]:
    """Get user's team ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT t.id FROM teams t
        JOIN users u ON t.owner_id = u.id
        WHERE u.username = ?
    ''', (username,))
    
    result = cursor.fetchone()
    conn.close()
    
    return result[0] if result else None

# === TEAM MEMBER MANAGEMENT ===
def add_member(username: str, member_name: str, leetcode_username: str) -> bool:
    """Add a member to user's team"""
    try:
        team_id = get_user_team_id(username)
        if not team_id:
            return False
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO members (team_id, name, leetcode_username) VALUES (?, ?, ?)",
            (team_id, member_name, leetcode_username)
        )
        
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False  # Member already exists

def remove_member(username: str, leetcode_username: str) -> bool:
    """Remove a member from user's team"""
    team_id = get_user_team_id(username)
    if not team_id:
        return False
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "DELETE FROM members WHERE team_id = ? AND leetcode_username = ?",
        (team_id, leetcode_username)
    )
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success

def get_team_members(username: str) -> List[Dict]:
    """Get all members of user's team"""
    team_id = get_user_team_id(username)
    if not team_id:
        return []
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT name, leetcode_username FROM members WHERE team_id = ? ORDER BY added_at",
        (team_id,)
    )
    
    members = []
    for row in cursor.fetchall():
        members.append({
            "name": row[0],
            "username": row[1]
        })
    
    conn.close()
    return members

# === LEETCODE DATA CACHING (Optional) ===
def cache_leetcode_data(username: str, data: dict) -> None:
    """Cache LeetCode data for performance"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    data_json = json.dumps(data)
    cursor.execute('''
        INSERT OR REPLACE INTO leetcode_cache (username, data, last_updated)
        VALUES (?, ?, CURRENT_TIMESTAMP)
    ''', (username, data_json))
    
    conn.commit()
    conn.close()

def get_cached_leetcode_data(username: str, max_age_hours: int = 1) -> Optional[dict]:
    """Get cached LeetCode data if not too old"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT data FROM leetcode_cache 
        WHERE username = ? 
        AND datetime(last_updated) > datetime('now', '-{} hours')
    '''.format(max_age_hours), (username,))
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return json.loads(result[0])
    return None

# === DATABASE UTILITIES ===
def get_database_stats() -> Dict:
    """Get database statistics"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    stats = {}
    
    # Count users
    cursor.execute("SELECT COUNT(*) FROM users")
    stats['total_users'] = cursor.fetchone()[0]
    
    # Count teams
    cursor.execute("SELECT COUNT(*) FROM teams")
    stats['total_teams'] = cursor.fetchone()[0]
    
    # Count members
    cursor.execute("SELECT COUNT(*) FROM members")
    stats['total_members'] = cursor.fetchone()[0]
    
    conn.close()
    return stats

def backup_database(backup_path: str) -> bool:
    """Create a backup of the database"""
    try:
        import shutil
        shutil.copy2(DATABASE_PATH, backup_path)
        return True
    except Exception:
        return False