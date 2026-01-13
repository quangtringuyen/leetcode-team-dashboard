#!/usr/bin/env python3
"""
Data Migration Script - Streamlit to FastAPI Backend

Migrates existing data from Streamlit format to new FastAPI backend format:
- members.json: Converts to per-user format
- history.json: Converts team history to per-user history
- Creates users.json with default credentials

Usage:
    python migrate_data.py [--dry-run]
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any
import bcrypt

# Configuration
DATA_DIR = "data"
OLD_MEMBERS_FILE = f"{DATA_DIR}/members.json"
OLD_HISTORY_FILE = f"{DATA_DIR}/history.json"
NEW_MEMBERS_FILE = f"{DATA_DIR}/members_new.json"
NEW_HISTORY_FILE = f"{DATA_DIR}/history_new.json"
NEW_USERS_FILE = f"{DATA_DIR}/users.json"
BACKUP_DIR = f"{DATA_DIR}/backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

def create_backup():
    """Create backup of existing data files"""
    print("📦 Creating backup...")
    os.makedirs(BACKUP_DIR, exist_ok=True)

    files_backed_up = []
    for file in [OLD_MEMBERS_FILE, OLD_HISTORY_FILE]:
        if os.path.exists(file):
            backup_file = os.path.join(BACKUP_DIR, os.path.basename(file))
            with open(file, 'r') as f:
                data = f.read()
            with open(backup_file, 'w') as f:
                f.write(data)
            files_backed_up.append(file)
            print(f"  ✅ Backed up: {file} → {backup_file}")

    print(f"\n✅ Backup created in: {BACKUP_DIR}")
    return files_backed_up

def load_json(filepath: str) -> Dict:
    """Load JSON file"""
    if not os.path.exists(filepath):
        print(f"⚠️  File not found: {filepath}")
        return {}

    with open(filepath, 'r') as f:
        return json.load(f)

def save_json(filepath: str, data: Dict):
    """Save JSON file"""
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"  ✅ Saved: {filepath}")

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def migrate_members(old_members: Dict) -> Dict:
    """
    Migrate members.json from:
    {
      "leetcodescamp": [
        {"username": "user1", "name": "Name 1"},
        ...
      ]
    }

    To:
    {
      "leetcodescamp": [
        {"username": "user1", "name": "Name 1"},
        ...
      ]
    }

    (Same format - FastAPI backend is compatible!)
    """
    print("\n📋 Migrating members...")

    # The format is already compatible!
    # Old format: { "username": [members] }
    # New format: Same!

    for team_name, members in old_members.items():
        print(f"  ✅ Team '{team_name}': {len(members)} members")
        for member in members:
            print(f"     - {member.get('name', 'N/A')} (@{member['username']})")

    return old_members

def migrate_history(old_history: Dict) -> Dict:
    """
    Migrate history.json from:
    {
      "leetcodescamp": {
        "username": [
          {"week_start": "2025-09-08", "username": "...", ...}
        ]
      }
    }

    To new format (per-user):
    {
      "leetcodescamp": [
        {
          "week_start": "2025-09-08",
          "member": "username",
          "totalSolved": 22,
          "easy": 11,
          "medium": 0,
          "hard": 0
        }
      ]
    }
    """
    print("\n📊 Migrating history...")

    new_history = {}

    for team_name, user_histories in old_history.items():
        print(f"\n  Team: {team_name}")

        if not isinstance(user_histories, dict):
            print(f"    ⚠️  Unexpected format for team {team_name}, skipping...")
            continue

        team_snapshots = []

        for username, snapshots in user_histories.items():
            print(f"    User: {username} - {len(snapshots)} snapshots")

            for snapshot in snapshots:
                # Normalize the snapshot
                week_start = snapshot.get('week_start') or snapshot.get('date', '')

                if not week_start:
                    continue

                normalized_snapshot = {
                    "week_start": week_start,
                    "member": username,
                    "totalSolved": snapshot.get('totalSolved', 0),
                    "easy": snapshot.get('Easy', 0),
                    "medium": snapshot.get('Medium', 0),
                    "hard": snapshot.get('Hard', 0)
                }

                # Avoid duplicates
                if normalized_snapshot not in team_snapshots:
                    team_snapshots.append(normalized_snapshot)

        # Sort by week_start
        team_snapshots.sort(key=lambda x: x['week_start'])
        new_history[team_name] = team_snapshots

        print(f"    ✅ Migrated {len(team_snapshots)} unique snapshots")

    return new_history

def create_default_users(team_name: str) -> Dict:
    """
    Create default users.json with the team owner

    Format:
    {
      "username": {
        "username": "...",
        "email": "...@example.com",
        "hashed_password": "..."
      }
    }
    """
    print("\n👤 Creating default user...")

    # Create a default user with the team name
    default_password = "changeme123"  # User must change this!

    users = {
        team_name: {
            "username": team_name,
            "email": f"{team_name}@example.com",
            "hashed_password": hash_password(default_password)
        }
    }

    print(f"  ✅ Created user: {team_name}")
    print(f"  ⚠️  DEFAULT PASSWORD: {default_password}")
    print(f"  ⚠️  IMPORTANT: Change this password after first login!")

    return users

def main():
    """Main migration function"""
    dry_run = "--dry-run" in sys.argv

    print("=" * 60)
    print("🔄 Data Migration: Streamlit → FastAPI Backend")
    print("=" * 60)

    if dry_run:
        print("\n⚠️  DRY RUN MODE - No files will be modified\n")

    # Step 1: Create backup
    if not dry_run:
        create_backup()
    else:
        print("\n📦 [DRY RUN] Would create backup...")

    # Step 2: Load existing data
    print("\n📂 Loading existing data...")
    old_members = load_json(OLD_MEMBERS_FILE)
    old_history = load_json(OLD_HISTORY_FILE)

    if not old_members:
        print("❌ No members.json found or file is empty!")
        print("   Nothing to migrate.")
        return

    # Detect team name (usually the first key)
    team_name = list(old_members.keys())[0] if old_members else "default_team"
    print(f"\n🏢 Detected team: {team_name}")

    # Step 3: Migrate members
    new_members = migrate_members(old_members)

    # Step 4: Migrate history
    new_history = migrate_history(old_history) if old_history else {}

    # Step 5: Create users
    new_users = create_default_users(team_name)

    # Step 6: Save migrated data
    if not dry_run:
        print("\n💾 Saving migrated data...")
        save_json(NEW_MEMBERS_FILE, new_members)
        save_json(NEW_HISTORY_FILE, new_history)
        save_json(NEW_USERS_FILE, new_users)

        # Move new files to replace old ones
        print("\n🔄 Replacing old files with migrated versions...")
        if os.path.exists(NEW_MEMBERS_FILE):
            os.replace(NEW_MEMBERS_FILE, OLD_MEMBERS_FILE)
            print(f"  ✅ Updated: {OLD_MEMBERS_FILE}")

        if os.path.exists(NEW_HISTORY_FILE):
            os.replace(NEW_HISTORY_FILE, OLD_HISTORY_FILE)
            print(f"  ✅ Updated: {OLD_HISTORY_FILE}")

        print(f"  ✅ Created: {NEW_USERS_FILE}")
    else:
        print("\n💾 [DRY RUN] Would save:")
        print(f"  - {NEW_MEMBERS_FILE}")
        print(f"  - {NEW_HISTORY_FILE}")
        print(f"  - {NEW_USERS_FILE}")

    # Step 7: Summary
    print("\n" + "=" * 60)
    print("✅ Migration Complete!")
    print("=" * 60)

    print(f"\n📊 Summary:")
    print(f"  Team: {team_name}")
    print(f"  Members: {len(old_members.get(team_name, []))}")
    print(f"  History snapshots: {sum(len(snapshots) for snapshots in new_history.get(team_name, []))}")
    print(f"  Users created: 1 (username: {team_name})")

    print(f"\n🔐 Login Credentials:")
    print(f"  Username: {team_name}")
    print(f"  Password: changeme123")
    print(f"  Email: {team_name}@example.com")

    print(f"\n⚠️  IMPORTANT:")
    print(f"  1. Login with the credentials above")
    print(f"  2. Change your password immediately!")
    print(f"  3. Your data has been preserved")
    print(f"  4. Backup available at: {BACKUP_DIR}")

    if not dry_run:
        print(f"\n🚀 Next Steps:")
        print(f"  1. Rebuild Docker containers:")
        print(f"     docker compose -f docker-compose.backend.yml down")
        print(f"     docker compose -f docker-compose.backend.yml build --no-cache")
        print(f"     docker compose -f docker-compose.backend.yml up -d")
        print(f"  2. Access API: http://localhost:8080/api/docs")
        print(f"  3. Login with username '{team_name}' and password 'changeme123'")
        print(f"  4. Change your password!")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Migration cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error during migration: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
