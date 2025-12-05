"""
Problem recommendation engine
Suggests problems based on skill level, weak tags, and difficulty progression
"""

from typing import Dict, List, Any
import random


# Company-specific problem lists (LeetCode problem IDs)
COMPANY_PROBLEMS = {
    "Google": [
        {"id": 1, "title": "Two Sum", "difficulty": "Easy", "tags": ["Array", "Hash Table"]},
        {"id": 146, "title": "LRU Cache", "difficulty": "Medium", "tags": ["Design", "Hash Table"]},
        {"id": 200, "title": "Number of Islands", "difficulty": "Medium", "tags": ["DFS", "BFS", "Graph"]},
        {"id": 42, "title": "Trapping Rain Water", "difficulty": "Hard", "tags": ["Array", "Two Pointers"]},
    ],
    "Meta": [
        {"id": 1, "title": "Two Sum", "difficulty": "Easy", "tags": ["Array", "Hash Table"]},
        {"id": 125, "title": "Valid Palindrome", "difficulty": "Easy", "tags": ["String", "Two Pointers"]},
        {"id": 236, "title": "LCA of Binary Tree", "difficulty": "Medium", "tags": ["Tree", "DFS"]},
        {"id": 273, "title": "Integer to English Words", "difficulty": "Hard", "tags": ["String", "Math"]},
    ],
    "Amazon": [
        {"id": 1, "title": "Two Sum", "difficulty": "Easy", "tags": ["Array", "Hash Table"]},
        {"id": 200, "title": "Number of Islands", "difficulty": "Medium", "tags": ["DFS", "BFS"]},
        {"id": 297, "title": "Serialize and Deserialize Binary Tree", "difficulty": "Hard", "tags": ["Tree", "Design"]},
    ],
    "Microsoft": [
        {"id": 206, "title": "Reverse Linked List", "difficulty": "Easy", "tags": ["Linked List"]},
        {"id": 15, "title": "3Sum", "difficulty": "Medium", "tags": ["Array", "Two Pointers"]},
        {"id": 23, "title": "Merge k Sorted Lists", "difficulty": "Hard", "tags": ["Linked List", "Heap"]},
    ],
}


def recommend_by_weak_tags(
    weak_tags: List[Dict[str, Any]],
    difficulty: str = "medium",
    limit: int = 5
) -> List[Dict[str, str]]:
    """
    Recommend problems based on weak tags.
    
    Args:
        weak_tags: List of weak tags from tag analysis
        difficulty: Target difficulty level
        limit: Number of recommendations
        
    Returns:
        List of problem recommendations
    """
    recommendations = []
    
    for weak_tag in weak_tags[:limit]:
        tag = weak_tag.get("tag", "")
        recommendations.append({
            "tag": tag,
            "difficulty": difficulty.capitalize(),
            "reason": f"Strengthen your {tag} skills",
            "search_query": f"{tag} {difficulty}",
            "leetcode_url": f"https://leetcode.com/problemset/all/?difficulty={difficulty.upper()}&topicSlugs={tag.lower().replace(' ', '-')}"
        })
    
    return recommendations


