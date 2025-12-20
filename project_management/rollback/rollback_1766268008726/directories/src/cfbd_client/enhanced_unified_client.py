"""
Enhanced Unified CFBD API client with additional endpoints for 2025 season coverage.
This extends the base UnifiedCFBDClient with missing endpoints identified in the audit.
"""

import logging
from typing import Any, Dict, List, Optional

from .unified_client import UnifiedCFBDClient

logger = logging.getLogger(__name__)


class EnhancedUnifiedCFBDClient(UnifiedCFBDClient):
    """
    Enhanced CFBD client with additional endpoints for comprehensive 2025 coverage.

    Adds support for:
    - Win probabilities
    - Game media content
    - Team rosters and depth charts
    - Advanced team statistics
    - Player statistics
    - Recruiting data
    - Team matchup history
    - Enhanced error handling
    """

    def __init__(self, config=None):
        """Initialize enhanced client"""
        super().__init__(config)
        logger.info("🚀 Enhanced CFBD Client initialized with additional endpoints")

    def get_win_probabilities(
        self,
        year: int,
        week: Optional[int] = None,
        season_type: str = "regular",
        team: Optional[str] = None,
    ) -> List[Dict]:
        """
        Get pregame win probability predictions.

        Args:
            year: Season year
            week: Week number (optional)
            season_type: 'regular', 'postseason', or 'both'
            team: Specific team (optional)

        Returns:
            List of win probability predictions
        """
        try:
            # Direct API call since this endpoint may not be in base client
            import cfbd
            from cfbd import GamesApi

            params = {"year": year, "seasonType": season_type, "team": team}
            if week:
                params["week"] = week

            games_api = GamesApi(self.api_client)
            data = games_api.get_win_probabilities(**params)

            if data:
                return [
                    item.to_dict() if hasattr(item, "to_dict") else item
                    for item in data
                ]
            return []

        except Exception as e:
            logger.warning(f"Win probabilities not available: {e}")
            return []

    def get_game_media(
        self,
        year: int,
        week: Optional[int] = None,
        season_type: str = "regular",
        team: Optional[str] = None,
        game_id: Optional[int] = None,
    ) -> List[Dict]:
        """
        Get game media content and highlights.

        Args:
            year: Season year
            week: Week number (optional)
            season_type: 'regular', 'postseason', or 'both'
            team: Specific team (optional)
            game_id: Specific game ID (optional)

        Returns:
            List of media content items
        """
        try:
            import cfbd
            from cfbd import GamesApi

            params = {"year": year, "seasonType": season_type, "team": team}
            if week:
                params["week"] = week
            if game_id:
                params["id"] = game_id

            games_api = GamesApi(self.api_client)
            data = games_api.get_game_media(**params)

            if data:
                return [
                    item.to_dict() if hasattr(item, "to_dict") else item
                    for item in data
                ]
            return []

        except Exception as e:
            logger.warning(f"Game media not available: {e}")
            return []

    def get_roster(self, team: str, year: int) -> List[Dict]:
        """
        Get team roster and depth chart information.

        Args:
            team: Team name or abbreviation
            year: Season year

        Returns:
            List of roster entries with player information
        """
        try:
            # Check if base client has this method
            if hasattr(super(), "get_roster"):
                return super().get_roster(team=team, year=year)

            # Direct API implementation
            import cfbd
            from cfbd import TeamsApi

            teams_api = TeamsApi(self.api_client)
            data = teams_api.get_roster(team=team, year=year)

            if data:
                return [
                    item.to_dict() if hasattr(item, "to_dict") else item
                    for item in data
                ]
            return []

        except Exception as e:
            logger.warning(f"Roster data not available for {team} {year}: {e}")
            return []

    def get_advanced_team_stats(
        self, year: int, team: Optional[str] = None, conference: Optional[str] = None
    ) -> List[Dict]:
        """
        Get advanced team statistics including EPA, success rates, etc.

        Args:
            year: Season year
            team: Specific team (optional)
            conference: Specific conference (optional)

        Returns:
            List of advanced team statistics
        """
        try:
            # Check if base client has this method
            if hasattr(super(), "get_advanced_stats"):
                return super().get_advanced_stats(year=year, team=team)

            # Direct API implementation
            import cfbd
            from cfbd import StatsApi

            stats_api = StatsApi(self.api_client)
            data = stats_api.get_advanced_team_stats(
                year=year, team=team, conference=conference
            )

            if data:
                return [
                    item.to_dict() if hasattr(item, "to_dict") else item
                    for item in data
                ]
            return []

        except Exception as e:
            logger.warning(f"Advanced team stats not available for {year}: {e}")
            return []

    def get_player_season_stats(
        self,
        year: int,
        team: Optional[str] = None,
        conference: Optional[str] = None,
        category: Optional[str] = None,
        position: Optional[str] = None,
    ) -> List[Dict]:
        """
        Get player season statistics.

        Args:
            year: Season year
            team: Specific team (optional)
            conference: Specific conference (optional)
            category: Stat category (passing, rushing, receiving, etc.)
            position: Specific position (optional)

        Returns:
            List of player statistics
        """
        try:
            # Check if base client has this method
            if hasattr(super(), "get_player_stats"):
                return super().get_player_stats(year=year, team=team, category=category)

            # Direct API implementation
            import cfbd
            from cfbd import PlayersApi

            players_api = PlayersApi(self.api_client)
            data = players_api.get_player_season_stats(
                year=year,
                team=team,
                conference=conference,
                category=category,
                position=position,
            )

            if data:
                return [
                    item.to_dict() if hasattr(item, "to_dict") else item
                    for item in data
                ]
            return []

        except Exception as e:
            logger.warning(f"Player season stats not available for {year}: {e}")
            return []

    def get_recruiting(self, year: int, team: Optional[str] = None) -> List[Dict]:
        """
        Get recruiting class rankings and commitments.

        Args:
            year: Recruiting class year
            team: Specific team (optional)

        Returns:
            List of recruiting information
        """
        try:
            # Direct API implementation
            import cfbd
            from cfbd import RecruitingApi

            recruiting_api = RecruitingApi(self.api_client)

            # Try different endpoint methods
            if hasattr(recruiting_api, "get_team_recruiting_rankings"):
                data = recruiting_api.get_team_recruiting_rankings(year=year, team=team)
            elif hasattr(recruiting_api, "get_recruiting"):
                data = recruiting_api.get_recruiting(year=year, team=team)
            else:
                logger.warning("Recruiting API methods not found")
                return []

            if data:
                return [
                    item.to_dict() if hasattr(item, "to_dict") else item
                    for item in data
                ]
            return []

        except Exception as e:
            logger.warning(f"Recruiting data not available for {year}: {e}")
            return []

    def get_team_matchup(self, team1: str, team2: str) -> List[Dict]:
        """
        Get historical matchup records between two teams.

        Args:
            team1: First team name
            team2: Second team name

        Returns:
            List of historical matchup data
        """
        try:
            # Direct API implementation
            import cfbd
            from cfbd import TeamsApi

            teams_api = TeamsApi(self.api_client)
            data = teams_api.get_team_matchup(team1=team1, team2=team2)

            if data:
                return [
                    item.to_dict() if hasattr(item, "to_dict") else item
                    for item in data
                ]
            return []

        except Exception as e:
            logger.warning(
                f"Team matchup data not available for {team1} vs {team2}: {e}"
            )
            return []

    def get_game_box_score(self, game_id: int) -> Optional[Dict]:
        """
        Get detailed game box score.

        Args:
            game_id: CFBD game ID

        Returns:
            Box score data or None if not found
        """
        try:
            # Direct API implementation
            import cfbd
            from cfbd import GamesApi

            games_api = GamesApi(self.api_client)
            data = games_api.get_game_box_score(game_id=game_id)

            if data:
                return data.to_dict() if hasattr(data, "to_dict") else data
            return None

        except Exception as e:
            logger.warning(f"Box score not available for game {game_id}: {e}")
            return None

    def get_team_talent(self, year: int, team: Optional[str] = None) -> List[Dict]:
        """
        Get team talent recruiting rankings.

        Args:
            year: Season year
            team: Specific team (optional)

        Returns:
            List of talent ranking data
        """
        try:
            # Check if base client has this method
            if hasattr(super(), "get_talent"):
                return super().get_talent(year=year, team=team)

            # Direct API implementation
            import cfbd
            from cfbd import TeamsApi

            teams_api = TeamsApi(self.api_client)
            data = teams_api.get_team_talent(year=year, team=team)

            if data:
                return [
                    item.to_dict() if hasattr(item, "to_dict") else item
                    for item in data
                ]
            return []

        except Exception as e:
            logger.warning(f"Team talent data not available for {year}: {e}")
            return []

    def get_elo(self, year: int, week: Optional[int] = None) -> List[Dict]:
        """
        Get Elo power ratings.

        Args:
            year: Season year
            week: Week number (optional)

        Returns:
            List of Elo ratings
        """
        try:
            # Check if base client has this method
            if hasattr(super(), "get_ratings"):
                return super().get_ratings(year=year, week=week)

            # Direct API implementation
            import cfbd
            from cfbd import RatingsApi

            ratings_api = RatingsApi(self.api_client)
            data = ratings_api.get_elo(year=year, week=week)

            if data:
                return [
                    item.to_dict() if hasattr(item, "to_dict") else item
                    for item in data
                ]
            return []

        except Exception as e:
            logger.warning(f"Elo ratings not available for {year}: {e}")
            return []

    # Enhanced convenience methods for common 2025 data patterns

    def get_2025_game_data(
        self,
        week: Optional[int] = None,
        include_win_probs: bool = True,
        include_media: bool = False,
    ) -> Dict[str, Any]:
        """
        Get comprehensive 2025 game data with optional enhancements.

        Args:
            week: Specific week (optional)
            include_win_probs: Whether to include win probabilities
            include_media: Whether to include media content

        Returns:
            Dictionary with games and optional enhanced data
        """
        try:
            # Get basic games
            games = self.get_games(year=2025, week=week)

            result = {
                "games": games,
                "season": 2025,
                "week": week,
                "total_games": len(games),
            }

            # Add win probabilities if requested
            if include_win_probs:
                win_probs = self.get_win_probabilities(year=2025, week=week)
                result["win_probabilities"] = win_probs

            # Add media if requested
            if include_media:
                media = self.get_game_media(year=2025, week=week)
                result["media"] = media

            return result

        except Exception as e:
            logger.error(f"Error getting 2025 game data: {e}")
            return {"error": str(e), "games": []}

    def get_2025_team_rosters(
        self, teams: Optional[List[str]] = None
    ) -> Dict[str, List[Dict]]:
        """
        Get 2025 roster data for specified teams or all FBS teams.

        Args:
            teams: List of team names (optional, will get all if None)

        Returns:
            Dictionary mapping team names to roster data
        """
        try:
            rosters = {}

            if not teams:
                # Get all FBS teams
                all_teams = self.get_teams(conference=None)  # Get all teams
                teams = [
                    team.get("school", team.get("team", ""))
                    for team in all_teams
                    if team.get("school")
                ]
                teams = [team for team in teams if team]  # Filter out empty names

            for team in teams:
                roster = self.get_roster(team=team, year=2025)
                if roster:
                    rosters[team] = roster

            return rosters

        except Exception as e:
            logger.error(f"Error getting 2025 rosters: {e}")
            return {}

    def get_comprehensive_2025_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive 2025 statistics from multiple endpoints.

        Returns:
            Dictionary with various 2025 statistical data
        """
        try:
            result = {
                "season": 2025,
                "timestamp": self._get_current_timestamp(),
                "data_sources": [],
            }

            # Basic team stats
            try:
                team_stats = self.get_advanced_team_stats(year=2025)
                result["advanced_team_stats"] = team_stats
                result["data_sources"].append("advanced_team_stats")
            except Exception as e:
                logger.warning(f"Could not get advanced team stats: {e}")

            # Player stats
            try:
                player_stats = self.get_player_season_stats(year=2025)
                result["player_stats"] = player_stats
                result["data_sources"].append("player_stats")
            except Exception as e:
                logger.warning(f"Could not get player stats: {e}")

            # Recruiting data (2025 recruiting class)
            try:
                recruiting = self.get_recruiting(year=2025)
                result["recruiting"] = recruiting
                result["data_sources"].append("recruiting")
            except Exception as e:
                logger.warning(f"Could not get recruiting data: {e}")

            # Team talent
            try:
                talent = self.get_team_talent(year=2025)
                result["team_talent"] = talent
                result["data_sources"].append("team_talent")
            except Exception as e:
                logger.warning(f"Could not get team talent: {e}")

            return result

        except Exception as e:
            logger.error(f"Error getting comprehensive 2025 stats: {e}")
            return {"error": str(e), "season": 2025}

    def _get_current_timestamp(self) -> str:
        """Get current timestamp for data tracking"""
        from datetime import datetime, timezone

        return datetime.now(timezone.utc).isoformat()

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get enhanced performance metrics"""
        base_metrics = (
            super().get_performance_metrics()
            if hasattr(super(), "get_performance_metrics")
            else {}
        )

        enhanced_metrics = {
            **base_metrics,
            "enhanced_endpoints_available": [
                "win_probabilities",
                "game_media",
                "rosters",
                "advanced_team_stats",
                "player_season_stats",
                "recruiting",
                "team_matchup",
                "game_box_score",
                "team_talent",
                "elo",
            ],
            "client_type": "EnhancedUnifiedCFBDClient",
            "season_2025_coverage": "Enhanced with additional endpoints",
        }

        return enhanced_metrics
