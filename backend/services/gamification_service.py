"""
Gamification Service
Handles streaks, points, achievements, and team challenges
"""

from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any
from backend.core.database import get_db_connection
import logging

logger = logging.getLogger(__name__)


class GamificationService:
    """Service for managing gamification features"""
    
    # Point values
    POINTS = {
        "easy": 1,
        "medium": 3,
        "hard": 5,
        "daily_challenge": 10,
        "streak_bonus": 2,
        "first_daily_solver": 5,
    }
    
    def record_daily_activity(self, username: str, problems_solved: int = 0, 
                             daily_challenge_completed: bool = False) -> Dict[str, Any]:
        """Record daily activity for a user"""
        try:
            today = date.today().isoformat()
            
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO daily_streaks (username, date, problems_solved, daily_challenge_completed)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(username, date) 
                    DO UPDATE SET 
                        problems_solved = problems_solved + ?,
                        daily_challenge_completed = ?
                """, (username, today, problems_solved, 1 if daily_challenge_completed else 0,
                      problems_solved, 1 if daily_challenge_completed else 0))
                
                conn.commit()
                
            return {"success": True, "date": today}
        except Exception as e:
            logger.error(f"Error recording daily activity for {username}: {e}")
            return {"success": False, "error": str(e)}
    
    def get_current_streak(self, username: str) -> int:
        """Get user's current streak"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Get all dates with activity, ordered desc
                cursor.execute("""
                    SELECT date FROM daily_streaks
                    WHERE username = ? AND (problems_solved > 0 OR daily_challenge_completed = 1)
                    ORDER BY date DESC
                """, (username,))
                
                dates = [row["date"] for row in cursor.fetchall()]
                
                if not dates:
                    return 0
                
                # Calculate streak
                streak = 0
                current_date = date.today()
                
                for activity_date in dates:
                    activity_date_obj = date.fromisoformat(activity_date)
                    
                    # Check if this date is consecutive
                    if activity_date_obj == current_date - timedelta(days=streak):
                        streak += 1
                    else:
                        break
                
                return streak
                
        except Exception as e:
            logger.error(f"Error getting streak for {username}: {e}")
            return 0
    
    def get_longest_streak(self, username: str) -> int:
        """Get user's longest streak ever"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT date FROM daily_streaks
                    WHERE username = ? AND (problems_solved > 0 OR daily_challenge_completed = 1)
                    ORDER BY date ASC
                """, (username,))
                
                dates = [date.fromisoformat(row["date"]) for row in cursor.fetchall()]
                
                if not dates:
                    return 0
                
                max_streak = 1
                current_streak = 1
                
                for i in range(1, len(dates)):
                    if dates[i] == dates[i-1] + timedelta(days=1):
                        current_streak += 1
                        max_streak = max(max_streak, current_streak)
                    else:
                        current_streak = 1
                
                return max_streak
                
        except Exception as e:
            logger.error(f"Error getting longest streak for {username}: {e}")
            return 0
    
    def award_points(self, username: str, points: int, reason: str, 
                    problem_title: Optional[str] = None, difficulty: Optional[str] = None) -> bool:
        """Award points to a user"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Record transaction
                cursor.execute("""
                    INSERT INTO point_transactions (username, points, reason, problem_title, difficulty)
                    VALUES (?, ?, ?, ?, ?)
                """, (username, points, reason, problem_title, difficulty))
                
                # Update user points
                cursor.execute("""
                    INSERT INTO user_points (username, points, weekly_points, monthly_points, all_time_points)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(username) DO UPDATE SET
                        points = points + ?,
                        weekly_points = weekly_points + ?,
                        monthly_points = monthly_points + ?,
                        all_time_points = all_time_points + ?,
                        last_updated = CURRENT_TIMESTAMP
                """, (username, points, points, points, points, points, points, points, points))
                
                conn.commit()
                
                # Check for achievements
                self.check_achievements(username)
                
                return True
                
        except Exception as e:
            logger.error(f"Error awarding points to {username}: {e}")
            return False
    
    def get_user_points(self, username: str) -> Dict[str, int]:
        """Get user's point totals"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT points, weekly_points, monthly_points, all_time_points
                    FROM user_points WHERE username = ?
                """, (username,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        "current": row["points"],
                        "weekly": row["weekly_points"],
                        "monthly": row["monthly_points"],
                        "all_time": row["all_time_points"]
                    }
                return {"current": 0, "weekly": 0, "monthly": 0, "all_time": 0}
                
        except Exception as e:
            logger.error(f"Error getting points for {username}: {e}")
            return {"current": 0, "weekly": 0, "monthly": 0, "all_time": 0}
    
    def check_achievements(self, username: str) -> List[str]:
        """Check and unlock achievements for a user"""
        newly_unlocked = []
        
        try:
            # Get user stats
            streak = self.get_current_streak(username)
            points = self.get_user_points(username)
            
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Get total problems solved
                cursor.execute("""
                    SELECT COUNT(*) as count FROM point_transactions
                    WHERE username = ? AND problem_title IS NOT NULL
                """, (username,))
                total_problems = cursor.fetchone()["count"]
                
                # Get daily challenges completed
                cursor.execute("""
                    SELECT COUNT(*) as count FROM daily_streaks
                    WHERE username = ? AND daily_challenge_completed = 1
                """, (username,))
                daily_challenges = cursor.fetchone()["count"]
                
                # Get hard problems solved
                cursor.execute("""
                    SELECT COUNT(*) as count FROM point_transactions
                    WHERE username = ? AND difficulty = 'Hard'
                """, (username,))
                hard_problems = cursor.fetchone()["count"]
                
                # Check achievements
                achievements_to_check = [
                    ("streak_7", streak >= 7),
                    ("streak_30", streak >= 30),
                    ("streak_100", streak >= 100),
                    ("problems_10", total_problems >= 10),
                    ("problems_50", total_problems >= 50),
                    ("problems_100", total_problems >= 100),
                    ("problems_500", total_problems >= 500),
                    ("daily_7", daily_challenges >= 7),
                    ("daily_30", daily_challenges >= 30),
                    ("hard_10", hard_problems >= 10),
                    ("hard_50", hard_problems >= 50),
                ]
                
                for achievement_key, condition in achievements_to_check:
                    if condition:
                        # Check if already unlocked
                        cursor.execute("""
                            SELECT id FROM user_achievements
                            WHERE username = ? AND achievement_key = ?
                        """, (username, achievement_key))
                        
                        if not cursor.fetchone():
                            # Unlock achievement
                            cursor.execute("""
                                INSERT INTO user_achievements (username, achievement_key)
                                VALUES (?, ?)
                            """, (username, achievement_key))
                            newly_unlocked.append(achievement_key)
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error checking achievements for {username}: {e}")
        
        return newly_unlocked
    
    def get_user_achievements(self, username: str) -> List[Dict[str, Any]]:
        """Get all achievements for a user"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT a.achievement_key, a.name, a.description, a.icon, a.category,
                           ua.unlocked_at
                    FROM achievements a
                    LEFT JOIN user_achievements ua 
                        ON a.achievement_key = ua.achievement_key AND ua.username = ?
                    ORDER BY ua.unlocked_at DESC NULLS LAST, a.category, a.name
                """, (username,))
                
                achievements = []
                for row in cursor.fetchall():
                    achievements.append({
                        "key": row["achievement_key"],
                        "name": row["name"],
                        "description": row["description"],
                        "icon": row["icon"],
                        "category": row["category"],
                        "unlocked": row["unlocked_at"] is not None,
                        "unlocked_at": row["unlocked_at"]
                    })
                
                return achievements
                
        except Exception as e:
            logger.error(f"Error getting achievements for {username}: {e}")
            return []
    
    def get_leaderboard(self, period: str = "weekly", limit: int = 10) -> List[Dict[str, Any]]:
        """Get points leaderboard"""
        try:
            field_map = {
                "weekly": "weekly_points",
                "monthly": "monthly_points",
                "all_time": "all_time_points"
            }
            
            field = field_map.get(period, "weekly_points")
            
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"""
                    SELECT username, {field} as points
                    FROM user_points
                    ORDER BY {field} DESC
                    LIMIT ?
                """, (limit,))
                
                leaderboard = []
                for i, row in enumerate(cursor.fetchall(), 1):
                    leaderboard.append({
                        "rank": i,
                        "username": row["username"],
                        "points": row["points"]
                    })
                
                return leaderboard
                
        except Exception as e:
            logger.error(f"Error getting leaderboard: {e}")
            return []


# Global instance
gamification_service = GamificationService()
