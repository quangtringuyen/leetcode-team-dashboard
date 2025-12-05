"""
Streak tracking utilities for LeetCode dashboard
Calculates daily and weekly solving streaks for team members
"""

from datetime import date, datetime, timedelta
from typing import Dict, List, Any
from collections import defaultdict


def calculate_streaks(history_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate current streak, longest streak, and streak history for a member.
    
    Args:
        history_data: List of weekly snapshots sorted by week_start (oldest first)
        
    Returns:
        Dict with current_streak, longest_streak, streak_history, last_active_date
    """
    if not history_data:
        return {
            "current_streak": 0,
            "longest_streak": 0,
            "streak_history": [],
            "last_active_date": None,
            "streak_status": "inactive"
        }
    
    # Sort by week_start to ensure chronological order
    sorted_data = sorted(history_data, key=lambda x: x.get("week_start", ""))
    
    # Calculate week-over-week activity
    active_weeks = []
    for i in range(len(sorted_data)):
        current = sorted_data[i]
        
        # Check if there was progress this week
        if i == 0:
            # First week - consider active if solved any problems
            if current.get("totalSolved", 0) > 0:
                active_weeks.append(current["week_start"])
        else:
            previous = sorted_data[i - 1]
            # Active if total increased
            if current.get("totalSolved", 0) > previous.get("totalSolved", 0):
                active_weeks.append(current["week_start"])
    
    # Calculate streaks
    current_streak = 0
    longest_streak = 0
    temp_streak = 0
    
    # Get today's week start (Monday)
    today = date.today()
    current_week_start = (today - timedelta(days=today.weekday())).isoformat()
    
    # Check streaks from most recent to oldest
    for i in range(len(active_weeks) - 1, -1, -1):
        week = active_weeks[i]
        
        if i == len(active_weeks) - 1:
            # Most recent active week
            temp_streak = 1
            
            # Check if it's current week or last week
            week_date = date.fromisoformat(week)
            last_week_start = (today - timedelta(days=today.weekday() + 7)).isoformat()
            
            if week >= last_week_start:
                current_streak = 1
        else:
            # Check if consecutive weeks
            current_week_date = date.fromisoformat(active_weeks[i])
            next_week_date = date.fromisoformat(active_weeks[i + 1])
            
            # Weeks are consecutive if exactly 7 days apart
            if (next_week_date - current_week_date).days == 7:
                temp_streak += 1
                if i == len(active_weeks) - 2:  # Second to last
                    current_streak = temp_streak
            else:
                # Streak broken
                longest_streak = max(longest_streak, temp_streak)
                temp_streak = 1
    
    longest_streak = max(longest_streak, temp_streak)
    
    # Determine streak status
    if not active_weeks:
        streak_status = "inactive"
        last_active = None
    else:
        last_active = active_weeks[-1]
        last_active_date = date.fromisoformat(last_active)
        days_since_active = (today - last_active_date).days
        
        if current_streak > 0:
            streak_status = "active"
        elif days_since_active <= 14:
            streak_status = "at_risk"
        else:
            streak_status = "broken"
    
    return {
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "active_weeks": active_weeks,
        "last_active_date": active_weeks[-1] if active_weeks else None,
        "streak_status": streak_status,
        "total_active_weeks": len(active_weeks)
    }


def get_team_streaks(history: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """
    Calculate streaks for all team members.
    
    Args:
        history: Dict mapping member usernames to their history data
        
    Returns:
        List of dicts with member, current_streak, longest_streak, etc.
    """
    team_streaks = []
    
    for member, member_history in history.items():
        streak_data = calculate_streaks(member_history)
        
        team_streaks.append({
            "member": member,
            **streak_data
        })
    
    # Sort by current streak (descending)
    team_streaks.sort(key=lambda x: x["current_streak"], reverse=True)
    
    return team_streaks


def get_streak_leaderboard(team_streaks: List[Dict[str, Any]], limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get top members by current streak.
    
    Args:
        team_streaks: Output from get_team_streaks()
        limit: Maximum number of members to return
        
    Returns:
        List of top streak holders
    """
    # Filter only active streaks
    active_streaks = [s for s in team_streaks if s["current_streak"] > 0]
    
    # Sort by current streak, then by longest streak
    active_streaks.sort(
        key=lambda x: (x["current_streak"], x["longest_streak"]), 
        reverse=True
    )
    
    return active_streaks[:limit]


def get_members_at_risk(team_streaks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Get members whose streaks are about to break.
    
    Args:
        team_streaks: Output from get_team_streaks()
        
    Returns:
        List of members with at-risk streaks
    """
    return [s for s in team_streaks if s["streak_status"] == "at_risk"]
