import sys
import os
import json
import sqlite3
import logging

# Ensure root directory is in path
sys.path.append(os.getcwd())

from backend.core.database import DB_PATH, init_db, get_db_connection
from backend.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate():
    logger.info(f"Starting migration to database: {DB_PATH}")
    
    # Initialize DB (creates tables and columns)
    init_db()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Migrate Members
    members_file = settings.MEMBERS_FILE
    if os.path.exists(members_file):
        logger.info(f"Reading members from {members_file}")
        try:
            with open(members_file, 'r') as f:
                all_members = json.load(f)
            
            count = 0
            for owner, members in all_members.items():
                for m in members:
                    username = m.get("username")
                    if not username: continue
                    name = m.get("name", username)
                    status = m.get("status", "active")
                    avatar = m.get("avatar")
                    
                    try:
                        cursor.execute("""
                            INSERT INTO members (username, name, avatar, team_owner, status)
                            VALUES (?, ?, ?, ?, ?)
                            ON CONFLICT(username) DO UPDATE SET
                            name=excluded.name,
                            avatar=excluded.avatar,
                            team_owner=excluded.team_owner,
                            status=excluded.status
                        """, (username, name, avatar, owner, status))
                        count += 1
                    except Exception as e:
                        logger.error(f"Error inserting member {username}: {e}")

            conn.commit()
            logger.info(f"Successfully migrated {count} members.")
            
        except Exception as e:
            logger.error(f"Error migrating members: {e}")
    else:
        logger.warning(f"Members file not found: {members_file}")

    # 2. Migrate History
    history_file = settings.HISTORY_FILE
    if os.path.exists(history_file):
        logger.info(f"Reading history from {history_file}")
        try:
            with open(history_file, 'r') as f:
                all_history = json.load(f)
            
            snap_count = 0
            for owner, members_history in all_history.items():
                for username, snapshots in members_history.items():
                    for s in snapshots:
                        week_start = s.get("week_start")
                        if not week_start: continue
                        
                        try:
                            cursor.execute("""
                                INSERT INTO snapshots (username, week_start, total_solved, easy, medium, hard, timestamp)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                                ON CONFLICT(username, week_start) DO UPDATE SET
                                total_solved=excluded.total_solved,
                                easy=excluded.easy,
                                medium=excluded.medium,
                                hard=excluded.hard,
                                timestamp=excluded.timestamp
                            """, (
                                username,
                                week_start,
                                s.get("totalSolved", 0),
                                s.get("easy", 0),
                                s.get("medium", 0),
                                s.get("hard", 0),
                                s.get("timestamp")
                            ))
                            snap_count += 1
                        except Exception as snapshot_err:
                            # If structure is different, log it
                            logger.warn(f"Failed to insert snapshot for {username} week {week_start}: {snapshot_err}")
                            
            conn.commit()
            logger.info(f"Successfully migrated {snap_count} snapshots.")
            
        except Exception as e:
            logger.error(f"Error migrating history: {e}")
    else:
        logger.warning(f"History file not found: {history_file}")

    conn.close()
    logger.info("Migration completed.")

if __name__ == "__main__":
    migrate()
