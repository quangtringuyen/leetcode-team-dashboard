#!/usr/bin/env python3
"""
Archive legacy JSON files that have been migrated to SQLite database.

This script moves the following files to an archive directory:
- history.json (replaced by snapshots table)
- members.json (replaced by members table)
- history.backup_normalize_*.json (old backups)

Files that are still in use (users.json, last_state.json) are NOT touched.
"""

import os
import shutil
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_DIR = "/app/data"
ARCHIVE_DIR = os.path.join(DATA_DIR, "archive_legacy_json")

# Files to archive (no longer actively used)
LEGACY_FILES = [
    "history.json",
    "members.json",
]

# Pattern-based files to archive
LEGACY_PATTERNS = [
    "history.backup_normalize_",  # Old history backups
]

def create_archive_dir():
    """Create archive directory if it doesn't exist"""
    if not os.path.exists(ARCHIVE_DIR):
        os.makedirs(ARCHIVE_DIR)
        logger.info(f"Created archive directory: {ARCHIVE_DIR}")
    return ARCHIVE_DIR

def archive_file(filename):
    """Move a file to the archive directory with timestamp"""
    source = os.path.join(DATA_DIR, filename)
    
    if not os.path.exists(source):
        logger.warning(f"File not found, skipping: {filename}")
        return False
    
    # Add timestamp to archived filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base, ext = os.path.splitext(filename)
    archived_name = f"{base}_archived_{timestamp}{ext}"
    destination = os.path.join(ARCHIVE_DIR, archived_name)
    
    try:
        shutil.move(source, destination)
        logger.info(f"✓ Archived: {filename} → {archived_name}")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to archive {filename}: {e}")
        return False

def main():
    """Main cleanup function"""
    logger.info("=" * 60)
    logger.info("Legacy JSON File Cleanup")
    logger.info("=" * 60)
    
    # Create archive directory
    archive_dir = create_archive_dir()
    logger.info(f"Archive location: {archive_dir}")
    logger.info("")
    
    archived_count = 0
    
    # Archive specific files
    logger.info("Archiving legacy files:")
    for filename in LEGACY_FILES:
        if archive_file(filename):
            archived_count += 1
    
    # Archive pattern-based files
    logger.info("")
    logger.info("Archiving pattern-matched files:")
    for pattern in LEGACY_PATTERNS:
        for filename in os.listdir(DATA_DIR):
            if filename.startswith(pattern) and filename.endswith(".json"):
                if archive_file(filename):
                    archived_count += 1
    
    logger.info("")
    logger.info("=" * 60)
    logger.info(f"Cleanup complete! Archived {archived_count} file(s)")
    logger.info("")
    logger.info("Files still in use (NOT archived):")
    logger.info("  - users.json (authentication)")
    logger.info("  - last_state.json (notification tracking)")
    logger.info("")
    logger.info("All team/snapshot data is now in SQLite database:")
    logger.info("  - members table (team members)")
    logger.info("  - snapshots table (historical data with ranks)")
    logger.info("  - notifications table (notification history)")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
