"""
Database helper functions for last_state management (notification tracking)
"""

from typing import Dict, Any
from backend.core.database import get_db_connection
import logging

logger = logging.getLogger(__name__)


def get_last_state(owner_username: str) -> Dict[str, Dict[str, Any]]:
    """Get last state for all members of a user"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT member_username, total_solved, easy, medium, hard, 
                       ranking, real_name, avatar, acceptance_rate
                FROM last_state
                WHERE owner_username = ?
            """, (owner_username,))
            rows = cursor.fetchall()
            
            state = {}
            for row in rows:
                state[row["member_username"]] = {
                    "username": row["member_username"],
                    "totalSolved": row["total_solved"],
                    "easy": row["easy"],
                    "medium": row["medium"],
                    "hard": row["hard"],
                    "ranking": row["ranking"],
                    "realName": row["real_name"],
                    "avatar": row["avatar"],
                    "acceptanceRate": row["acceptance_rate"]
                }
            return state
    except Exception as e:
        logger.error(f"Error getting last_state for {owner_username}: {e}")
        return {}


def update_last_state(owner_username: str, member_data: Dict[str, Dict[str, Any]]) -> bool:
    """Update last state for members"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            for member_username, data in member_data.items():
                cursor.execute("""
                    INSERT OR REPLACE INTO last_state 
                    (owner_username, member_username, total_solved, easy, medium, hard,
                     ranking, real_name, avatar, acceptance_rate, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    owner_username,
                    data.get("username", member_username),
                    data.get("totalSolved", 0),
                    data.get("easy", 0),
                    data.get("medium", 0),
                    data.get("hard", 0),
                    data.get("ranking"),
                    data.get("realName"),
                    data.get("avatar"),
                    data.get("acceptanceRate")
                ))
            
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"Error updating last_state for {owner_username}: {e}")
        return False
