"""
Utility helpers for building opponent-adjusted advanced metrics with CFBD data.

This module centralizes the logic for:
- Fetching team-level advanced season stats from the CFBD Stats API
- Calculating per-game opponent-adjusted metrics using real data
- Falling back to play-by-play derived stats when season aggregates are unavailable
"""

from __future__ import annotations

import logging
import time
from typing import Any, Callable, Dict, Optional, Tuple

import numpy as np
import pandas as pd

try:
    from cfbd import StatsApi
    from cfbd.rest import ApiException
except ImportError:  # pragma: no cover - handled gracefully when cfbd not installed
    StatsApi = None  # type: ignore
    ApiException = Exception  # type: ignore

LOGGER = logging.getLogger(__name__)

ADVANCED_METRIC_COLUMNS: Tuple[str, ...] = (
    'home_adjusted_epa', 'home_adjusted_epa_allowed',
    'away_adjusted_epa', 'away_adjusted_epa_allowed',
    'home_adjusted_rushing_epa', 'home_adjusted_rushing_epa_allowed',
    'away_adjusted_rushing_epa', 'away_adjusted_rushing_epa_allowed',
    'home_adjusted_passing_epa', 'home_adjusted_passing_epa_allowed',
    'away_adjusted_passing_epa', 'away_adjusted_passing_epa_allowed',
    'home_adjusted_success', 'home_adjusted_success_allowed',
    'away_adjusted_success', 'away_adjusted_success_allowed',
    'home_adjusted_standard_down_success', 'home_adjusted_standard_down_success_allowed',
    'away_adjusted_standard_down_success', 'away_adjusted_standard_down_success_allowed',
    'home_adjusted_passing_down_success', 'home_adjusted_passing_down_success_allowed',
    'away_adjusted_passing_down_success', 'away_adjusted_passing_down_success_allowed',
    'home_adjusted_line_yards', 'home_adjusted_line_yards_allowed',
    'away_adjusted_line_yards', 'away_adjusted_line_yards_allowed',
    'home_adjusted_second_level_yards', 'home_adjusted_second_level_yards_allowed',
    'away_adjusted_second_level_yards', 'away_adjusted_second_level_yards_allowed',
    'home_adjusted_open_field_yards', 'home_adjusted_open_field_yards_allowed',
    'away_adjusted_open_field_yards', 'away_adjusted_open_field_yards_allowed',
    'home_adjusted_explosiveness', 'home_adjusted_explosiveness_allowed',
    'away_adjusted_explosiveness', 'away_adjusted_explosiveness_allowed',
    'home_adjusted_rush_explosiveness', 'home_adjusted_rush_explosiveness_allowed',
    'away_adjusted_rush_explosiveness', 'away_adjusted_rush_explosiveness_allowed',
    'home_adjusted_pass_explosiveness', 'home_adjusted_pass_explosiveness_allowed',
    'away_adjusted_pass_explosiveness', 'away_adjusted_pass_explosiveness_allowed',
    'home_total_havoc_offense', 'home_front_seven_havoc_offense', 'home_db_havoc_offense',
    'away_total_havoc_offense', 'away_front_seven_havoc_offense', 'away_db_havoc_offense',
    'home_total_havoc_defense', 'home_front_seven_havoc_defense', 'home_db_havoc_defense',
    'away_total_havoc_defense', 'away_front_seven_havoc_defense', 'away_db_havoc_defense',
    'home_points_per_opportunity_offense', 'away_points_per_opportunity_offense',
    'home_points_per_opportunity_defense', 'away_points_per_opportunity_defense',
    'home_avg_start_offense', 'home_avg_start_defense',
    'away_avg_start_offense', 'away_avg_start_defense',
)


def _camel_key(key: str) -> str:
    parts = key.split('_')
    return parts[0] + ''.join(word.capitalize() for word in parts[1:])


def _get_value(container: Any, key: str) -> Any:
    if container is None:
        return None
    if isinstance(container, dict):
        if key in container:
            return container[key]
        camel = _camel_key(key)
        return container.get(camel)
    return getattr(container, key, None)


