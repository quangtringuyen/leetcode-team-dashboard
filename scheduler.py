#!/usr/bin/env python3
"""
Scheduler service for automatic data fetching and recording.
Runs as a background service to capture LeetCode data every Monday at midnight.
"""
import os
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import schedule

print("Starting scheduler service...", flush=True)

try:
    print("Importing core modules...", flush=True)
    from core.storage import choose_storage
    from services.members_service import MembersService
    from services.history_service import HistoryService
    from backend.utils.leetcodeapi import fetch_user_data
    
    print("Importing backend modules...", flush=True)
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from backend.core.config import settings
    from backend.core.storage import read_json, write_json
    from backend.utils.notification_service import (
        check_and_notify_new_submissions,
        check_and_notify_milestones,
        notify_daily_challenge
    )
    print("Imports completed successfully.", flush=True)
except Exception as e:
    print(f"CRITICAL ERROR during imports: {e}", flush=True)
    import traceback
    traceback.print_exc()
    raise

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataScheduler:
    """Handles automatic data fetching and recording on schedule."""

    def __init__(self):
        self.storage = choose_storage()
        self.members_service = MembersService(self.storage)
        self.history_service = HistoryService(self.storage)
        logger.info(f"Initialized DataScheduler with {type(self.storage).__name__}")

    def check_new_submissions(self):
        """Check for new submissions and send notifications."""
        logger.info("Checking for new submissions...")
        
        try:
            # Load team members
            all_members = read_json(settings.MEMBERS_FILE, default={})
            
            # Flatten members list (handle multiple teams if any, though usually it's by owner)
            # Structure is {owner: [members]}
            user_members = []
            for owner, members in all_members.items():
                user_members.extend(members)
                
            if not user_members:
                return
            
            # Load last state
            last_state = read_json(settings.LAST_STATE_FILE, default={})
            # Flatten last state? No, last_state is {owner: {username: data}}
            # Wait, api/notifications.py assumes last_state is {username: {username: data}} which is weird.
            # Let's check how it's stored.
            # In api/notifications.py: last_state.get(username, {}) where username is current_user.
            # So last_state is keyed by OWNER username.
            
            # We need to process per owner to update the correct state file structure
            for owner, members in all_members.items():
                user_last_state = last_state.get(owner, {})
                new_state = {}
                
                with ThreadPoolExecutor(max_workers=5) as executor:
                    future_to_member = {
                        executor.submit(fetch_user_data, member["username"]): member
                        for member in members
                    }
                    
                    for future in as_completed(future_to_member):
                        member = future_to_member[future]
                        member_username = member["username"]
                        member_name = member.get("name", member_username)
                        
                        try:
                            current_data = future.result()
                            if not current_data:
                                continue
                            
                            # Save to new state
                            new_state[member_username] = current_data
                            
                            # Compare with previous state
                            if member_username in user_last_state:
                                previous_data = user_last_state[member_username]
                                
                                current_total = current_data.get("totalSolved", 0)
                                previous_total = previous_data.get("totalSolved", 0)
                                
                                if current_total > previous_total:
                                    logger.info(f"Detected change for {member_username}: {previous_total} -> {current_total} (+{current_total - previous_total})")
                                
                                # Check for new submissions
                                check_and_notify_new_submissions(
                                    current_data,
                                    previous_data,
                                    member_username,
                                    member_name
                                )
                                
                                # Check for milestones
                                check_and_notify_milestones(
                                    current_data,
                                    previous_data,
                                    member_username,
                                    member_name
                                )
                        except Exception as e:
                            logger.error(f"Error checking submissions for {member_username}: {e}")
                
                # Update last state for this owner
                user_last_state.update(new_state)
                last_state[owner] = user_last_state
                
            # Save updated state
            write_json(settings.LAST_STATE_FILE, last_state)
            logger.info("Submission check completed.")
            
        except Exception as e:
            logger.error(f"Error in check_new_submissions: {e}", exc_info=True)

    def check_daily_challenge(self):
        """Fetch and notify daily challenge."""
        logger.info("Checking daily challenge...")
        try:
            from backend.utils.leetcodeapi import fetch_daily_challenge
            challenge = fetch_daily_challenge()
            if challenge:
                notify_daily_challenge(challenge)
                logger.info(f"Notified daily challenge: {challenge.get('title')}")
            else:
                logger.warning("Failed to fetch daily challenge")
        except Exception as e:
            logger.error(f"Error checking daily challenge: {e}", exc_info=True)

    def fetch_and_record_all_teams(self):
        """Fetch data for all teams and record to history."""
        logger.info("Starting scheduled data fetch...")

        try:
            # Load all members from all teams
            all_members = self.members_service.load_all_members()

            if not all_members:
                logger.warning("No team members found in the system")
                return

            teams_processed = 0
            members_processed = 0

            # Process each team/owner
            for owner, members in all_members.items():
                if not members:
                    logger.info(f"No members for team '{owner}', skipping")
                    continue

                logger.info(f"Processing team '{owner}' with {len(members)} members")
                team_data = []

                # Fetch data for each member
                for member in members:
                    username = member.get("username")
                    name = member.get("name", username)

                    if not username:
                        logger.warning(f"Member missing username: {member}")
                        continue

                    try:
                        logger.info(f"Fetching data for {username}...")
                        user_data = fetch_user_data(username)

                        if user_data:
                            user_data["name"] = name
                            user_data["username"] = username
                            team_data.append(user_data)
                            members_processed += 1
                            logger.info(f"Successfully fetched data for {username}: {user_data.get('totalSolved', 0)} problems solved")
                        else:
                            logger.warning(f"No data returned for {username}")

                    except Exception as e:
                        logger.error(f"Error fetching data for {username}: {e}")
                        continue

                    # Rate limiting - be nice to LeetCode API
                    time.sleep(1)

                # Record weekly snapshot for this team
                if team_data:
                    try:
                        self.history_service.record_weekly(owner, team_data)
                        teams_processed += 1
                        logger.info(f"Recorded weekly snapshot for team '{owner}' with {len(team_data)} members")
                    except Exception as e:
                        logger.error(f"Error recording history for team '{owner}': {e}")

            logger.info(f"Scheduled fetch completed: {teams_processed} teams, {members_processed} members processed")

        except Exception as e:
            logger.error(f"Error in fetch_and_record_all_teams: {e}", exc_info=True)

    def run_scheduler(self):
        """Run the scheduler loop."""
        from backend.core.database import get_db_connection
        import json
        
        # Load settings from database
        def get_setting(key: str, default):
            try:
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT value FROM system_settings WHERE key = ?", (key,))
                    row = cursor.fetchone()
                    if row:
                        try:
                            return json.loads(row["value"])
                        except:
                            return row["value"]
                return default
            except Exception as e:
                logger.warning(f"Failed to load setting {key}, using default: {e}")
                return default
        
        # Get scheduler settings
        snapshot_day = get_setting("snapshot_schedule_day", "monday").lower()
        snapshot_time = get_setting("snapshot_schedule_time", "00:00")
        notification_interval = int(get_setting("notification_check_interval", 15))
        
        logger.info(f"Configuring scheduler with settings from database:")
        logger.info(f"  - Snapshot: Every {snapshot_day} at {snapshot_time}")
        logger.info(f"  - Notifications: Every {notification_interval} minutes")
        
        # Clear any existing jobs
        schedule.clear()
        
        # Schedule the snapshot job based on settings
        day_mapping = {
            "monday": schedule.every().monday,
            "tuesday": schedule.every().tuesday,
            "wednesday": schedule.every().wednesday,
            "thursday": schedule.every().thursday,
            "friday": schedule.every().friday,
            "saturday": schedule.every().saturday,
            "sunday": schedule.every().sunday,
        }
        
        if snapshot_day in day_mapping:
            day_mapping[snapshot_day].at(snapshot_time).do(self.fetch_and_record_all_teams)
        else:
            logger.warning(f"Invalid snapshot day '{snapshot_day}', defaulting to Monday")
            schedule.every().monday.at(snapshot_time).do(self.fetch_and_record_all_teams)
        
        # Schedule submission check based on settings
        schedule.every(notification_interval).minutes.do(self.check_new_submissions)
        
        # Schedule daily challenge notification (08:00 AM)
        schedule.every().day.at("08:00").do(self.check_daily_challenge)
        
        # Schedule weekly backup (Sunday at 02:00 AM)
        schedule.every().sunday.at("02:00").do(self.backup_data)

        logger.info("Scheduler started. Waiting for scheduled tasks...")

    def backup_data(self):
        """Backup the data directory."""
        import shutil
        import glob
        
        logger.info("Starting weekly data backup...")
        try:
            # Source directory (data/)
            data_dir = settings.DATA_DIR
            
            # Backup directory (backups/)
            backup_dir = os.path.join(os.path.dirname(data_dir), "backups")
            os.makedirs(backup_dir, exist_ok=True)
            
            # Timestamp for the backup
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"leetcode_backup_{timestamp}"
            backup_path = os.path.join(backup_dir, backup_filename)
            
            # Create zip archive
            shutil.make_archive(backup_path, 'zip', data_dir)
            
            logger.info(f"Backup created successfully: {backup_path}.zip")
            
            # Cleanup old backups (keep last 5)
            backups = sorted(glob.glob(os.path.join(backup_dir, "leetcode_backup_*.zip")))
            if len(backups) > 5:
                for old_backup in backups[:-5]:
                    os.remove(old_backup)
                    logger.info(f"Removed old backup: {old_backup}")
                    
        except Exception as e:
            logger.error(f"Error creating backup: {e}", exc_info=True)
        logger.info("Scheduled jobs:")
        for job in schedule.get_jobs():
            logger.info(f"  - {job}")

        # Optional: Run immediately on startup for testing
        if os.environ.get("RUN_ON_STARTUP", "false").lower() == "true":
            logger.info("RUN_ON_STARTUP enabled, running initial fetch...")
            self.fetch_and_record_all_teams()
            self.check_new_submissions()

        # Keep the scheduler running
        print("Entering main loop...", flush=True)
        while True:
            try:
                schedule.run_pending()
                if int(time.time()) % 60 == 0:
                    print("Heartbeat: Scheduler is alive", flush=True)
                time.sleep(1)  # Check every second instead of 60 to be more responsive
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(5)

def main():
    """Main entry point for the scheduler service."""
    logger.info("=" * 60)
    logger.info("LeetCode Team Dashboard - Data Scheduler")
    logger.info("=" * 60)
    logger.info(f"Environment: {os.environ.get('ENVIRONMENT', 'production')}")
    logger.info(f"Storage: {'S3' if os.environ.get('AWS_ACCESS_KEY_ID') else 'Local'}")

    scheduler = DataScheduler()

    # Verify Discord Webhook on startup
    if settings.DISCORD_WEBHOOK_URL:
        logger.info(f"Discord Webhook configured: {settings.DISCORD_WEBHOOK_URL[:10]}...")
    else:
        logger.warning("DISCORD_WEBHOOK_URL is not set. Discord notifications will not be sent.")

    try:
        scheduler.run_scheduler()
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
    except Exception as e:
        logger.error(f"Scheduler crashed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
