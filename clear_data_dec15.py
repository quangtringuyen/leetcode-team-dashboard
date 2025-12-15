#!/usr/bin/env python3
"""
Script to clear data for December 15, 2025
This script will:
1. Create a backup of the database
2. Delete snapshots for the specific date
3. Clear API cache to ensure fresh data
4. Provide a summary of deleted records

Note: Notifications are preserved and NOT deleted.
"""

import os
import sys
import sqlite3
import logging
from datetime import datetime
from shutil import copy2

# Add parent directory to path to import backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.config import settings
from backend.core.database import get_db_connection, DB_PATH

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Target date to clear
TARGET_DATE = "2024-12-15"  # Format: YYYY-MM-DD

def create_backup():
    """Create a backup of the database before clearing data"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(settings.DATA_DIR, "../backups")
    os.makedirs(backup_dir, exist_ok=True)
    
    backup_path = os.path.join(backup_dir, f"leetcode_before_clear_dec15_{timestamp}.db")
    
    try:
        copy2(DB_PATH, backup_path)
        logger.info(f"✅ Backup created: {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"❌ Failed to create backup: {e}")
        raise

def get_snapshot_count_for_date(date_str: str) -> int:
    """Get count of snapshots for a specific date"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Check for snapshots with week_start matching the date
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM snapshots 
            WHERE week_start = ? OR DATE(timestamp) = ?
        """, (date_str, date_str))
        
        result = cursor.fetchone()
        return result['count'] if result else 0



def list_snapshots_for_date(date_str: str):
    """List all snapshots that will be deleted"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, username, week_start, total_solved, easy, medium, hard, timestamp
            FROM snapshots 
            WHERE week_start = ? OR DATE(timestamp) = ?
            ORDER BY username, timestamp
        """, (date_str, date_str))
        
        snapshots = cursor.fetchall()
        
        if snapshots:
            logger.info(f"\n📊 Found {len(snapshots)} snapshot(s) for {date_str}:")
            logger.info("-" * 80)
            for snap in snapshots:
                logger.info(f"  ID: {snap['id']:4d} | User: {snap['username']:20s} | "
                          f"Week: {snap['week_start']:12s} | "
                          f"Solved: {snap['total_solved']:4d} (E:{snap['easy']:3d} M:{snap['medium']:3d} H:{snap['hard']:3d}) | "
                          f"Time: {snap['timestamp']}")
            logger.info("-" * 80)
        else:
            logger.info(f"ℹ️  No snapshots found for {date_str}")
        
        return snapshots

def delete_snapshots_for_date(date_str: str) -> int:
    """Delete snapshots for a specific date"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM snapshots 
            WHERE week_start = ? OR DATE(timestamp) = ?
        """, (date_str, date_str))
        
        deleted_count = cursor.rowcount
        conn.commit()
        
        return deleted_count



def clear_api_cache():
    """Clear API cache to ensure fresh data"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM api_cache")
        deleted_count = cursor.rowcount
        conn.commit()
        return deleted_count

def main():
    """Main function to clear data for December 15, 2025"""
    logger.info("=" * 80)
    logger.info(f"🗑️  Data Clearing Script for {TARGET_DATE}")
    logger.info("=" * 80)
    
    # Step 1: Create backup
    logger.info("\n📦 Step 1: Creating backup...")
    try:
        backup_path = create_backup()
    except Exception as e:
        logger.error(f"❌ Backup failed. Aborting operation for safety.")
        return 1
    
    # Step 2: Check what will be deleted
    logger.info(f"\n🔍 Step 2: Checking data for {TARGET_DATE}...")
    snapshot_count = get_snapshot_count_for_date(TARGET_DATE)
    
    logger.info(f"  - Snapshots to delete: {snapshot_count}")
    logger.info(f"  - Notifications: PRESERVED (not deleted)")
    
    if snapshot_count == 0:
        logger.info(f"\n✅ No snapshots found for {TARGET_DATE}. Nothing to delete.")
        return 0
    
    # Step 3: List snapshots
    logger.info(f"\n📋 Step 3: Listing snapshots...")
    list_snapshots_for_date(TARGET_DATE)
    
    # Step 4: Confirm deletion
    logger.info(f"\n⚠️  Step 4: Confirmation")
    logger.info(f"  This will delete:")
    logger.info(f"    - {snapshot_count} snapshot(s)")
    logger.info(f"    - Notifications: PRESERVED (not deleted)")
    logger.info(f"  Backup saved at: {backup_path}")
    
    response = input("\n  Proceed with deletion? (yes/no): ").strip().lower()
    
    if response != 'yes':
        logger.info("❌ Operation cancelled by user.")
        return 0
    
    # Step 5: Delete data
    logger.info(f"\n🗑️  Step 5: Deleting data...")
    
    deleted_snapshots = delete_snapshots_for_date(TARGET_DATE)
    logger.info(f"  ✅ Deleted {deleted_snapshots} snapshot(s)")
    logger.info(f"  ℹ️  Notifications preserved (not deleted)")
    
    # Step 6: Clear cache
    logger.info(f"\n🧹 Step 6: Clearing API cache...")
    deleted_cache = clear_api_cache()
    logger.info(f"  ✅ Cleared {deleted_cache} cache entry(ies)")
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("✅ OPERATION COMPLETED SUCCESSFULLY")
    logger.info("=" * 80)
    logger.info(f"📊 Summary:")
    logger.info(f"  - Snapshots deleted: {deleted_snapshots}")
    logger.info(f"  - Notifications: PRESERVED")
    logger.info(f"  - Cache entries cleared: {deleted_cache}")
    logger.info(f"  - Backup location: {backup_path}")
    logger.info("=" * 80)
    logger.info(f"\n💡 You can now record a new snapshot for {TARGET_DATE}")
    logger.info(f"   To restore the backup if needed, run:")
    logger.info(f"   cp {backup_path} {DB_PATH}")
    logger.info("=" * 80)
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        logger.info("\n\n❌ Operation cancelled by user (Ctrl+C)")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
