import os
import json
import sqlite3
import logging
import sys

# Add project root to path
# __file__ is backend/fix_missing_members.py
# parent is backend/
# grandparent is root (leetcode-dashboard)
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

# If running on NAS, settings might need manual adjustment or rely on .env finding
# We assume .env is in project root
os.chdir(project_root)

from backend.core.database import DB_PATH
from backend.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TARGET_OWNER = "leetcodescamp"

def fix_migration():
    logger.info(f"Starting recovery migration to {DB_PATH}")
    
    if not os.path.exists(DB_PATH):
        logger.error(f"Database file not found at {DB_PATH}!")
        return

    # Connect to DB
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Helper to insert/update member
    def upsert_member(username, name, avatar, status="active"):
        if not username: return False
        try:
            cursor.execute("""
                INSERT INTO members (username, name, avatar, team_owner, status)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(username) DO UPDATE SET
                team_owner=excluded.team_owner,
                status=excluded.status
            """, (username, name, avatar, TARGET_OWNER, status))
            return True
        except Exception as e:
            logger.error(f"Failed to upsert {username}: {e}")
            return False

    total_added = 0
    
    # 1. Process members.json
    fpath = os.path.join(settings.DATA_DIR, settings.MEMBERS_FILE)
    if os.path.exists(fpath):
        logger.info(f"Processing {fpath}...")
        try:
            with open(fpath, 'r') as f:
                content = json.load(f)
            
            flat_list = []
            if isinstance(content, dict):
                for _, members in content.items():
                    flat_list.extend(members)
            elif isinstance(content, list):
                flat_list = content
                
            for m in flat_list:
                if upsert_member(m.get("username"), m.get("name"), m.get("avatar"), m.get("status", "active")):
                    total_added += 1
        except Exception as e:
            logger.error(f"Error processing members.json: {e}")
    else:
        logger.warning(f"members.json not found at {fpath}")

    # 2. Process last_state.json (Crucial for gimmealeadtocode)
    fpath = os.path.join(settings.DATA_DIR, "last_state.json")
    if os.path.exists(fpath):
        logger.info(f"Processing {fpath}...")
        try:
            with open(fpath, 'r') as f:
                content = json.load(f)
            
            if isinstance(content, dict):
                for owner, members_data in content.items():
                    logger.info(f"  Found owner key in last_state: {owner}")
                    if isinstance(members_data, dict):
                        for username, data in members_data.items():
                            name = data.get("realName") or data.get("name") or username
                            avatar = data.get("avatar")
                            if upsert_member(username, name, avatar):
                                total_added += 1
                                if username == "gimmealeadtocode":
                                    logger.info("!!! FOUND AND ADDED gimmealeadtocode FROM last_state.json !!!")
                                    # Double check immediate read
                                    cursor.execute("SELECT * FROM members WHERE username='gimmealeadtocode'")
                                    logger.info(f"Intermediate check: {cursor.fetchone()}")
        except Exception as e:
            logger.error(f"Error processing last_state.json: {e}")
    else:
        logger.warning(f"last_state.json not found at {fpath}")

    # 3. Recover History (optional but good)
    history_file = os.path.join(settings.DATA_DIR, settings.HISTORY_FILE)
    if os.path.exists(history_file):
        logger.info(f"Processing {history_file}...")
        try:
            with open(history_file, 'r') as f:
                content = json.load(f)
            
            snap_count = 0
            if isinstance(content, dict):
                for owner, members_history in content.items():
                    for username, snapshots in members_history.items():
                        # Ensure member exists first - crucial if history exists but member deleted
                        upsert_member(username, username, None)
                        
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
            logger.info(f"Verified/Recovered {snap_count} snapshots.")
        except Exception as e:
            logger.error(f"Error recovering history: {e}")

    conn.commit()
    logger.info(f"Total processed/upserted members: {total_added}")
    
    # Force owner
    cursor.execute("UPDATE members SET team_owner = ?", (TARGET_OWNER,))
    conn.commit()
    
    # Verify result
    cursor.execute("SELECT count(*) FROM members")
    count = cursor.fetchone()[0]
    logger.info(f"Total members in DB now: {count}")
    
    cursor.execute("SELECT * FROM members WHERE username='gimmealeadtocode'")
    jadie = cursor.fetchone()
    if jadie:
        logger.info(f"Verification: gimmealeadtocode is in DB: {jadie}")
    else:
        logger.error("Verification: gimmealeadtocode is STILL NOT in DB!")

    conn.close()

if __name__ == "__main__":
    fix_migration()
