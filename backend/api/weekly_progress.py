"""
Get current week's progress by comparing live data with last snapshot
"""
from fastapi import APIRouter, Depends
from typing import Dict, Any
from datetime import date, timedelta
import logging

from backend.api.auth import get_current_user
from backend.core.database import get_user_history_from_db
from backend.utils.leetcodeapi import fetch_user_data
from backend.core.storage import read_json
from backend.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/current-week-progress")
async def get_current_week_progress(current_user: dict = Depends(get_current_user)):
    """
    Get current week's progress by comparing live totals with last week's snapshot.
    This provides real-time weekly progress without waiting for weekly snapshots.
    """
    username = current_user["username"]
    
    # Get members list
    all_members = read_json(settings.MEMBERS_FILE, default={})
    user_members = all_members.get(username, [])
    
    if not user_members:
        return {
            "current_week_total": 0,
            "previous_week_total": 0,
            "weekly_change": 0,
            "members_progress": []
        }
    
    # Get last week's snapshot data
    user_history_dict = get_user_history_from_db(username)
    
    # Calculate last week's start date
    today = date.today()
    last_week_start = (today - timedelta(days=today.weekday() + 7)).isoformat()
    
    # Get last week's totals from snapshots
    last_week_data = {}
    for member_username, snapshots in user_history_dict.items():
        for snapshot in snapshots:
            if snapshot.get("week_start") == last_week_start:
                last_week_data[member_username] = snapshot.get("totalSolved", 0)
                break
    
    # Fetch current live data for all members
    current_totals = {}
    members_progress = []
    
    for member in user_members:
        member_username = member.get("username")
        if not member_username:
            continue
            
        try:
            # Fetch live data
            live_data = fetch_user_data(member_username)
            if live_data:
                current_total = live_data.get("totalSolved", 0)
                current_totals[member_username] = current_total
                
                # Calculate this week's progress
                last_week_total = last_week_data.get(member_username, current_total)
                week_progress = current_total - last_week_total
                
                members_progress.append({
                    "username": member_username,
                    "name": member.get("name", member_username),
                    "current_total": current_total,
                    "last_week_total": last_week_total,
                    "week_progress": week_progress
                })
        except Exception as e:
            logger.error(f"Error fetching data for {member_username}: {e}")
            continue
    
    # Calculate team totals
    current_week_total = sum(m["week_progress"] for m in members_progress)
    previous_week_total_sum = sum(last_week_data.values())
    current_total_sum = sum(current_totals.values())
    
    # Calculate previous week's progress (if we have data from 2 weeks ago)
    two_weeks_ago_start = (today - timedelta(days=today.weekday() + 14)).isoformat()
    two_weeks_ago_data = {}
    for member_username, snapshots in user_history_dict.items():
        for snapshot in snapshots:
            if snapshot.get("week_start") == two_weeks_ago_start:
                two_weeks_ago_data[member_username] = snapshot.get("totalSolved", 0)
                break
    
    previous_week_total = 0
    if two_weeks_ago_data:
        for member_username in last_week_data.keys():
            last_week_val = last_week_data.get(member_username, 0)
            two_weeks_val = two_weeks_ago_data.get(member_username, last_week_val)
            previous_week_total += (last_week_val - two_weeks_val)
    
    # Calculate week-over-week change
    weekly_change = 0
    if previous_week_total > 0:
        weekly_change = ((current_week_total - previous_week_total) / previous_week_total) * 100
    elif current_week_total > 0:
        weekly_change = 100
    
    return {
        "current_week_total": current_week_total,
        "previous_week_total": previous_week_total,
        "weekly_change": round(weekly_change, 1),
        "members_progress": sorted(members_progress, key=lambda x: x["week_progress"], reverse=True)
    }
