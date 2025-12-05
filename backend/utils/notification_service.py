"""
Smart notification service
Sends notifications for streaks, milestones, and inactivity
"""

from typing import Dict, List, Any, Optional
from datetime import date, datetime, timedelta
import logging

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
            "created_at": datetime.utcnow().isoformat()
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
            "created_at": datetime.utcnow().isoformat()
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
            "created_at": datetime.utcnow().isoformat()
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
        
        # Discord integration (placeholder)
        if "discord" in channels:
            logger.info(f"Would send to Discord: {notification['title']}")
            # TODO: Integrate with Discord webhook
        
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
            notification_service.send_notification(notification, channels=["in_app"])
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
            notification_service.send_notification(notification, channels=["in_app"])
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
        notification_service.send_notification(notification, channels=["in_app"])
        notifications.append(notification)
    
    return notifications
