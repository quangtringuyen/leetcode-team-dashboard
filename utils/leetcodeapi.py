import requests
import json
from datetime import datetime

def fetch_user_data(username):
    query = '''
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
        }
        userCalendar {
          submissionCalendar
        }
      }
    }
    '''
    variables = {"username": username}
    response = requests.post(
        "https://leetcode.com/graphql",
        json={"query": query, "variables": variables}
    )

    if response.status_code != 200:
        raise Exception(f"GraphQL Error: {response.status_code}\n{response.text}")

    user_data = response.json()["data"]["matchedUser"]
    profile = user_data.get("profile", {})

    # Process submission stats
    stats_raw = user_data.get("submitStats", {}).get("acSubmissionNum", [])
    stats = {i["difficulty"]: i["count"] for i in stats_raw}
    stats["Total"] = sum(stats.values())

    # Process submission calendar
    calendar_json = user_data.get("userCalendar", {}).get("submissionCalendar", "{}")
    submission_history = {}
    try:
        calendar_data = json.loads(calendar_json)
        for ts, count in calendar_data.items():
            date = datetime.utcfromtimestamp(int(ts)).strftime("%Y-%m-%d")
            submission_history[date] = count
    except Exception as e:
        print("⚠️ Failed to parse submission calendar:", e)

    return {
        "username": user_data.get("username"),
        "real_name": profile.get("realName", ""),
        "avatar": profile.get("userAvatar", ""),
        "ranking": profile.get("ranking", "N/A"),
        "stats": stats,
        "submission_history": submission_history
    }
