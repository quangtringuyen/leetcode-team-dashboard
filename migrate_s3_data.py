#!/usr/bin/env python3
"""
S3-Aware Data Migration Script - Streamlit to FastAPI Backend

Handles migration for data stored in AWS S3 or local files.
Automatically detects S3 configuration and migrates accordingly.

Usage:
    python migrate_s3_data.py [--dry-run] [--local-only] [--s3-only]
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional
import bcrypt

# Try to import boto3 for S3 support
try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    S3_AVAILABLE = True
except ImportError:
    S3_AVAILABLE = False
    print("⚠️  boto3 not installed. S3 support disabled.")
    print("   Install with: pip install boto3")

# Configuration from environment
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION", "ap-southeast-1")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "")
S3_PREFIX = os.getenv("S3_PREFIX", "prod")

# File paths
DATA_DIR = "data"
MEMBERS_FILE = "members.json"
HISTORY_FILE = "history.json"
USERS_FILE = "users.json"

class StorageManager:
    """Handles both S3 and local file storage"""

    def __init__(self):
        self.use_s3 = self._should_use_s3()
        if self.use_s3:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                region_name=AWS_DEFAULT_REGION
            )
            print(f"✅ S3 enabled: s3://{S3_BUCKET_NAME}/{S3_PREFIX}/")
        else:
            print(f"✅ Local storage: {DATA_DIR}/")

    def _should_use_s3(self) -> bool:
        """Check if S3 should be used"""
        return (
            S3_AVAILABLE and
            AWS_ACCESS_KEY_ID and
            AWS_SECRET_ACCESS_KEY and
            S3_BUCKET_NAME
        )

    def _get_s3_key(self, filename: str) -> str:
        """Get S3 key for file"""
        return f"{S3_PREFIX}/{filename}"

    def read_json(self, filename: str) -> Dict:
        """Read JSON from S3 or local file"""
        if self.use_s3:
            try:
                key = self._get_s3_key(filename)
                response = self.s3_client.get_object(
                    Bucket=S3_BUCKET_NAME,
                    Key=key
                )
                data = json.loads(response['Body'].read().decode('utf-8'))
                print(f"  📥 Downloaded from S3: {key}")
                return data
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchKey':
                    print(f"  ⚠️  File not found in S3: {key}")
                    return {}
                raise
        else:
            filepath = os.path.join(DATA_DIR, filename)
            if not os.path.exists(filepath):
                print(f"  ⚠️  File not found locally: {filepath}")
                return {}
            with open(filepath, 'r') as f:
                data = json.load(f)
                print(f"  📂 Loaded from local: {filepath}")
                return data

    def write_json(self, filename: str, data: Dict):
        """Write JSON to S3 or local file"""
        json_str = json.dumps(data, indent=2)

        if self.use_s3:
            key = self._get_s3_key(filename)
            self.s3_client.put_object(
                Bucket=S3_BUCKET_NAME,
                Key=key,
                Body=json_str.encode('utf-8'),
                ContentType='application/json'
            )
            print(f"  📤 Uploaded to S3: {key}")
        else:
            filepath = os.path.join(DATA_DIR, filename)
            os.makedirs(DATA_DIR, exist_ok=True)
            with open(filepath, 'w') as f:
                f.write(json_str)
            print(f"  💾 Saved locally: {filepath}")

    def backup_file(self, filename: str, backup_suffix: str):
        """Create backup of file"""
        backup_name = f"{filename.replace('.json', '')}_{backup_suffix}.json"

        if self.use_s3:
            try:
                source_key = self._get_s3_key(filename)
                backup_key = self._get_s3_key(backup_name)

                # Copy in S3
                self.s3_client.copy_object(
                    Bucket=S3_BUCKET_NAME,
                    CopySource={'Bucket': S3_BUCKET_NAME, 'Key': source_key},
                    Key=backup_key
                )
                print(f"  ✅ S3 backup created: {backup_key}")
                return True
            except ClientError as e:
                if e.response['Error']['Code'] != 'NoSuchKey':
                    print(f"  ⚠️  Failed to backup {filename}: {e}")
                return False
        else:
            source_path = os.path.join(DATA_DIR, filename)
            backup_path = os.path.join(DATA_DIR, backup_name)

            if os.path.exists(source_path):
                with open(source_path, 'r') as f:
                    data = f.read()
                with open(backup_path, 'w') as f:
                    f.write(data)
                print(f"  ✅ Local backup created: {backup_path}")
                return True
            return False

    def list_backups(self) -> List[str]:
        """List available backups"""
        backups = []

        if self.use_s3:
            try:
                prefix = f"{S3_PREFIX}/"
                response = self.s3_client.list_objects_v2(
                    Bucket=S3_BUCKET_NAME,
                    Prefix=prefix
                )

                if 'Contents' in response:
                    for obj in response['Contents']:
                        key = obj['Key']
                        if 'backup' in key:
                            backups.append(key)
            except ClientError:
                pass
        else:
            if os.path.exists(DATA_DIR):
                for filename in os.listdir(DATA_DIR):
                    if 'backup' in filename and filename.endswith('.json'):
                        backups.append(filename)

        return backups

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def migrate_members(old_members: Dict) -> Dict:
    """Migrate members - format is already compatible!"""
    print("\n📋 Migrating members...")

    for team_name, members in old_members.items():
        print(f"  ✅ Team '{team_name}': {len(members)} members")
        for member in members:
            print(f"     - {member.get('name', 'N/A')} (@{member['username']})")

    return old_members

def migrate_history(old_history: Dict) -> Dict:
    """Migrate history to new format"""
    print("\n📊 Migrating history...")

    new_history = {}

    for team_name, user_histories in old_history.items():
        print(f"\n  Team: {team_name}")

        if not isinstance(user_histories, dict):
            print(f"    ⚠️  Unexpected format, skipping...")
            continue

        team_snapshots = []

        for username, snapshots in user_histories.items():
            print(f"    User: {username} - {len(snapshots)} snapshots")

            for snapshot in snapshots:
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

                if normalized_snapshot not in team_snapshots:
                    team_snapshots.append(normalized_snapshot)

        team_snapshots.sort(key=lambda x: x['week_start'])
        new_history[team_name] = team_snapshots

        print(f"    ✅ Migrated {len(team_snapshots)} unique snapshots")

    return new_history

def create_default_users(team_name: str) -> Dict:
    """Create default users.json"""
    print("\n👤 Creating default user...")

    default_password = "changeme123"

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
    local_only = "--local-only" in sys.argv
    s3_only = "--s3-only" in sys.argv

    print("=" * 60)
    print("🔄 S3-Aware Data Migration: Streamlit → FastAPI")
    print("=" * 60)

    if dry_run:
        print("\n⚠️  DRY RUN MODE - No changes will be made\n")

    # Initialize storage manager
    storage = StorageManager()

    if local_only and storage.use_s3:
        print("\n⚠️  --local-only specified, forcing local storage")
        storage.use_s3 = False

    if s3_only and not storage.use_s3:
        print("\n❌ --s3-only specified but S3 is not configured!")
        print("   Check your .env file for AWS credentials")
        return

    # Create backups
    if not dry_run:
        print("\n📦 Creating backups...")
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        storage.backup_file(MEMBERS_FILE, f"backup_{timestamp}")
        storage.backup_file(HISTORY_FILE, f"backup_{timestamp}")
    else:
        print("\n📦 [DRY RUN] Would create backups...")

    # Load existing data
    print("\n📂 Loading existing data...")
    old_members = storage.read_json(MEMBERS_FILE)
    old_history = storage.read_json(HISTORY_FILE)

    if not old_members:
        print("\n❌ No members data found!")
        print("   Nothing to migrate.")
        return

    # Detect team name
    team_name = list(old_members.keys())[0] if old_members else "default_team"
    print(f"\n🏢 Detected team: {team_name}")

    # Migrate data
    new_members = migrate_members(old_members)
    new_history = migrate_history(old_history) if old_history else {}
    new_users = create_default_users(team_name)

    # Save migrated data
    if not dry_run:
        print("\n💾 Saving migrated data...")
        storage.write_json(MEMBERS_FILE, new_members)
        storage.write_json(HISTORY_FILE, new_history)
        storage.write_json(USERS_FILE, new_users)
    else:
        print("\n💾 [DRY RUN] Would save migrated data")

    # Summary
    print("\n" + "=" * 60)
    print("✅ Migration Complete!")
    print("=" * 60)

    print(f"\n📊 Summary:")
    print(f"  Storage: {'S3' if storage.use_s3 else 'Local'}")
    print(f"  Team: {team_name}")
    print(f"  Members: {len(old_members.get(team_name, []))}")
    print(f"  History snapshots: {sum(len(s) for s in new_history.values())}")

    print(f"\n🔐 Login Credentials:")
    print(f"  Username: {team_name}")
    print(f"  Password: changeme123")
    print(f"  Email: {team_name}@example.com")

    if storage.use_s3:
        print(f"\n☁️  S3 Storage:")
        print(f"  Bucket: {S3_BUCKET_NAME}")
        print(f"  Prefix: {S3_PREFIX}")
        print(f"  Files:")
        print(f"    - {S3_PREFIX}/{MEMBERS_FILE}")
        print(f"    - {S3_PREFIX}/{HISTORY_FILE}")
        print(f"    - {S3_PREFIX}/{USERS_FILE}")

        backups = storage.list_backups()
        if backups:
            print(f"\n  Backups available:")
            for backup in backups[:5]:  # Show first 5
                print(f"    - {backup}")

    print(f"\n⚠️  IMPORTANT:")
    print(f"  1. Verify data in your storage ({'S3' if storage.use_s3 else 'local'})")
    print(f"  2. Rebuild Docker containers")
    print(f"  3. Login and change password immediately!")

    if not dry_run:
        print(f"\n🚀 Next Steps:")
        print(f"  docker compose -f docker-compose.backend.yml down")
        print(f"  docker compose -f docker-compose.backend.yml build --no-cache")
        print(f"  docker compose -f docker-compose.backend.yml up -d")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    try:
        main()
    except NoCredentialsError:
        print("\n❌ AWS credentials not found!")
        print("   Check your .env file or AWS configuration")
        sys.exit(1)
    except ClientError as e:
        print(f"\n❌ AWS S3 Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Migration cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
