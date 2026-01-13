from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from backend.core.security import get_current_user
from backend.core.config import settings
from backend.core.database import get_db_connection
from backend.utils.leetcodeapi import fetch_user_data, check_leetcode_user_exists
from datetime import datetime

router = APIRouter()
logger = logging.getLogger(__name__)

class TeamMember(BaseModel):
    username: str
    name: Optional[str] = None
    status: str = "active"  # active, suspended, etc.

class UpdateMember(BaseModel):
    name: Optional[str] = None
    status: str = "active"
    username: Optional[str] = None # Allow updating username

def get_members_list_internal(owner_username: str) -> List[dict]:
    """Internal helper to get members list for a team owner"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Include avatar as it is often needed by consumers
        cursor.execute("SELECT username, name, team_owner, status, avatar FROM members WHERE team_owner = ?", (owner_username,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


@router.get("/members", response_model=List[dict])
def get_team_members(current_user: dict = Depends(get_current_user)):
    """Get all team members with their latest stats"""
    user_members = []
    
    # 1. Load members from DB
    current_username = current_user["username"]
    logger.info(f"get_team_members called for user: {current_username}")
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT username, name, team_owner, status FROM members WHERE team_owner = ?", (current_username,))
        rows = cursor.fetchall()
        user_members = [dict(row) for row in rows]

    logger.info(f"Found {len(user_members)} members for user {current_username}")

    if not user_members:
        logger.warning(f"No members found for user {current_username}. this might be a mismatch with team_owner in DB.")
        return []

    # 2. Fetch live LeetCode stats in parallel
    results = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_member = {
            executor.submit(fetch_user_data, member["username"]): member 
            for member in user_members if member.get("status") != "suspended"
        }
        
        # Add suspended members with 0 stats (or just skipped stats)
        for member in user_members:
            if member.get("status") == "suspended":
                member_data = member.copy()
                member_data.update({
                    "totalSolved": 0,
                    "easy": 0,
                    "medium": 0, 
                    "hard": 0,
                    "ranking": 0,
                    "contributionPoints": 0,
                    "reputation": 0
                })
                results.append(member_data)

        for future in as_completed(future_to_member):
            member = future_to_member[future]
            try:
                data = future.result()
                if data:
                    member_data = member.copy()
                    member_data.update(data)
                    results.append(member_data)
                else:
                    # Failed to fetch, return member info with 0 stats
                    member_data = member.copy()
                    member_data.update({"totalSolved": 0})
                    results.append(member_data)
            except Exception as e:
                logger.error(f"Error fetching data for {member['username']}: {e}")
                member_data = member.copy()
                member_data.update({"totalSolved": 0})
                results.append(member_data)

    # Sort by total solved descending
    results.sort(key=lambda x: x.get("totalSolved", 0), reverse=True)
    return results

@router.post("/members")
def add_team_member(member: TeamMember, current_user: dict = Depends(get_current_user)):
    """Add a new team member"""
    username = member.username
    if not username:
        raise HTTPException(status_code=400, detail="Username is required")

    # 1. Check if member already exists in DB for this owner
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM members WHERE username = ? AND team_owner = ?", (username, current_user["username"]))
        if cursor.fetchone():
             raise HTTPException(status_code=400, detail="Member already exists")

    # 2. Verify LeetCode user exists
    if not check_leetcode_user_exists(username):
         raise HTTPException(status_code=404, detail="LeetCode user not found")

    # 3. Add to Database
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO members (username, name, team_owner, status, created_at) 
            VALUES (?, ?, ?, ?, ?)
        """, (
            username, 
            member.name or username, 
            current_user["username"], 
            member.status,
            datetime.utcnow().isoformat()
        ))
        conn.commit()

    # 4. Fetch initial stats and record history immediately
    try:
        leetcode_data = fetch_user_data(username)
        if leetcode_data:
            from datetime import date, timedelta
            today = date.today()
            week_start = (today - timedelta(days=today.weekday())).isoformat()
            
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR IGNORE INTO snapshots 
                    (username, week_start, total_solved, easy, medium, hard, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    username,
                    week_start,
                    leetcode_data.get("totalSolved", 0),
                    leetcode_data.get("easy", 0),
                    leetcode_data.get("medium", 0),
                    leetcode_data.get("hard", 0),
                    datetime.utcnow().isoformat()
                ))
                conn.commit()
    except Exception as e:
        logger.error(f"Failed to record initial history for {username}: {e}")

    return {"message": "Member added successfully", "username": username}

