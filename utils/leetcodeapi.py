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
        return {
            "username": data["username"],
            "realName": profile.get("realName", ""),
            "avatar": profile["userAvatar"],
            "ranking": profile.get("ranking", ""),
            "totalSolved": total_solved,
            "submissions": submissions
        }
    else:
        return None
