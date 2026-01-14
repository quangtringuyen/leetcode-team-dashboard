import os
import json
import sqlite3
import logging
import sys

# Ensure root directory is in path
sys.path.append(os.getcwd())

from backend.core.database import DB_PATH
from backend.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TARGET_OWNER = "leetcodescamp"

def fix_migration():
    logger.info(f"Starting recovery migration to {DB_PATH}")
    
    if not os.path.exists(DB_PATH):
        logger.error("Database file not found!")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Recover ALL members from JSOn
    members_file = os.path.join(settings.DATA_DIR, settings.MEMBERS_FILE)
    if os.path.exists(members_file):
        try:
            with open(members_file, 'r') as f:
                content = json.load(f)
            
            # handle both {owner: [members]} and [members] structures
            all_members_flat = []
            if isinstance(content, dict):
                for owner, members in content.items():
                    for m in members:
                        all_members_flat.append(m)
            elif isinstance(content, list):
                all_members_flat = content

            count = 0
            for m in all_members_flat:
                username = m.get("username")
                if not username: continue
                name = m.get("name", username)
                status = m.get("status", "active")
                avatar = m.get("avatar")
                
                cursor.execute("""
                    INSERT INTO members (username, name, avatar, team_owner, status)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(username) DO UPDATE SET
                    team_owner=excluded.team_owner,
                    status=excluded.status
                """, (username, name, avatar, TARGET_OWNER, status))
                count += 1

            conn.commit()
            logger.info(f"Verified/Recovered {count} members into owner '{TARGET_OWNER}'")

            # 1.5 Force any existing members to the target owner
            cursor.execute("UPDATE members SET team_owner = ?", (TARGET_OWNER,))
            conn.commit()
            logger.info(f"Forced all existing members to owner '{TARGET_OWNER}'")
            
        except Exception as e:
            logger.error(f"Error recovering members: {e}")

    # 2. Recover ALL history from JSON
    history_file = os.path.join(settings.DATA_DIR, settings.HISTORY_FILE)
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r') as f:
                content = json.load(f)
            
            snap_count = 0
            # Flatten history from all possible owners
            if isinstance(content, dict):
                for owner, members_history in content.items():
                    for username, snapshots in members_history.items():
                        for s in snapshots:
                            week_start = s.get("week_start")
                            if not week_start: continue
                            cursor.execute("""
                                INSERT OR IGNORE INTO snapshots (username, week_start, total_solved, easy, medium, hard, timestamp)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, (
                                username, week_start,
                                s.get("totalSolved", 0), s.get("easy", 0),
                                s.get("medium", 0), s.get("hard", 0),
                                s.get("timestamp")
                            ))
                            snap_count += 1
            
            conn.commit()
            logger.info(f"Verified/Recovered {snap_count} snapshots.")
            
        except Exception as e:
            logger.error(f"Error recovering history: {e}")

    # 3. Recover members from last_state.json (sometimes more up-to-date)
    last_state_file = os.path.join(settings.DATA_DIR, "last_state.json")
    if os.path.exists(last_state_file):
        try:
            with open(last_state_file, 'r') as f:
                content = json.load(f)
            
            added_count = 0
            # last_state.json is {owner: {username: data}}
            if isinstance(content, dict):
                for owner, members_data in content.items():
                    if not isinstance(members_data, dict): continue
                    for username, data in members_data.items():
                        name = data.get("realName") or data.get("name") or username
                        avatar = data.get("avatar")
                        
                        cursor.execute("""
                            INSERT INTO members (username, name, avatar, team_owner, status)
                            VALUES (?, ?, ?, ?, 'active')
                            ON CONFLICT(username) DO UPDATE SET
                            team_owner=excluded.team_owner
                        """, (username, name, avatar, TARGET_OWNER))
                        added_count += 1
            
            conn.commit()
            logger.info(f"Verified/Recovered {added_count} members from last_state.json into owner '{TARGET_OWNER}'")
            
        except Exception as e:
            logger.error(f"Error recovering from last_state: {e}")

    conn.close()
    logger.info("Recovery completed.")

if __name__ == "__main__":
    fix_migration()
