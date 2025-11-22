"""High-level dataset helpers that wrap the CFBD client."""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

import pandas as pd

from .client import CFBDClient

_REQUIRED_GAME_COLUMNS = [
    "id",
    "home_team",
    "away_team",
    "home_points",
    "away_points",
    "week",
    "season",
    "fetched_at",
]

_REQUIRED_RATINGS_COLUMNS = [
    "team",
    "conference",
    "rating_type",
    "rating_value",
    "fetched_at",
]

_REQUIRED_LINE_COLUMNS = [
    "game_id",
    "provider",
    "spread",
    "over_under",
    "fetched_at",
]

_REQUIRED_RECRUITING_COLUMNS = [
    "team",
    "rank",
    "points",
    "avg_rating",
    "fetched_at",
]

_REQUIRED_WEATHER_COLUMNS = [
    "game_id",
    "home_team",
    "away_team",
    "temperature",
    "temperature_high",
    "temperature_low",
    "wind_speed",
    "weather_condition",
    "fetched_at",
]

_REQUIRED_MEDIA_COLUMNS = [
    "game_id",
    "tv",
    "radio",
    "satellite",
    "internet",
    "fetched_at",
]

_REQUIRED_PREDICTED_COLUMNS = [
    "team",
    "opponent",
    "predicted_margin",
    "win_probability",
    "is_home",
    "fetched_at",
]


def fetch_games(
    client: CFBDClient,
    *,
    year: int,
    week: int,
    season_type: str = "regular",
) -> pd.DataFrame:
    """Return normalized game data for the specified week."""

    raw_games = client.get_games(year=year, week=week, season_type=season_type)
    records: List[Dict[str, Any]] = []
    fetched_at = _timestamp()

    for game in raw_games or []:
        records.append(
            {
                "id": game.get("id"),
                "home_team": _normalize_team(game.get("home_team")),
                "away_team": _normalize_team(game.get("away_team")),
                "home_points": game.get("home_points"),
                "away_points": game.get("away_points"),
                "week": game.get("week"),
                "season": game.get("season"),
                "fetched_at": fetched_at,
            }
        )

    df = pd.DataFrame.from_records(records)
    _validate_columns(df, _REQUIRED_GAME_COLUMNS)
    return df[_REQUIRED_GAME_COLUMNS]


def fetch_ratings(client: CFBDClient, *, year: int, week: int) -> pd.DataFrame:
    """Return team ratings for the specified week."""

    raw_ratings = client.get_ratings(year=year, week=week)
    fetched_at = _timestamp()
    records = [
        {
            "team": _normalize_team(entry.get("team")),
            "conference": entry.get("conference"),
            "rating_type": entry.get("rating_type"),
            "rating_value": entry.get("rating"),
            "fetched_at": fetched_at,
        }
        for entry in (raw_ratings or [])
    ]

    df = pd.DataFrame.from_records(records)
    _validate_columns(df, _REQUIRED_RATINGS_COLUMNS)
    return df[_REQUIRED_RATINGS_COLUMNS]


def fetch_lines(client: CFBDClient, *, year: int, week: int) -> pd.DataFrame:
    """Return betting lines for each provider for the week."""

    raw_lines = client.get_lines(year=year, week=week)
    fetched_at = _timestamp()
    records: List[Dict[str, Any]] = []

    for game in raw_lines or []:
        game_id = game.get("game_id") or game.get("id")
        for line in game.get("lines", []):
            records.append(
                {
                    "game_id": game_id,
                    "provider": line.get("provider"),
                    "spread": line.get("spread"),
                    "over_under": line.get("overUnder") or line.get("over_under"),
                    "fetched_at": fetched_at,
                }
            )

    df = pd.DataFrame.from_records(records)
    _validate_columns(df, _REQUIRED_LINE_COLUMNS)
    return df[_REQUIRED_LINE_COLUMNS]


