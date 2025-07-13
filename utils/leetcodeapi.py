import requests

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
