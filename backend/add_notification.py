
import sqlite3
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = "/app/data/leetcode.db"

def add_system_notification():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    title = "System Restored"
    message = "Historical data and member profiles have been successfully restored. Welcome back!"
    type_ = "info" # info, success, warning, error
    timestamp = datetime.now().isoformat()
    
    try:
        # Check if notifications table exists (it should)
        cursor.execute("INSERT INTO notifications (title, message, type, timestamp, read) VALUES (?, ?, ?, ?, ?)", 
                       (title, message, type_, timestamp, 0))
        conn.commit()
        logger.info("Notification added successfully.")
    except Exception as e:
        logger.error(f"Error adding notification: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    add_system_notification()
