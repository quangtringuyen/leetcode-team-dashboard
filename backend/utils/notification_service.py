"""
Smart notification service
Sends notifications for streaks, milestones, and inactivity
"""

from typing import Dict, List, Any, Optional
from datetime import date, datetime, timedelta, timezone
import logging
from backend.core.config import settings

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending various types of notifications"""
    
    def __init__(self):
        self.notifications = []  # Store notifications in memory for now
    
    def create_streak_at_risk_notification(
        self,
        member: str,
        member_name: str,
        current_streak: int,
        last_active_date: str
    ) -> Dict[str, Any]:
        """Create notification for streak at risk"""
        return {
            "type": "streak_at_risk",
            "member": member,
            "member_name": member_name,
            "title": f"⚠️ {member_name}'s {current_streak}-week streak is at risk!",
            "message": f"{member_name} hasn't solved problems since {last_active_date}. Their {current_streak}-week streak is about to break!",
            "priority": "high",
            "action": "Solve a problem to maintain your streak",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    
    def create_milestone_notification(
        self,
        member: str,
        member_name: str,
        milestone_type: str,
        milestone_value: int
    ) -> Dict[str, Any]:
        """Create notification for milestones"""
        messages = {
            "total_solved": f"🎉 {member_name} reached {milestone_value} problems solved!",
            "streak": f"🔥 {member_name} achieved a {milestone_value}-week streak!",
            "first_hard": f"💪 {member_name} solved their first Hard problem!",
            "100_problems": f"🏆 {member_name} hit the 100 problems milestone!",
        }
        
        return {
            "type": "milestone",
            "member": member,
            "member_name": member_name,
            "milestone_type": milestone_type,
            "title": messages.get(milestone_type, f"Milestone achieved: {milestone_value}"),
            "message": f"Congratulations to {member_name} on this achievement!",
            "priority": "medium",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    
    def create_inactivity_notification(
        self,
        member: str,
        member_name: str,
        days_inactive: int
    ) -> Dict[str, Any]:
        """Create notification for inactive members"""
        return {
            "type": "inactivity",
            "member": member,
            "member_name": member_name,
            "title": f"📅 {member_name} has been inactive for {days_inactive} days",
            "message": f"We haven't seen {member_name} solve problems in {days_inactive} days. Time to get back on track!",
            "priority": "low",
            "action": "Start with an Easy problem to warm up",
            "created_at": datetime.now(timezone.utc).isoformat()
        }

    def create_problem_solved_notification(
        self,
        member: str,
        member_name: str,
        count: int,
        difficulty_breakdown: Dict[str, int]
    ) -> Dict[str, Any]:
        """Create notification for new problems solved"""
        # Determine message based on difficulty
        details = []
        if difficulty_breakdown.get("easy"):
            details.append(f"{difficulty_breakdown['easy']} Easy")
        if difficulty_breakdown.get("medium"):
            details.append(f"{difficulty_breakdown['medium']} Medium")
        if difficulty_breakdown.get("hard"):
            details.append(f"{difficulty_breakdown['hard']} Hard")
        
        detail_str = ", ".join(details)
        
        return {
            "type": "problem_solved",
            "member": member,
            "member_name": member_name,
            "title": f"🚀 {member_name} solved {count} new problem{'s' if count > 1 else ''}!",
            "message": f"{member_name} just solved {count} problem{'s' if count > 1 else ''} ({detail_str}). Keep it up!",
            "priority": "low",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    
    def create_daily_digest(
        self,
        team_stats: Dict[str, Any],
        top_performers: List[Dict[str, Any]],
        team_name: str = "Your Team"
    ) -> Dict[str, Any]:
        """Create daily digest notification"""
        return {
            "type": "daily_digest",
            "title": f"📊 Daily Digest for {team_name}",
            "team_stats": team_stats,
            "top_performers": top_performers,
            "message": f"Here's what happened today with {team_name}",
            "priority": "low",
            "created_at": datetime.utcnow().isoformat()
        }
    
    def send_notification(
        self,
        notification: Dict[str, Any],
        channels: List[str] = ["in_app"]
    ) -> bool:
        """
        Send notification through specified channels.
        
        Args:
            notification: Notification data
            channels: List of channels (in_app, email, slack, discord)
            
        Returns:
            True if sent successfully
        """
        # For now, just store in memory (in-app notifications)
        if "in_app" in channels:
            self.notifications.append(notification)
            logger.info(f"Notification created: {notification['type']} for {notification.get('member', 'team')}")
        
        # Email integration (placeholder)
        if "email" in channels:
            logger.info(f"Would send email: {notification['title']}")
            # TODO: Integrate with SendGrid/AWS SES
        
        # Slack integration (placeholder)
        if "slack" in channels:
            logger.info(f"Would send to Slack: {notification['title']}")
            # TODO: Integrate with Slack webhook
        
        # Discord integration
        if "discord" in channels:
            if not settings.DISCORD_WEBHOOK_URL:
                logger.warning("Discord channel requested but DISCORD_WEBHOOK_URL not set")
            else:
                try:
                    import requests
                    
                    # Format message for Discord
                    discord_payload = {
                        "username": "LeetCode Dashboard",
                        "avatar_url": "https://leetcode.com/static/images/LeetCode_logo_rvs.png",
                        "embeds": [{
                            "title": notification["title"],
                            "description": notification["message"],
                            "color": 16753920 if notification.get("priority") == "high" else 5814783,
                            "footer": {"text": "LeetCode Team Dashboard"},
                            "timestamp": notification.get("created_at", datetime.now(timezone.utc).isoformat())
                        }]
                    }
                    
                    logger.info(f"Sending Discord webhook to {settings.DISCORD_WEBHOOK_URL[:10]}...")
                    response = requests.post(settings.DISCORD_WEBHOOK_URL, json=discord_payload, timeout=10)
                    
                    if response.status_code not in [200, 204]:
                        logger.error(f"Discord API error {response.status_code}: {response.text}")
                    else:
                        logger.info(f"Sent Discord notification: {notification['title']}")
                        
                except Exception as e:
                    logger.error(f"Failed to send Discord notification: {str(e)}")
        
        return True
    
    def get_notifications(
        self,
        member: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get recent notifications"""
        if member:
            filtered = [n for n in self.notifications if n.get("member") == member]
        else:
            filtered = self.notifications
        
        # Sort by created_at descending
        sorted_notifications = sorted(
            filtered,
            key=lambda x: x.get("created_at", ""),
            reverse=True
        )
        
        return sorted_notifications[:limit]
    
    def clear_notifications(self, member: Optional[str] = None):
        """Clear notifications"""
        if member:
            self.notifications = [n for n in self.notifications if n.get("member") != member]
        else:
            self.notifications = []


