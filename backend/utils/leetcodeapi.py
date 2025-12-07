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
        import time
        start_time = time.time()

        response = requests.post(
            LEETCODE_API_URL,
            json={"query": query, "variables": {"username": username}},
            headers={"Content-Type": "application/json"},
            timeout=30  # Increased timeout to 30 seconds
        )

        elapsed = time.time() - start_time
        logger.info(f"fetch_user_data({username}): {elapsed:.2f}s - Status: {response.status_code}")

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

            if difficulty == "all":
                total_solved = count  # Use the "All" count as total
            elif difficulty == "easy":
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
        
        # Use cached monthly fetch
        challenges = _fetch_monthly_challenges(year, month)
        
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

from functools import lru_cache

@lru_cache(maxsize=12)  # Cache last 12 months requested
def _fetch_monthly_challenges(year: int, month: int) -> List[Dict[str, Any]]:
    """
    Fetch all daily challenges for a specific month (Cached)
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
            return []

        data = response.json()
        return data.get("data", {}).get("dailyCodingChallengeV2", {}).get("challenges", [])
        
    except Exception as e:
        logger.error(f"Error fetching monthly challenges for {year}-{month}: {e}")
        return []


def fetch_submissions_with_tags(username: str, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Fetch recent accepted submissions with problem tags.
    
    Args:
        username: LeetCode username
        limit: Number of submissions to fetch
        
    Returns:
        List of submissions with tags
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
            timeout=15
        )
        
        if response.status_code != 200:
            logger.error(f"LeetCode API returned status {response.status_code}")
            return []
        
        data = response.json()
        submissions = data.get("data", {}).get("recentAcSubmissionList", [])
        
        # For each submission, fetch problem details including tags (in parallel)
        submissions_with_tags = []
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        def process_submission(sub):
            title_slug = sub.get("titleSlug")
            if title_slug:
                # Fetch problem details (tags are available via problem query)
                problem_data = _fetch_problem_details(title_slug)
                if problem_data:
                    return {
                        "title": sub.get("title"),
                        "titleSlug": title_slug,
                        "timestamp": sub.get("timestamp"),
                        "tags": problem_data.get("tags", []),
                        "difficulty": problem_data.get("difficulty")
                    }
            return None

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(process_submission, sub) for sub in submissions]
            for future in as_completed(futures):
                result = future.result()
                if result:
                    submissions_with_tags.append(result)
        
        return submissions_with_tags
        
    except Exception as e:
        logger.error(f"Error fetching submissions with tags for {username}: {e}")
        return []


def _fetch_problem_details(title_slug: str) -> Optional[Dict[str, Any]]:
    """
    Fetch problem details including tags (internal helper).
    Cached in database to avoid repeated API calls.
    
    Args:
        title_slug: Problem title slug
        
    Returns:
        Dict with problem details or None
    """
    # Check DB cache first
    try:
        from backend.core.database import get_cached_data, set_cached_data
        cache_key = f"problem_details_{title_slug}"
        cached_data = get_cached_data(cache_key, ttl_seconds=86400 * 30)  # Cache for 30 days
        if cached_data:
            return cached_data
    except ImportError:
        pass  # Fallback if circular import or other issue
        
    query = """
    query questionData($titleSlug: String!) {
        question(titleSlug: $titleSlug) {
            questionId
            title
            difficulty
            topicTags {
                name
                slug
            }
        }
    }
    """
    
    try:
        response = requests.post(
            LEETCODE_API_URL,
            json={"query": query, "variables": {"titleSlug": title_slug}},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code != 200:
            return None
        
        data = response.json()
        question = data.get("data", {}).get("question")
        
        if not question:
            return None
        
        tags = [tag.get("name") for tag in question.get("topicTags", [])]
        
        result = {
            "questionId": question.get("questionId"),
            "title": question.get("title"),
            "difficulty": question.get("difficulty"),
            "tags": tags
        }
        
        # Save to DB cache
        try:
            from backend.core.database import set_cached_data
            set_cached_data(cache_key, result)
        except:
            pass
            
        return result
        
    except Exception as e:
        logger.warning(f"Error fetching problem details for {title_slug}: {e}")
        return None
