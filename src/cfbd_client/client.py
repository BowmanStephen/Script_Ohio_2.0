"""
LEGACY CFBD API Client - DEPRECATED

This module is deprecated and will be removed in a future version.
All new code should use UnifiedCFBDClient from src.cfbd_client.unified_client.

Migration:
    OLD: from src.cfbd_client.client import CFBDClient
    NEW: from src.cfbd_client.unified_client import UnifiedCFBDClient

This legacy client is kept for backward compatibility only.
"""
from __future__ import annotations

import warnings

warnings.warn(
    "src.cfbd_client.client.CFBDClient is deprecated. "
    "Use UnifiedCFBDClient from src.cfbd_client.unified_client instead.",
    DeprecationWarning,
    stacklevel=2
)

import json
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Final, Optional

import requests


HOST_MAP: Final[Dict[str, str]] = {
    "production": "https://api.collegefootballdata.com",
    "next": "https://apinext.collegefootballdata.com",
}

_LOGGER = logging.getLogger("cfbd_client")
if not _LOGGER.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    _LOGGER.addHandler(handler)
_LOGGER.setLevel(logging.INFO)


class CFBDClientError(RuntimeError):
    """Base exception for CFBD client errors."""


@dataclass(slots=True)
class RequestConfig:
    """Configuration for outgoing CFBD requests."""

    method: str
    endpoint: str
    params: Optional[Dict[str, Any]] = None


@dataclass(slots=True)
class ClientMetrics:
    """Aggregated telemetry for the CFBD client."""

    total_requests: int = 0
    successful_requests: int = 0
    retries: int = 0
    rate_limit_hits: int = 0
    server_errors: int = 0
    client_errors: int = 0
    auth_errors: int = 0
    network_errors: int = 0
    total_latency_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        avg_latency = (
            self.total_latency_ms / self.successful_requests
            if self.successful_requests
            else 0.0
        )
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "retries": self.retries,
            "rate_limit_hits": self.rate_limit_hits,
            "server_errors": self.server_errors,
            "client_errors": self.client_errors,
            "auth_errors": self.auth_errors,
            "network_errors": self.network_errors,
            "average_latency_ms": round(avg_latency, 2),
        }


