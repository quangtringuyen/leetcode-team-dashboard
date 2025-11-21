"""
Analytics and history endpoints
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import date, datetime, timedelta
from backend.core.security import get_current_user
from backend.core.storage import read_json, write_json
from backend.core.config import settings
from utils.leetcodeapi import fetch_user_data

router = APIRouter()

class WeeklySnapshot(BaseModel):
    week_start: str
    member: str
    totalSolved: int
    easy: int
    medium: int
    hard: int

@router.get("/history", response_model=List[WeeklySnapshot])
async def get_history(current_user: dict = Depends(get_current_user)):
    """Get historical weekly snapshots"""
    username = current_user["username"]

    history = read_json(settings.HISTORY_FILE, default={})
    user_history = history.get(username, [])

    return [WeeklySnapshot(**snapshot) for snapshot in user_history]

@router.post("/snapshot")
async def record_snapshot(current_user: dict = Depends(get_current_user)):
    """Record current week snapshot for all team members"""
    username = current_user["username"]

    # Get team members
    all_members = read_json(settings.MEMBERS_FILE, default={})
    user_members = all_members.get(username, [])

    if not user_members:
        return {"message": "No team members to snapshot", "count": 0}

    # Calculate week start (Monday)
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_start_str = week_start.isoformat()

    # Load history
    history = read_json(settings.HISTORY_FILE, default={})
    user_history = history.get(username, [])

    # Record snapshot for each member
    snapshots_added = 0
    for member in user_members:
        data = fetch_user_data(member["username"])
        if data:
            # Check if snapshot already exists for this week/member
            exists = any(
                s["week_start"] == week_start_str and s["member"] == member["username"]
                for s in user_history
            )

            if not exists:
                # Extract difficulty counts
                submissions = data.get("submissions", [])
                easy = next((s["count"] for s in submissions if s.get("difficulty") == "Easy"), 0)
                medium = next((s["count"] for s in submissions if s.get("difficulty") == "Medium"), 0)
                hard = next((s["count"] for s in submissions if s.get("difficulty") == "Hard"), 0)

                snapshot = {
                    "week_start": week_start_str,
                    "member": member["username"],
                    "totalSolved": data.get("totalSolved", 0),
                    "easy": easy,
                    "medium": medium,
                    "hard": hard,
                    "timestamp": datetime.utcnow().isoformat()
                }
                user_history.append(snapshot)
                snapshots_added += 1

    # Save history
    history[username] = user_history
    write_json(settings.HISTORY_FILE, history)

    return {
        "message": f"Recorded {snapshots_added} snapshots for week {week_start_str}",
        "count": snapshots_added,
        "week_start": week_start_str
    }

@router.get("/trends")
async def get_trends(
    weeks: int = 12,
    current_user: dict = Depends(get_current_user)
):
    """Get trend data for the last N weeks"""
    username = current_user["username"]

    history = read_json(settings.HISTORY_FILE, default={})
    user_history = history.get(username, [])

    if not user_history:
        return {"weeks": [], "members": {}}

    # Sort by week
    sorted_history = sorted(user_history, key=lambda x: x["week_start"])

    # Get last N weeks
    recent_history = sorted_history[-weeks * 10:]  # Approximate

    # Group by member
    trends = {}
    for snapshot in recent_history:
        member = snapshot["member"]
        if member not in trends:
            trends[member] = []
        trends[member].append({
            "week": snapshot["week_start"],
            "total": snapshot["totalSolved"],
            "easy": snapshot.get("easy", 0),
            "medium": snapshot.get("medium", 0),
            "hard": snapshot.get("hard", 0)
        })

    # Get unique weeks
    weeks_list = sorted(list(set(s["week_start"] for s in recent_history)))[-weeks:]

    return {
        "weeks": weeks_list,
        "members": trends
    }

@router.get("/week-over-week")
async def get_week_over_week(current_user: dict = Depends(get_current_user)):
    """Get week-over-week changes for team members"""
    username = current_user["username"]

    history = read_json(settings.HISTORY_FILE, default={})
    user_history = history.get(username, [])

    if not user_history:
        return []

    # Sort by week
    sorted_history = sorted(user_history, key=lambda x: x["week_start"])

    # Get last 2 weeks
    today = date.today()
    this_week_start = (today - timedelta(days=today.weekday())).isoformat()
    last_week_start = (today - timedelta(days=today.weekday() + 7)).isoformat()

    # Group by member
    this_week_data = {
        s["member"]: s["totalSolved"]
        for s in sorted_history
        if s["week_start"] == this_week_start
    }

    last_week_data = {
        s["member"]: s["totalSolved"]
        for s in sorted_history
        if s["week_start"] == last_week_start
    }

    # Calculate changes
    changes = []
    all_members = set(list(this_week_data.keys()) + list(last_week_data.keys()))

    for member in all_members:
        this_week = this_week_data.get(member, 0)
        last_week = last_week_data.get(member, 0)
        change = this_week - last_week

        changes.append({
            "member": member,
            "thisWeek": this_week,
            "lastWeek": last_week,
            "change": change
        })

    # Sort by change descending
    changes.sort(key=lambda x: x["change"], reverse=True)

    return changes
