"""
LeetCode API client for fetching user data
"""

import requests
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

LEETCODE_API_URL = "https://leetcode.com/graphql"
LEETCODE_PROFILE_URL = "https://leetcode.com/{username}/"


def fetch_user_data(username: str) -> Optional[Dict[str, Any]]:
    """
    Fetch user profile data from LeetCode GraphQL API

    Args:
        username: LeetCode username

    Returns:
        Dict with user data or None if user not found
    """
    query = """
    query getUserProfile($username: String!) {
        matchedUser(username: $username) {
            username
            profile {
                realName
                userAvatar
                ranking
            }
            submitStats {
                acSubmissionNum {
                    difficulty
                    count
                }
                totalSubmissionNum {
                    difficulty
                    count
                }
            }
        }
    }
    """

    try:
        response = requests.post(
            LEETCODE_API_URL,
            json={"query": query, "variables": {"username": username}},
            headers={"Content-Type": "application/json"},
            timeout=10
        )

        if response.status_code != 200:
            logger.error(f"LeetCode API returned status {response.status_code}")
            return None

        data = response.json()

        if not data.get("data") or not data["data"].get("matchedUser"):
            logger.warning(f"User {username} not found on LeetCode")
            return None

        user_data = data["data"]["matchedUser"]
        profile = user_data.get("profile", {})
        submit_stats = user_data.get("submitStats", {})

        # Parse submission stats
        ac_submissions = submit_stats.get("acSubmissionNum", [])
        total_solved = 0
        easy = medium = hard = 0

        for stat in ac_submissions:
            difficulty = stat.get("difficulty", "").lower()
            count = stat.get("count", 0)
            total_solved += count

            if difficulty == "easy":
                easy = count
            elif difficulty == "medium":
                medium = count
            elif difficulty == "hard":
                hard = count

        return {
            "username": user_data.get("username"),
            "realName": profile.get("realName"),
            "avatar": profile.get("userAvatar"),
            "ranking": profile.get("ranking"),
            "totalSolved": total_solved,
            "easy": easy,
            "medium": medium,
            "hard": hard,
            "totalAttempted": sum(s.get("count", 0) for s in submit_stats.get("totalSubmissionNum", [])),
            "acceptanceRate": round((total_solved / max(1, sum(s.get("count", 0) for s in submit_stats.get("totalSubmissionNum", [])))) * 100, 2) if total_solved > 0 else 0,
            "submissions": []  # Can be populated separately
        }

    except requests.RequestException as e:
        logger.error(f"Error fetching data for user {username}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error processing user {username}: {e}")
        return None


def fetch_recent_submissions(username: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Fetch recent accepted submissions for a user

    Args:
        username: LeetCode username
        limit: Number of submissions to fetch

    Returns:
        List of recent submissions
    """
    query = """
    query getRecentSubmissions($username: String!, $limit: Int!) {
        recentAcSubmissionList(username: $username, limit: $limit) {
            title
            titleSlug
            timestamp
        }
    }
    """

    try:
        response = requests.post(
            LEETCODE_API_URL,
            json={"query": query, "variables": {"username": username, "limit": limit}},
            headers={"Content-Type": "application/json"},
            timeout=10
        )

        if response.status_code != 200:
            logger.error(f"LeetCode API returned status {response.status_code}")
            return []

        data = response.json()

        submissions = data.get("data", {}).get("recentAcSubmissionList", [])

        return [
            {
                "title": sub.get("title"),
                "titleSlug": sub.get("titleSlug"),
                "timestamp": sub.get("timestamp"),
                "date": sub.get("timestamp")
            }
            for sub in submissions
        ]

    except Exception as e:
        logger.error(f"Error fetching submissions for user {username}: {e}")
        return []


def fetch_daily_challenge() -> Optional[Dict[str, Any]]:
    """
    Fetch today's LeetCode daily challenge

    Returns:
        Dict with daily challenge info or None if not available
    """
    query = """
    query questionOfToday {
        activeDailyCodingChallengeQuestion {
            date
            link
            question {
                questionId
                title
                titleSlug
                difficulty
            }
        }
    }
    """

    try:
        response = requests.post(
            LEETCODE_API_URL,
            json={"query": query},
            headers={"Content-Type": "application/json"},
            timeout=10
        )

        if response.status_code != 200:
            logger.error(f"LeetCode API returned status {response.status_code}")
            return None

        data = response.json()

        challenge_data = data.get("data", {}).get("activeDailyCodingChallengeQuestion")

        if not challenge_data:
            return None

        question = challenge_data.get("question", {})

        return {
            "date": challenge_data.get("date"),
            "link": challenge_data.get("link"),
            "questionId": question.get("questionId"),
            "title": question.get("title"),
            "titleSlug": question.get("titleSlug"),
            "difficulty": question.get("difficulty")
        }

    except Exception as e:
        logger.error(f"Error fetching daily challenge: {e}")
        return None


def fetch_daily_challenge_by_date(target_date: str) -> Optional[Dict[str, Any]]:
    """
    Fetch daily challenge for a specific date

    Args:
        target_date: Date in YYYY-MM-DD format

    Returns:
        Dict with daily challenge info or None if not available
    """
    query = """
    query dailyCodingQuestionRecords($year: Int!, $month: Int!) {
        dailyCodingChallengeV2(year: $year, month: $month) {
            challenges {
                date
                link
                question {
                    questionId
                    title
                    titleSlug
                    difficulty
                }
            }
        }
    }
    """

    try:
        from datetime import datetime
        date_obj = datetime.strptime(target_date, "%Y-%m-%d")
        year = date_obj.year
        month = date_obj.month

        response = requests.post(
            LEETCODE_API_URL,
            json={
                "query": query,
                "variables": {"year": year, "month": month}
            },
            headers={"Content-Type": "application/json"},
            timeout=10
        )

        if response.status_code != 200:
            logger.error(f"LeetCode API returned status {response.status_code}")
            return None

        data = response.json()
        challenges = data.get("data", {}).get("dailyCodingChallengeV2", {}).get("challenges", [])

        # Find the challenge for the target date
        for challenge in challenges:
            if challenge.get("date") == target_date:
                question = challenge.get("question", {})
                return {
                    "date": challenge.get("date"),
                    "link": challenge.get("link"),
                    "questionId": question.get("questionId"),
                    "title": question.get("title"),
                    "titleSlug": question.get("titleSlug"),
                    "difficulty": question.get("difficulty")
                }

        return None

    except Exception as e:
        logger.error(f"Error fetching daily challenge for {target_date}: {e}")
        return None
