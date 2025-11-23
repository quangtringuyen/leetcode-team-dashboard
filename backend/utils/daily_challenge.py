"""
Check if a user has completed today's daily challenge
"""
import requests
from typing import Optional
from datetime import date
import logging

logger = logging.getLogger(__name__)

LEETCODE_API_URL = "https://leetcode.com/graphql"


def check_daily_challenge_completion(username: str, question_title_slug: str) -> bool:
    """
    Check if a user has completed a specific problem (daily challenge)
    
    Args:
        username: LeetCode username
        question_title_slug: The titleSlug of the daily challenge question
        
    Returns:
        True if the user has completed the problem, False otherwise
    """
    query = """
    query getUserSubmissions($username: String!, $titleSlug: String!) {
        recentAcSubmissionList(username: $username, limit: 100) {
            titleSlug
            timestamp
        }
    }
    """
    
    try:
        response = requests.post(
            LEETCODE_API_URL,
            json={
                "query": query,
                "variables": {
                    "username": username,
                    "titleSlug": question_title_slug
                }
            },
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code != 200:
            logger.error(f"LeetCode API returned status {response.status_code}")
            return False
        
        data = response.json()
        submissions = data.get("data", {}).get("recentAcSubmissionList", [])
        
        # Check if any submission matches the daily challenge
        today = date.today()
        for submission in submissions:
            if submission.get("titleSlug") == question_title_slug:
                # Check if submission was made today
                timestamp = int(submission.get("timestamp", 0))
                submission_date = date.fromtimestamp(timestamp)
                if submission_date == today:
                    return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error checking daily challenge completion for {username}: {e}")
        return False
