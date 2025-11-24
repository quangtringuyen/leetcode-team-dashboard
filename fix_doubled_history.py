#!/usr/bin/env python3
"""
Script to fix doubled historical data in history.json
All snapshots before 2025-11-24 have doubled values due to a bug in the old code.
This script divides totalSolved and difficulty counts by 2 for those snapshots.
"""

import json
import os
import sys
from datetime import datetime
import boto3
from io import BytesIO

# Configuration
CUTOFF_DATE = "2025-11-24"
HISTORY_FILE = "data/history.json"

def use_s3():
    """Check if S3 configuration is available"""
    required_keys = ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_DEFAULT_REGION", "S3_BUCKET_NAME", "S3_PREFIX"]
    return all(os.environ.get(k) for k in required_keys)

def get_s3_client():
    """Get configured S3 client"""
    return boto3.client(
        "s3",
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
        region_name=os.environ.get("AWS_DEFAULT_REGION"),
    )

def get_s3_bucket_key(local_path):
    """Get S3 bucket and key from local path"""
    bucket = os.environ.get("S3_BUCKET_NAME")
    prefix = os.environ.get("S3_PREFIX", "").rstrip("/")
    key = f"{prefix}/{local_path.lstrip('/')}"
    return bucket, key

def read_history():
    """Read history from S3 or local file"""
    if use_s3():
        try:
            bucket, key = get_s3_bucket_key(HISTORY_FILE)
            s3_client = get_s3_client()
            obj = s3_client.get_object(Bucket=bucket, Key=key)
            data = json.loads(obj["Body"].read().decode("utf-8"))
            print(f"✓ Read history from S3: s3://{bucket}/{key}")
            return data
        except Exception as e:
            print(f"✗ Error reading from S3: {e}")
            sys.exit(1)
    else:
        if not os.path.exists(HISTORY_FILE):
            print(f"✗ File not found: {HISTORY_FILE}")
            sys.exit(1)
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            print(f"✓ Read history from local file: {HISTORY_FILE}")
            return data

def write_history(data, filename):
    """Write history to S3 or local file"""
    if use_s3():
        try:
            bucket, key = get_s3_bucket_key(filename)
            s3_client = get_s3_client()
            buf = BytesIO(json.dumps(data, indent=2).encode("utf-8"))
            s3_client.upload_fileobj(buf, bucket, key)
            print(f"✓ Wrote to S3: s3://{bucket}/{key}")
        except Exception as e:
            print(f"✗ Error writing to S3: {e}")
            sys.exit(1)
    else:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            print(f"✓ Wrote to local file: {filename}")

def fix_snapshot(snapshot, week_start):
    """Fix a single snapshot by dividing doubled values by 2"""
    if week_start >= CUTOFF_DATE:
        # Don't fix snapshots from Nov 24 onwards
        return snapshot, False

    modified = False
    fixed = snapshot.copy()

    # Fix totalSolved
    if "totalSolved" in fixed and fixed["totalSolved"] > 0:
        fixed["totalSolved"] = fixed["totalSolved"] // 2
        modified = True

    # Fix difficulty counts - handle both capitalized and lowercase keys
    for old_key, new_key in [("Easy", "easy"), ("Medium", "medium"), ("Hard", "hard")]:
        # Check if old capitalized key exists
        if old_key in fixed and fixed[old_key] > 0:
            fixed[old_key] = fixed[old_key] // 2
            modified = True
        # Check if new lowercase key exists
        if new_key in fixed and fixed[new_key] > 0:
            fixed[new_key] = fixed[new_key] // 2
            modified = True

    return fixed, modified

def main():
    print("=" * 70)
    print("Fix Doubled Historical Data Script")
    print("=" * 70)
    print(f"Cutoff date: {CUTOFF_DATE}")
    print(f"Snapshots before this date will have values divided by 2")
    print()

    # Read current history
    history = read_history()

    # Create backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"data/backup_{timestamp}/history.json"
    print(f"\n📦 Creating backup: {backup_file}")
    write_history(history, backup_file)

    # Fix the data
    print(f"\n🔧 Fixing doubled values...")
    print()

    total_snapshots = 0
    fixed_snapshots = 0

    for owner, member_data in history.items():
        print(f"Owner: {owner}")
        for member_username, snapshots in member_data.items():
            member_fixed = 0
            for i, snapshot in enumerate(snapshots):
                week_start = snapshot.get("week_start", "")
                total_snapshots += 1

                fixed_snapshot, was_modified = fix_snapshot(snapshot, week_start)

                if was_modified:
                    # Show before/after for first few
                    if fixed_snapshots < 3:
                        print(f"  {member_username} ({week_start}):")
                        print(f"    Before: totalSolved={snapshot.get('totalSolved')}, "
                              f"Easy/easy={snapshot.get('Easy', snapshot.get('easy', 0))}, "
                              f"Medium/medium={snapshot.get('Medium', snapshot.get('medium', 0))}, "
                              f"Hard/hard={snapshot.get('Hard', snapshot.get('hard', 0))}")
                        print(f"    After:  totalSolved={fixed_snapshot.get('totalSolved')}, "
                              f"Easy/easy={fixed_snapshot.get('Easy', fixed_snapshot.get('easy', 0))}, "
                              f"Medium/medium={fixed_snapshot.get('Medium', fixed_snapshot.get('medium', 0))}, "
                              f"Hard/hard={fixed_snapshot.get('Hard', fixed_snapshot.get('hard', 0))}")

                    # Replace in the list
                    snapshots[i] = fixed_snapshot
                    fixed_snapshots += 1
                    member_fixed += 1

            if member_fixed > 0:
                print(f"  ✓ Fixed {member_fixed} snapshots for {member_username}")

    print()
    print(f"📊 Summary:")
    print(f"  Total snapshots: {total_snapshots}")
    print(f"  Fixed snapshots: {fixed_snapshots}")
    print(f"  Unchanged snapshots: {total_snapshots - fixed_snapshots}")
    print()

    # Confirm before writing
    if len(sys.argv) > 1 and sys.argv[1] == "--yes":
        response = "yes"
        print("Write fixed data to history.json? (yes/no): yes (auto-confirmed)")
    else:
        response = input("Write fixed data to history.json? (yes/no): ").strip().lower()

    if response != "yes":
        print("❌ Aborted. No changes written.")
        sys.exit(0)

    # Write fixed history
    print(f"\n💾 Writing fixed history...")
    write_history(history, HISTORY_FILE)

    print()
    print("=" * 70)
    print("✅ Done! Historical data has been fixed.")
    print("=" * 70)
    print()
    print(f"Backup saved at: {backup_file}")
    print()
    print("Next steps:")
    print("  1. Refresh your dashboard to see the corrected data")
    print("  2. Week-over-week comparisons should now be accurate")
    print()

if __name__ == "__main__":
    main()
