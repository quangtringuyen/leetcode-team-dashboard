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

from core.storage import choose_storage
from services.members_service import MembersService
from services.history_service import HistoryService
from utils.leetcodeapi import fetch_user_data

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
        # Schedule the job for every Monday at midnight
        schedule.every().monday.at("00:00").do(self.fetch_and_record_all_teams)

        logger.info("Scheduler started. Waiting for scheduled tasks...")
        logger.info("Scheduled jobs:")
        for job in schedule.get_jobs():
            logger.info(f"  - {job}")

        # Optional: Run immediately on startup for testing
        if os.environ.get("RUN_ON_STARTUP", "false").lower() == "true":
            logger.info("RUN_ON_STARTUP enabled, running initial fetch...")
            self.fetch_and_record_all_teams()

        # Keep the scheduler running
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute


def main():
    """Main entry point for the scheduler service."""
    logger.info("=" * 60)
    logger.info("LeetCode Team Dashboard - Data Scheduler")
    logger.info("=" * 60)
    logger.info(f"Environment: {os.environ.get('ENVIRONMENT', 'production')}")
    logger.info(f"Storage: {'S3' if os.environ.get('AWS_ACCESS_KEY_ID') else 'Local'}")

    scheduler = DataScheduler()

    try:
        scheduler.run_scheduler()
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
    except Exception as e:
        logger.error(f"Scheduler crashed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
