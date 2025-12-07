from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional
from backend.core.security import get_current_user
from backend.core.database import get_db_connection
from backend.utils.notification_service import notification_service
import json

router = APIRouter()

@router.get("")
async def get_notification_logs(
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get notification logs from database"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        query = "SELECT * FROM notifications"
        params = []
        
        if status:
            query += " WHERE status = ?"
            params.append(status)
            
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        notifications = []
        for row in rows:
            notif = dict(row)
            if notif.get("metadata"):
                try:
                    notif["metadata"] = json.loads(notif["metadata"])
                except:
                    notif["metadata"] = {}
            notifications.append(notif)
            
        # Get total count
        count_query = "SELECT COUNT(*) as count FROM notifications"
        if status:
            count_query += " WHERE status = ?"
            cursor.execute(count_query, (status,))
        else:
            cursor.execute(count_query)
            
        total = cursor.fetchone()["count"]
        
        return {
            "notifications": notifications,
            "total": total,
            "limit": limit,
            "offset": offset
        }

@router.post("/{notification_id}/resend")
async def resend_notification(
    notification_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Resend a specific notification"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM notifications WHERE id = ?", (notification_id,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Notification not found")
            
        notification = dict(row)
        
        # Reconstruct notification object
        payload = {
            "type": notification["type"],
            "title": notification["title"],
            "message": notification["message"],
            "member": notification["recipient"],
            "created_at": notification["created_at"]
        }
        
        if notification.get("metadata"):
            try:
                metadata = json.loads(notification["metadata"])
                payload.update(metadata)
            except:
                pass
                
        # Send
        # We force 'discord' channel for resend as that's usually what we want
        # But we should probably check what channels were originally intended or just default to discord/in_app
        success = notification_service.send_notification(payload, channels=["discord", "in_app"])
        
        # Update status if successful
        if success:
            cursor.execute(
                "UPDATE notifications SET status = 'sent', sent_at = CURRENT_TIMESTAMP WHERE id = ?", 
                (notification_id,)
            )
            conn.commit()
            return {"success": True, "message": "Notification resent successfully"}
        else:
            return {"success": False, "message": "Failed to resend notification"}
