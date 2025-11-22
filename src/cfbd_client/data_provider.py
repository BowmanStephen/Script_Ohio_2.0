"""Shared CFBD data provider for agents."""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import os

from .client import CFBDClient
from .datasets import (
    fetch_games,
    fetch_lines,
    fetch_predicted_points,
    fetch_ratings,
)

CACHE_TTL = 300  # seconds


@dataclass
class CacheEntry:
    value: Any
    timestamp: float


class CFBDDataProvider:
    """High-level helper that wraps the REST CFBD client with light caching."""

    def __init__(
        self,
        cfbd_client: Optional[CFBDClient] = None,
        telemetry_hook = None,
    ) -> None:
        self.telemetry_hook = telemetry_hook
        self.cfbd_client = cfbd_client or CFBDClient(telemetry_hook=telemetry_hook)
        self._cache: Dict[str, CacheEntry] = {}

    def get_recent_games(
        self,
        *,
        season: int,
        week: Optional[int] = None,
        team: Optional[str] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        df = fetch_games(self.cfbd_client, year=season, week=week)
        if team:
            df = df[
                (df["home_team"] == team.lower())
                | (df["away_team"] == team.lower())
            ]
        if df.empty:
            return []
        return df.head(limit).to_dict("records")

    def get_team_ratings(
        self,
        *,
        season: int,
        week: Optional[int] = None,
        team: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        df = fetch_ratings(self.cfbd_client, year=season, week=week)
        if team:
            df = df[df["team"] == team.lower()]
        return df.to_dict("records")

    def get_predicted_points(
        self,
        *,
        season: int,
        week: Optional[int] = None,
        team: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        df = fetch_predicted_points(self.cfbd_client, year=season, week=week)
        if team:
            df = df[df["team"] == team.lower()]
        return df.to_dict("records")

    def get_lines(
        self,
        *,
        season: int,
        week: int,
        team: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        df = fetch_lines(self.cfbd_client, year=season, week=week)
        if team:
            df = df[df["game_id"].isin(self._game_ids_for_team(season, week, team))]
        return df.to_dict("records")

    def get_adjusted_team_metrics(self, *, team: str, season: int) -> Dict[str, Any]:
        """
        Get adjusted team metrics using pure REST API calls.
        Returns team ratings with offense/defense/special teams breakdowns.
        """
        cache_key = f"adj_metrics:{team}:{season}"
        cached = self._cache.get(cache_key)
        if cached and time.time() - cached.timestamp < CACHE_TTL:
            return cached.value

        try:
            # Use SP+ ratings via REST API as the primary source for adjusted metrics
            sp_data = self.cfbd_client.get_sp_ratings(year=season, team=team)
            if not sp_data:
                print(f"⚠️ Warning: No SP+ ratings data found for {team} ({season})")
                return {}

            # SP+ response is a list, usually one item if team is specified
            # Item format: {'year': 2024, 'team': 'Ohio State', 'rating': 28.5, 'offense': {'rating': 42.1, ...}, 'defense': {'rating': 13.6, ...}, ...}
            # We need to map it to: {'team': ..., 'year': ..., 'rating': ..., 'offense': ..., 'defense': ..., 'specialTeams': ...}

            record = sp_data[0]
            metrics = {
                "team": record.get("team"),
                "year": record.get("year"),
                "rating": record.get("rating"),
                "offense": record.get("offense", {}).get("rating"),
                "defense": record.get("defense", {}).get("rating"),
                "specialTeams": record.get("specialTeams", {}).get("rating"),
            }

            # Cache the result
            self._cache[cache_key] = CacheEntry(value=metrics, timestamp=time.time())
            return metrics

        except Exception as e:
            print(f"⚠️ Warning: Failed to fetch adjusted team metrics via REST: {e}")
            # Return empty dict to prevent crashes, but maintain expected interface
            return {
                "team": team,
                "year": season,
                "rating": None,
                "offense": None,
                "defense": None,
                "specialTeams": None,
            }

    def get_team_snapshot(
        self,
        *,
        team: str,
        season: int,
        week: Optional[int] = None,
    ) -> Dict[str, Any]:
        games = self.get_recent_games(season=season, week=week, team=team, limit=3)
        ratings = self.get_team_ratings(season=season, week=week, team=team)
        predicted = self.get_predicted_points(season=season, week=week, team=team)
        adjusted = self.get_adjusted_team_metrics(team=team, season=season)

        return {
            "team": team,
            "season": season,
            "week": week,
            "recent_games": games,
            "ratings": ratings,
            "predicted_points": predicted,
            "adjusted_metrics": adjusted,
        }

    def _game_ids_for_team(self, season: int, week: int, team: str) -> List[Any]:
        games = self.get_recent_games(season=season, week=week, team=team, limit=20)
        return [game.get("id") for game in games if game.get("id") is not None]

__all__ = ["CFBDDataProvider"]
