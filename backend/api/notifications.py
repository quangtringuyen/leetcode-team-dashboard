"""
Notifications API endpoints
"""

from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from backend.core.security import get_current_user
from backend.core.storage import read_json
from backend.core.config import settings
from backend.utils.notification_service import (
    notification_service,
    check_and_notify_streaks,
    check_and_notify_milestones
)
from backend.utils.streak_tracker import get_team_streaks

router = APIRouter()


@router.get("/notifications")
async def get_notifications(
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """
    Get recent notifications for the current user's team.
    """
    username = current_user["username"]
    
    # Get all notifications (in-app)
    notifications = notification_service.get_notifications(limit=limit)
    
    return {
        "notifications": notifications,
        "count": len(notifications),
        "unread_count": len([n for n in notifications if not n.get("read", False)])
    }


@router.post("/notifications/check-streaks")
async def check_streak_notifications(current_user: dict = Depends(get_current_user)):
    """
    Check for streak-related notifications and create them.
    """
    username = current_user["username"]
    
    # Load history
    history = read_json(settings.HISTORY_FILE, default={})
    user_history_dict = history.get(username, {})
    
    if not user_history_dict:
        return {"notifications": [], "count": 0}
    
    # Calculate streaks
    team_streaks = get_team_streaks(user_history_dict)
    
    # Get member names
    all_members = read_json(settings.MEMBERS_FILE, default={})
    user_members = all_members.get(username, [])
    member_names = {m["username"]: m.get("name", m["username"]) for m in user_members}
    
    # Add names to streak data
    for streak in team_streaks:
        streak["name"] = member_names.get(streak["member"], streak["member"])
    
    # Check and create notifications
    notifications = check_and_notify_streaks(team_streaks)
    
    return {
        "notifications": notifications,
        "count": len(notifications),
        "message": f"Created {len(notifications)} streak notifications"
    }


@router.post("/notifications/send-digest")
async def send_daily_digest(current_user: dict = Depends(get_current_user)):
    """
    Generate and send daily digest notification.
    """
    username = current_user["username"]
    
    # Get team stats
    all_members = read_json(settings.MEMBERS_FILE, default={})
    user_members = all_members.get(username, [])
    
    # Calculate today's stats
    total_members = len(user_members)
    total_solved = sum(m.get("totalSolved", 0) for m in user_members)
    
    # Get top performers
    top_performers = sorted(
        user_members,
        key=lambda x: x.get("totalSolved", 0),
        reverse=True
    )[:3]
    
    team_stats = {
        "total_members": total_members,
        "total_solved": total_solved,
        "average_solved": total_solved // total_members if total_members > 0 else 0
    }
    
    # Create digest notification
    digest = notification_service.create_daily_digest(
        team_stats=team_stats,
        top_performers=[
            {
                "name": p.get("name", p["username"]),
                "totalSolved": p.get("totalSolved", 0)
            }
            for p in top_performers
        ],
        team_name=f"{username}'s Team"
    )
    
    notification_service.send_notification(digest, channels=["in_app"])
    
    return {
        "notification": digest,
        "message": "Daily digest created"
    }


@router.delete("/notifications")
async def clear_notifications(current_user: dict = Depends(get_current_user)):
    """
    Clear all notifications.
    """
    notification_service.clear_notifications()
    
    return {"message": "All notifications cleared"}


@router.get("/notifications/settings")
async def get_notification_settings(current_user: dict = Depends(get_current_user)):
    """
    Get notification settings for the current user.
    """
    # Placeholder for notification preferences
    return {
        "email_enabled": False,
        "slack_enabled": False,
        "discord_enabled": False,
        "in_app_enabled": True,
        "streak_alerts": True,
        "milestone_celebrations": True,
        "daily_digest": False,
        "inactivity_reminders": True
    }


@router.put("/notifications/settings")
async def update_notification_settings(
    settings_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """
    Update notification settings.
    """
    # Placeholder - would save to database
    return {
        "message": "Notification settings updated",
        "settings": settings_data
    }
