#!/usr/bin/env python3
"""
Fix historical data with doubled totalSolved values.

This script identifies and fixes snapshots where totalSolved doesn't match
the sum of easy + medium + hard problems.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

def fix_history_data(history_file: str = "data/history.json", backup: bool = True):
    """
    Fix totalSolved doubling bug in history data.

    Args:
        history_file: Path to history.json
        backup: Whether to create a backup before fixing
    """
    history_path = Path(history_file)

    if not history_path.exists():
        print(f"❌ Error: {history_file} not found")
        return False

    print("=" * 70)
    print("🔧 Fixing Historical Data - totalSolved Doubling Bug")
    print("=" * 70)

    # Read history
    with open(history_path, 'r') as f:
        history = json.load(f)

    # Backup original file
    if backup:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = history_path.with_suffix(f'.backup_{timestamp}.json')
        with open(backup_path, 'w') as f:
            json.dump(history, f, indent=2)
        print(f"✅ Backup created: {backup_path}\n")

    # Track changes
    total_snapshots = 0
    fixed_snapshots = 0
    changes = []

    # Fix each owner's data
    for owner, members_data in history.items():
        for member_username, snapshots in members_data.items():
            for snapshot in snapshots:
                total_snapshots += 1

                old_total = snapshot.get('totalSolved', 0)
                easy = snapshot.get('easy', 0)
                medium = snapshot.get('medium', 0)
                hard = snapshot.get('hard', 0)

                # Calculate correct totalSolved
                correct_total = easy + medium + hard

                # Check if it needs fixing (tolerance of 1 for rounding errors)
                if abs(old_total - correct_total) > 1:
                    diff = old_total - correct_total
                    week = snapshot.get('week_start', 'unknown')

                    changes.append({
                        'member': member_username,
                        'week': week,
                        'old_total': old_total,
                        'new_total': correct_total,
                        'diff': diff,
                        'easy': easy,
                        'medium': medium,
                        'hard': hard
                    })

                    # Fix it
                    snapshot['totalSolved'] = correct_total
                    fixed_snapshots += 1

    # Save fixed data
    with open(history_path, 'w') as f:
        json.dump(history, f, indent=2)

    # Print summary
    print(f"{'=' * 70}")
    print(f"📊 Fix Summary")
    print(f"{'=' * 70}")
    print(f"Total snapshots processed: {total_snapshots}")
    print(f"Snapshots fixed: {fixed_snapshots}")
    print(f"Snapshots unchanged: {total_snapshots - fixed_snapshots}")

    if changes:
        print(f"\n{'=' * 70}")
        print(f"📝 Details of Fixed Snapshots (showing first 20)")
        print(f"{'=' * 70}")
        for i, change in enumerate(changes[:20], 1):
            print(f"\n{i}. {change['member']} - Week of {change['week']}")
            print(f"   Old totalSolved: {change['old_total']}")
            print(f"   Easy: {change['easy']}, Medium: {change['medium']}, Hard: {change['hard']}")
            print(f"   New totalSolved: {change['new_total']} (E+M+H = {change['new_total']})")
            print(f"   Correction: {change['diff']} (was approximately doubled)")

        if len(changes) > 20:
            print(f"\n... and {len(changes) - 20} more fixes")

    print(f"\n{'=' * 70}")
    print(f"✅ Historical data has been fixed!")
    print(f"✅ File saved: {history_path}")
    print(f"{'=' * 70}")

    return True

def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Fix totalSolved doubling bug in historical data'
    )
    parser.add_argument(
        '--file',
        default='data/history.json',
        help='Path to history.json file (default: data/history.json)'
    )
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Skip creating backup file'
    )

    args = parser.parse_args()

    success = fix_history_data(
        history_file=args.file,
        backup=not args.no_backup
    )

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
