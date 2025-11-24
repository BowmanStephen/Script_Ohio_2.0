"""
Utilities for loading CFBD rating systems (SP+, FPI, Elo, SRS).
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LIBRARY_DIR = PROJECT_ROOT / "src" / "ratings"
DEFAULT_LIBRARY_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger(__name__)


def _normalize_team_name(team_name: Optional[str]) -> Optional[str]:
    if not team_name or not isinstance(team_name, str):
        return None
    team = team_name.strip()
    replacements = {
        "Ohio St.": "Ohio State",
        "Ohio St": "Ohio State",
        "Miami-FL": "Miami",
        "Miami (FL)": "Miami",
        "Miami-Florida": "Miami",
        "Miami-OH": "Miami OH",
        "Miami (OH)": "Miami OH",
        "San Jose St.": "San Jose State",
        "UAB": "UAB",
    }
    team = replacements.get(team, team)
    return team


def _fetch_graphql_ratings(season: int) -> pd.DataFrame:
    """Fetch SP+, FPI, SRS, Elo via GraphQL."""
    try:
        from src.data_sources.cfbd_graphql import CFBDGraphQLClient  # type: ignore
    except ImportError:
        logger.debug("GraphQL client not available; skipping SP+/FPI fetch.")
        return pd.DataFrame()

    api_key = os.getenv("CFBD_API_KEY")
    if not api_key:
        logger.debug("CFBD_API_KEY not set; skipping GraphQL fetch.")
        return pd.DataFrame()

    try:
        client = CFBDGraphQLClient(api_key=api_key)
        response = client.get_ratings(season=season)
        records = response.get("ratings") or response.get("data", {}).get("ratings")
        if not records:
            logger.warning("No ratings returned from GraphQL query.")
            return pd.DataFrame()
        df = pd.DataFrame(records)
        rename_map = {
            "spOverall": "sp_rating",
            "fpi": "fpi_rating",
            "elo": "elo_rating",
            "srs": "srs_rating",
        }
        df = df.rename(columns=rename_map)
        df["team"] = df["team"].apply(_normalize_team_name)
        df["season"] = season
        df["source"] = "graphql"
        keep_cols = ["team", "season", "sp_rating", "fpi_rating", "elo_rating", "srs_rating", "source"]
        return df[keep_cols]
    except Exception as exc:  # pragma: no cover - network dependent
        logger.warning("GraphQL ratings fetch failed: %s", exc)
        return pd.DataFrame()


def _fetch_rest_elo(season: int) -> pd.DataFrame:
    """Fetch Elo ratings via REST as a fallback."""
    try:
        from src.cfbd_client.unified_client import UnifiedCFBDClient  # type: ignore
    except ImportError:
        logger.debug("Unified CFBD client unavailable; cannot fetch REST Elo.")
        return pd.DataFrame()

    try:
        client = UnifiedCFBDClient()
        elo_data = client.get_ratings(year=season)
        if not elo_data:
            return pd.DataFrame()
        df = pd.DataFrame(elo_data)
        if "team" not in df.columns or "elo" not in df.columns:
            return pd.DataFrame()
        df = df.rename(columns={"elo": "elo_rating"})
        df["team"] = df["team"].apply(_normalize_team_name)
        df["season"] = season
        df["source"] = "rest"
        return df[["team", "season", "elo_rating", "source"]]
    except Exception as exc:  # pragma: no cover - network dependent
        logger.warning("REST Elo fetch failed: %s", exc)
        return pd.DataFrame()


def load_cfbd_ratings(
    season: int = 2025,
    refresh: bool = False,
    cache_path: Optional[Path] = None,
) -> pd.DataFrame:
    """Load CFBD ratings (SP+, FPI, Elo, SRS) with caching."""
    cache_path = cache_path or DEFAULT_LIBRARY_DIR / f"cfbd_ratings_{season}.csv"
    if not refresh and cache_path.exists():
        return pd.read_csv(cache_path)

    graphql_df = _fetch_graphql_ratings(season)
    rest_df = _fetch_rest_elo(season)

    if graphql_df.empty and rest_df.empty:
        logger.warning("No CFBD ratings available (GraphQL and REST both empty).")
        empty = pd.DataFrame(
            {
                "team": [],
                "season": [],
                "sp_rating": [],
                "fpi_rating": [],
                "elo_rating": [],
                "srs_rating": [],
                "source": [],
            }
        )
        return empty

    df = graphql_df
    if not rest_df.empty:
        if df.empty:
            df = rest_df
        else:
            df = df.merge(
                rest_df[["team", "elo_rating"]],
                on="team",
                how="left",
                suffixes=("", "_rest"),
            )
            df["elo_rating"] = df["elo_rating"].fillna(df.pop("elo_rating_rest"))

    df["season"] = season
    missing_cols = ["sp_rating", "fpi_rating", "elo_rating", "srs_rating", "source"]
    for col in missing_cols:
        if col not in df.columns:
            df[col] = pd.NA

    df = df[["team", "season", "sp_rating", "fpi_rating", "elo_rating", "srs_rating", "source"]]
    df = df.dropna(subset=["team"]).drop_duplicates(subset=["team"])

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(cache_path, index=False)
    return df


__all__ = ["load_cfbd_ratings"]

