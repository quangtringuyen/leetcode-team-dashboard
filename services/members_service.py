# services/members_service.py
from __future__ import annotations
from typing import List, Dict, Any

from backend.core.database import get_db_connection

# Replaces Storage-based implementation with DB implementation
class MembersService:
    def __init__(self, storage: Any = None):
        # Storage is no longer used but kept for signature compatibility if needed
        pass

    def load_all_members(self) -> Dict[str, Any]:
        """Load all members grouped by team owner"""
        result = {}
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT username, name, team_owner, status FROM members WHERE status != 'suspended'")
            rows = cursor.fetchall()
            
            for row in rows:
                owner = row["team_owner"]
                member = dict(row)
                if owner not in result:
                    result[owner] = []
                result[owner].append(member)
        return result

    def save_all_members(self, all_members: Dict[str, Any]) -> None:
        # DB is source of truth, this might be legacy sync?
        # For now, do nothing or implement complex sync if needed.
        # Scheduler doesn't call this.
        pass

    def load_members(self, owner: str) -> List[Dict[str, str]]:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT username, name, team_owner, status FROM members WHERE team_owner = ?", (owner,))
            return [dict(row) for row in cursor.fetchall()]

    def save_members(self, owner: str, members: List[Dict[str, str]]) -> None:
        pass

    def add_member(self, owner: str, name: str, username: str) -> bool:
        # Handled by API
        return True

    def remove_member(self, owner: str, username: str) -> None:
        # Handled by API
        pass
