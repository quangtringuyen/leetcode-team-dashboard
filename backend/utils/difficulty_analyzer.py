"""
Difficulty trend analysis utilities
Tracks progression through Easy → Medium → Hard problems
"""

from typing import Dict, List, Any
from datetime import date, timedelta


def calculate_difficulty_trends(history_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate difficulty distribution trends over time.
    
    Args:
        history_data: List of weekly snapshots sorted by week_start
        
    Returns:
        Dict with difficulty trends, progression status, and recommendations
    """
    if not history_data:
        return {
            "trends": [],
            "current_distribution": {"easy": 0, "medium": 0, "hard": 0},
            "progression_status": "no_data",
            "stuck_on_difficulty": None,
            "recommendation": "Start solving Easy problems"
        }
    
    # Sort by week_start
    sorted_data = sorted(history_data, key=lambda x: x.get("week_start", ""))
    
    # Calculate trends
    trends = []
    for snapshot in sorted_data:
        easy = snapshot.get("easy", 0)
        medium = snapshot.get("medium", 0)
        hard = snapshot.get("hard", 0)
        total = easy + medium + hard
        
        if total > 0:
            trends.append({
                "week": snapshot.get("week_start"),
                "easy": easy,
                "medium": medium,
                "hard": hard,
                "total": total,
                "easy_pct": round((easy / total) * 100, 1),
                "medium_pct": round((medium / total) * 100, 1),
                "hard_pct": round((hard / total) * 100, 1)
            })
    
    if not trends:
        return {
            "trends": [],
            "current_distribution": {"easy": 0, "medium": 0, "hard": 0},
            "progression_status": "no_data",
            "stuck_on_difficulty": None,
            "recommendation": "Start solving problems"
        }
    
    # Get current distribution
    current = trends[-1]
    current_distribution = {
        "easy": current["easy"],
        "medium": current["medium"],
        "hard": current["hard"],
        "easy_pct": current["easy_pct"],
        "medium_pct": current["medium_pct"],
        "hard_pct": current["hard_pct"]
    }
    
    # Analyze progression status
    progression_status, stuck_on, recommendation = _analyze_progression(trends)
    
    return {
        "trends": trends,
        "current_distribution": current_distribution,
        "progression_status": progression_status,
        "stuck_on_difficulty": stuck_on,
        "recommendation": recommendation
    }


def _analyze_progression(trends: List[Dict[str, Any]]) -> tuple:
    """
    Analyze if user is progressing through difficulties or stuck.
    
    Returns:
        (progression_status, stuck_on_difficulty, recommendation)
    """
    if len(trends) < 4:
        return ("insufficient_data", None, "Keep solving to establish a pattern")
    
    # Look at last 4 weeks
    recent = trends[-4:]
    
    # Calculate average percentages
    avg_easy = sum(w["easy_pct"] for w in recent) / len(recent)
    avg_medium = sum(w["medium_pct"] for w in recent) / len(recent)
    avg_hard = sum(w["hard_pct"] for w in recent) / len(recent)
    
    # Check for growth in harder problems
    first_two = trends[-4:-2]
    last_two = trends[-2:]
    
    avg_medium_first = sum(w["medium_pct"] for w in first_two) / 2
    avg_medium_last = sum(w["medium_pct"] for w in last_two) / 2
    
    avg_hard_first = sum(w["hard_pct"] for w in first_two) / 2
    avg_hard_last = sum(w["hard_pct"] for w in last_two) / 2
    
    # Determine status
    if avg_easy > 80:
        return (
            "stuck_on_easy",
            "easy",
            "Try solving more Medium problems to progress"
        )
    elif avg_easy > 60 and avg_medium < 30:
        return (
            "mostly_easy",
            "easy",
            "Good foundation! Start mixing in Medium problems"
        )
    elif avg_medium > 70 and avg_hard < 10:
        return (
            "stuck_on_medium",
            "medium",
            "You're ready for Hard problems! Try 1-2 per week"
        )
    elif avg_medium_last > avg_medium_first + 10:
        return (
            "progressing_to_medium",
            None,
            "Great progress on Medium problems! Keep it up"
        )
    elif avg_hard_last > avg_hard_first + 5:
        return (
            "progressing_to_hard",
            None,
            "Excellent! You're tackling Hard problems"
        )
    elif avg_hard > 20:
        return (
            "advanced",
            None,
            "Strong performance across all difficulties!"
        )
    else:
        return (
            "balanced",
            None,
            "Good mix of difficulties. Keep challenging yourself!"
        )


def get_team_difficulty_trends(history: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """
    Get difficulty trends for all team members.
    
    Args:
        history: Dict mapping member usernames to their history data
        
    Returns:
        List of dicts with member and their difficulty trends
    """
    team_trends = []
    
    for member, member_history in history.items():
        trend_data = calculate_difficulty_trends(member_history)
        
        team_trends.append({
            "member": member,
            **trend_data
        })
    
    return team_trends


def get_stuck_members(team_trends: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Get members who are stuck on a particular difficulty.
    
    Args:
        team_trends: Output from get_team_difficulty_trends()
        
    Returns:
        List of members stuck on a difficulty
    """
    stuck = []
    
    for trend in team_trends:
        if trend["stuck_on_difficulty"]:
            stuck.append({
                "member": trend["member"],
                "stuck_on": trend["stuck_on_difficulty"],
                "status": trend["progression_status"],
                "recommendation": trend["recommendation"],
                "current_distribution": trend["current_distribution"]
            })
    
    return stuck
