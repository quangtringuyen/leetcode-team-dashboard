
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
    type_ = "system_info" 
    recipient = "all"
    status = "sent"
    created_at = datetime.now().isoformat()
    
    try:
        # Correct Schema: id, type, title, message, recipient, status, metadata, created_at, sent_at
        cursor.execute("""
            INSERT INTO notifications (type, title, message, recipient, status, created_at) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (type_, title, message, recipient, status, created_at))
        conn.commit()
        logger.info("Notification added successfully.")
    except Exception as e:
        logger.error(f"Error adding notification: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    add_system_notification()