def recommend_by_difficulty_progression(
    current_distribution: Dict[str, int],
    progression_status: str
) -> List[Dict[str, str]]:
    """
    Recommend problems based on difficulty progression.
    
    Args:
        current_distribution: Current Easy/Medium/Hard counts
        progression_status: Current progression status
        
    Returns:
        List of recommendations
    """
    recommendations = []
    
    easy = current_distribution.get("easy", 0)
    medium = current_distribution.get("medium", 0)
    hard = current_distribution.get("hard", 0)
    total = easy + medium + hard
    
    if total == 0:
        return [{
            "difficulty": "Easy",
            "reason": "Start with Easy problems to build foundation",
            "count": 10,
            "search_query": "easy beginner"
        }]
    
    easy_pct = (easy / total) * 100 if total > 0 else 0
    medium_pct = (medium / total) * 100 if total > 0 else 0
    hard_pct = (hard / total) * 100 if total > 0 else 0
    
    # Stuck on easy
    if easy_pct > 70:
        recommendations.append({
            "difficulty": "Medium",
            "reason": "You're ready for Medium problems! Start with easier Medium ones",
            "count": 5,
            "search_query": "medium acceptance-rate-high"
        })
    
    # Stuck on medium
    elif medium_pct > 70 and hard_pct < 10:
        recommendations.append({
            "difficulty": "Hard",
            "reason": "Challenge yourself with Hard problems (1-2 per week)",
            "count": 2,
            "search_query": "hard acceptance-rate-high"
        })
    
    # Good balance, keep progressing
    elif medium_pct > 40 and hard_pct > 10:
        recommendations.append({
            "difficulty": "Mixed",
            "reason": "Great balance! Continue with 60% Medium, 30% Easy, 10% Hard",
            "count": 10,
            "search_query": "medium hard"
        })
    
    # Need more medium
    elif easy_pct > 50 and medium_pct < 30:
        recommendations.append({
            "difficulty": "Medium",
            "reason": "Increase Medium problem ratio to 40-50%",
            "count": 5,
            "search_query": "medium"
        })
    
    return recommendations


def recommend_by_company(
    company: str,
    difficulty: str = "all",
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Get company-specific problem recommendations.
    
    Args:
        company: Company name (Google, Meta, Amazon, Microsoft)
        difficulty: Filter by difficulty (easy/medium/hard/all)
        limit: Number of problems to return
        
    Returns:
        List of recommended problems
    """
    if company not in COMPANY_PROBLEMS:
        return []
    
    problems = COMPANY_PROBLEMS[company]
    
    # Filter by difficulty
    if difficulty.lower() != "all":
        problems = [p for p in problems if p["difficulty"].lower() == difficulty.lower()]
    
    # Return limited results
    return problems[:limit]


def get_personalized_recommendations(
    member_data: Dict[str, Any],
    limit: int = 10
) -> Dict[str, Any]:
    """
    Generate personalized problem recommendations for a member.
    
    Args:
        member_data: Member's analysis data (tags, difficulty, etc.)
        limit: Number of recommendations
        
    Returns:
        Dict with various recommendation categories
    """
    recommendations = {
        "by_weak_tags": [],
        "by_difficulty": [],
        "by_company": {},
        "daily_practice_plan": {}
    }
    
    # Recommendations by weak tags
    weak_tags = member_data.get("weak_tags", [])
    if weak_tags:
        recommendations["by_weak_tags"] = recommend_by_weak_tags(weak_tags, limit=5)
    
    # Recommendations by difficulty progression
    current_dist = member_data.get("current_distribution", {})
    progression_status = member_data.get("progression_status", "")
    if current_dist:
        recommendations["by_difficulty"] = recommend_by_difficulty_progression(
            current_dist,
            progression_status
        )
    
    # Company-specific recommendations
    for company in ["Google", "Meta", "Amazon", "Microsoft"]:
        recommendations["by_company"][company] = recommend_by_company(company, limit=3)
    
    # Daily practice plan
    total_solved = current_dist.get("easy", 0) + current_dist.get("medium", 0) + current_dist.get("hard", 0)
    
    if total_solved < 50:
        plan = {
            "easy": 2,
            "medium": 1,
            "hard": 0,
            "focus": "Build foundation with Easy problems"
        }
    elif total_solved < 150:
        plan = {
            "easy": 1,
            "medium": 2,
            "hard": 0,
            "focus": "Focus on Medium problems"
        }
    else:
        plan = {
            "easy": 1,
            "medium": 2,
            "hard": 1,
            "focus": "Balanced practice across all difficulties"
        }
    
    recommendations["daily_practice_plan"] = plan
    
    return recommendations