# Global notification service instance
notification_service = NotificationService()


def check_and_notify_streaks(team_streaks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Check streaks and create notifications for at-risk members.
    
    Args:
        team_streaks: List of streak data from get_team_streaks()
        
    Returns:
        List of created notifications
    """
    notifications = []
    
    for streak in team_streaks:
        if streak.get("streak_status") == "at_risk" and streak.get("current_streak", 0) > 0:
            notification = notification_service.create_streak_at_risk_notification(
                member=streak["member"],
                member_name=streak.get("name", streak["member"]),
                current_streak=streak["current_streak"],
                last_active_date=streak.get("last_active_date", "unknown")
            )
            notification_service.send_notification(notification, channels=["in_app", "discord"])
            notifications.append(notification)
    
    return notifications


def check_and_notify_milestones(
    current_data: Dict[str, int],
    previous_data: Dict[str, int],
    member: str,
    member_name: str
) -> List[Dict[str, Any]]:
    """
    Check for milestones and create notifications.
    
    Args:
        current_data: Current problem counts
        previous_data: Previous problem counts
        member: Member username
        member_name: Member display name
        
    Returns:
        List of created notifications
    """
    notifications = []
    
    current_total = current_data.get("totalSolved", 0)
    previous_total = previous_data.get("totalSolved", 0)
    
    # Check for milestone achievements
    milestones = [10, 25, 50, 100, 200, 500, 1000]
    
    for milestone in milestones:
        if previous_total < milestone <= current_total:
            notification = notification_service.create_milestone_notification(
                member=member,
                member_name=member_name,
                milestone_type="total_solved",
                milestone_value=milestone
            )
            notification_service.send_notification(notification, channels=["in_app", "discord"])
            notifications.append(notification)
    
    # Check for first hard problem
    current_hard = current_data.get("hard", 0)
    previous_hard = previous_data.get("hard", 0)
    
    if previous_hard == 0 and current_hard > 0:
        notification = notification_service.create_milestone_notification(
            member=member,
            member_name=member_name,
            milestone_type="first_hard",
            milestone_value=1
        )
        notification_service.send_notification(notification, channels=["in_app", "discord"])
        notifications.append(notification)
    
    return notifications


def check_and_notify_new_submissions(
    current_data: Dict[str, int],
    previous_data: Dict[str, int],
    member: str,
    member_name: str
) -> List[Dict[str, Any]]:
    """
    Check for new submissions and create notifications.
    
    Args:
        current_data: Current problem counts
        previous_data: Previous problem counts
        member: Member username
        member_name: Member display name
        
    Returns:
        List of created notifications
    """
    notifications = []
    
    current_total = current_data.get("totalSolved", 0)
    previous_total = previous_data.get("totalSolved", 0)
    
    diff = current_total - previous_total
    
    if diff > 0:
        # Calculate difficulty breakdown of new problems
        easy_diff = current_data.get("easy", 0) - previous_data.get("easy", 0)
        medium_diff = current_data.get("medium", 0) - previous_data.get("medium", 0)
        hard_diff = current_data.get("hard", 0) - previous_data.get("hard", 0)
        
        difficulty_breakdown = {
            "easy": max(0, easy_diff),
            "medium": max(0, medium_diff),
            "hard": max(0, hard_diff)
        }
        
        # Fetch recent submissions to get the actual timestamp
        from backend.utils.leetcodeapi import fetch_recent_submissions
        recent_subs = fetch_recent_submissions(member, limit=5)
        
        # Default to now if no submissions found (fallback)
        resolved_at = datetime.now(timezone.utc).isoformat()
        
        if recent_subs:
            # Sort by timestamp descending just in case
            recent_subs.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
            latest_sub = recent_subs[0]
            timestamp = latest_sub.get("timestamp")
            if timestamp:
                try:
                    # Convert timestamp (seconds) to ISO format
                    resolved_at = datetime.fromtimestamp(int(timestamp), tz=timezone.utc).isoformat()
                except Exception:
                    pass
        
        notification = notification_service.create_problem_solved_notification(
            member=member,
            member_name=member_name,
            count=diff,
            difficulty_breakdown=difficulty_breakdown
        )
        
        # Override created_at with actual resolved time
        notification["created_at"] = resolved_at
        
        # Send to Discord and In-App
        notification_service.send_notification(notification, channels=["in_app", "discord"])
        notifications.append(notification)
        
    return notifications
