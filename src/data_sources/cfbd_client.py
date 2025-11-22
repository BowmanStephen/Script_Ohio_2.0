"""
LEGACY CFBD Data Source - DEPRECATED

This module is deprecated and will be removed in a future version.
All new code should use UnifiedCFBDClient from src.cfbd_client.unified_client.

Migration:
    OLD: from src.data_sources.cfbd_client import CFBDRESTDataSource
    NEW: from src.cfbd_client.unified_client import UnifiedCFBDClient

This legacy module is kept for backward compatibility only.
"""

from __future__ import annotations

import os
import warnings
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

from src.cfbd_client.client import CFBDClient as _LegacyCFBDClient, RequestConfig
from .cfbd_cache_manager import CFBDCacheManager, CFBDCacheConfig

warnings.warn(
    "src.data_sources.cfbd_client is deprecated. "
    "Use UnifiedCFBDClient from src.cfbd_client.unified_client instead.",
    DeprecationWarning,
    stacklevel=2
)

TelemetryHook = Optional[Callable[[Dict[str, Any]], None]]


@dataclass(slots=True)
class CFBDClientConfig:
    """Configuration envelope for REST/Next CFBD access."""

    api_key: Optional[str] = None
    host: str = "production"
    telemetry_hook: TelemetryHook = None
    metrics_log_path: Optional[str] = None

    def resolve_api_key(self) -> str:
        key = self.api_key or os.getenv("CFBD_API_KEY")
        if not key:
            raise ValueError("CFBD_API_KEY is required for CFBD client operations.")
        return key


def build_cfbd_rest_client(
    config: Optional[CFBDClientConfig] = None,
) -> _LegacyCFBDClient:
    """Factory that wires the modern CFBD REST client with host switching and telemetry."""

    cfg = config or CFBDClientConfig()
    return _LegacyCFBDClient(
        api_key=cfg.resolve_api_key(),
        host=cfg.host,
        telemetry_hook=cfg.telemetry_hook,
        metrics_log_path=cfg.metrics_log_path,
    )


class CFBDRESTDataSource:
    """Wrapper providing ergonomic access patterns for Script Ohio agents and notebooks."""

    def __init__(
        self,
        client: Optional[_LegacyCFBDClient] = None,
        config: Optional[CFBDClientConfig] = None,
        cache_manager: Optional[CFBDCacheManager] = None,
    ) -> None:
        self._config = config or CFBDClientConfig()
        self._client = client or build_cfbd_rest_client(self._config)
        cache_disabled = os.getenv("CFBD_CACHE_DISABLED", "").lower() in {"1", "true", "yes"}
        if cache_disabled:
            self._cache: Optional[CFBDCacheManager] = None
        else:
            self._cache = cache_manager or CFBDCacheManager(CFBDCacheConfig())

    @property
    def host(self) -> str:
        return self._config.host

    def switch_host(self, host: str) -> None:
        """Switch between production and Next endpoints without rebuilding the object."""

        self._config.host = host
        self._client = build_cfbd_rest_client(self._config)

    def fetch_games(
        self,
        *,
        year: int,
        week: Optional[int] = None,
        season_type: str = "regular",
        team: Optional[str] = None,
    ) -> Any:
        params = {
            "year": year,
            "week": week,
            "seasonType": season_type,
            "team": team,
        }
        return self._cached_fetch(
            "games",
            params,
            lambda: self._client.get_games(
                year=year,
                week=week,
                season_type=season_type,
                team=team,
            ),
        )

    def fetch_ratings(self, *, year: int, week: Optional[int] = None) -> Any:
        params = {"year": year, "week": week}
        return self._cached_fetch(
            "ratings",
            params,
            lambda: self._client.get_ratings(year=year, week=week),
        )

    def fetch_lines(self, *, year: int, week: int) -> Any:
        params = {"year": year, "week": week}
        return self._cached_fetch(
            "lines",
            params,
            lambda: self._client.get_lines(year=year, week=week),
        )

    def fetch_recruiting(self, *, year: int) -> Any:
        params = {"year": year}
        return self._cached_fetch(
            "recruiting",
            params,
            lambda: self._client.get_recruiting(year=year),
        )

    def fetch_team_talent(self, *, year: int) -> Any:
        params = {"year": year}
        return self._cached_fetch(
            "team_talent",
            params,
            lambda: self._client.get_team_talent(year=year),
        )

    def fetch_weather(self, *, year: int, week: Optional[int] = None) -> Any:
        params = {"year": year, "week": week}
        return self._cached_fetch(
            "weather",
            params,
            lambda: self._client.get_game_weather(year=year, week=week),
        )

    def fetch_media(self, *, year: int, week: Optional[int] = None) -> Any:
        params = {"year": year, "week": week}
        return self._cached_fetch(
            "media",
            params,
            lambda: self._client.get_game_media(year=year, week=week),
        )

    def fetch_raw(
        self,
        method: str,
        endpoint: str,
        *,
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Pass-through helper for endpoints not yet modeled."""

        label = f"raw:{endpoint}"
        return self._cached_fetch(
            label,
            params,
            lambda: self._client._request(  # pylint: disable=protected-access
                RequestConfig(method=method, endpoint=endpoint, params=params)
            ),
        )

    def _cached_fetch(
        self,
        label: str,
        params: Optional[Dict[str, Any]],
        fetcher: Callable[[], Any],
    ) -> Any:
        if not self._cache:
            return fetcher()
        return self._cache.get_or_fetch(label, params, fetcher)

