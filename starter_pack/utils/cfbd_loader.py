"""
CFBD Data Loader Utilities - PARTIALLY DEPRECATED

This module provides CFBDSession and RateLimiter utilities which are still useful.
However, for direct CFBD API access, prefer UnifiedCFBDClient.

For new code:
    - Use UnifiedCFBDClient from src.cfbd_client.unified_client for API calls
    - This module's CFBDSession can still be used for notebook/demo contexts
    - RateLimiter is still useful for custom rate limiting needs

Migration:
    OLD: CFBDLoader (if it exists)
    NEW: UnifiedCFBDClient from src.cfbd_client.unified_client
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence

import pandas as pd

from starter_pack.config.data_config import get_starter_pack_config

DEFAULT_HOST = "https://api.collegefootballdata.com"
RATE_LIMIT_SECONDS = 0.17  # 6 req/sec == 0.166..., round up for safety


class CFBDLoaderError(RuntimeError):
    """Raised when live data cannot be fetched."""


def _ensure_cfbd_available():
    try:
        import cfbd  # noqa: F401
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise CFBDLoaderError(
            "cfbd package missing. Install it via `pip install cfbd` or "
            "`pip install -r requirements-optional.txt`."
        ) from exc


class RateLimiter:
    """Simple time-based rate limiter for CFBD API calls."""

    def __init__(self, delay_seconds: float = RATE_LIMIT_SECONDS) -> None:
        self.delay_seconds = delay_seconds
        self._last_call = 0.0

    def wait(self) -> None:
        now = time.perf_counter()
        delta = now - self._last_call
        if delta < self.delay_seconds:
            time.sleep(self.delay_seconds - delta)
        self._last_call = time.perf_counter()


@dataclass
class CFBDSession:
    """Context manager that wires up cfbd.ApiClient + typed APIs."""

    api_key: str
    host: str = DEFAULT_HOST

    def __post_init__(self) -> None:
        _ensure_cfbd_available()
        import cfbd

        self._cfbd = cfbd

    def __enter__(self):
        # Clean API key - remove "Bearer " prefix if present
        clean_key = self.api_key.replace("Bearer ", "").strip() if self.api_key else self.api_key
        
        configuration = self._cfbd.Configuration()
        # Use access_token for CFBD v5.13.2+ (API v2 compatible)
        # This is the correct pattern for the updated Python package
        configuration.access_token = clean_key
        configuration.host = self.host
        self.api_client = self._cfbd.ApiClient(configuration)
        self.games_api = self._cfbd.GamesApi(self.api_client)
        self.stats_api = self._cfbd.StatsApi(self.api_client)
        self.drives_api = self._cfbd.DrivesApi(self.api_client)
        self.plays_api = self._cfbd.PlaysApi(self.api_client)
        self.teams_api = self._cfbd.TeamsApi(self.api_client)
        self.ratings_api = self._cfbd.RatingsApi(self.api_client)
        self.betting_api = self._cfbd.BettingApi(self.api_client)
        return self

    def __exit__(self, exc_type, exc, tb):
        # ApiClient may not have close() in all versions - handle gracefully
        if hasattr(self.api_client, 'close'):
            self.api_client.close()


def live_cfbd_session(*, api_key: Optional[str] = None, host: str = DEFAULT_HOST) -> CFBDSession:
    """
    Convenience helper for QA/diagnostics scripts that need a managed CFBD session.

    Returns a CFBDSession context manager configured with the hardened auth +
    host settings so callers only need to write:

        with live_cfbd_session(host="https://apinext.collegefootballdata.com") as session:
            games = session.games_api.get_games(year=2025)
    """

    key = api_key or os.environ.get("CFBD_API_KEY") or os.environ.get("CFBD_API_TOKEN")
    if not key:
        raise CFBDLoaderError(
            "CFBD API key missing. Set CFBD_API_KEY or pass `api_key` to live_cfbd_session."
        )
    return CFBDSession(api_key=key, host=host)


def _records_to_frame(records: Sequence[object]) -> pd.DataFrame:
    rows = []
    for record in records:
        if hasattr(record, "to_dict"):
            rows.append(record.to_dict())  # type: ignore
        elif isinstance(record, dict):
            rows.append(record)
        else:
            rows.append({"value": record})
    return pd.DataFrame(rows)


@dataclass
class CFBDLoader:
    """High-level helper for notebooks to pull fresh CFBD data on demand."""

    cache_dir: Optional[Path] = None
    host: str = DEFAULT_HOST
    api_key: Optional[str] = None

    def __post_init__(self) -> None:
        config = get_starter_pack_config()
        self.cache_dir = Path(self.cache_dir or (config.data_dir / "live_cache"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.rate_limiter = RateLimiter()

    # ------------------------------------------------------------------ #
    # Public fetch helpers
    # ------------------------------------------------------------------ #
    def fetch_games(
        self,
        *,
        season: int,
        season_type: str = "regular",
        week: Optional[int] = None,
        use_cache: bool = True,
        persist_cache: bool = True,
    ) -> pd.DataFrame:
        cache_path = self._cache_path("games", season, season_type, week)
        if use_cache and cache_path.exists():
            return pd.read_csv(cache_path, low_memory=False)

        frame = self._fetch_with_session(
            dataset="games",
            request_kwargs={"year": season, "season_type": season_type, "week": week},
        )
        if persist_cache:
            frame.to_csv(cache_path, index=False)
        return frame

    def fetch_team_season_stats(
        self,
        *,
        season: int,
        dataset: str = "season_stats",
        method: str = "team",
        use_cache: bool = True,
        persist_cache: bool = True,
    ) -> pd.DataFrame:
        dataset_name = "advanced_season_stats" if method == "advanced" else dataset
        cache_path = self._cache_path(dataset_name, season, "full")
        if use_cache and cache_path.exists():
            return pd.read_csv(cache_path, low_memory=False)

        if method == "advanced":
            frame = self._fetch_with_session(
                dataset="advanced_season_stats",
                request_kwargs={"year": season},
            )
        else:
            frame = self._fetch_with_session(
                dataset="season_stats",
                request_kwargs={"year": season},
            )

        if persist_cache:
            frame.to_csv(cache_path, index=False)
        return frame

    def fetch_drives(
        self,
        *,
        season: int,
        use_cache: bool = True,
        persist_cache: bool = True,
    ) -> pd.DataFrame:
        cache_path = self._cache_path("drives", season, "full")
        if use_cache and cache_path.exists():
            return pd.read_csv(cache_path, low_memory=False)

        frame = self._fetch_with_session(
            dataset="drives",
            request_kwargs={"year": season},
        )
        if persist_cache:
            frame.to_csv(cache_path, index=False)
        return frame

    # ------------------------------------------------------------------ #
    # Internal plumbing
    # ------------------------------------------------------------------ #
    def _fetch_with_session(self, *, dataset: str, request_kwargs: dict) -> pd.DataFrame:
        api_key = self._resolve_api_key()
        with CFBDSession(api_key=api_key, host=self.host) as session:
            self.rate_limiter.wait()
            if dataset == "games":
                response = session.games_api.get_games(**{k: v for k, v in request_kwargs.items() if v is not None})
            elif dataset == "season_stats":
                response = session.stats_api.get_team_season_stats(**request_kwargs)
            elif dataset == "advanced_season_stats":
                response = session.stats_api.get_advanced_season_stats(**request_kwargs)
            elif dataset == "drives":
                response = session.drives_api.get_drives(**request_kwargs)
            else:
                raise ValueError(f"Unsupported dataset '{dataset}'")

        frame = _records_to_frame(response)
        if frame.empty:
            raise CFBDLoaderError(f"No records returned for {dataset} with params {request_kwargs}")
        return frame

    def _cache_path(self, dataset: str, season: int, season_type: str, week: Optional[int] = None) -> Path:
        parts = [dataset, str(season), season_type]
        if week is not None:
            parts.append(f"week{week:02d}")
        filename = "_".join(parts) + ".csv"
        return self.cache_dir / filename

    def _resolve_api_key(self) -> str:
        key = self.api_key or os.environ.get("CFBD_API_KEY") or os.environ.get("CFBD_API_TOKEN")
        if not key:
            raise CFBDLoaderError("CFBD API key missing. Set CFBD_API_KEY or pass `api_key` to CFBDLoader.")
        return key


__all__ = [
    "CFBDLoader",
    "CFBDLoaderError",
    "CFBDSession",
    "live_cfbd_session",
    "RateLimiter",
    "_records_to_frame",
]

