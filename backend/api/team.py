"""
Team management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from backend.core.security import get_current_user
from backend.core.storage import read_json, write_json
from backend.core.config import settings
from backend.utils.leetcodeapi import fetch_user_data

router = APIRouter()

class TeamMember(BaseModel):
    username: str
    name: Optional[str] = None

class TeamMemberResponse(BaseModel):
    username: str
    name: str
    avatar: Optional[str] = None
    totalSolved: int = 0
    ranking: Optional[int] = None

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
                ranking=leetcode_data.get("ranking")
            ))
        else:
            # If fetch fails, return basic data
            result.append(TeamMemberResponse(
                username=member["username"],
                name=member.get("name", member["username"]),
                totalSolved=0
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
            "totalMembers": 0,
            "totalSolved": 0,
            "averageSolved": 0,
            "topSolver": None
        }

    # Fetch data for all members
    members_data = []
    for member in user_members:
        data = fetch_user_data(member["username"])
        if data:
            members_data.append(data)

    total_solved = sum(m.get("totalSolved", 0) for m in members_data)
    avg_solved = total_solved // len(members_data) if members_data else 0
    top_solver = max(members_data, key=lambda x: x.get("totalSolved", 0)) if members_data else None

    return {
        "totalMembers": len(user_members),
        "totalSolved": total_solved,
        "averageSolved": avg_solved,
        "topSolver": {
            "username": top_solver["username"],
            "totalSolved": top_solver["totalSolved"]
        } if top_solver else None
    }
