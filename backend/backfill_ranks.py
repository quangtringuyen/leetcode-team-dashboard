#!/usr/bin/env python3
"""
Backfill historical rank data for all snapshots.
Calculates rank for each week based on total_solved and updates the snapshots table.
"""

import sqlite3
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = "/app/data/leetcode.db"

def backfill_ranks():
    """Calculate and save historical ranks for all snapshots"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Get all unique week_start dates
        cursor.execute("SELECT DISTINCT week_start FROM snapshots ORDER BY week_start")
        weeks = [row[0] for row in cursor.fetchall()]
        
        logger.info(f"Found {len(weeks)} weeks to process")
        
        total_updated = 0
        
        for week in weeks:
            # Get all snapshots for this week, ordered by total_solved descending
            cursor.execute("""
                SELECT id, username, total_solved 
                FROM snapshots 
                WHERE week_start = ? 
                ORDER BY total_solved DESC, username ASC
            """, (week,))
            
            snapshots = cursor.fetchall()
            
            # Assign ranks
            for rank, (snapshot_id, username, total_solved) in enumerate(snapshots, start=1):
                cursor.execute("""
                    UPDATE snapshots 
                    SET rank = ? 
                    WHERE id = ?
                """, (rank, snapshot_id))
                total_updated += 1
            
            logger.info(f"Week {week}: Ranked {len(snapshots)} members")
        
        conn.commit()
        logger.info(f"Successfully updated {total_updated} snapshot ranks")
        
        # Verify
        cursor.execute("SELECT COUNT(*) FROM snapshots WHERE rank IS NOT NULL")
        count = cursor.fetchone()[0]
        logger.info(f"Total snapshots with rank: {count}")
        
    except Exception as e:
        logger.error(f"Error backfilling ranks: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    backfill_ranks()
