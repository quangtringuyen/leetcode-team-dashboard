"""
Database schema for gamification features
Run this to add new tables for streaks, points, achievements, and team challenges
"""

import sqlite3
import logging
from backend.core.database import get_db_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_gamification_tables():
    """Create all tables needed for gamification features"""
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 1. Daily Streaks Table
        logger.info("Creating daily_streaks table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_streaks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                date DATE NOT NULL,
                problems_solved INTEGER DEFAULT 0,
                daily_challenge_completed INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(username, date)
            )
        """)
        
        # 2. User Points Table
        logger.info("Creating user_points table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_points (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                points INTEGER DEFAULT 0,
                weekly_points INTEGER DEFAULT 0,
                monthly_points INTEGER DEFAULT 0,
                all_time_points INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(username)
            )
        """)
        
        # 3. Point Transactions (for audit trail)
        logger.info("Creating point_transactions table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS point_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                points INTEGER NOT NULL,
                reason TEXT NOT NULL,
                problem_title TEXT,
                difficulty TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 4. Achievements Table
        logger.info("Creating achievements table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                achievement_key TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                icon TEXT,
                points_required INTEGER,
                category TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 5. User Achievements (unlocked achievements)
        logger.info("Creating user_achievements table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                achievement_key TEXT NOT NULL,
                unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(username, achievement_key),
                FOREIGN KEY (achievement_key) REFERENCES achievements(achievement_key)
            )
        """)
        
        # 6. Team Challenges
        logger.info("Creating team_challenges table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS team_challenges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                goal_type TEXT NOT NULL,
                goal_value INTEGER NOT NULL,
                current_value INTEGER DEFAULT 0,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 7. Team Challenge Participants
        logger.info("Creating challenge_participants table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS challenge_participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                challenge_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                contribution INTEGER DEFAULT 0,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(challenge_id, username),
                FOREIGN KEY (challenge_id) REFERENCES team_challenges(id)
            )
        """)
        
        # 8. Problem Recommendations
        logger.info("Creating problem_recommendations table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS problem_recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                problem_title TEXT NOT NULL,
                problem_slug TEXT NOT NULL,
                difficulty TEXT,
                topics TEXT,
                reason TEXT,
                priority INTEGER DEFAULT 0,
                completed INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 9. Solution Shares
        logger.info("Creating solution_shares table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS solution_shares (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                problem_title TEXT NOT NULL,
                problem_slug TEXT NOT NULL,
                solution_text TEXT,
                language TEXT,
                time_complexity TEXT,
                space_complexity TEXT,
                kudos_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 10. Solution Kudos
        logger.info("Creating solution_kudos table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS solution_kudos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                solution_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(solution_id, username),
                FOREIGN KEY (solution_id) REFERENCES solution_shares(id)
            )
        """)
        
        # Create indexes for better performance
        logger.info("Creating indexes...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_streaks_username_date ON daily_streaks(username, date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_points_username ON user_points(username)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_username ON point_transactions(username, created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_achievements_username ON user_achievements(username)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_recommendations_username ON problem_recommendations(username, completed)")
        
        conn.commit()
        logger.info("✓ All gamification tables created successfully!")


def seed_achievements():
    """Seed initial achievements"""
    
    achievements = [
        # Streak Achievements
        ("streak_7", "Week Warrior", "Maintain a 7-day streak", "🔥", 0, "streak"),
        ("streak_30", "Month Master", "Maintain a 30-day streak", "🔥🔥", 0, "streak"),
        ("streak_100", "Century Solver", "Maintain a 100-day streak", "🔥🔥🔥", 0, "streak"),
        
        # Problem Count Achievements
        ("problems_10", "Getting Started", "Solve 10 problems", "🌱", 0, "problems"),
        ("problems_50", "Problem Solver", "Solve 50 problems", "🌿", 0, "problems"),
        ("problems_100", "Centurion", "Solve 100 problems", "🌳", 0, "problems"),
        ("problems_500", "Elite Coder", "Solve 500 problems", "🏆", 0, "problems"),
        
        # Daily Challenge Achievements
        ("daily_7", "Challenge Accepted", "Complete 7 daily challenges", "📅", 0, "daily"),
        ("daily_30", "Daily Devotee", "Complete 30 daily challenges", "📅📅", 0, "daily"),
        
        # Difficulty Achievements
        ("hard_10", "Hard Mode", "Solve 10 hard problems", "💪", 0, "difficulty"),
        ("hard_50", "Hard Core", "Solve 50 hard problems", "💪💪", 0, "difficulty"),
        
        # Speed Achievements
        ("first_solver", "Speed Demon", "First to solve daily challenge", "⚡", 0, "speed"),
        
        # Team Achievements
        ("team_challenge_1", "Team Player", "Complete a team challenge", "👥", 0, "team"),
        ("team_challenge_5", "Team Champion", "Complete 5 team challenges", "👥👥", 0, "team"),
    ]
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        for achievement in achievements:
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO achievements 
                    (achievement_key, name, description, icon, points_required, category)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, achievement)
            except Exception as e:
                logger.error(f"Error inserting achievement {achievement[0]}: {e}")
        
        conn.commit()
        logger.info(f"✓ Seeded {len(achievements)} achievements")


if __name__ == "__main__":
    logger.info("=" * 70)
    logger.info("Gamification Database Setup")
    logger.info("=" * 70)
    
    create_gamification_tables()
    seed_achievements()
    
    logger.info("=" * 70)
    logger.info("Setup complete!")
    logger.info("=" * 70)
