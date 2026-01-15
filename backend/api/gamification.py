"""
Gamification API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from backend.core.security import get_current_user
from backend.services.gamification_service import gamification_service

router = APIRouter()

# --- Data Models ---

class StreakResponse(BaseModel):
    current_streak: int
    longest_streak: int
    streak_history: List[str] = [] # List of dates

class PointsResponse(BaseModel):
    current: int
    weekly: int
    monthly: int
    all_time: int
    
class AchievementResponse(BaseModel):
    key: str
    name: str
    description: str
    icon: str
    category: str
    unlocked: bool
    unlocked_at: Optional[str] = None

class LeaderboardEntry(BaseModel):
    rank: int
    username: str
    points: int

# --- Endpoints ---

class TeamStreakResponse(BaseModel):
    current_streak: int
    active_today: bool
    history: List[str]

# 1. Streaks

@router.get("/team-streak", response_model=TeamStreakResponse)
async def get_team_streak(current_user: dict = Depends(get_current_user)):
    """Get the collective team streak"""
    return gamification_service.get_team_streak()

@router.get("/streak", response_model=StreakResponse)
async def get_my_streak(current_user: dict = Depends(get_current_user)):
    """Get current user's streak info"""
    username = current_user["username"]
    current = gamification_service.get_current_streak(username)
    longest = gamification_service.get_longest_streak(username)
    
    return {
        "current_streak": current,
        "longest_streak": longest,
        "streak_history": [] # TODO: specific history query if needed
    }

@router.get("/streak/{username}", response_model=StreakResponse)
async def get_user_streak(username: str, current_user: dict = Depends(get_current_user)):
    """Get any user's streak info"""
    current = gamification_service.get_current_streak(username)
    longest = gamification_service.get_longest_streak(username)
    
    return {
        "current_streak": current,
        "longest_streak": longest,
        "streak_history": []
    }

# 2. Points

@router.get("/points", response_model=PointsResponse)
async def get_my_points(current_user: dict = Depends(get_current_user)):
    """Get current user's points"""
    return gamification_service.get_user_points(current_user["username"])

@router.get("/points/{username}", response_model=PointsResponse)
async def get_user_points(username: str, current_user: dict = Depends(get_current_user)):
    """Get any user's points"""
    return gamification_service.get_user_points(username)

@router.get("/leaderboard", response_model=List[LeaderboardEntry])
async def get_leaderboard(period: str = "weekly", limit: int = 10, current_user: dict = Depends(get_current_user)):
    """Get points leaderboard (period: weekly, monthly, all_time)"""
    return gamification_service.get_leaderboard(period, limit)

# 3. Achievements

@router.get("/achievements", response_model=List[AchievementResponse])
async def get_my_achievements(current_user: dict = Depends(get_current_user)):
    """Get current user's achievements"""
    return gamification_service.get_user_achievements(current_user["username"])

@router.get("/achievements/{username}", response_model=List[AchievementResponse])
async def get_user_achievements(username: str, current_user: dict = Depends(get_current_user)):
    """Get any user's achievements"""
    return gamification_service.get_user_achievements(username)

# 4. Activity Recording (Internal/For Testing)
# In production, this would be called by the scheduler or webhook

class ActivityRecord(BaseModel):
    problems_solved: int = 0
    daily_challenge: bool = False

@router.post("/activity/record")
async def record_activity(activity: ActivityRecord, current_user: dict = Depends(get_current_user)):
    """Record activity manually (for testing/manual entry)"""
    result = gamification_service.record_daily_activity(
        current_user["username"], 
        problems_solved=activity.problems_solved,
        daily_challenge_completed=activity.daily_challenge
    )
    
    # If activity recorded successfully, check for achievements
    if result.get("success"):
        # Determine points (simple logic for manual recording)
        points = 0
        reason = "Manual Entry"
        if activity.daily_challenge:
            points += 10
            reason += " + Daily Challenge"
        if activity.problems_solved > 0:
            points += (activity.problems_solved * 1) # Assume easy for manual
            reason += f" + {activity.problems_solved} Problems"
            
        if points > 0:
            gamification_service.award_points(current_user["username"], points, reason)
            
    return result

