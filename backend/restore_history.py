
import sqlite3
import os
import shutil
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

ACTIVE_DB_PATH = "/volume2/docker/leetcode-dashboard/data/leetcode.db"
BACKUP_DB_PATH = "/volume2/docker/leetcode-dashboard/backups/leetcode_backup_20260111_020000/leetcode.db"
TEMP_BACKUP_PATH = "/volume2/docker/leetcode-dashboard/data/leetcode.db.pre_merge_backup"

def merge_snapshots():
    if not os.path.exists(BACKUP_DB_PATH):
        logger.error(f"Backup database not found at {BACKUP_DB_PATH}")
        return

    if not os.path.exists(ACTIVE_DB_PATH):
        logger.error(f"Active database not found at {ACTIVE_DB_PATH}")
        return

    # 1. Create a safety backup of the active DB
    logger.info("Creating safety backup of active database...")
    shutil.copy2(ACTIVE_DB_PATH, TEMP_BACKUP_PATH)
    logger.info(f"Backed up to {TEMP_BACKUP_PATH}")

    try:
        # Connect to databases
        src_conn = sqlite3.connect(BACKUP_DB_PATH)
        dst_conn = sqlite3.connect(ACTIVE_DB_PATH)
        
        src_cursor = src_conn.cursor()
        dst_cursor = dst_conn.cursor()

        # Get snapshots from source
        logger.info("Reading snapshots from backup database...")
        # We specifically want the missing weeks: Dec 8, 15, 22, 29, Jan 5.
        # But we can just try to insert all of them with IGNORE to be safe.
        src_cursor.execute("SELECT username, week_start, total_solved, easy, medium, hard, timestamp FROM snapshots")
        snapshots = src_cursor.fetchall()
        
        logger.info(f"Found {len(snapshots)} snapshots in backup.")

        # Insert into destination
        logger.info("Merging snapshots into active database...")
        inserted_count = 0
        for snap in snapshots:
            try:
                # Assuming (username, week_start) should be unique, but schema might not enforce it strictly 
                # or might rely on ID. Let's check for existence first to avoid duplicates if no unique constraint exists.
                username, week_start = snap[0], snap[1]
                
                check_sql = "SELECT 1 FROM snapshots WHERE username = ? AND week_start = ?"
                dst_cursor.execute(check_sql, (username, week_start))
                if dst_cursor.fetchone():
                    # Snapshot exists, skip
                    continue
                
                insert_sql = """
                INSERT INTO snapshots (username, week_start, total_solved, easy, medium, hard, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """
                dst_cursor.execute(insert_sql, snap)
                inserted_count += 1
                
            except Exception as e:
                logger.error(f"Error inserting snapshot {snap}: {e}")

        dst_conn.commit()
        logger.info(f"Successfully merged {inserted_count} missing snapshots.")
        
    except Exception as e:
        logger.error(f"An error occurred during merge: {e}")
        # Build might fail if run locally without paths, but this is designed for the NAS environment
    finally:
        if 'src_conn' in locals(): src_conn.close()
        if 'dst_conn' in locals(): dst_conn.close()

if __name__ == "__main__":
    merge_snapshots()
