"""Utilities for mapping CFBD data into the 86-feature training schema."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REFERENCE_DATASET = PROJECT_ROOT / "model_pack" / "updated_training_data.csv"


@lru_cache(maxsize=1)
def _load_reference_columns(path: Path = DEFAULT_REFERENCE_DATASET) -> List[str]:
    if not path.exists():
        raise FileNotFoundError(
            f"Reference dataset not found at {path}. Ensure updated_training_data.csv exists."
        )
    with path.open("r", encoding="utf-8") as handle:
        header = handle.readline().strip()
    return header.split(",")


def _extract(record: Dict[str, Any], *candidates: str) -> Any:
    """Extract value from record using candidate keys, handling both dicts and objects."""
    for key in candidates:
        # Handle dict-like objects
        if isinstance(record, dict):
            if key in record:
                return record[key]
        # Handle objects with attributes (e.g., Mock objects, REST API objects)
        else:
            if hasattr(record, key):
                return getattr(record, key)
            # Also try snake_case to camelCase conversion for object attributes
            camel_key = key.replace("_", "")
            if hasattr(record, camel_key):
                return getattr(record, camel_key)
    return None


def _coerce_bool(value: Any) -> Optional[bool]:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes"}:
            return True
        if lowered in {"false", "0", "no"}:
            return False
    if isinstance(value, (int, float)):
        return bool(value)
    return None


@dataclass(slots=True)
class FeatureEngineeringConfig:
    season: Optional[int] = None
    enforce_reference_schema: bool = True
    reference_dataset: Path = DEFAULT_REFERENCE_DATASET


class CFBDFeatureEngineer:
    """Transforms CFBD payloads into the 86-feature dataset compatible with the models."""

    def __init__(self, config: Optional[FeatureEngineeringConfig] = None) -> None:
        self.config = config or FeatureEngineeringConfig()
        self._reference_columns = _load_reference_columns(self.config.reference_dataset)

    # ------------------------------------------------------------------ #
    # Public helpers
    # ------------------------------------------------------------------ #
    def prepare_games_frame(
        self,
        games_payload: Any,
        *,
        source: str = "rest",
    ) -> pd.DataFrame:
        """Normalize raw REST payloads into a pandas DataFrame."""

        records = self._unwrap_payload(games_payload, source=source)
        normalized = [self._normalize_record(record, source=source) for record in records if record]
        games_df = pd.DataFrame(normalized)

        if games_df.empty:
            return pd.DataFrame(columns=self._reference_columns)

        if "season" not in games_df.columns or games_df["season"].isna().all():
            if self.config.season is not None:
                games_df["season"] = self.config.season

        for column in ("home_points", "away_points"):
            if column not in games_df.columns:
                games_df[column] = 0.0
            games_df[column] = (
                pd.to_numeric(games_df[column], errors="coerce")
                .fillna(0)
                .astype(float)
            )
        games_df["margin"] = (games_df["home_points"] - games_df["away_points"]).abs()
        if "conference_game" not in games_df.columns:
            games_df["conference_game"] = False
        else:
            games_df["conference_game"] = games_df["conference_game"].fillna(False).astype(bool)

        return games_df

    def merge_spreads(self, games_df: pd.DataFrame, lines_payload: Iterable[Dict[str, Any]]) -> pd.DataFrame:
        """Merge betting spread data from the lines endpoint into the games frame."""

        if games_df.empty:
            return games_df

        spread_map: Dict[int, float] = {}
        for line in lines_payload or []:
            game_id = _extract(line, "gameId", "game_id", "id")
            spread = _extract(line, "spread", "spreadOpen")
            if game_id is None or spread is None:
                continue
            try:
                spread_map[int(game_id)] = float(spread)
            except (TypeError, ValueError):
                continue

        if not spread_map:
            return games_df

        spread_series = pd.Series(spread_map, name="spread_lookup")
        spread_series.index.name = "id"
        merged = games_df.merge(
            spread_series,
            how="left",
            left_on="id",
            right_index=True,
        )
        if "spread" not in merged.columns:
            merged["spread"] = pd.NA
        merged["spread"] = merged["spread"].combine_first(merged["spread_lookup"])
        merged = merged.drop(columns=["spread_lookup"])
        return merged

    def build_feature_frame(
        self,
        games_df: pd.DataFrame,
        metrics_by_game: Optional[Dict[Any, Dict[str, Any]]] = None,
    ) -> pd.DataFrame:
        """Attach advanced metrics and align to the reference 86-feature schema."""

        if games_df.empty:
            return pd.DataFrame(columns=self._reference_columns)

        working = games_df.copy()
        working = self._add_game_key(working)

        if metrics_by_game:
            metrics_df = pd.DataFrame.from_dict(metrics_by_game, orient="index")
            metrics_df.index.name = "id"
            working = working.merge(metrics_df, how="left", left_on="id", right_index=True)

        if "spread" not in working.columns:
            working["spread"] = pd.NA

        if self.config.enforce_reference_schema:
            working = self._align_to_reference(working)

        return working

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _unwrap_payload(self, payload: Any, *, source: str) -> List[Dict[str, Any]]:
        """Unwrap REST API payload into list of records."""
        if payload is None:
            return []
        if isinstance(payload, list):
            # Convert REST objects to dicts if needed
            if source == "rest":
                converted = []
                for item in payload:
                    if isinstance(item, dict):
                        converted.append(item)
                    elif hasattr(item, "to_dict"):
                        to_dict_method = getattr(item, "to_dict")
                        # Check if to_dict is actually callable and not just a Mock
                        if callable(to_dict_method):
                            try:
                                result = to_dict_method()
                                # Only use if it returns a dict, not a Mock
                                if isinstance(result, dict):
                                    converted.append(result)
                                else:
                                    converted.append(self._object_to_dict(item))
                            except (AttributeError, TypeError):
                                converted.append(self._object_to_dict(item))
                        else:
                            converted.append(self._object_to_dict(item))
                    else:
                        # Fallback: convert object attributes to dict
                        converted.append(self._object_to_dict(item))
                return converted
            return payload
        if isinstance(payload, dict):
            if "data" in payload:
                if isinstance(payload["data"], list):
                    return payload["data"]
                # If "data" exists but is not a list, return empty (malformed)
                return []
        # Handle single object
        if source == "rest" and not isinstance(payload, dict):
            if hasattr(payload, "to_dict"):
                to_dict_method = getattr(payload, "to_dict")
                if callable(to_dict_method):
                    try:
                        result = to_dict_method()
                        if isinstance(result, dict):
                            return [result]
                    except (AttributeError, TypeError):
                        pass
            return [self._object_to_dict(payload)]
        return [payload] if isinstance(payload, dict) else []
    
    def _object_to_dict(self, obj: Any) -> Dict[str, Any]:
        """Convert object with attributes to dictionary."""
        result = {}
        # Try to get all attributes from the object
        # For Mock objects, we can use dir() to get all attributes
        for attr_name in dir(obj):
            # Skip private/magic methods
            if attr_name.startswith("_") and attr_name not in ["__dict__", "__class__"]:
                continue
            # Skip callable methods (except to_dict which we handle separately)
            if attr_name == "to_dict":
                continue
            try:
                attr_value = getattr(obj, attr_name)
                if not callable(attr_value):
                    result[attr_name] = attr_value
            except (AttributeError, TypeError):
                continue
        return result

    def _normalize_record(self, record: Dict[str, Any], *, source: str) -> Dict[str, Any]:
        """Normalize REST API record into standard format."""
        normalized = {
            "id": _extract(record, "id", "game_id", "gameId"),
            "start_date": _extract(record, "start_date", "startDate"),
            "season": _extract(record, "season"),
            "season_type": _extract(record, "season_type", "seasonType"),
            "week": _extract(record, "week"),
            "neutral_site": _coerce_bool(_extract(record, "neutral_site", "neutralSite")),
            "home_team": _extract(record, "home_team", "homeTeam"),
            "away_team": _extract(record, "away_team", "awayTeam"),
            "home_conference": _extract(record, "home_conference", "homeConference"),
            "away_conference": _extract(record, "away_conference", "awayConference"),
            "home_points": _extract(record, "home_points", "homePoints"),
            "away_points": _extract(record, "away_points", "awayPoints"),
            "home_elo": _extract(record, "home_elo", "homeElo", "homeStartElo"),
            "away_elo": _extract(record, "away_elo", "awayElo", "awayStartElo"),
            "home_talent": _extract(record, "home_talent", "homeTalent"),
            "away_talent": _extract(record, "away_talent", "awayTalent"),
            "spread": _extract(record, "spread"),
            "conference_game": _coerce_bool(_extract(record, "conference_game", "conferenceGame")),
        }

        media = record.get("media")
        if isinstance(media, list) and media:
            normalized["media"] = media

        normalized["game_key"] = normalized.get("game_key") or self._build_game_key(normalized)
        return normalized

    def _build_game_key(self, record: Dict[str, Any]) -> Optional[str]:
        season = record.get("season") or self.config.season
        week = record.get("week")
        home = record.get("home_team")
        away = record.get("away_team")
        if season is None or week is None or home is None or away is None:
            return None
        return f"{season}_{week}_{home}_{away}"

    def _add_game_key(self, df: pd.DataFrame) -> pd.DataFrame:
        if "game_key" not in df.columns or df["game_key"].isna().any():
            df = df.copy()
            df["game_key"] = df.apply(
                lambda row: row.get("game_key")
                or self._build_game_key(
                    {
                        "season": row.get("season"),
                        "week": row.get("week"),
                        "home_team": row.get("home_team"),
                        "away_team": row.get("away_team"),
                    }
                ),
                axis=1,
            )
        return df

    def _align_to_reference(self, df: pd.DataFrame) -> pd.DataFrame:
        aligned = df.copy()
        for column in self._reference_columns:
            if column not in aligned.columns:
                aligned[column] = pd.NA

        aligned = aligned[self._reference_columns]
        return aligned


def calculate_points_per_drive(drives_df: pd.DataFrame) -> float:
    """
    Calculate Points Per Drive (PPD) from drive data.
    
    Args:
        drives_df: DataFrame containing drive data with columns:
                  'start_offense_score', 'end_offense_score'
                  
    Returns:
        Points per drive value
    """
    if drives_df.empty:
        return 0.0
        
    # Calculate points gained by offense per drive
    points = drives_df['end_offense_score'] - drives_df['start_offense_score']
    return points.mean()


def calculate_explosive_drive_rate(drives_df: pd.DataFrame, yards_threshold: float = 10.0) -> float:
    """
    Calculate Explosive Drive Rate.
    Defined as percentage of drives averaging >= yards_threshold yards per play.
    
    Args:
        drives_df: DataFrame containing drive data
        yards_threshold: Yards per play threshold for explosive drive
        
    Returns:
        Explosive drive rate (0.0 to 1.0)
    """
    if drives_df.empty:
        return 0.0
        
    # Avoid division by zero
    valid_drives = drives_df[drives_df['plays'] > 0].copy()
    if valid_drives.empty:
        return 0.0
        
    valid_drives['ypp'] = valid_drives['yards'] / valid_drives['plays']
    explosive_count = (valid_drives['ypp'] >= yards_threshold).sum()
    
    return explosive_count / len(drives_df)
