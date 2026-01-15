#!/usr/bin/env python3
"""
Database-specific backup script.
Creates a backup of the SQLite database file with proper locking.
"""

import os
import shutil
import sqlite3
from datetime import datetime
import logging
import glob

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_DIR = "/app/data"
DB_FILE = "leetcode.db"
DB_PATH = os.path.join(DATA_DIR, DB_FILE)
BACKUP_DIR = "/app/backups"


def backup_database():
    """Create a backup of the SQLite database using the backup API"""
    try:
        os.makedirs(BACKUP_DIR, exist_ok=True)
        
        # Timestamp for the backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"leetcode_backup_{timestamp}"
        backup_db_path = os.path.join(BACKUP_DIR, backup_filename, DB_FILE)
        
        # Create backup directory
        os.makedirs(os.path.dirname(backup_db_path), exist_ok=True)
        
        logger.info(f"Starting database backup to {backup_db_path}...")
        
        # Use SQLite's backup API for safe backup (handles locking)
        source_conn = sqlite3.connect(DB_PATH)
        backup_conn = sqlite3.connect(backup_db_path)
        
        with backup_conn:
            source_conn.backup(backup_conn)
        
        source_conn.close()
        backup_conn.close()
        
        # Get database size
        db_size_mb = os.path.getsize(backup_db_path) / (1024 * 1024)
        logger.info(f"✓ Database backup created successfully: {backup_db_path} ({db_size_mb:.2f} MB)")
        
        # Cleanup old backups (keep last 10)
        cleanup_old_backups()
        
        return backup_db_path
        
    except Exception as e:
        logger.error(f"Error creating database backup: {e}", exc_info=True)
        return None


def cleanup_old_backups(keep_count=10):
    """Remove old backups, keeping only the most recent ones"""
    try:
        # Find all backup directories
        backup_dirs = sorted(glob.glob(os.path.join(BACKUP_DIR, "leetcode_backup_*")))
        
        if len(backup_dirs) > keep_count:
            for old_backup in backup_dirs[:-keep_count]:
                shutil.rmtree(old_backup)
                logger.info(f"✓ Removed old backup: {old_backup}")
            logger.info(f"Kept {keep_count} most recent backups")
        else:
            logger.info(f"Total backups: {len(backup_dirs)} (keeping all)")
            
    except Exception as e:
        logger.error(f"Error cleaning up old backups: {e}")


def verify_backup(backup_path):
    """Verify the backup database integrity"""
    try:
        conn = sqlite3.connect(backup_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()[0]
        conn.close()
        
        if result == "ok":
            logger.info(f"✓ Backup integrity verified: {backup_path}")
            return True
        else:
            logger.error(f"✗ Backup integrity check failed: {result}")
            return False
    except Exception as e:
        logger.error(f"Error verifying backup: {e}")
        return False


if __name__ == "__main__":
    logger.info("=" * 70)
    logger.info("Database Backup Script")
    logger.info("=" * 70)
    
    backup_path = backup_database()
    
    if backup_path:
        verify_backup(backup_path)
        logger.info("=" * 70)
        logger.info("Backup complete!")
        logger.info("=" * 70)
    else:
        logger.error("Backup failed!")
