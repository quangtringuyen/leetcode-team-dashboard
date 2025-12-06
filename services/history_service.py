# services/history_service.py
from __future__ import annotations
from typing import Dict, Any, List, Optional
from datetime import date, timedelta

from core.storage import Storage

HISTORY_PATH = "data/history.json"


def iso_week_start(d: date) -> date:
    return d - timedelta(days=d.weekday())


from datetime import datetime
from backend.core.database import get_db_connection

class HistoryService:
    def __init__(self, storage: Storage):
        self.storage = storage

    def load_history(self) -> Dict[str, Any]:
        # Legacy support or just return empty if not used
        return {}

    def save_history(self, hist: Dict[str, Any]) -> None:
        pass

    def record_weekly(self, owner: str, team_data: List[Dict[str, Any]], when: Optional[date] = None) -> Dict[str, Any]:
        week_start_str = iso_week_start(when or date.today()).isoformat()
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            for member in team_data:
                uname = member["username"]
                total = int(member.get("totalSolved", 0))
                
                # Extract difficulty
                easy = int(member.get("easy", 0))
                medium = int(member.get("medium", 0))
                hard = int(member.get("hard", 0))
                
                # If difficulty not in top level, check submissions list (legacy format)
                if easy == 0 and medium == 0 and hard == 0:
                     for s in member.get("submissions", []):
                        if s.get("difficulty") == "Easy":
                            easy = int(s.get("count", 0))
                        elif s.get("difficulty") == "Medium":
                            medium = int(s.get("count", 0))
                        elif s.get("difficulty") == "Hard":
                            hard = int(s.get("count", 0))

                try:
                    cursor.execute("""
                    INSERT OR IGNORE INTO snapshots 
                    (username, week_start, total_solved, easy, medium, hard, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        uname,
                        week_start_str,
                        total,
                        easy,
                        medium,
                        hard,
                        datetime.utcnow().isoformat()
                    ))
                except Exception as e:
                    print(f"Error recording history for {uname}: {e}")
            
            conn.commit()
            
        return {}
