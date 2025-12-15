#!/usr/bin/env python3
"""
Delete all Dec 8, 2025 snapshots that were incorrectly recorded on Dec 10.

All Dec 8 snapshots were taken on Dec 10 at 15:08, which means they include
problems solved on Dec 8, 9, and 10. This makes them incorrect baselines.

Solution: Delete all Dec 8 snapshots. Week-over-week will use Dec 1 snapshots
as the baseline instead, which is correct.
"""

import os
import sys
import logging
from datetime import datetime
from shutil import copy2

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.config import settings
from backend.core.database import get_db_connection, DB_PATH

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_backup():
    """Create a backup before deletion"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(settings.DATA_DIR, "../backups")
    os.makedirs(backup_dir, exist_ok=True)
    
    backup_path = os.path.join(backup_dir, f"leetcode_before_delete_dec8_{timestamp}.db")
    
    try:
        copy2(DB_PATH, backup_path)
        logger.info(f"✅ Backup created: {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"❌ Failed to create backup: {e}")
        raise

def show_snapshots():
    """Show all Dec 8 snapshots that will be deleted"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT username, total_solved, timestamp
            FROM snapshots
            WHERE week_start = '2025-12-08'
            ORDER BY username
        """)
        
        snapshots = cursor.fetchall()
        
        logger.info("\n📊 Dec 8 Snapshots to be Deleted:")
        logger.info("=" * 80)
        for snap in snapshots:
            logger.info(f"  {snap['username']:20s} | Total: {snap['total_solved']:3d} | "
                       f"Recorded: {snap['timestamp']}")
        logger.info("=" * 80)
        logger.info(f"Total: {len(snapshots)} snapshots")
        
        return len(snapshots)

def delete_dec8_snapshots():
    """Delete all Dec 8 snapshots"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM snapshots WHERE week_start = '2025-12-08'")
        deleted_count = cursor.rowcount
        
        # Clear API cache
        cursor.execute("DELETE FROM api_cache")
        cache_count = cursor.rowcount
        
        conn.commit()
        
        logger.info(f"\n✅ Deleted {deleted_count} Dec 8 snapshot(s)")
        logger.info(f"✅ Cleared {cache_count} cache entry(ies)")
        
        return deleted_count

def main():
    """Main function"""
    logger.info("=" * 80)
    logger.info("Delete Incorrect Dec 8 Snapshots")
    logger.info("=" * 80)
    
    # Step 1: Show what will be deleted
    logger.info("\n📋 Step 1: Snapshots to Delete")
    count = show_snapshots()
    
    # Step 2: Create backup
    logger.info("\n📦 Step 2: Creating Backup")
    try:
        backup_path = create_backup()
    except Exception as e:
        logger.error("❌ Backup failed. Aborting.")
        return 1
    
    # Step 3: Explain the issue
    logger.info("\n⚠️  Step 3: Why Delete?")
    logger.info("  Problem:")
    logger.info("    - All Dec 8 snapshots were recorded on Dec 10 at 15:08")
    logger.info("    - They include problems from Dec 8, 9, and 10")
    logger.info("    - This makes them incorrect baselines")
    logger.info("")
    logger.info("  Solution:")
    logger.info("    - Delete all Dec 8 snapshots")
    logger.info("    - Week-over-week will use Dec 1 snapshots instead")
    logger.info("    - This gives correct week-over-week calculations")
    logger.info("")
    logger.info("  Impact:")
    logger.info("    - Week-over-week will show changes from Dec 1 to current")
    logger.info("    - This is accurate since Dec 8 snapshots were wrong anyway")
    
    # Step 4: Confirm
    logger.info(f"\n⚠️  Step 4: Confirmation")
    logger.info(f"  This will delete {count} Dec 8 snapshot(s)")
    logger.info(f"  Backup saved at: {backup_path}")
    
    response = input("\nProceed with deletion? (yes/no): ").strip().lower()
    
    if response != 'yes':
        logger.info("❌ Operation cancelled")
        return 0
    
    # Step 5: Delete
    logger.info("\n🗑️  Step 5: Deleting Snapshots")
    deleted = delete_dec8_snapshots()
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("✅ DELETION COMPLETED SUCCESSFULLY")
    logger.info("=" * 80)
    logger.info(f"\n📊 Summary:")
    logger.info(f"  - Deleted: {deleted} Dec 8 snapshot(s)")
    logger.info(f"  - Backup: {backup_path}")
    logger.info(f"\n💡 Next Steps:")
    logger.info(f"  1. Refresh the dashboard")
    logger.info(f"  2. Week-over-week will now compare with Dec 1 snapshots")
    logger.info(f"  3. Future snapshots will run at 07:30 Monday (correct time)")
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
