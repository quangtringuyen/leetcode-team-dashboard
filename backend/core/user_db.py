"""
Database helper functions for user management
"""

from typing import Optional, Dict, Any
from backend.core.database import get_db_connection
import logging

logger = logging.getLogger(__name__)


def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Get user from database by username"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT username, email, full_name, hashed_password, disabled
                FROM users
                WHERE username = ?
            """, (username,))
            row = cursor.fetchone()
            
            if row:
                return {
                    "username": row["username"],
                    "email": row["email"],
                    "full_name": row["full_name"],
                    "hashed_password": row["hashed_password"],
                    "disabled": bool(row["disabled"])
                }
            return None
    except Exception as e:
        logger.error(f"Error getting user {username}: {e}")
        return None


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get user from database by email"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT username, email, full_name, hashed_password, disabled
                FROM users
                WHERE email = ?
            """, (email,))
            row = cursor.fetchone()
            
            if row:
                return {
                    "username": row["username"],
                    "email": row["email"],
                    "full_name": row["full_name"],
                    "hashed_password": row["hashed_password"],
                    "disabled": bool(row["disabled"])
                }
            return None
    except Exception as e:
        logger.error(f"Error getting user by email {email}: {e}")
        return None


def create_user(username: str, email: str, hashed_password: str, full_name: Optional[str] = None) -> bool:
    """Create a new user in the database"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (username, email, full_name, hashed_password, disabled)
                VALUES (?, ?, ?, ?, 0)
            """, (username, email, full_name or "", hashed_password))
            conn.commit()
            logger.info(f"Created user: {username}")
            return True
    except Exception as e:
        logger.error(f"Error creating user {username}: {e}")
        return False


def update_user(username: str, email: Optional[str] = None, full_name: Optional[str] = None, 
                hashed_password: Optional[str] = None) -> bool:
    """Update user information"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            updates = []
            params = []
            
            if email is not None:
                updates.append("email = ?")
                params.append(email)
            if full_name is not None:
                updates.append("full_name = ?")
                params.append(full_name)
            if hashed_password is not None:
                updates.append("hashed_password = ?")
                params.append(hashed_password)
            
            if not updates:
                return True
            
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(username)
            
            query = f"UPDATE users SET {', '.join(updates)} WHERE username = ?"
            cursor.execute(query, params)
            conn.commit()
            logger.info(f"Updated user: {username}")
            return True
    except Exception as e:
        logger.error(f"Error updating user {username}: {e}")
        return False


def get_all_users() -> Dict[str, Dict[str, Any]]:
    """Get all users from database (for backward compatibility)"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT username, email, full_name, hashed_password, disabled
                FROM users
            """)
            rows = cursor.fetchall()
            
            users = {}
            for row in rows:
                users[row["username"]] = {
                    "username": row["username"],
                    "email": row["email"],
                    "full_name": row["full_name"],
                    "hashed_password": row["hashed_password"],
                    "disabled": bool(row["disabled"])
                }
            return users
    except Exception as e:
        logger.error(f"Error getting all users: {e}")
        return {}