class CFBDClient:
    """Synchronous CFBD API client with enforced rate limiting and retries."""

    _throttle_interval: Final[float] = 0.17
    _max_attempts: Final[int] = 3
    _retry_delays: Final[tuple[float, ...]] = (0.0, 1.0, 2.0, 4.0)

    def __init__(
        self,
        api_key: Optional[str] = None,
        host: Optional[str] = None,
        session: Optional[requests.Session] = None,
        telemetry_hook: Optional[Callable[[Dict[str, Any]], None]] = None,
        metrics_log_path: Optional[str] = None,
    ) -> None:
        self._api_key = api_key or os.getenv("CFBD_API_KEY")
        if not self._api_key:
            raise ValueError(
                "CFBD_API_KEY is required. Set the environment variable or pass api_key explicitly."
            )

        host_choice = (host or os.getenv("CFBD_HOST") or "production").lower()
        if host_choice not in HOST_MAP:
            raise ValueError(
                "CFBD_HOST must be one of {'production', 'next'} — "
                f"received '{host_choice}'."
            )
        self._base_url = HOST_MAP[host_choice]

        self._session = session or requests.Session()
        self._last_request_ts = 0.0
        self._metrics = ClientMetrics()
        self._telemetry_hook = telemetry_hook
        self._metrics_log_path = Path(metrics_log_path) if metrics_log_path else None
        if self._metrics_log_path and not self._metrics_log_path.parent.exists():
            self._metrics_log_path.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _log(self, level: int, message: str) -> None:
        _LOGGER.log(level, f"[{self._now()}] {logging.getLevelName(level)}: {message}")

    def _throttle(self) -> None:
        """Ensure at least `_throttle_interval` seconds between request start times."""
        elapsed = time.monotonic() - self._last_request_ts
        if elapsed < self._throttle_interval:
            time.sleep(self._throttle_interval - elapsed)

    def _request(self, config: RequestConfig) -> Any:
        """Execute a CFBD API request with throttling, retries, and structured logging."""
        endpoint = config.endpoint
        params = config.params or {}

        last_error: Optional[Exception] = None
        for attempt in range(1, self._max_attempts + 1):
            self._throttle()
            request_start = time.monotonic()
            self._last_request_ts = request_start
            self._metrics.total_requests += 1

            try:
                response = self._session.request(
                    method=config.method,
                    url=f"{self._base_url}{endpoint}",
                    params=params,
                    headers={"Authorization": f"Bearer {self._api_key}"},
                    timeout=30,
                )
            except requests.RequestException as exc:
                last_error = exc
                latency_ms = (time.monotonic() - request_start) * 1000
                self._log(
                    logging.WARNING,
                    (
                        f"{config.method} {endpoint} (network_error, latency_ms={latency_ms:.0f}, attempt={attempt})"
                    ),
                )
                self._record_metrics(
                    status=None,
                    latency_ms=latency_ms,
                    attempt=attempt,
                    event="network_error",
                )
                self._emit_telemetry(
                    method=config.method,
                    endpoint=endpoint,
                    params=params,
                    status=None,
                    latency_ms=latency_ms,
                    attempt=attempt,
                    outcome="network_error",
                )
                self._metrics.retries += 1
                self._metrics.network_errors += 1
                self._apply_backoff(attempt)
                continue

            latency_ms = (time.monotonic() - request_start) * 1000
            status = response.status_code
            log_message = (
                f"{config.method} {endpoint} (status={status}, latency_ms={latency_ms:.0f}, attempt={attempt})"
            )

            if 200 <= status < 300:
                self._log(logging.INFO, log_message)
                self._record_metrics(
                    status=status,
                    latency_ms=latency_ms,
                    attempt=attempt,
                    event="success",
                )
                self._emit_telemetry(
                    method=config.method,
                    endpoint=endpoint,
                    params=params,
                    status=status,
                    latency_ms=latency_ms,
                    attempt=attempt,
                    outcome="success",
                )
                return self._safe_json(response)

            if status in (401, 403):
                self._log(logging.ERROR, log_message + " -- authentication failure")
                self._record_metrics(
                    status=status,
                    latency_ms=latency_ms,
                    attempt=attempt,
                    event="auth_error",
                )
                self._emit_telemetry(
                    method=config.method,
                    endpoint=endpoint,
                    params=params,
                    status=status,
                    latency_ms=latency_ms,
                    attempt=attempt,
                    outcome="auth_error",
                )
                self._metrics.auth_errors += 1
                raise CFBDClientError(
                    "Invalid API key. Obtain a valid key at https://collegefootballdata.com/key"
                )

            if status == 429:
                self._log(logging.WARNING, log_message + " -- rate limit hit, waiting 60s")
                self._record_metrics(
                    status=status,
                    latency_ms=latency_ms,
                    attempt=attempt,
                    event="rate_limit",
                )
                self._emit_telemetry(
                    method=config.method,
                    endpoint=endpoint,
                    params=params,
                    status=status,
                    latency_ms=latency_ms,
                    attempt=attempt,
                    outcome="rate_limit",
                )
                self._metrics.rate_limit_hits += 1
                self._metrics.retries += 1
                time.sleep(60)
                continue

            if 500 <= status < 600:
                self._log(logging.WARNING, log_message + " -- server error, retrying")
                self._record_metrics(
                    status=status,
                    latency_ms=latency_ms,
                    attempt=attempt,
                    event="server_error",
                )
                self._emit_telemetry(
                    method=config.method,
                    endpoint=endpoint,
                    params=params,
                    status=status,
                    latency_ms=latency_ms,
                    attempt=attempt,
                    outcome="server_error",
                )
                self._metrics.server_errors += 1
                self._metrics.retries += 1
                self._apply_backoff(attempt)
                continue

            # Other 4xx errors
            try:
                detail = response.json()
            except ValueError:
                detail = response.text
            self._log(logging.ERROR, log_message + f" -- {detail}")
            self._record_metrics(
                status=status,
                latency_ms=latency_ms,
                attempt=attempt,
                event="client_error",
            )
            self._emit_telemetry(
                method=config.method,
                endpoint=endpoint,
                params=params,
                status=status,
                latency_ms=latency_ms,
                attempt=attempt,
                outcome="client_error",
            )
            self._metrics.client_errors += 1
            raise CFBDClientError(
                (
                    "CFBD request failed with status {status}. "
                    "Method={method}, endpoint={endpoint}, params={params}, detail={detail}"
                ).format(
                    status=status,
                    method=config.method,
                    endpoint=endpoint,
                    params=params,
                    detail=detail,
                )
            )

        raise CFBDClientError(
            "CFBD request exhausted retries. Last error: " + (str(last_error) if last_error else "Unknown error")
        )

    def _apply_backoff(self, attempt: int) -> None:
        delay = self._retry_delays[min(attempt, len(self._retry_delays) - 1)]
        if delay > 0:
            time.sleep(delay)

    @staticmethod
    def _safe_json(response: requests.Response) -> Any:
        if not response.content:
            return None
        try:
            return response.json()
        except json.JSONDecodeError as exc:  # pragma: no cover - extremely rare
            raise CFBDClientError(f"Failed to decode CFBD response JSON: {exc}") from exc

    def get_metrics(self) -> Dict[str, Any]:
        """Return a snapshot of client metrics."""

        return self._metrics.to_dict()

    def reset_metrics(self) -> None:
        """Reset stored metrics."""

        self._metrics = ClientMetrics()

    def get_games(
        self,
        *,
        year: int,
        week: Optional[int] = None,
        season_type: str = "regular",
        team: Optional[str] = None,
    ) -> Any:
        """Fetch games for the specified season/week/team."""

        params: Dict[str, Any] = {"year": year, "seasonType": season_type}
        if week is not None:
            params["week"] = week
        if team is not None:
            params["team"] = team

        config = RequestConfig(method="GET", endpoint="/games", params=params)
        return self._request(config)

    def get_ratings(
        self,
        *,
        year: int,
        week: Optional[int] = None,
        season_type: str = "regular",
    ) -> Any:
        """Fetch team ratings for a given week."""

        params: Dict[str, Any] = {"year": year, "seasonType": season_type}
        if week is not None:
            params["week"] = week

        config = RequestConfig(method="GET", endpoint="/ratings", params=params)
        return self._request(config)

    def get_sp_ratings(
        self,
        *,
        year: int,
        team: Optional[str] = None,
    ) -> Any:
        """Fetch SP+ ratings for a given year."""

        params: Dict[str, Any] = {"year": year}
        if team is not None:
            params["team"] = team

        config = RequestConfig(method="GET", endpoint="/ratings/sp", params=params)
        return self._request(config)

    def get_lines(
        self,
        *,
        year: int,
        week: int,
        season_type: str = "regular",
    ) -> Any:
        """Fetch betting lines for the specified week."""

        params: Dict[str, Any] = {"year": year, "week": week, "seasonType": season_type}
        config = RequestConfig(method="GET", endpoint="/lines", params=params)
        return self._request(config)

    def get_recruiting(self, *, year: int) -> Any:
        """Fetch team recruiting rankings for a season."""

        config = RequestConfig(method="GET", endpoint="/recruiting/teams", params={"year": year})
        return self._request(config)

    def get_game_weather(
        self,
        *,
        year: int,
        week: Optional[int] = None,
        season_type: str = "regular",
    ) -> Any:
        """Fetch weather reports for games in the specified window."""

        params: Dict[str, Any] = {"year": year, "seasonType": season_type}
        if week is not None:
            params["week"] = week

        config = RequestConfig(method="GET", endpoint="/game/weather", params=params)
        return self._request(config)

    def get_game_media(
        self,
        *,
        year: int,
        week: Optional[int] = None,
        season_type: str = "regular",
    ) -> Any:
        """Fetch broadcast assignments for games."""

        params: Dict[str, Any] = {"year": year, "seasonType": season_type}
        if week is not None:
            params["week"] = week

        config = RequestConfig(method="GET", endpoint="/game/media", params=params)
        return self._request(config)

    def get_predicted_points(
        self,
        *,
        year: int,
        week: Optional[int] = None,
        season_type: str = "regular",
    ) -> Any:
        """Fetch predicted points / win probability data."""

        params: Dict[str, Any] = {"year": year, "seasonType": season_type}
        if week is not None:
            params["week"] = week

        config = RequestConfig(method="GET", endpoint="/ratings/predicted", params=params)
        return self._request(config)

    def _record_metrics(
        self,
        *,
        status: Optional[int],
        latency_ms: float,
        attempt: int,
        event: str,
    ) -> None:
        self._metrics.total_latency_ms += latency_ms
        if status is not None and 200 <= status < 300:
            self._metrics.successful_requests += 1

    def _emit_telemetry(
        self,
        *,
        method: str,
        endpoint: str,
        params: Dict[str, Any],
        status: Optional[int],
        latency_ms: float,
        attempt: int,
        outcome: str,
    ) -> None:
        event = {
            "timestamp": self._now(),
            "method": method,
            "endpoint": endpoint,
            "params": params,
            "status": status,
            "latency_ms": round(latency_ms, 2),
            "attempt": attempt,
            "outcome": outcome,
        }
        if self._telemetry_hook:
            self._telemetry_hook(event)
        if self._metrics_log_path:
            with self._metrics_log_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(event) + "\n")


__all__ = ["CFBDClient", "CFBDClientError"]
