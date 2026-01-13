import sqlite3
import logging
from contextlib import contextmanager
from backend.core.config import settings
import os

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(settings.DATA_DIR, "leetcode.db")

def init_db():
    """Initialize the database with tables"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Members table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS members (
            username TEXT PRIMARY KEY,
            name TEXT,
            avatar TEXT,
            team_owner TEXT,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Ensure status column exists (migration for existing DBs)
        try:
            cursor.execute("SELECT status FROM members LIMIT 1")
        except sqlite3.OperationalError:
            logger.info("Adding missing 'status' column to members table")
            cursor.execute("ALTER TABLE members ADD COLUMN status TEXT DEFAULT 'active'")
        
        # Snapshots table (Weekly history)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            week_start TEXT,
            total_solved INTEGER,
            easy INTEGER,
            medium INTEGER,
            hard INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (username) REFERENCES members (username),
            UNIQUE(username, week_start)
        )
        """)
        
        # Create indices for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_username ON snapshots(username)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_week ON snapshots(week_start)")
        
        # API Cache table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS api_cache (
            key TEXT PRIMARY KEY,
            data TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # System Settings table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Notifications table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            title TEXT,
            message TEXT,
            recipient TEXT,
            status TEXT,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            sent_at TIMESTAMP
        )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_notifications_status ON notifications(status)")
        
        # Insert default settings if not exist
        cursor.execute("INSERT OR IGNORE INTO system_settings (key, value) VALUES ('weekly_goal', '100')")
        cursor.execute("INSERT OR IGNORE INTO system_settings (key, value) VALUES ('team_name', '\"LeetCode Team\"')")
        cursor.execute("INSERT OR IGNORE INTO system_settings (key, value) VALUES ('snapshot_schedule_day', '\"monday\"')")
        cursor.execute("INSERT OR IGNORE INTO system_settings (key, value) VALUES ('snapshot_schedule_time', '\"07:30\"')")  # Changed from 00:00 to 07:30 to align with LeetCode's UTC 00:00 (GMT+7 07:00)
        cursor.execute("INSERT OR IGNORE INTO system_settings (key, value) VALUES ('notification_check_interval', '15')")
        cursor.execute("INSERT OR IGNORE INTO system_settings (key, value) VALUES ('problems_per_member_weekly', '3')")
        
        conn.commit()
        logger.info("Database initialized successfully")

@contextmanager
def get_db_connection():
    """Get database connection with row factory"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Return rows as dict-like objects
    try:
        yield conn
    finally:
        conn.close()

def get_user_history_from_db(owner_username: str) -> dict:
    """
    Fetch history for all members of a team owner.
    Returns data in the legacy dictionary format: {username: [snapshots]}
    """
    history = {}
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Get members belonging to this owner
        cursor.execute("SELECT username FROM members WHERE team_owner = ?", (owner_username,))
        members = [row["username"] for row in cursor.fetchall()]
        
        if not members:
            return {}
            
        # Get snapshots for these members
        placeholders = ",".join(["?"] * len(members))
        cursor.execute(f"""
            SELECT * FROM snapshots 
            WHERE username IN ({placeholders})
            ORDER BY week_start ASC
        """, members)
        
        rows = cursor.fetchall()
        
        for row in rows:
            username = row["username"]
            if username not in history:
                history[username] = []
                
            snapshot = {
                "week_start": row["week_start"],
                "member": username,
                "totalSolved": row["total_solved"],
                "easy": row["easy"],
                "medium": row["medium"],
                "hard": row["hard"],
                "timestamp": row["timestamp"]
            }
            history[username].append(snapshot)
            
    return history

def get_cached_data(key: str, ttl_seconds: int = 3600) -> dict | list | None:
    """Get data from cache if valid"""
    import json
    from datetime import datetime, timedelta
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT data, timestamp FROM api_cache WHERE key = ?", (key,))
        row = cursor.fetchone()
        
        if row:
            # Check expiry
            # timestamp is string in SQLite usually
            cached_time = datetime.fromisoformat(row["timestamp"])
            if datetime.now() - cached_time < timedelta(seconds=ttl_seconds):
                try:
                    return json.loads(row["data"])
                except:
                    return None
            else:
                # Expired
                return None
    return None

def set_cached_data(key: str, data: dict | list):
    """Save data to cache"""
    import json
    from datetime import datetime
    
    json_data = json.dumps(data)
    now = datetime.now().isoformat()
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT OR REPLACE INTO api_cache (key, data, timestamp)
        VALUES (?, ?, ?)
        """, (key, json_data, now))
        conn.commit()

def get_team_members_from_db(owner_username: str) -> list:
    """Fetch all members for a team owner"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT username, name, team_owner, status FROM members WHERE team_owner = ?", (owner_username,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

