"""
Notifications API endpoints
"""

from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from backend.core.security import get_current_user
from backend.core.storage import read_json, write_json
from backend.core.config import settings
from backend.utils.notification_service import (
    notification_service,
    check_and_notify_streaks,
    check_and_notify_milestones,
    check_and_notify_new_submissions
)
from backend.utils.streak_tracker import get_team_streaks
from backend.utils.leetcodeapi import fetch_user_data
from concurrent.futures import ThreadPoolExecutor, as_completed

router = APIRouter()

@router.get("/health")
async def notifications_health():
    return {"status": "ok"}


@router.get("")
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


@router.post("/check-streaks")
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


@router.post("/check-submissions")
async def check_new_submissions(current_user: dict = Depends(get_current_user)):
    """
    Check for new problem submissions and create notifications.
    Compares current data with last checked state.
    """
    username = current_user["username"]
    
    # Load team members
    all_members = read_json(settings.MEMBERS_FILE, default={})
    user_members = all_members.get(username, [])
    
    if not user_members:
        return {"notifications": [], "count": 0}
    
    # Load last state
    last_state = read_json(settings.LAST_STATE_FILE, default={})
    user_last_state = last_state.get(username, {})
    
    notifications = []
    new_state = {}
    
    # Fetch current data in parallel
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_member = {
            executor.submit(fetch_user_data, member["username"]): member
            for member in user_members
        }
        
        for future in as_completed(future_to_member):
            member = future_to_member[future]
            member_username = member["username"]
            member_name = member.get("name", member_username)
            
            try:
                current_data = future.result()
                if not current_data:
                    continue
                
                # Save to new state
                new_state[member_username] = current_data
                
                # Compare with previous state
                if member_username in user_last_state:
                    previous_data = user_last_state[member_username]
                    
                    # Check for new submissions
                    new_notifs = check_and_notify_new_submissions(
                        current_data,
                        previous_data,
                        member_username,
                        member_name
                    )
                    notifications.extend(new_notifs)
                    
                    # Check for milestones
                    milestone_notifs = check_and_notify_milestones(
                        current_data,
                        previous_data,
                        member_username,
                        member_name
                    )
                    notifications.extend(milestone_notifs)
            
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error checking submissions for {member_username}: {e}")
    
    # Update last state
    # Merge with existing state to preserve members who weren't fetched successfully
    user_last_state.update(new_state)
    last_state[username] = user_last_state
    write_json(settings.LAST_STATE_FILE, last_state)
    
    return {
        "notifications": notifications,
        "count": len(notifications),
        "message": f"Created {len(notifications)} notifications"
    }


@router.post("/send-digest")
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


@router.delete("")
async def clear_notifications(current_user: dict = Depends(get_current_user)):
    """
    Clear all notifications.
    """
    notification_service.clear_notifications()
    
    return {"message": "All notifications cleared"}


@router.get("/settings")
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


@router.put("/settings")
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
