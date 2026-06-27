import requests

from companion_mcp.state import mcp
from core.config import load_config as _load_config
from core.retroachievements_api import get_user_summary as _get_user_summary, RetroAchievementsError

RA_BASE_URL = "https://retroachievements.org/API"


def _get_credentials() -> tuple[str, str]:
    cfg = _load_config()
    username = cfg.get("retroachievements_username", "").strip()
    api_key = cfg.get("retroachievements_api_key", "").strip()
    return username, api_key


@mcp.tool()
def get_ra_user_summary(recent_games: int = 5) -> dict:
    """Get RetroAchievements account summary: points, rank, and recent games with completion %."""
    username, api_key = _get_credentials()
    if not username or not api_key:
        return {"error": "RetroAchievements credentials not configured in companion app."}

    try:
        data = _get_user_summary(username, api_key, recent_games=recent_games)
    except RetroAchievementsError as exc:
        return {"error": str(exc)}

    recently_played = data.get("RecentlyPlayed") or []
    games = []
    for game in recently_played[:recent_games]:
        possible = game.get("NumPossibleAchievements", 0) or 0
        achieved = game.get("NumAchieved", 0) or 0
        pct = round(achieved / possible * 100, 1) if possible else 0
        games.append({
            "game_id": game.get("GameID"),
            "title": game.get("Title"),
            "achievements_earned": achieved,
            "achievements_total": possible,
            "completion_pct": pct,
        })

    return {
        "username": data.get("Username") or username,
        "total_points": data.get("TotalPoints", 0),
        "rank": data.get("Rank"),
        "recent_games": games,
    }


@mcp.tool()
def get_ra_game_progress(game_id: int) -> dict:
    """Get achievement progress for a specific game by its RetroAchievements game ID."""
    username, api_key = _get_credentials()
    if not username or not api_key:
        return {"error": "RetroAchievements credentials not configured in companion app."}

    try:
        response = requests.get(
            f"{RA_BASE_URL}/API_GetGameInfoAndUserProgress.php",
            params={"y": api_key, "u": username, "g": game_id},
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as exc:
        return {"error": f"Network error: {exc}"}
    except ValueError as exc:
        return {"error": f"Invalid response from RetroAchievements: {exc}"}

    raw_achievements = data.get("Achievements") or {}
    if not isinstance(raw_achievements, dict):
        raw_achievements = {}
    achievements = []
    for _, ach in raw_achievements.items():
        achievements.append({
            "title": ach.get("Title"),
            "points": ach.get("Points", 0),
            "earned": bool(ach.get("DateEarned")),
            "description": ach.get("Description", ""),
        })

    earned = sum(1 for a in achievements if a["earned"])
    total = len(achievements)
    pct = round(earned / total * 100, 1) if total else 0

    return {
        "title": data.get("Title"),
        "game_id": game_id,
        "achievements": achievements,
        "earned": earned,
        "total": total,
        "completion_pct": pct,
    }
