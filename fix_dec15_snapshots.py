#!/usr/bin/env python3
"""
Reconstruct Dec 15 snapshots to represent the state at END of Dec 14.

Current Dec 15 snapshots were taken at 14:15 Vietnam time (07:15 UTC),
which includes problems solved on Dec 15 morning. They should represent
the state at the end of Dec 14 (before any Dec 15 problems).

Formula: Dec 15 = Dec 8 snapshot + problems from Dec 8-14
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
from backend.utils.leetcodeapi import fetch_recent_submissions

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
    
    backup_path = os.path.join(backup_dir, f"leetcode_before_fix_dec15_{timestamp}.db")
    
    try:
        copy2(DB_PATH, backup_path)
        logger.info(f"✅ Backup created: {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"❌ Failed to create backup: {e}")
        raise

def count_problems_in_range(username, start_day, end_day):
    """Count problems solved in a date range (Dec 8-14, 2025)"""
    try:
        submissions = fetch_recent_submissions(username, limit=100)
        
        count = 0
        problems_found = []
        
        for sub in submissions:
            ts = int(sub.get('timestamp', 0))
            if ts > 0:
                dt = datetime.fromtimestamp(ts)
                # Check if in Dec 2025 and within day range
                if (dt.year == 2025 and dt.month == 12 and start_day <= dt.day <= end_day):
                    count += 1
                    problems_found.append({
                        'title': sub.get('title'),
                        'date': dt.strftime('%Y-%m-%d'),
                        'time': dt.strftime('%H:%M:%S')
                    })
        
        return count, problems_found
    except Exception as e:
        logger.error(f"Error fetching submissions for {username}: {e}")
        return 0, []

def reconstruct_dec15_snapshots():
    """Reconstruct Dec 15 snapshots"""
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Get all Dec 8 snapshots (which should now be correct)
        cursor.execute("""
            SELECT username, total_solved, easy, medium, hard
            FROM snapshots
            WHERE week_start = '2025-12-08'
            ORDER BY username
        """)
        
        dec8_snapshots = cursor.fetchall()
        
        if not dec8_snapshots:
            logger.error("❌ No Dec 8 snapshots found!")
            logger.error("   Please run reconstruct_dec8_snapshots.py first!")
            return []
        
        logger.info(f"\n📊 Found {len(dec8_snapshots)} Dec 8 snapshots")
        logger.info("=" * 100)
        
        reconstructed = []
        
        # Process each member
        for snap in dec8_snapshots:
            username = snap['username']
            dec8_total = snap['total_solved']
            
            logger.info(f"\n🔍 Processing {username}...")
            logger.info(f"   Dec 8 baseline: {dec8_total}")
            
            # Count problems from Dec 8-14
            count_dec8_14, problems = count_problems_in_range(username, 8, 14)
            
            if problems:
                logger.info(f"   Problems Dec 8-14: {count_dec8_14}")
                for p in problems[:5]:  # Show first 5
                    logger.info(f"     - {p['date']} {p['time']}: {p['title']}")
                if len(problems) > 5:
                    logger.info(f"     ... and {len(problems) - 5} more")
            else:
                logger.info(f"   Problems Dec 8-14: 0")
            
            # Calculate Dec 15 value (state at end of Dec 14)
            dec15_total = dec8_total + count_dec8_14
            
            reconstructed.append({
                'username': username,
                'dec8_total': dec8_total,
                'added': count_dec8_14,
                'dec15_total': dec15_total,
                'easy': snap['easy'],
                'medium': snap['medium'],
                'hard': snap['hard']
            })
            
            logger.info(f"   ✅ Dec 15 estimate: {dec15_total} ({dec8_total} + {count_dec8_14})")
        
        logger.info("\n" + "=" * 100)
        
        return reconstructed

def update_dec15_snapshots(reconstructed):
    """Update Dec 15 snapshots with correct values"""
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        updated = 0
        
        for data in reconstructed:
            try:
                cursor.execute("""
                    UPDATE snapshots
                    SET total_solved = ?,
                        timestamp = ?
                    WHERE username = ? AND week_start = '2025-12-15'
                """, (
                    data['dec15_total'],
                    datetime.utcnow().isoformat(),
                    data['username']
                ))
                
                if cursor.rowcount > 0:
                    updated += 1
                else:
                    logger.warning(f"⚠️  No Dec 15 snapshot found for {data['username']}")
            except Exception as e:
                logger.error(f"Error updating snapshot for {data['username']}: {e}")
        
        # Clear API cache
        cursor.execute("DELETE FROM api_cache")
        
        conn.commit()
        
        logger.info(f"\n✅ Updated {updated} Dec 15 snapshots")
        logger.info("✅ Cleared API cache")
        
        return updated

def main():
    """Main function"""
    logger.info("=" * 100)
    logger.info("Fix Dec 15 Snapshots")
    logger.info("=" * 100)
    
    # Step 1: Create backup
    logger.info("\n📦 Step 1: Creating Backup")
    try:
        backup_path = create_backup()
    except Exception as e:
        logger.error("❌ Backup failed. Aborting.")
        return 1
    
    # Step 2: Explain the issue
    logger.info("\n📋 Step 2: The Problem")
    logger.info("  Current Dec 15 snapshots were taken at 14:15 Vietnam time")
    logger.info("  This includes problems solved on Dec 15 morning (07:00-14:15)")
    logger.info("  They should represent state at END of Dec 14")
    logger.info("")
    logger.info("  Solution: Dec 15 = Dec 8 snapshot + problems from Dec 8-14")
    
    # Step 3: Confirm
    response = input("\nProceed with reconstruction? (yes/no): ").strip().lower()
    
    if response != 'yes':
        logger.info("❌ Operation cancelled")
        return 0
    
    # Step 4: Reconstruct
    logger.info("\n🔧 Step 3: Reconstructing Dec 15 Snapshots")
    reconstructed = reconstruct_dec15_snapshots()
    
    if not reconstructed:
        logger.error("❌ Reconstruction failed")
        return 1
    
    # Step 5: Show summary
    logger.info("\n📊 Step 4: Summary")
    logger.info("=" * 100)
    logger.info(f"{'Username':<20} | {'Dec 8':<8} | {'Added':<8} | {'Dec 15 (Fixed)':<15}")
    logger.info("-" * 100)
    for data in reconstructed:
        logger.info(f"{data['username']:<20} | {data['dec8_total']:<8} | "
                   f"{data['added']:<8} | {data['dec15_total']:<15}")
    logger.info("=" * 100)
    
    # Step 6: Confirm update
    response = input("\nUpdate Dec 15 snapshots with these values? (yes/no): ").strip().lower()
    
    if response != 'yes':
        logger.info("❌ Operation cancelled")
        return 0
    
    # Step 7: Update
    logger.info("\n💾 Step 5: Updating Dec 15 Snapshots")
    updated = update_dec15_snapshots(reconstructed)
    
    # Summary
    logger.info("\n" + "=" * 100)
    logger.info("✅ FIX COMPLETED SUCCESSFULLY")
    logger.info("=" * 100)
    logger.info(f"\n📊 Summary:")
    logger.info(f"  - Reconstructed: {len(reconstructed)} members")
    logger.info(f"  - Updated: {updated} Dec 15 snapshots")
    logger.info(f"  - Backup: {backup_path}")
    logger.info(f"\n💡 Next Steps:")
    logger.info(f"  1. Refresh the dashboard")
    logger.info(f"  2. Dec 15 snapshots now represent state at END of Dec 14")
    logger.info(f"  3. Week-over-week will show correct Dec 8 → Dec 15 changes")
    logger.info("=" * 100)
    
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
