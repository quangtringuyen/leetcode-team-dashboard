#!/usr/bin/env python3
"""
Reconstruct Dec 8 snapshots by calculating: Dec 1 snapshot + problems from Dec 1-7

Since the original Dec 8 snapshots were taken at the wrong time (Dec 10),
we can reconstruct them by:
1. Taking the Dec 1 snapshot value (correct baseline)
2. Counting problems solved from Dec 1-7
3. Creating new Dec 8 snapshots with the calculated values

Note: This is an estimate based on recent submissions from LeetCode API.
If a member solved >100 problems since Dec 1, some may be missed.
"""

import os
import sys
import logging
from datetime import datetime
from shutil import copy2
from concurrent.futures import ThreadPoolExecutor, as_completed

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
    
    backup_path = os.path.join(backup_dir, f"leetcode_before_reconstruct_dec8_{timestamp}.db")
    
    try:
        copy2(DB_PATH, backup_path)
        logger.info(f"✅ Backup created: {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"❌ Failed to create backup: {e}")
        raise

def count_problems_in_range(username, start_day, end_day):
    """Count problems solved in a date range (Dec 1-7, 2025)"""
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

def reconstruct_dec8_snapshots():
    """Reconstruct Dec 8 snapshots"""
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Get all Dec 1 snapshots
        cursor.execute("""
            SELECT username, total_solved, easy, medium, hard
            FROM snapshots
            WHERE week_start = '2025-12-01'
            ORDER BY username
        """)
        
        dec1_snapshots = cursor.fetchall()
        
        if not dec1_snapshots:
            logger.error("❌ No Dec 1 snapshots found!")
            return 0
        
        logger.info(f"\n📊 Found {len(dec1_snapshots)} Dec 1 snapshots")
        logger.info("=" * 100)
        
        reconstructed = []
        
        # Process each member
        for snap in dec1_snapshots:
            username = snap['username']
            dec1_total = snap['total_solved']
            
            logger.info(f"\n🔍 Processing {username}...")
            logger.info(f"   Dec 1 baseline: {dec1_total}")
            
            # Count problems from Dec 1-7
            count_dec1_7, problems = count_problems_in_range(username, 1, 7)
            
            if problems:
                logger.info(f"   Problems Dec 1-7: {count_dec1_7}")
                for p in problems[:5]:  # Show first 5
                    logger.info(f"     - {p['date']} {p['time']}: {p['title']}")
                if len(problems) > 5:
                    logger.info(f"     ... and {len(problems) - 5} more")
            else:
                logger.info(f"   Problems Dec 1-7: 0")
            
            # Calculate Dec 8 value
            dec8_total = dec1_total + count_dec1_7
            
            reconstructed.append({
                'username': username,
                'dec1_total': dec1_total,
                'added': count_dec1_7,
                'dec8_total': dec8_total,
                'easy': snap['easy'],
                'medium': snap['medium'],
                'hard': snap['hard']
            })
            
            logger.info(f"   ✅ Dec 8 estimate: {dec8_total} ({dec1_total} + {count_dec1_7})")
        
        logger.info("\n" + "=" * 100)
        
        return reconstructed

def insert_dec8_snapshots(reconstructed):
    """Insert reconstructed Dec 8 snapshots into database"""
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        inserted = 0
        
        for data in reconstructed:
            try:
                cursor.execute("""
                    INSERT INTO snapshots 
                    (username, week_start, total_solved, easy, medium, hard, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    data['username'],
                    '2025-12-08',
                    data['dec8_total'],
                    data['easy'],  # Using Dec 1 difficulty breakdown
                    data['medium'],
                    data['hard'],
                    datetime.utcnow().isoformat()
                ))
                inserted += 1
            except Exception as e:
                logger.error(f"Error inserting snapshot for {data['username']}: {e}")
        
        # Clear API cache
        cursor.execute("DELETE FROM api_cache")
        
        conn.commit()
        
        logger.info(f"\n✅ Inserted {inserted} Dec 8 snapshots")
        logger.info("✅ Cleared API cache")
        
        return inserted

def main():
    """Main function"""
    logger.info("=" * 100)
    logger.info("Reconstruct Dec 8 Snapshots")
    logger.info("=" * 100)
    
    # Step 1: Create backup
    logger.info("\n📦 Step 1: Creating Backup")
    try:
        backup_path = create_backup()
    except Exception as e:
        logger.error("❌ Backup failed. Aborting.")
        return 1
    
    # Step 2: Explain the method
    logger.info("\n📋 Step 2: Reconstruction Method")
    logger.info("  Formula: Dec 8 = Dec 1 snapshot + problems from Dec 1-7")
    logger.info("  Data source: LeetCode API (last ~100 submissions)")
    logger.info("  ⚠️  Limitation: If a member solved >100 problems since Dec 1, some may be missed")
    
    # Step 3: Confirm
    response = input("\nProceed with reconstruction? (yes/no): ").strip().lower()
    
    if response != 'yes':
        logger.info("❌ Operation cancelled")
        return 0
    
    # Step 4: Reconstruct
    logger.info("\n🔧 Step 3: Reconstructing Dec 8 Snapshots")
    reconstructed = reconstruct_dec8_snapshots()
    
    if not reconstructed:
        logger.error("❌ Reconstruction failed")
        return 1
    
    # Step 5: Show summary
    logger.info("\n📊 Step 4: Summary")
    logger.info("=" * 100)
    logger.info(f"{'Username':<20} | {'Dec 1':<8} | {'Added':<8} | {'Dec 8':<8}")
    logger.info("-" * 100)
    for data in reconstructed:
        logger.info(f"{data['username']:<20} | {data['dec1_total']:<8} | "
                   f"{data['added']:<8} | {data['dec8_total']:<8}")
    logger.info("=" * 100)
    
    # Step 6: Confirm insertion
    response = input("\nInsert these Dec 8 snapshots? (yes/no): ").strip().lower()
    
    if response != 'yes':
        logger.info("❌ Operation cancelled")
        return 0
    
    # Step 7: Insert
    logger.info("\n💾 Step 5: Inserting Dec 8 Snapshots")
    inserted = insert_dec8_snapshots(reconstructed)
    
    # Summary
    logger.info("\n" + "=" * 100)
    logger.info("✅ RECONSTRUCTION COMPLETED SUCCESSFULLY")
    logger.info("=" * 100)
    logger.info(f"\n📊 Summary:")
    logger.info(f"  - Reconstructed: {len(reconstructed)} members")
    logger.info(f"  - Inserted: {inserted} Dec 8 snapshots")
    logger.info(f"  - Backup: {backup_path}")
    logger.info(f"\n💡 Next Steps:")
    logger.info(f"  1. Refresh the dashboard")
    logger.info(f"  2. Week-over-week will now show Dec 8 → Current")
    logger.info(f"  3. Verify the numbers look correct")
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