@router.put("/members/{original_username}")
def update_team_member(
    original_username: str, 
    member_update: UpdateMember, 
    current_user: dict = Depends(get_current_user)
):
    """Update a team member (name, status, or username)"""
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Check if member exists
        cursor.execute("SELECT * FROM members WHERE username = ? AND team_owner = ?", (original_username, current_user["username"]))
        member = cursor.fetchone()
        
        if not member:
            # Try case-insensitive lookup
            cursor.execute("SELECT * FROM members WHERE lower(username) = lower(?) AND team_owner = ?", (original_username, current_user["username"]))
            member = cursor.fetchone()
            
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")
        
        actual_username = member["username"]
        new_username = member_update.username
        
        # If changing username, duplicate check and validation
        if new_username and new_username != actual_username:
            # Check duplicate
            cursor.execute("SELECT 1 FROM members WHERE username = ? AND team_owner = ?", (new_username, current_user["username"]))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="New username already belongs to a member")
            
            # Verify LeetCode
            if not check_leetcode_user_exists(new_username):
                raise HTTPException(status_code=404, detail=f"LeetCode user {new_username} not found")

            # Update Member
            try:
                # Update members table
                cursor.execute("""
                    UPDATE members 
                    SET username = ?, name = ?, status = ? 
                    WHERE username = ?
                """, (new_username, member_update.name or new_username, member_update.status, actual_username))
                
                # Update snapshots table (manual update necessary if no CASCADE)
                cursor.execute("UPDATE snapshots SET username = ? WHERE username = ?", (new_username, actual_username))
                
                conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"Error updating username: {e}")
                raise HTTPException(status_code=500, detail="Database error updating member")
        else:
            # Just updating name/status
            cursor.execute("""
                UPDATE members 
                SET name = ?, status = ? 
                WHERE username = ?
            """, (member_update.name or member["name"], member_update.status, actual_username))
            conn.commit()
            
    return {"message": "Member updated successfully"}

@router.delete("/members/{member_id}")
def remove_team_member(member_id: str, current_user: dict = Depends(get_current_user)):
    """Remove a team member"""
    
    with get_db_connection() as conn:
        # Check exist
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM members WHERE username = ? AND team_owner = ?", (member_id, current_user["username"]))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Member not found")
            
        # Delete from members (Historical snapshots remain in DB)
        cursor.execute("DELETE FROM members WHERE username = ? AND team_owner = ?", (member_id, current_user["username"]))
        conn.commit()
        
    return {"message": "Member removed successfully"}

@router.get("/stats")
def get_team_stats(current_user: dict = Depends(get_current_user)):
    """Get aggregated team statistics"""
    
    # 1. Get members from DB
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM members WHERE team_owner = ? AND status != 'suspended'", (current_user["username"],))
        rows = cursor.fetchall()
        user_members = [dict(row) for row in rows]
        
    if not user_members:
        return {"totalSolved": 0, "easy": 0, "medium": 0, "hard": 0, "memberCount": 0}

    total_stats = {"totalSolved": 0, "easy": 0, "medium": 0, "hard": 0}
    
    # 2. Fetch live data
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(fetch_user_data, member["username"]) for member in user_members]
        for future in as_completed(futures):
            try:
                data = future.result()
                if data:
                    total_stats["totalSolved"] += data.get("totalSolved", 0)
                    total_stats["easy"] += data.get("easy", 0)
                    total_stats["medium"] += data.get("medium", 0)
                    total_stats["hard"] += data.get("hard", 0)
            except:
                pass

    total_stats["memberCount"] = len(user_members)
    return total_stats

@router.get("/export/excel")
def export_excel(current_user: dict = Depends(get_current_user)):
    """Export team data to Excel"""
    from fastapi.responses import FileResponse
    import pandas as pd
    import os
    
    try:
        # 1. Get Members Data
        # Re-use logic from get_team_members but we need the raw list
        members_data = get_team_members(current_user)
        
        # 2. Get Week Over Week Data
        # Fetch directly since importing might be circular
        # Actually importing analytics here IS safe if analytics imports team (team doesn't import analytics at top level)
        from backend.api.analytics import get_week_over_week_internal
        wow_data = get_week_over_week_internal(current_user["username"], weeks=4)
        
        # 3. Create DataFrame
        df_current = pd.DataFrame(members_data)
        df_wow = pd.DataFrame(wow_data)
        
        # Create Excel
        filename = f"leetcode_team_export_{datetime.now().strftime('%Y%m%d')}.xlsx"
        filepath = os.path.join(settings.DATA_DIR, filename)
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            if not df_current.empty:
                df_current.to_excel(writer, sheet_name='Current Stats', index=False)
            if not df_wow.empty:
                df_wow.to_excel(writer, sheet_name='Week over Week', index=False)
                
        return FileResponse(filepath, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', filename=filename)
        
    except Exception as e:
        logger.error(f"Export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
