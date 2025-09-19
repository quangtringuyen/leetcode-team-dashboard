# services/history_service.py
from __future__ import annotations
from typing import Dict, Any, List, Optional
from datetime import date, timedelta

from core.storage import Storage

HISTORY_PATH = "data/history.json"


def iso_week_start(d: date) -> date:
    return d - timedelta(days=d.weekday())


class HistoryService:
    def __init__(self, storage: Storage):
        self.storage = storage

    def load_history(self) -> Dict[str, Any]:
        return self.storage.read_json(HISTORY_PATH, default={})

    def save_history(self, hist: Dict[str, Any]) -> None:
        self.storage.write_json(HISTORY_PATH, hist)

    def record_weekly(self, owner: str, team_data: List[Dict[str, Any]], when: Optional[date] = None) -> Dict[str, Any]:
        hist = self.load_history()
        hist.setdefault(owner, {})

        week_start_str = iso_week_start(when or date.today()).isoformat()
        changed = False

        for member in team_data:
            uname = member["username"]
            name = member.get("name", uname)
            total = int(member.get("totalSolved", 0))
            easy = medium = hard = 0
            for s in member.get("submissions", []):
                if s.get("difficulty") == "Easy":
                    easy = int(s.get("count", 0))
                elif s.get("difficulty") == "Medium":
                    medium = int(s.get("count", 0))
                elif s.get("difficulty") == "Hard":
                    hard = int(s.get("count", 0))
            hist[owner].setdefault(uname, [])
            if not any(s.get("week_start") == week_start_str for s in hist[owner][uname]):
                hist[owner][uname].append({
                    "week_start": week_start_str,
                    "username": uname,
                    "name": name,
                    "totalSolved": total,
                    "Easy": easy, "Medium": medium, "Hard": hard
                })
                changed = True

        if changed:
            self.save_history(hist)
        return hist
