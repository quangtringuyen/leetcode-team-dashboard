#!/usr/bin/env python3
"""
Migration script to update snapshot schedule time from 00:00 to 07:30
This fixes the timezone mismatch issue with LeetCode's UTC reset time.

Run this script to update existing databases.
"""

import os
import sys
import sqlite3
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.config import settings
from backend.core.database import get_db_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def update_snapshot_time():
    """Update the snapshot schedule time to 07:30"""
    logger.info("=" * 80)
    logger.info("Updating Snapshot Schedule Time")
    logger.info("=" * 80)
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Check current value
        cursor.execute("SELECT value FROM system_settings WHERE key = 'snapshot_schedule_time'")
        row = cursor.fetchone()
        
        if row:
            current_value = row['value']
            logger.info(f"Current snapshot time: {current_value}")
        else:
            logger.info("No existing snapshot time setting found")
            current_value = None
        
        # Update to 07:30
        cursor.execute("""
            INSERT OR REPLACE INTO system_settings (key, value, updated_at)
            VALUES ('snapshot_schedule_time', '"07:30"', CURRENT_TIMESTAMP)
        """)
        
        conn.commit()
        
        logger.info("✅ Updated snapshot time to 07:30 GMT+7")
        logger.info("")
        logger.info("Why 07:30?")
        logger.info("  - LeetCode resets at 00:00 UTC")
        logger.info("  - 00:00 UTC = 07:00 GMT+7")
        logger.info("  - 07:30 GMT+7 gives a 30-minute buffer")
        logger.info("  - This ensures all problems solved on Sunday are captured")
        logger.info("")
        logger.info("⚠️  IMPORTANT: Restart the scheduler container for changes to take effect:")
        logger.info("   docker-compose restart scheduler")
        logger.info("=" * 80)

if __name__ == "__main__":
    try:
        update_snapshot_time()
    except Exception as e:
        logger.error(f"Error updating snapshot time: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
