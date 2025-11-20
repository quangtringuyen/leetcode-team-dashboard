import requests
import time
from datetime import datetime, timedelta

# Headers to mimic a real browser and bypass filtering
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Origin': 'https://leetcode.com',
    'Referer': 'https://leetcode.com/',
    'Connection': 'keep-alive',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
}

def _make_request_with_retry(url, json_data, max_retries=3, timeout=15):
    """Make HTTP request with retry logic and proper headers."""
    for attempt in range(max_retries):
        try:
            response = requests.post(
                url,
                json=json_data,
                headers=HEADERS,
                timeout=timeout,
                verify=True
            )
            if response.status_code == 200:
                return response
            elif response.status_code == 429:  # Rate limited
                wait_time = (2 ** attempt) * 2  # Exponential backoff
                print(f"Rate limited. Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
                continue
            else:
                print(f"Request failed with status {response.status_code}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return response
        except requests.exceptions.RequestException as e:
            print(f"Request error (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise
    return None

def fetch_user_data(username):
    url = "https://leetcode.com/graphql"
    query = """
    query getUserProfile($username: String!) {
      matchedUser(username: $username) {
        username
        profile {
          realName
          userAvatar
          ranking
        }
        submitStatsGlobal {
          acSubmissionNum {
            difficulty
            count
            submissions
          }
        }
      }
    }
    """
    try:
        response = _make_request_with_retry(url, {"query": query, "variables": {"username": username}})
        if response and response.status_code == 200:
            data = response.json()["data"]["matchedUser"]
            profile = data["profile"]
            submissions = data["submitStatsGlobal"]["acSubmissionNum"]
            total_solved = sum([s["count"] for s in submissions])
            total_attempted = sum([s.get("submissions", 0) for s in submissions])

            # Calculate acceptance rate
            acceptance_rate = (total_solved / total_attempted) * 100 if total_attempted > 0 else None

            return {
                "username": data["username"],
                "realName": profile.get("realName", ""),
                "avatar": profile["userAvatar"],
                "ranking": profile.get("ranking", ""),
                "totalSolved": total_solved,
                "totalAttempted": total_attempted,
                "submissions": submissions,
                "acceptanceRate": round(acceptance_rate, 2) if acceptance_rate is not None else None
            }
        else:
            print(f"Failed to fetch data for {username}")
            return None
    except Exception as e:
        print(f"Error fetching user data for {username}: {e}")
        return None


def fetch_recent_submissions(username, limit=20):
    """
    Fetch recent accepted submissions for a user.
    Returns list of recent submissions with problem details.
    """
    url = "https://leetcode.com/graphql"
    query = """
    query recentAcSubmissions($username: String!, $limit: Int!) {
      recentAcSubmissionList(username: $username, limit: $limit) {
        id
        title
        titleSlug
        timestamp
      }
    }
    """
    try:
        response = _make_request_with_retry(
            url,
            {"query": query, "variables": {"username": username, "limit": limit}}
        )
        if response and response.status_code == 200:
            data = response.json()
            submissions = data.get("data", {}).get("recentAcSubmissionList", [])
            # Convert timestamps and format data
            result = []
            for sub in submissions:
                if sub and "timestamp" in sub:
                    timestamp = int(sub["timestamp"])
                    date = datetime.fromtimestamp(timestamp).date()
                    result.append({
                        "title": sub.get("title", "Unknown"),
                        "titleSlug": sub.get("titleSlug", ""),
                        "date": date,
                        "timestamp": timestamp
                    })
            return result
        return []
    except Exception as e:
        print(f"Error fetching recent submissions for {username}: {e}")
        return []


def fetch_daily_challenge():
    """
    Fetch today's LeetCode daily challenge.
    """
    url = "https://leetcode.com/graphql"
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
        response = _make_request_with_retry(url, {"query": query})
        if response and response.status_code == 200:
            data = response.json()
            challenge = data.get("data", {}).get("activeDailyCodingChallengeQuestion", {})
            if challenge:
                question = challenge.get("question", {})
                return {
                    "date": challenge.get("date"),
                    "link": f"https://leetcode.com{challenge.get('link', '')}",
                    "title": question.get("title"),
                    "titleSlug": question.get("titleSlug"),
                    "difficulty": question.get("difficulty"),
                    "questionId": question.get("questionId")
                }
        return None
    except Exception as e:
        print(f"Error fetching daily challenge: {e}")
        return None
