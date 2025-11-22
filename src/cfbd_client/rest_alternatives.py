"""
REST API alternatives for GraphQL functionality.
Provides equivalent functionality using REST endpoints with appropriate caching.
"""

import time
from typing import Dict, List, Optional, Any
from src.cfbd_client.unified_client import UnifiedCFBDClient

class CFBDRestAlternatives:
    """REST alternatives for GraphQL functionality"""
    
    def __init__(self, client: UnifiedCFBDClient):
        self.client = client
        self.polling_interval = 30  # seconds
    
    def get_game_updates(self, game_id: str) -> Dict[str, Any]:
        """Get game updates via REST polling"""
        # Use games endpoint with game_id filter
        # Assuming 2025 season for current updates
        games = self.client.get_games(year=2025)
        
        # Handle ID comparison robustly
        try:
            gid = int(game_id)
        except ValueError:
            gid = game_id
            
        return next((g for g in games if g.get('id') == gid or str(g.get('id')) == str(game_id)), None)
    
    def get_team_trends(self, team: str, years: int = 3) -> List[Dict[str, Any]]:
        """Get team performance trends via REST"""
        trends = []
        # Range excluding 2025? Or including? Plan says `range(2025 - years, 2025)`.
        # If years=3, this gives 2022, 2023, 2024.
        # Assuming we want historical trends.
        for year in range(2025 - years, 2025):
            games = self.client.get_games(year=year, team=team)
            # Process games for trends
            trends.extend(self._process_team_trends(games, year, team))
        return trends
    
    def _process_team_trends(self, games: List[Dict], year: int, team: str) -> List[Dict]:
        """Process games to extract trend data"""
        processed = []
        for game in games:
             is_home = game.get("home_team") == team
             points = game.get("home_points") if is_home else game.get("away_points")
             opponent = game.get("away_team") if is_home else game.get("home_team")
             opp_points = game.get("away_points") if is_home else game.get("home_points")
             
             if points is None: continue # Skip unplayed
             
             margin = points - (opp_points or 0)
             
             processed.append({
                 "year": year,
                 "week": game.get("week"),
                 "opponent": opponent,
                 "points": points,
                 "margin": margin,
                 "result": "W" if margin > 0 else ("L" if margin < 0 else "T")
             })
        return processed

