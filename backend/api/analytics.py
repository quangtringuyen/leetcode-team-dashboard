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
    # Calculate changes
    changes = []
    all_members = set(list(this_week_data.keys()) + list(last_week_data.keys()))

    # Calculate ranks
    this_week_ranks = {
        m: i + 1 
        for i, (m, _) in enumerate(sorted(this_week_data.items(), key=lambda x: x[1], reverse=True))
    }
    last_week_ranks = {
        m: i + 1 
        for i, (m, _) in enumerate(sorted(last_week_data.items(), key=lambda x: x[1], reverse=True))
    }

    for member in all_members:
        this_week = this_week_data.get(member, 0)
        last_week = last_week_data.get(member, 0)
        change = this_week - last_week
        
        # Calculate percentage change
        if last_week > 0:
            pct_change = (change / last_week) * 100
        elif this_week > 0:
            pct_change = 100.0
        else:
            pct_change = 0.0
            
        # Calculate rank delta (positive means improved rank, e.g. 5 -> 3 is +2)
        this_rank = this_week_ranks.get(member)
        last_rank = last_week_ranks.get(member)
        
        rank_delta = 0
        if this_rank and last_rank:
            rank_delta = last_rank - this_rank

        # Format week date
        week_date_obj = date.fromisoformat(this_week_start)
        formatted_week = week_date_obj.strftime("%b %d, %Y")

        changes.append({
            "week": formatted_week,
            "member": member,
            "previous": last_week,
            "current": this_week,
            "change": change,
            "pct_change": round(pct_change, 1),
            "rank": this_rank,
            "rank_delta": rank_delta
        })

    # Sort by current total descending (to match rank)
    changes.sort(key=lambda x: x["current"], reverse=True)

    return changes

@router.get("/weekly-progress")
async def get_weekly_progress(
    weeks: int = 12,
    current_user: dict = Depends(get_current_user)
):
    """
    Get weekly progress for all team members with forward-fill.
    Forward-fill ensures smooth lines even when snapshots are missing.
    """
    username = current_user["username"]
    
    # Load history
    history = read_json(settings.HISTORY_FILE, default={})
    user_history_dict = history.get(username, {})
    
    if not user_history_dict:
        return {"weeks": [], "members": {}}
    
    # Get team members for names
    all_members = read_json(settings.MEMBERS_FILE, default={})
    user_members = all_members.get(username, [])
    member_names = {m["username"]: m.get("name", m["username"]) for m in user_members}
    
    # Determine week range
    today = date.today()
    end_week = today - timedelta(days=today.weekday())  # This week's Monday
    start_week = end_week - timedelta(weeks=weeks-1)
    
    # Generate all weeks in range
    all_weeks = []
    current = start_week
    while current <= end_week:
        all_weeks.append(current.isoformat())
        current += timedelta(weeks=1)
    
    # Process each member with forward-fill
    members_data = {}
    for member_username, snapshots in user_history_dict.items():
        # Sort snapshots by week
        sorted_snapshots = sorted(snapshots, key=lambda x: x.get("week_start", ""))
        
        # Create lookup dict
        snapshot_dict = {s["week_start"]: s["totalSolved"] for s in sorted_snapshots}
        
        # Forward-fill algorithm
        filled_data = []
        last_value = 0
        for week in all_weeks:
            if week in snapshot_dict:
                last_value = snapshot_dict[week]
            filled_data.append(last_value)
        
        members_data[member_username] = {
            "name": member_names.get(member_username, member_username),
            "data": filled_data
        }
    
    return {
        "weeks": all_weeks,
        "members": members_data
    }

@router.get("/accepted-trend")
async def get_accepted_trend(
    days: int = 30,
    current_user: dict = Depends(get_current_user)
):
    """
    Get daily accepted problems trend.
    Primary: Use LeetCode calendar API
    Fallback: Use weekly snapshots (place gains on Monday)
    """
    import requests
    import json as json_lib
    
    username = current_user["username"]
    
    # Get team members
    all_members = read_json(settings.MEMBERS_FILE, default={})
    user_members = all_members.get(username, [])
    
    if not user_members:
        return []
    
    # Calculate date range
    end_date = date.today()
    start_date = end_date - timedelta(days=days-1)
    
    # Try calendar API for each member
    result = []
    members_with_calendar = set()
    
    for member in user_members:
        member_username = member["username"]
        member_name = member.get("name", member_username)
        
        # Fetch calendar data
        try:
            url = f"https://leetcode.com/api/user_submission_calendar/?username={member_username}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Parse submission calendar
            calendar_str = data.get("submission_calendar", "{}")
            calendar = json_lib.loads(calendar_str)
            
            if calendar:
                members_with_calendar.add(member_username)
                
                # Convert timestamps to dates and filter by range
                for timestamp_str, count in calendar.items():
                    timestamp = int(timestamp_str)
                    submission_date = datetime.utcfromtimestamp(timestamp).date()
                    
                    if start_date <= submission_date <= end_date:
                        result.append({
                            "date": submission_date.isoformat(),
                            "member": member_name,
                            "username": member_username,
                            "accepted": int(count)
                        })
        except Exception:
            # Calendar API failed, will use fallback
            pass
    
    # Fallback: Use snapshot diffs for members without calendar data
    history = read_json(settings.HISTORY_FILE, default={})
    user_history_dict = history.get(username, {})
    
    for member in user_members:
        member_username = member["username"]
        member_name = member.get("name", member_username)
        
        # Skip if we already have calendar data
        if member_username in members_with_calendar:
            continue
        
        # Get snapshots for this member
        snapshots = user_history_dict.get(member_username, [])
        if not snapshots:
            continue
        
        # Sort by week
        sorted_snapshots = sorted(snapshots, key=lambda x: x.get("week_start", ""))
        
        # Calculate weekly gains and place on Monday
        for i in range(1, len(sorted_snapshots)):
            prev = sorted_snapshots[i-1]
            curr = sorted_snapshots[i]
            
            prev_total = prev.get("totalSolved", 0)
            curr_total = curr.get("totalSolved", 0)
            gain = curr_total - prev_total
            
            if gain > 0:
                week_start = curr.get("week_start")
                if week_start:
                    week_date = date.fromisoformat(week_start)
                    if start_date <= week_date <= end_date:
                        result.append({
                            "date": week_date.isoformat(),
                            "member": member_name,
                            "username": member_username,
                            "accepted": gain
                        })
    
    # Sort by date
    result.sort(key=lambda x: x["date"])
    
    return result