def _nested_get(container: Any, *keys: str) -> Any:
    value = container
    for key in keys:
        value = _get_value(value, key)
        if value is None:
            return None
    return value


def _to_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _adjust(primary: Optional[float], opponent: Optional[float]) -> Optional[float]:
    if primary is None or opponent is None:
        return None
    return primary - opponent


class AdvancedMetricsBuilder:
    """
    Build opponent-adjusted advanced metrics using CFBD Stats + play-by-play data.
    """

    def __init__(
        self,
        api_client: Any,
        season: int,
        rate_limit_callback: Optional[Callable[[], None]] = None,
    ) -> None:
        self.api_client = api_client
        self.season = season
        self._stats_api = StatsApi(api_client) if StatsApi else None
        self._rate_limit = rate_limit_callback or (lambda: None)
        self._team_stats_cache: Dict[str, Dict[str, Any]] = {}
        self._team_lookup: Dict[str, Dict[str, Any]] = {}
        self._missing_teams: set[str] = set()

    # ------------------------------------------------------------------ #
    # Public helpers
    # ------------------------------------------------------------------ #
    def build_metrics_for_games(
        self,
        games_df: pd.DataFrame,
        plays_df: Optional[pd.DataFrame] = None,
    ) -> Dict[Any, Dict[str, Optional[float]]]:
        metrics_by_game: Dict[Any, Dict[str, Optional[float]]] = {}
        team_stats_available = self._load_team_stats()

        if team_stats_available:
            for row in games_df.itertuples():
                game_id, home_team, away_team = self._resolve_game_fields(row)
                if not home_team or not away_team:
                    continue
                stats_metrics = self._compose_from_team_stats(home_team, away_team)
                if stats_metrics:
                    metrics_by_game[game_id] = stats_metrics

        if plays_df is not None and not plays_df.empty:
            play_metrics = self._calculate_from_play_data(games_df, plays_df)
            for game_id, values in play_metrics.items():
                metrics_by_game.setdefault(game_id, {}).update(values)

        return metrics_by_game

    # ------------------------------------------------------------------ #
    # Stats API helpers
    # ------------------------------------------------------------------ #
    def _load_team_stats(self) -> bool:
        if self._team_stats_cache:
            return True

        stats = self._fetch_advanced_stats_for_season(self.season)
        if not stats and self.season > 2000:
            LOGGER.warning(
                "No advanced stats for %s, falling back to %s",
                self.season,
                self.season - 1,
            )
            stats = self._fetch_advanced_stats_for_season(self.season - 1)

        if not stats:
            LOGGER.warning("Advanced season stats unavailable; relying on play-by-play only")
            return False

        self._team_stats_cache = stats
        self._team_lookup = {name.lower(): metrics for name, metrics in stats.items()}
        return True

    def _fetch_advanced_stats_for_season(self, season: int) -> Dict[str, Dict[str, Any]]:
        if not self._stats_api:
            LOGGER.warning("StatsApi unavailable; cannot fetch advanced stats")
            return {}

        try:
            records = self._stats_api.get_advanced_season_stats(year=season)
            self._rate_limit()
        except ApiException as exc:  # pragma: no cover - network failure
            LOGGER.warning("Stats API error (%s): %s", exc.status, exc.reason)
            if exc.status == 429:
                LOGGER.warning("Rate limit exceeded fetching advanced stats; sleeping briefly")
                time.sleep(1.0)
            return {}
        except Exception as exc:  # pragma: no cover - unexpected
            LOGGER.warning("Stats API error: %s", exc)
            return {}

        stats_by_team: Dict[str, Dict[str, Any]] = {}
        for record in records or []:
            data = record.to_dict() if hasattr(record, "to_dict") else record
            team_name = data.get('team') or data.get('school')
            if not team_name:
                continue
            stats_by_team[team_name] = self._extract_team_metrics(data)

        LOGGER.info("Fetched advanced stats for %d teams (%s)", len(stats_by_team), season)
        return stats_by_team

    def _extract_team_metrics(self, data: Dict[str, Any]) -> Dict[str, Dict[str, Optional[float]]]:
        offense = self._extract_side_metrics(data.get('offense') or {})
        defense = self._extract_side_metrics(data.get('defense') or {}, defensive=True)
        return {'offense': offense, 'defense': defense}

    def _extract_side_metrics(
        self,
        side_data: Dict[str, Any],
        defensive: bool = False,
    ) -> Dict[str, Optional[float]]:
        metrics = {
            'ppa': _to_float(_get_value(side_data, 'ppa')),
            'success_rate': _to_float(_get_value(side_data, 'success_rate')),
            'explosiveness': _to_float(_get_value(side_data, 'explosiveness')),
            'rush_ppa': _to_float(_nested_get(side_data, 'rushing_plays', 'ppa')),
            'rush_success': _to_float(_nested_get(side_data, 'rushing_plays', 'success_rate')),
            'rush_explosiveness': _to_float(_nested_get(side_data, 'rushing_plays', 'explosiveness')),
            'pass_ppa': _to_float(_nested_get(side_data, 'passing_plays', 'ppa')),
            'pass_success': _to_float(_nested_get(side_data, 'passing_plays', 'success_rate')),
            'pass_explosiveness': _to_float(_nested_get(side_data, 'passing_plays', 'explosiveness')),
            'standard_success': _to_float(_nested_get(side_data, 'standard_downs', 'success_rate')),
            'passing_down_success': _to_float(_nested_get(side_data, 'passing_downs', 'success_rate')),
            'line_yards': _to_float(_get_value(side_data, 'line_yards')),
            'second_level_yards': _to_float(_get_value(side_data, 'second_level_yards')),
            'open_field_yards': _to_float(_get_value(side_data, 'open_field_yards')),
            'points_per_opportunity': _to_float(_get_value(side_data, 'points_per_opportunity')),
            'avg_start': _to_float(_nested_get(side_data, 'field_position', 'average_start')),
        }

        if defensive:
            havoc_front = _to_float(_nested_get(side_data, 'havoc', 'front_seven'))
            havoc_db = _to_float(_nested_get(side_data, 'havoc', 'db'))
            metrics['havoc_front'] = havoc_front
            metrics['havoc_db'] = havoc_db
            metrics['havoc_total'] = (
                (havoc_front or 0.0) + (havoc_db or 0.0)
                if havoc_front is not None or havoc_db is not None
                else None
            )

        return metrics

    # ------------------------------------------------------------------ #
    # Play-by-play fallback helpers
    # ------------------------------------------------------------------ #
    def _calculate_from_play_data(
        self,
        games_df: pd.DataFrame,
        plays_df: pd.DataFrame,
    ) -> Dict[Any, Dict[str, Optional[float]]]:
        if plays_df.empty:
            return {}

        plays = plays_df.copy()
        if 'game_id' not in plays.columns or 'offense' not in plays.columns:
            LOGGER.warning("Play-by-play data missing offense identifiers; skipping custom calculations")
            return {}

        plays['game_id'] = pd.to_numeric(plays['game_id'], errors='coerce')
        plays = plays.dropna(subset=['game_id'])

        numeric_columns = ['ppa', 'success', 'yards_gained', 'line_yards', 'down', 'distance']
        for col in numeric_columns:
            if col in plays.columns:
                plays[col] = pd.to_numeric(plays[col], errors='coerce')

        if 'success' in plays.columns:
            plays['success'] = pd.to_numeric(plays['success'], errors='coerce')
        else:
            plays['success'] = pd.Series(np.nan, index=plays.index, dtype=float)
        plays['rush'] = plays.get('rush', False).astype(float) if 'rush' in plays.columns else 0.0
        plays['pass'] = plays.get('pass', False).astype(float) if 'pass' in plays.columns else 0.0

        plays['is_standard_down'] = self._identify_standard_downs(plays)
        plays['is_passing_down'] = plays['is_standard_down'] == 0

        offense_game_stats = self._group_offense_by_game(plays)
        offense_season_stats = self._group_offense_by_game(plays, by_game=False)
        defense_season_stats = self._group_defense_by_game(plays, by_game=False)

        metrics_by_game: Dict[Any, Dict[str, Optional[float]]] = {}
        for row in games_df.itertuples():
            game_id, home_team, away_team = self._resolve_game_fields(row)
            if not home_team or not away_team:
                continue

            game_offense_stats = offense_game_stats.get(game_id, {})
            home_off_game = game_offense_stats.get(self._normalize_team(home_team))
            away_off_game = game_offense_stats.get(self._normalize_team(away_team))

            if not home_off_game or not away_off_game:
                continue

            home_def_season = defense_season_stats.get(self._normalize_team(home_team))
            away_def_season = defense_season_stats.get(self._normalize_team(away_team))
            home_off_season = offense_season_stats.get(self._normalize_team(home_team))
            away_off_season = offense_season_stats.get(self._normalize_team(away_team))

            metrics: Dict[str, Optional[float]] = {}
            metrics.update(self._compose_metric_side(
                prefix='home',
                offense_stats=home_off_game,
                defense_season_stats=away_def_season,
                opponent_offense_stats=away_off_game,
                defense_stats=home_off_game, # Using home offense game stats as proxy for defense game stats if needed, or fix logic
            ))
            metrics.update(self._compose_metric_side(
                prefix='away',
                offense_stats=away_off_game,
                defense_season_stats=home_def_season,
                opponent_offense_stats=home_off_game,
                defense_stats=away_off_game,
            ))
            metrics_by_game[game_id] = metrics

        LOGGER.info("Calculated play-by-play advanced metrics for %d games", len(metrics_by_game))
        return metrics_by_game

    def _identify_standard_downs(self, plays: pd.DataFrame) -> pd.Series:
        downs = plays['down'].fillna(0)
        distance = plays['distance'].fillna(0)
        is_standard = (
            ((downs <= 2) & (distance <= 7)) |
            ((downs == 3) & (distance <= 4)) |
            ((downs == 4) & (distance <= 4))
        )
        return is_standard.astype(int)

    def _group_offense_by_game(self, plays: pd.DataFrame, by_game: bool = True) -> Dict[Any, Dict[str, Dict[str, Optional[float]]]]:
        group_fields = ['game_id', 'offense'] if by_game else ['offense']
        grouped = plays.groupby(group_fields)
        results: Dict[Any, Dict[str, Dict[str, Optional[float]]]] = {}

        for keys, group in grouped:
            if by_game:
                game_id, team = keys
                storage = results.setdefault(game_id, {})
            else:
                team = keys
                storage = results

            team_key = self._normalize_team(team)
            storage[team_key] = self._summarize_offense_group(group)

        return results

    def _group_defense_by_game(self, plays: pd.DataFrame, by_game: bool = True) -> Dict[Any, Dict[str, Dict[str, Optional[float]]]]:
        group_fields = ['game_id', 'defense'] if by_game else ['defense']
        grouped = plays.groupby(group_fields)
        results: Dict[Any, Dict[str, Dict[str, Optional[float]]]] = {}

        for keys, group in grouped:
            if by_game:
                game_id, team = keys
                storage = results.setdefault(game_id, {})
            else:
                team = keys
                storage = results

            team_key = self._normalize_team(team)
            storage[team_key] = self._summarize_defense_group(group)

        return results

    def _summarize_offense_group(self, group: pd.DataFrame) -> Dict[str, Optional[float]]:
        rush_group = group[group.get('rush', 0) == 1]
        pass_group = group[group.get('pass', 0) == 1]
        standard_group = group[group['is_standard_down'] == 1]
        passing_group = group[group['is_standard_down'] == 0]

        summary = {
            'ppa': group['ppa'].mean(),
            'success_rate': group['success'].mean(),
            'explosiveness': group['ppa'].std(ddof=0),
            'rush_ppa': rush_group['ppa'].mean(),
            'rush_success': rush_group['success'].mean(),
            'rush_explosiveness': rush_group['ppa'].std(ddof=0),
            'pass_ppa': pass_group['ppa'].mean(),
            'pass_success': pass_group['success'].mean(),
            'pass_explosiveness': pass_group['ppa'].std(ddof=0),
            'standard_success': standard_group['success'].mean(),
            'passing_down_success': passing_group['success'].mean(),
            'line_yards': self._estimate_line_yards(rush_group),
            'second_level_yards': self._estimate_second_level_yards(rush_group),
            'open_field_yards': self._estimate_open_field_yards(rush_group),
            'points_per_opportunity': self._estimate_points_per_opportunity(group),
            'avg_start': self._estimate_average_start(group),
        }

        return {k: _to_float(v) for k, v in summary.items()}

    def _summarize_defense_group(self, group: pd.DataFrame) -> Dict[str, Optional[float]]:
        rush_group = group[group.get('rush', 0) == 1]
        pass_group = group[group.get('pass', 0) == 1]
        summary = {
            'ppa': group['ppa'].mean(),
            'success_rate': group['success'].mean(),
            'explosiveness': group['ppa'].std(ddof=0),
            'rush_ppa': rush_group['ppa'].mean(),
            'rush_success': rush_group['success'].mean(),
            'rush_explosiveness': rush_group['ppa'].std(ddof=0),
            'pass_ppa': pass_group['ppa'].mean(),
            'pass_success': pass_group['success'].mean(),
            'pass_explosiveness': pass_group['ppa'].std(ddof=0),
            'standard_success': group[group['is_standard_down'] == 1]['success'].mean(),
            'passing_down_success': group[group['is_standard_down'] == 0]['success'].mean(),
            'line_yards': self._estimate_line_yards(rush_group),
            'second_level_yards': self._estimate_second_level_yards(rush_group),
            'open_field_yards': self._estimate_open_field_yards(rush_group),
            'points_per_opportunity': self._estimate_points_per_opportunity(group),
            'avg_start': self._estimate_average_start(group),
            'havoc_front': self._estimate_front_seven_havoc(group),
            'havoc_db': self._estimate_db_havoc(group),
        }
        summary['havoc_total'] = (
            (summary['havoc_front'] or 0.0) + (summary['havoc_db'] or 0.0)
            if summary['havoc_front'] is not None or summary['havoc_db'] is not None
            else None
        )
        return {k: _to_float(v) for k, v in summary.items()}

    # ------------------------------------------------------------------ #
    # Metric composition helpers
    # ------------------------------------------------------------------ #
    def _compose_from_team_stats(self, home_team: str, away_team: str) -> Optional[Dict[str, Optional[float]]]:
        home_stats = self._find_team_stats(home_team)
        away_stats = self._find_team_stats(away_team)

        if not home_stats or not away_stats:
            return None

        metrics: Dict[str, Optional[float]] = {}
        metrics.update(self._compose_metric_side('home', home_stats['offense'], away_stats['defense'], away_stats['offense'], home_stats['defense']))
        metrics.update(self._compose_metric_side('away', away_stats['offense'], home_stats['defense'], home_stats['offense'], away_stats['defense']))
        return metrics

    def _compose_metric_side(
        self,
        prefix: str,
        offense_stats: Dict[str, Optional[float]],
        defense_season_stats: Optional[Dict[str, Optional[float]]],
        opponent_offense_stats: Optional[Dict[str, Optional[float]]],
        defense_stats: Dict[str, Optional[float]],
    ) -> Dict[str, Optional[float]]:
        defense_season_stats = defense_season_stats or {}
        opponent_offense_stats = opponent_offense_stats or {}
        metrics = {
            f'{prefix}_adjusted_epa': _adjust(offense_stats.get('ppa'), defense_season_stats.get('ppa')),
            f'{prefix}_adjusted_epa_allowed': _adjust(defense_stats.get('ppa'), opponent_offense_stats.get('ppa')),
            f'{prefix}_adjusted_rushing_epa': _adjust(offense_stats.get('rush_ppa'), defense_season_stats.get('rush_ppa')),
            f'{prefix}_adjusted_rushing_epa_allowed': _adjust(defense_stats.get('rush_ppa'), opponent_offense_stats.get('rush_ppa')),
            f'{prefix}_adjusted_passing_epa': _adjust(offense_stats.get('pass_ppa'), defense_season_stats.get('pass_ppa')),
            f'{prefix}_adjusted_passing_epa_allowed': _adjust(defense_stats.get('pass_ppa'), opponent_offense_stats.get('pass_ppa')),
            f'{prefix}_adjusted_success': _adjust(offense_stats.get('success_rate'), defense_season_stats.get('success_rate')),
            f'{prefix}_adjusted_success_allowed': _adjust(defense_stats.get('success_rate'), opponent_offense_stats.get('success_rate')),
            f'{prefix}_adjusted_standard_down_success': _adjust(offense_stats.get('standard_success'), defense_season_stats.get('standard_success')),
            f'{prefix}_adjusted_standard_down_success_allowed': _adjust(defense_stats.get('standard_success'), opponent_offense_stats.get('standard_success')),
            f'{prefix}_adjusted_passing_down_success': _adjust(offense_stats.get('passing_down_success'), defense_season_stats.get('passing_down_success')),
            f'{prefix}_adjusted_passing_down_success_allowed': _adjust(defense_stats.get('passing_down_success'), opponent_offense_stats.get('passing_down_success')),
            f'{prefix}_adjusted_line_yards': _adjust(offense_stats.get('line_yards'), defense_season_stats.get('line_yards')),
            f'{prefix}_adjusted_line_yards_allowed': _adjust(defense_stats.get('line_yards'), opponent_offense_stats.get('line_yards')),
            f'{prefix}_adjusted_second_level_yards': _adjust(offense_stats.get('second_level_yards'), defense_season_stats.get('second_level_yards')),
            f'{prefix}_adjusted_second_level_yards_allowed': _adjust(defense_stats.get('second_level_yards'), opponent_offense_stats.get('second_level_yards')),
            f'{prefix}_adjusted_open_field_yards': _adjust(offense_stats.get('open_field_yards'), defense_season_stats.get('open_field_yards')),
            f'{prefix}_adjusted_open_field_yards_allowed': _adjust(defense_stats.get('open_field_yards'), opponent_offense_stats.get('open_field_yards')),
            f'{prefix}_adjusted_explosiveness': _adjust(offense_stats.get('explosiveness'), defense_season_stats.get('explosiveness')),
            f'{prefix}_adjusted_explosiveness_allowed': _adjust(defense_stats.get('explosiveness'), opponent_offense_stats.get('explosiveness')),
            f'{prefix}_adjusted_rush_explosiveness': _adjust(offense_stats.get('rush_explosiveness'), defense_season_stats.get('rush_explosiveness')),
            f'{prefix}_adjusted_rush_explosiveness_allowed': _adjust(defense_stats.get('rush_explosiveness'), opponent_offense_stats.get('rush_explosiveness')),
            f'{prefix}_adjusted_pass_explosiveness': _adjust(offense_stats.get('pass_explosiveness'), defense_season_stats.get('pass_explosiveness')),
            f'{prefix}_adjusted_pass_explosiveness_allowed': _adjust(defense_stats.get('pass_explosiveness'), opponent_offense_stats.get('pass_explosiveness')),
            f'{prefix}_total_havoc_offense': defense_season_stats.get('havoc_total'),
            f'{prefix}_front_seven_havoc_offense': defense_season_stats.get('havoc_front'),
            f'{prefix}_db_havoc_offense': defense_season_stats.get('havoc_db'),
            f'{prefix}_total_havoc_defense': defense_stats.get('havoc_total'),
            f'{prefix}_front_seven_havoc_defense': defense_stats.get('havoc_front'),
            f'{prefix}_db_havoc_defense': defense_stats.get('havoc_db'),
            f'{prefix}_points_per_opportunity_offense': offense_stats.get('points_per_opportunity'),
            f'{prefix}_points_per_opportunity_defense': defense_stats.get('points_per_opportunity'),
            f'{prefix}_avg_start_offense': offense_stats.get('avg_start'),
            f'{prefix}_avg_start_defense': defense_stats.get('avg_start'),
        }
        return metrics

    # ------------------------------------------------------------------ #
    # Utility helpers
    # ------------------------------------------------------------------ #
    def _resolve_game_fields(self, row: Any) -> Tuple[Any, Optional[str], Optional[str]]:
        game_id = getattr(row, 'id', None)
        home_team = getattr(row, 'home_team', None)
        away_team = getattr(row, 'away_team', None)
        if pd.isna(game_id) or game_id in (None, ''):
            season = getattr(row, 'season', self.season)
            week = getattr(row, 'week', 0)
            game_id = f"{season}_{week}_{home_team}_{away_team}"
        return game_id, home_team, away_team

    def _find_team_stats(self, team_name: Optional[str]) -> Optional[Dict[str, Dict[str, Optional[float]]]]:
        if not team_name:
            return None
        normalized = self._normalize_team(team_name)
        stats = self._team_lookup.get(normalized)
        if stats:
            return stats
        if normalized not in self._missing_teams:
            LOGGER.warning("Advanced stats not found for team '%s'", team_name)
            self._missing_teams.add(normalized)
        return None

    def _normalize_team(self, team_name: Any) -> str:
        return str(team_name).strip().lower()

    def _estimate_line_yards(self, rush_group: pd.DataFrame) -> Optional[float]:
        if rush_group.empty:
            return None
        yards = rush_group['yards_gained'].clip(lower=0)
        return (yards.clip(upper=10) * 0.5).mean()

    def _estimate_second_level_yards(self, rush_group: pd.DataFrame) -> Optional[float]:
        if rush_group.empty:
            return None
        yards = rush_group['yards_gained'].clip(lower=0) - 5
        yards = yards.clip(lower=0, upper=5)
        return yards.mean()

    def _estimate_open_field_yards(self, rush_group: pd.DataFrame) -> Optional[float]:
        if rush_group.empty:
            return None
        yards = rush_group['yards_gained'].clip(lower=0) - 10
        yards = yards.clip(lower=0)
        return yards.mean()

    def _estimate_points_per_opportunity(self, group: pd.DataFrame) -> Optional[float]:
        if 'scoring' not in group.columns:
            return None
        scoring_plays = group[group['scoring'] == True]
        if scoring_plays.empty:
            return None
        points = scoring_plays.get('points', pd.Series(dtype=float)).fillna(0).sum()
        opportunities = len(scoring_plays)
        if opportunities == 0:
            return None
        return points / opportunities if points else None

    def _estimate_average_start(self, group: pd.DataFrame) -> Optional[float]:
        if 'yard_line' not in group.columns:
            return None
        yard_line = pd.to_numeric(group['yard_line'], errors='coerce').dropna()
        if yard_line.empty:
            return None
        return yard_line.mean()

    def _estimate_front_seven_havoc(self, group: pd.DataFrame) -> Optional[float]:
        indicators = (
            (group.get('rush', 0) == 1) & (group.get('yards_gained', 0) <= 0)
        ) | group.get('sack', False)
        return indicators.mean() if len(group) > 0 else None

    def _estimate_db_havoc(self, group: pd.DataFrame) -> Optional[float]:
        if 'play_type' not in group.columns:
            return None
        play_types = group['play_type'].astype(str).str.lower()
        db_havoc = play_types.str.contains('interception|pass breakup|fumble').astype(int)
        return db_havoc.mean() if len(group) > 0 else None


__all__ = [
    'ADVANCED_METRIC_COLUMNS',
    'AdvancedMetricsBuilder',
]
