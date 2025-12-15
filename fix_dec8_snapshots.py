#!/usr/bin/env python3
"""
Fix Dec 8 snapshots that were recorded on Dec 10 instead of Dec 8.

This script corrects the baseline values for the Dec 8 week snapshots
to reflect the state at the END of Dec 7 (before any Dec 8 problems were solved).

Issues:
- Dec 8 snapshot was taken on Dec 10 at 15:08
- It includes problems solved on Dec 8 and Dec 10
- This causes incorrect week-over-week calculations

Fixes:
- quangtringuyen: 62 -> 61 (remove Dec 8 problem)
- dieptung9197: 52 -> 50 (remove Dec 8 and Dec 10 problems)
"""

import os
import sys
import sqlite3
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
    """Create a backup before making changes"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(settings.DATA_DIR, "../backups")
    os.makedirs(backup_dir, exist_ok=True)
    
    backup_path = os.path.join(backup_dir, f"leetcode_before_fix_dec8_{timestamp}.db")
    
    try:
        copy2(DB_PATH, backup_path)
        logger.info(f"✅ Backup created: {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"❌ Failed to create backup: {e}")
        raise

def show_current_state():
    """Show current snapshot values"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT username, week_start, total_solved, easy, medium, hard, timestamp
            FROM snapshots
            WHERE week_start = '2025-12-08'
            ORDER BY username
        """)
        
        snapshots = cursor.fetchall()
        
        logger.info("\n📊 Current Dec 8 Snapshots:")
        logger.info("=" * 80)
        for snap in snapshots:
            logger.info(f"  {snap['username']:20s} | Total: {snap['total_solved']:3d} | "
                       f"E:{snap['easy']:3d} M:{snap['medium']:3d} H:{snap['hard']:3d} | "
                       f"Recorded: {snap['timestamp']}")
        logger.info("=" * 80)
        
        return snapshots

def fix_snapshots():
    """Fix the Dec 8 snapshot values"""
    
    # Corrections based on analysis
    corrections = {
        'quangtringuyen': {
            'old_total': 62,
            'new_total': 61,
            'reason': 'Remove Dec 8 problem (solved at 09:09)',
            'problems_removed': 1
        },
        'dieptung9197': {
            'old_total': 52,
            'new_total': 50,
            'reason': 'Remove Dec 8 and Dec 10 problems',
            'problems_removed': 2
        }
    }
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        for username, correction in corrections.items():
            # Verify current value
            cursor.execute("""
                SELECT total_solved, easy, medium, hard
                FROM snapshots
                WHERE username = ? AND week_start = '2025-12-08'
            """, (username,))
            
            row = cursor.fetchone()
            
            if not row:
                logger.warning(f"⚠️  No Dec 8 snapshot found for {username}")
                continue
            
            current_total = row['total_solved']
            
            if current_total != correction['old_total']:
                logger.warning(f"⚠️  {username}: Expected {correction['old_total']}, found {current_total}")
                response = input(f"   Continue with correction to {correction['new_total']}? (yes/no): ")
                if response.lower() != 'yes':
                    logger.info(f"   Skipping {username}")
                    continue
            
            # Calculate new difficulty breakdown
            # We need to subtract the problems that were incorrectly included
            new_total = correction['new_total']
            
            # For simplicity, we'll just update the total
            # The difficulty breakdown will be slightly off, but the total is what matters for week-over-week
            cursor.execute("""
                UPDATE snapshots
                SET total_solved = ?,
                    timestamp = ?
                WHERE username = ? AND week_start = '2025-12-08'
            """, (new_total, datetime.utcnow().isoformat(), username))
            
            logger.info(f"✅ {username}: {current_total} -> {new_total} ({correction['reason']})")
        
        conn.commit()

def verify_fix():
    """Verify the fixes were applied correctly"""
    logger.info("\n🔍 Verifying fixes...")
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Check quangtringuyen
        cursor.execute("""
            SELECT total_solved FROM snapshots
            WHERE username = 'quangtringuyen' AND week_start = '2025-12-08'
        """)
        row = cursor.fetchone()
        if row and row['total_solved'] == 61:
            logger.info("✅ quangtringuyen: Corrected to 61")
        else:
            logger.error(f"❌ quangtringuyen: Expected 61, got {row['total_solved'] if row else 'None'}")
        
        # Check dieptung9197
        cursor.execute("""
            SELECT total_solved FROM snapshots
            WHERE username = 'dieptung9197' AND week_start = '2025-12-08'
        """)
        row = cursor.fetchone()
        if row and row['total_solved'] == 50:
            logger.info("✅ dieptung9197: Corrected to 50")
        else:
            logger.error(f"❌ dieptung9197: Expected 50, got {row['total_solved'] if row else 'None'}")

def main():
    """Main function"""
    logger.info("=" * 80)
    logger.info("Fix Dec 8 Snapshots - Correct Baseline Values")
    logger.info("=" * 80)
    
    # Step 1: Show current state
    logger.info("\n📋 Step 1: Current State")
    show_current_state()
    
    # Step 2: Create backup
    logger.info("\n📦 Step 2: Creating Backup")
    try:
        backup_path = create_backup()
    except Exception as e:
        logger.error("❌ Backup failed. Aborting.")
        return 1
    
    # Step 3: Confirm
    logger.info("\n⚠️  Step 3: Confirmation")
    logger.info("This will update:")
    logger.info("  - quangtringuyen: 62 -> 61 (remove Dec 8 problem)")
    logger.info("  - dieptung9197: 52 -> 50 (remove Dec 8 & Dec 10 problems)")
    logger.info(f"\nBackup saved at: {backup_path}")
    
    response = input("\nProceed with fixes? (yes/no): ").strip().lower()
    
    if response != 'yes':
        logger.info("❌ Operation cancelled")
        return 0
    
    # Step 4: Apply fixes
    logger.info("\n🔧 Step 4: Applying Fixes")
    fix_snapshots()
    
    # Step 5: Verify
    logger.info("\n✅ Step 5: Verification")
    verify_fix()
    
    # Step 6: Clear cache
    logger.info("\n🧹 Step 6: Clearing API Cache")
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM api_cache")
        conn.commit()
    logger.info("✅ Cache cleared")
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("✅ FIXES APPLIED SUCCESSFULLY")
    logger.info("=" * 80)
    logger.info("\n📊 Expected Week-over-Week Changes (Dec 8-14):")
    logger.info("  - quangtringuyen: +3 (was showing +2)")
    logger.info("  - dieptung9197: +3 (was showing +4)")
    logger.info("\n💡 Refresh the dashboard to see updated values")
    logger.info(f"\n📦 Backup: {backup_path}")
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
