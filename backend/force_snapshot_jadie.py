
import sqlite3
import requests
import json
from datetime import date, timedelta
import logging
import sys
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = "/app/data/leetcode.db"



def fetch_leetcode_stats(username):
    url = "https://leetcode.com/graphql"
    query = """
    query getUserProfile($username: String!) {
        matchedUser(username: $username) {
            submitStats {
                acSubmissionNum {
                    difficulty
                    count
                }
            }
        }
    }
    """
    try:
        response = requests.post(url, json={"query": query, "variables": {"username": username}}, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code == 200:
            data = response.json()
            if "data" in data and "matchedUser" in data["data"]:
                stats = data["data"]["matchedUser"]["submitStats"]["acSubmissionNum"]
                result = {"total": 0, "easy": 0, "medium": 0, "hard": 0}
                for s in stats:
                    if s["difficulty"] == "All": result["total"] = s["count"]
                    if s["difficulty"] == "Easy": result["easy"] = s["count"]
                    if s["difficulty"] == "Medium": result["medium"] = s["count"]
                    if s["difficulty"] == "Hard": result["hard"] = s["count"]
                return result
            else:
                logger.error(f"Unexpected data structure: {data}")
        else:
            logger.error(f"HTTP {response.status_code}: {response.text}")
    except Exception as e:
        logger.error(f"Failed to fetch {username}: {e}")
    return None

def force_snapshot(username):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if snapshot exists
    cursor.execute("SELECT count(*) FROM snapshots WHERE username=?", (username,))
    if cursor.fetchone()[0] > 0:
        logger.info(f"Snapshot already exists for {username}")
        conn.close()
        return

    logger.info(f"Fetching stats for {username}...")
    stats = fetch_leetcode_stats(username)
    
    if stats:
        today = date.today()
        # Calculate start of week (Monday)
        week_start = (today - timedelta(days=today.weekday())).isoformat()
        
        logger.info(f"Inserting snapshot for {username}: {stats}")
        cursor.execute("""
            INSERT INTO snapshots (username, week_start, total_solved, easy, medium, hard, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (username, week_start, stats["total"], stats["easy"], stats["medium"], stats["hard"], today.isoformat()))
        conn.commit()
    else:
        logger.error("Could not fetch stats.")
        
    conn.close()

if __name__ == "__main__":
    force_snapshot("gimmealeadtocode")
