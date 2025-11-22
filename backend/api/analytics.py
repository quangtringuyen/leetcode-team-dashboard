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
from backend.utils.leetcodeapi import fetch_user_data

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
    # History structure: {owner: {member_username: [snapshots]}}
    user_history_dict = history.get(username, {})

    # Flatten all snapshots from all members
    all_snapshots = []
    for member_username, snapshots in user_history_dict.items():
        all_snapshots.extend(snapshots)

    return [WeeklySnapshot(**snapshot) for snapshot in all_snapshots]

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

    # Load history - Structure: {owner: {member_username: [snapshots]}}
    history = read_json(settings.HISTORY_FILE, default={})
    if username not in history:
        history[username] = {}
    user_history = history[username]

    # Record snapshot for each member
    snapshots_added = 0
    for member in user_members:
        member_username = member["username"]
        data = fetch_user_data(member_username)
        if data:
            # Initialize member's history if not exists
            if member_username not in user_history:
                user_history[member_username] = []

            # Check if snapshot already exists for this week/member
            exists = any(
                s.get("week_start") == week_start_str
                for s in user_history[member_username]
            )

            if not exists:
                # Extract difficulty counts
                submissions = data.get("submissions", [])
                easy = next((s["count"] for s in submissions if s.get("difficulty") == "Easy"), 0)
                medium = next((s["count"] for s in submissions if s.get("difficulty") == "Medium"), 0)
                hard = next((s["count"] for s in submissions if s.get("difficulty") == "Hard"), 0)

                snapshot = {
                    "week_start": week_start_str,
                    "member": member_username,
                    "totalSolved": data.get("totalSolved", 0),
                    "easy": int(easy),
                    "medium": int(medium),
                    "hard": int(hard),
                    "timestamp": datetime.utcnow().isoformat()
                }
                user_history[member_username].append(snapshot)
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
    # History structure: {owner: {member_username: [snapshots]}}
    user_history_dict = history.get(username, {})

    if not user_history_dict:
        return {"weeks": [], "members": {}}

    # Group by member and extract recent weeks
    trends = {}
    all_weeks = set()

    for member_username, snapshots in user_history_dict.items():
        # Sort by week
        sorted_snapshots = sorted(snapshots, key=lambda x: x.get("week_start", ""))

        # Get last N weeks worth of snapshots
        recent_snapshots = sorted_snapshots[-weeks:]

        trends[member_username] = []
        for snapshot in recent_snapshots:
            week_start = snapshot.get("week_start")
            if week_start:
                all_weeks.add(week_start)
                trends[member_username].append({
                    "week": week_start,
                    "total": snapshot.get("totalSolved", 0),
                    "easy": snapshot.get("easy", 0),
                    "medium": snapshot.get("medium", 0),
                    "hard": snapshot.get("hard", 0)
                })

    # Get unique weeks
    weeks_list = sorted(list(all_weeks))[-weeks:]

    return {
        "weeks": weeks_list,
        "members": trends
    }

@router.get("/week-over-week")
async def get_week_over_week(current_user: dict = Depends(get_current_user)):
    """Get week-over-week changes for team members"""
    username = current_user["username"]

    history = read_json(settings.HISTORY_FILE, default={})
    # History structure: {owner: {member_username: [snapshots]}}
    user_history_dict = history.get(username, {})

    if not user_history_dict:
        return []

    # Get last 2 weeks
    today = date.today()
    this_week_start = (today - timedelta(days=today.weekday())).isoformat()
    last_week_start = (today - timedelta(days=today.weekday() + 7)).isoformat()

    # Extract data for each member
    this_week_data = {}
    last_week_data = {}

    for member_username, snapshots in user_history_dict.items():
        for snapshot in snapshots:
            week = snapshot.get("week_start")
            total = snapshot.get("totalSolved", 0)

            if week == this_week_start:
                this_week_data[member_username] = total
            elif week == last_week_start:
                last_week_data[member_username] = total

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