def fetch_recruiting(client: CFBDClient, *, year: int) -> pd.DataFrame:
    """Return recruiting rankings for the specified year."""

    raw = client.get_recruiting(year=year)
    fetched_at = _timestamp()
    records = [
        {
            "team": _normalize_team(entry.get("team")),
            "rank": entry.get("rank"),
            "points": entry.get("points"),
            "avg_rating": entry.get("avgRating") or entry.get("average_rating"),
            "fetched_at": fetched_at,
        }
        for entry in (raw or [])
    ]

    df = pd.DataFrame.from_records(records)
    _validate_columns(df, _REQUIRED_RECRUITING_COLUMNS)
    return df[_REQUIRED_RECRUITING_COLUMNS]


def fetch_weather(
    client: CFBDClient,
    *,
    year: int,
    week: Optional[int] = None,
    season_type: str = "regular",
) -> pd.DataFrame:
    """Return game weather information for the requested window."""

    raw = client.get_game_weather(year=year, week=week, season_type=season_type)
    fetched_at = _timestamp()
    records = [
        {
            "game_id": entry.get("game_id") or entry.get("id"),
            "home_team": _normalize_team(entry.get("home_team")),
            "away_team": _normalize_team(entry.get("away_team")),
            "temperature": entry.get("temperature"),
            "temperature_high": entry.get("temperatureHigh") or entry.get("temperature_high"),
            "temperature_low": entry.get("temperatureLow") or entry.get("temperature_low"),
            "wind_speed": entry.get("windSpeed") or entry.get("wind_speed"),
            "weather_condition": entry.get("condition") or entry.get("weather_condition"),
            "fetched_at": fetched_at,
        }
        for entry in (raw or [])
    ]

    df = pd.DataFrame.from_records(records)
    _validate_columns(df, _REQUIRED_WEATHER_COLUMNS)
    return df[_REQUIRED_WEATHER_COLUMNS]


def fetch_media(
    client: CFBDClient,
    *,
    year: int,
    week: Optional[int] = None,
    season_type: str = "regular",
) -> pd.DataFrame:
    """Return broadcast assignments for games."""

    raw = client.get_game_media(year=year, week=week, season_type=season_type)
    fetched_at = _timestamp()
    records = [
        {
            "game_id": entry.get("game_id") or entry.get("id"),
            "tv": entry.get("tv"),
            "radio": entry.get("radio"),
            "satellite": entry.get("satellite"),
            "internet": entry.get("internet"),
            "fetched_at": fetched_at,
        }
        for entry in (raw or [])
    ]

    df = pd.DataFrame.from_records(records)
    _validate_columns(df, _REQUIRED_MEDIA_COLUMNS)
    return df[_REQUIRED_MEDIA_COLUMNS]


def fetch_predicted_points(
    client: CFBDClient,
    *,
    year: int,
    week: Optional[int] = None,
    season_type: str = "regular",
) -> pd.DataFrame:
    """Return predicted point margins and win probabilities."""

    raw = client.get_predicted_points(year=year, week=week, season_type=season_type)
    fetched_at = _timestamp()
    records = [
        {
            "team": _normalize_team(entry.get("team")),
            "opponent": _normalize_team(entry.get("opponent")),
            "predicted_margin": entry.get("predictedMargin") or entry.get("predicted_margin"),
            "win_probability": entry.get("winProbability") or entry.get("win_probability"),
            "is_home": entry.get("isHome") if "isHome" in entry else entry.get("is_home"),
            "fetched_at": fetched_at,
        }
        for entry in (raw or [])
    ]

    df = pd.DataFrame.from_records(records)
    _validate_columns(df, _REQUIRED_PREDICTED_COLUMNS)
    return df[_REQUIRED_PREDICTED_COLUMNS]


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_team(name: Any) -> Any:
    if not isinstance(name, str):
        return name
    simplified = re.sub(r"\s+", "_", name.strip().lower())
    return simplified


def _validate_columns(df: pd.DataFrame, required: Iterable[str]) -> None:
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


__all__ = [
    "fetch_games",
    "fetch_ratings",
    "fetch_lines",
    "fetch_recruiting",
    "fetch_weather",
    "fetch_media",
    "fetch_predicted_points",
]
