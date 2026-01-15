#!/usr/bin/env python3
"""
Migrate remaining JSON files to SQLite database.

Migrates:
1. users.json → users table
2. last_state.json → last_state table (for notification tracking)
3. Archives the JSON files after successful migration
"""

import os
import json
import sqlite3
import shutil
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_DIR = "/app/data"
DB_PATH = os.path.join(DATA_DIR, "leetcode.db")
USERS_JSON = os.path.join(DATA_DIR, "users.json")
LAST_STATE_JSON = os.path.join(DATA_DIR, "last_state.json")
ARCHIVE_DIR = os.path.join(DATA_DIR, "archive_json_migration")


def create_tables(conn):
    """Create tables for users and last_state"""
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            email TEXT,
            full_name TEXT,
            hashed_password TEXT NOT NULL,
            disabled INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create last_state table for notification tracking
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS last_state (
            owner_username TEXT NOT NULL,
            member_username TEXT NOT NULL,
            total_solved INTEGER DEFAULT 0,
            easy INTEGER DEFAULT 0,
            medium INTEGER DEFAULT 0,
            hard INTEGER DEFAULT 0,
            ranking INTEGER,
            real_name TEXT,
            avatar TEXT,
            acceptance_rate REAL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (owner_username, member_username)
        )
    """)
    
    conn.commit()
    logger.info("✓ Created database tables")


def migrate_users(conn):
    """Migrate users.json to users table"""
    if not os.path.exists(USERS_JSON):
        logger.warning("users.json not found, skipping")
        return 0
    
    with open(USERS_JSON, 'r') as f:
        users_data = json.load(f)
    
    cursor = conn.cursor()
    migrated = 0
    
    for username, user_info in users_data.items():
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO users 
                (username, email, full_name, hashed_password, disabled)
                VALUES (?, ?, ?, ?, ?)
            """, (
                user_info.get("username", username),
                user_info.get("email", ""),
                user_info.get("full_name", ""),
                user_info.get("hashed_password"),
                1 if user_info.get("disabled", False) else 0
            ))
            migrated += 1
        except Exception as e:
            logger.error(f"Failed to migrate user {username}: {e}")
    
    conn.commit()
    logger.info(f"✓ Migrated {migrated} users to database")
    return migrated


def migrate_last_state(conn):
    """Migrate last_state.json to last_state table"""
    if not os.path.exists(LAST_STATE_JSON):
        logger.warning("last_state.json not found, skipping")
        return 0
    
    with open(LAST_STATE_JSON, 'r') as f:
        last_state_data = json.load(f)
    
    cursor = conn.cursor()
    migrated = 0
    
    for owner_username, members in last_state_data.items():
        for member_username, member_data in members.items():
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO last_state 
                    (owner_username, member_username, total_solved, easy, medium, hard, 
                     ranking, real_name, avatar, acceptance_rate, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    owner_username,
                    member_data.get("username", member_username),
                    member_data.get("totalSolved", 0),
                    member_data.get("easy", 0),
                    member_data.get("medium", 0),
                    member_data.get("hard", 0),
                    member_data.get("ranking"),
                    member_data.get("realName"),
                    member_data.get("avatar"),
                    member_data.get("acceptanceRate")
                ))
                migrated += 1
            except Exception as e:
                logger.error(f"Failed to migrate last_state for {owner_username}/{member_username}: {e}")
    
    conn.commit()
    logger.info(f"✓ Migrated {migrated} last_state entries to database")
    return migrated


def archive_json_file(filepath):
    """Archive a JSON file with timestamp"""
    if not os.path.exists(filepath):
        return False
    
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    
    filename = os.path.basename(filepath)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base, ext = os.path.splitext(filename)
    archived_name = f"{base}_migrated_{timestamp}{ext}"
    destination = os.path.join(ARCHIVE_DIR, archived_name)
    
    try:
        shutil.copy2(filepath, destination)  # Copy first (safer)
        os.remove(filepath)  # Then remove original
        logger.info(f"✓ Archived: {filename} → {archived_name}")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to archive {filename}: {e}")
        return False


def main():
    """Main migration function"""
    logger.info("=" * 70)
    logger.info("JSON to SQLite Migration")
    logger.info("=" * 70)
    logger.info("")
    
    try:
        # Connect to database
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        
        # Create tables
        logger.info("Step 1: Creating database tables...")
        create_tables(conn)
        logger.info("")
        
        # Migrate users
        logger.info("Step 2: Migrating users.json...")
        users_count = migrate_users(conn)
        logger.info("")
        
        # Migrate last_state
        logger.info("Step 3: Migrating last_state.json...")
        state_count = migrate_last_state(conn)
        logger.info("")
        
        # Close connection
        conn.close()
        
        # Archive JSON files
        logger.info("Step 4: Archiving JSON files...")
        archive_json_file(USERS_JSON)
        archive_json_file(LAST_STATE_JSON)
        logger.info("")
        
        logger.info("=" * 70)
        logger.info("Migration Summary:")
        logger.info(f"  - Users migrated: {users_count}")
        logger.info(f"  - Last state entries migrated: {state_count}")
        logger.info(f"  - Archive location: {ARCHIVE_DIR}")
        logger.info("")
        logger.info("✓ Migration complete!")
        logger.info("")
        logger.info("All data is now in SQLite database:")
        logger.info("  - users table (authentication)")
        logger.info("  - last_state table (notification tracking)")
        logger.info("  - members table (team members)")
        logger.info("  - snapshots table (historical data with ranks)")
        logger.info("  - notifications table (notification history)")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise


if __name__ == "__main__":
    main()
