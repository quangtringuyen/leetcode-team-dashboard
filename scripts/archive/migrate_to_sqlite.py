import os
import sys
import logging
from datetime import datetime

# Add parent directory to path to import backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.config import settings
from backend.core.storage import read_json
from backend.core.database import init_db, get_db_connection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_data():
    """Migrate data from JSON files to SQLite"""
    logger.info("Starting migration to SQLite...")
    
    # Initialize DB
    init_db()
    
    # 1. Migrate Members
    members_data = read_json(settings.MEMBERS_FILE, default={})
    count_members = 0
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        for owner, members in members_data.items():
            for member in members:
                try:
                    cursor.execute("""
                    INSERT OR REPLACE INTO members (username, name, avatar, team_owner)
                    VALUES (?, ?, ?, ?)
                    """, (
                        member["username"],
                        member.get("name", member["username"]),
                        member.get("avatar"),
                        owner
                    ))
                    count_members += 1
                except Exception as e:
                    logger.error(f"Error migrating member {member['username']}: {e}")
        
        conn.commit()
    logger.info(f"Migrated {count_members} members")

    # 2. Migrate History
    history_data = read_json(settings.HISTORY_FILE, default={})
    count_snapshots = 0
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # History structure: {owner: {username: [snapshots]}}
        for owner, user_history in history_data.items():
            for username, snapshots in user_history.items():
                for snapshot in snapshots:
                    try:
                        # Handle key variations (Easy vs easy)
                        easy = snapshot.get("easy", snapshot.get("Easy", 0))
                        medium = snapshot.get("medium", snapshot.get("Medium", 0))
                        hard = snapshot.get("hard", snapshot.get("Hard", 0))
                        
                        cursor.execute("""
                        INSERT OR REPLACE INTO snapshots 
                        (username, week_start, total_solved, easy, medium, hard, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            username,
                            snapshot.get("week_start"),
                            snapshot.get("totalSolved", 0),
                            int(easy),
                            int(medium),
                            int(hard),
                            snapshot.get("timestamp", datetime.utcnow().isoformat())
                        ))
                        count_snapshots += 1
                    except Exception as e:
                        logger.error(f"Error migrating snapshot for {username}: {e}")
        
        conn.commit()
    logger.info(f"Migrated {count_snapshots} snapshots")
    logger.info("Migration completed successfully! 🎉")

if __name__ == "__main__":
    migrate_data()
