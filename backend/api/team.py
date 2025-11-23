"""
Team management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import io
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from backend.core.security import get_current_user
from backend.core.storage import read_json, write_json
from backend.core.config import settings
from backend.utils.leetcodeapi import fetch_user_data

router = APIRouter()

def get_members_list_internal(username: str) -> List[Dict[str, Any]]:
    """Helper to get members list for internal use"""
    all_members = read_json(settings.MEMBERS_FILE, default={})
    return all_members.get(username, [])

class TeamMember(BaseModel):
    username: str
    name: Optional[str] = None

class TeamMemberResponse(BaseModel):
    username: str
    name: str
    avatar: Optional[str] = None
    totalSolved: int = 0
    ranking: Optional[int] = None
    easy: int = 0
    medium: int = 0
    hard: int = 0

@router.get("/members", response_model=List[TeamMemberResponse])
async def get_team_members(current_user: dict = Depends(get_current_user)):
    """Get all team members for current user"""
    username = current_user["username"]

    # Load all members
    all_members = read_json(settings.MEMBERS_FILE, default={})
    user_members = all_members.get(username, [])

    # Fetch fresh data for each member
    result = []
    for member in user_members:
        leetcode_data = fetch_user_data(member["username"])
        if leetcode_data:
            result.append(TeamMemberResponse(
                username=member["username"],
                name=member.get("name", member["username"]),
                avatar=leetcode_data.get("avatar"),
                totalSolved=leetcode_data.get("totalSolved", 0),
                ranking=leetcode_data.get("ranking"),
                easy=leetcode_data.get("easy", 0),
                medium=leetcode_data.get("medium", 0),
                hard=leetcode_data.get("hard", 0)
            ))
        else:
            # If fetch fails, return basic data
            result.append(TeamMemberResponse(
                username=member["username"],
                name=member.get("name", member["username"]),
                totalSolved=0,
                easy=0,
                medium=0,
                hard=0
            ))

    # Sort by totalSolved descending
    result.sort(key=lambda x: x.totalSolved, reverse=True)

    return result

@router.post("/members", status_code=status.HTTP_201_CREATED)
async def add_team_member(
    member: TeamMember,
    current_user: dict = Depends(get_current_user)
):
    """Add a new team member"""
    username = current_user["username"]

    # Verify LeetCode user exists
    leetcode_data = fetch_user_data(member.username)
    if not leetcode_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"LeetCode user '{member.username}' not found"
        )

    # Load all members
    all_members = read_json(settings.MEMBERS_FILE, default={})
    user_members = all_members.get(username, [])

    # Check if already exists
    if any(m["username"] == member.username for m in user_members):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User '{member.username}' is already in your team"
        )

    # Add new member
    user_members.append({
        "username": member.username,
        "name": member.name or leetcode_data.get("realName", member.username)
    })

    all_members[username] = user_members
    write_json(settings.MEMBERS_FILE, all_members)

    return {
        "message": f"Added {member.username} to team",
        "member": {
            "username": member.username,
            "name": member.name or leetcode_data.get("realName", member.username)
        }
    }

@router.delete("/members/{member_username}")
async def remove_team_member(
    member_username: str,
    current_user: dict = Depends(get_current_user)
):
    """Remove a team member"""
    username = current_user["username"]

    # Load all members
    all_members = read_json(settings.MEMBERS_FILE, default={})
    user_members = all_members.get(username, [])

    # Find and remove member
    user_members = [m for m in user_members if m["username"] != member_username]

    all_members[username] = user_members
    write_json(settings.MEMBERS_FILE, all_members)

    return {"message": f"Removed {member_username} from team"}

@router.get("/stats")
async def get_team_stats(current_user: dict = Depends(get_current_user)):
    """Get overall team statistics"""
    username = current_user["username"]

    # Load members
    all_members = read_json(settings.MEMBERS_FILE, default={})
    user_members = all_members.get(username, [])

    if not user_members:
        return {
            "total_members": 0,
            "total_problems_solved": 0,
            "average_solved": 0,
            "difficulty_breakdown": {
                "easy": 0,
                "medium": 0,
                "hard": 0
            }
        }

    # Fetch data for all members
    members_data = []
    for member in user_members:
        data = fetch_user_data(member["username"])
        if data:
            members_data.append(data)

    total_solved = sum(m.get("totalSolved", 0) for m in members_data)
    avg_solved = total_solved // len(members_data) if members_data else 0
    
    # Aggregate difficulty breakdown
    total_easy = sum(m.get("easySolved", 0) for m in members_data)
    total_medium = sum(m.get("mediumSolved", 0) for m in members_data)
    total_hard = sum(m.get("hardSolved", 0) for m in members_data)

    return {
        "total_members": len(user_members),
        "total_problems_solved": total_solved,
        "average_solved": avg_solved,
        "difficulty_breakdown": {
            "easy": total_easy,
            "medium": total_medium,
            "hard": total_hard
        }
    }

@router.get("/export/excel")
async def export_team_excel(current_user: dict = Depends(get_current_user)):
    """Export team data to Excel format"""
    username = current_user["username"]
    
    # Get team members with fresh data
    all_members = read_json(settings.MEMBERS_FILE, default={})
    user_members = all_members.get(username, [])
    
    # Fetch fresh data for each member
    members_data = []
    for member in user_members:
        leetcode_data = fetch_user_data(member["username"])
        if leetcode_data:
            members_data.append({
                "username": member["username"],
                "name": member.get("name", member["username"]),
                "totalSolved": leetcode_data.get("totalSolved", 0),
                "easySolved": leetcode_data.get("easySolved", 0),
                "mediumSolved": leetcode_data.get("mediumSolved", 0),
                "hardSolved": leetcode_data.get("hardSolved", 0),
                "ranking": leetcode_data.get("ranking", "N/A")
            })
    
    # Create Excel workbook
    wb = openpyxl.Workbook()
    
    # Team Members Sheet
    ws_members = wb.active
    ws_members.title = "Team Members"
    
    # Header styling
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")
    
    # Headers
    headers = ["Username", "Name", "Total Solved", "Easy", "Medium", "Hard", "Ranking"]
    for col, header in enumerate(headers, 1):
        cell = ws_members.cell(row=1, column=col, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center")
    
    # Data rows
    for row, member in enumerate(members_data, 2):
        ws_members.cell(row=row, column=1, value=member["username"])
        ws_members.cell(row=row, column=2, value=member["name"])
        ws_members.cell(row=row, column=3, value=member["totalSolved"])
        ws_members.cell(row=row, column=4, value=member["easySolved"])
        ws_members.cell(row=row, column=5, value=member["mediumSolved"])
        ws_members.cell(row=row, column=6, value=member["hardSolved"])
        ws_members.cell(row=row, column=7, value=str(member["ranking"]))
    
    # Auto-adjust column widths
    for column in ws_members.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            if cell.value:
                max_length = max(max_length, len(str(cell.value)))
        ws_members.column_dimensions[column_letter].width = max_length + 2
    
    # Statistics Sheet
    ws_stats = wb.create_sheet("Statistics")
    ws_stats.cell(row=1, column=1, value="Metric").font = header_font
    ws_stats.cell(row=1, column=2, value="Value").font = header_font
    
    total_solved = sum(m["totalSolved"] for m in members_data)
    total_easy = sum(m["easySolved"] for m in members_data)
    total_medium = sum(m["mediumSolved"] for m in members_data)
    total_hard = sum(m["hardSolved"] for m in members_data)
    avg_solved = total_solved // len(members_data) if members_data else 0
    
    stats = [
        ("Total Members", len(members_data)),
        ("Total Problems Solved", total_solved),
        ("Average Solved per Member", avg_solved),
        ("Total Easy", total_easy),
        ("Total Medium", total_medium),
        ("Total Hard", total_hard)
    ]
    
    for row, (metric, value) in enumerate(stats, 2):
        ws_stats.cell(row=row, column=1, value=metric)
        ws_stats.cell(row=row, column=2, value=value)
    
    ws_stats.column_dimensions['A'].width = 30
    ws_stats.column_dimensions['B'].width = 15
    
    # Save to BytesIO
    excel_file = io.BytesIO()
    wb.save(excel_file)
    excel_file.seek(0)
    
    # Generate filename with current date
    filename = f"team-data-{datetime.now().strftime('%Y-%m-%d')}.xlsx"
    
    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/backup")
async def backup_team_data(current_user: dict = Depends(get_current_user)):
    """Export all user data as JSON backup"""
    username = current_user["username"]
    
    # Load all data files
    all_members = read_json(settings.MEMBERS_FILE, default={})
    all_history = read_json(settings.HISTORY_FILE, default={})
    all_snapshots = read_json(settings.SNAPSHOTS_FILE, default={})
    
    # Extract user-specific data
    backup_data = {
        "version": "1.0",
        "exported_at": datetime.now().isoformat(),
        "username": username,
        "members": all_members.get(username, []),
        "history": all_history.get(username, []),
        "snapshots": all_snapshots.get(username, [])
    }
    
    return backup_data

class RestoreBackup(BaseModel):
    version: str
    username: str
    members: List[Dict[str, Any]]
    history: Optional[List[Dict[str, Any]]] = []
    snapshots: Optional[List[Dict[str, Any]]] = []

@router.post("/restore")
async def restore_team_data(
    backup: RestoreBackup,
    current_user: dict = Depends(get_current_user)
):
    """Restore data from JSON backup"""
    username = current_user["username"]
    
    # Validate backup version
    if backup.version != "1.0":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported backup version: {backup.version}"
        )
    
    # Load current data
    all_members = read_json(settings.MEMBERS_FILE, default={})
    all_history = read_json(settings.HISTORY_FILE, default={})
    all_snapshots = read_json(settings.SNAPSHOTS_FILE, default={})
    
    # Restore data
    all_members[username] = backup.members
    all_history[username] = backup.history or []
    all_snapshots[username] = backup.snapshots or []
    
    # Write back to files
    write_json(settings.MEMBERS_FILE, all_members)
    write_json(settings.HISTORY_FILE, all_history)
    write_json(settings.SNAPSHOTS_FILE, all_snapshots)
    
    return {
        "message": "Data restored successfully",
        "members_restored": len(backup.members),
        "history_entries": len(backup.history or []),
        "snapshots_restored": len(backup.snapshots or [])
    }
