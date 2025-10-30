import requests
from datetime import datetime, timedelta

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
    response = requests.post(url, json={"query": query, "variables": {"username": username}})
    if response.status_code == 200:
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
        response = requests.post(
            url,
            json={"query": query, "variables": {"username": username, "limit": limit}},
            timeout=15
        )
        if response.status_code == 200:
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
        response = requests.post(url, json={"query": query}, timeout=15)
        if response.status_code == 200:
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
