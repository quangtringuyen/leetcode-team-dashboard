
import os
import sys
import logging
import sqlite3

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from backend.core.database import DB_PATH
from backend.utils.leetcodeapi import fetch_user_data
from backend.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def force_update(username):
    logger.info(f"Fetching data for {username}...")
    data = fetch_user_data(username)
    
    if not data:
        logger.error(f"Could not fetch data for {username}")
        return

    logger.info(f"Got data: {data}")
    
    # Update DB
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # We don't have a direct 'update member stats' function in DB that separates stats from profile
    # But usually we rely on snapshots or just cache. 
    # Wait, the analytics endpoints often fetch live data OR use snapshots. 
    # The 'Difficulty Distribution' often uses history.
    
    # Let's check how analytics.py gets data.
    # get_difficulty_trends uses get_user_history_from_db.
    # So if this user has NO history (snapshots), they won't show up in trends.
    
    # We need to create at least ONE snapshot for them to appear in history-based charts.
    
    from datetime import date, timedelta
    today = date.today()
    week_start = (today - timedelta(days=today.weekday())).isoformat()
    
    logger.info(f"Inserting pseudo-snapshot for {week_start}...")
    
    try:
        cursor.execute("""
            INSERT OR IGNORE INTO snapshots (username, week_start, total_solved, easy, medium, hard, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            username, 
            week_start,
            data.get("totalSolved", 0),
            data.get("easy", 0),
            data.get("medium", 0),
            data.get("hard", 0),
            today.isoformat()
        ))
        conn.commit()
        logger.info("Snapshot inserted/updated.")
        
    except Exception as e:
        logger.error(f"Error updating DB: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    force_update("gimmealeadtocode")
