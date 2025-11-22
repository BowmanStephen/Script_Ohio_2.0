"""CFBD GraphQL subscription manager."""
from __future__ import annotations

import threading
import time
from collections import deque
from typing import Any, Callable, Deque, Dict, List, Optional

try:
    from cfbd_client import GraphQLSubscriptionClient, GraphQLRequest
except ImportError:  # pragma: no cover - optional dependency
    GraphQLSubscriptionClient = None  # type: ignore
    GraphQLRequest = None  # type: ignore


class CFBDSubscriptionHandle:
    """Wraps subscription state so callers can stop feeds cleanly."""

    def __init__(self, handle: Any):
        self._handle = handle

    def stop(self) -> None:
        if self._handle:
            self._handle.stop()


class CFBDSubscriptionManager:
    """Starts GraphQL subscriptions and keeps a rolling cache of events."""

    def __init__(
        self,
        subscription_client: Optional[GraphQLSubscriptionClient] = None,
        telemetry_hook: Optional[Callable[[Dict[str, Any]], None]] = None,
        max_events: int = 100,
    ) -> None:
        if GraphQLSubscriptionClient is None or GraphQLRequest is None:
            raise RuntimeError("GraphQL subscription client is not available in this environment")

        self._client = subscription_client or GraphQLSubscriptionClient(telemetry_hook=telemetry_hook)
        self._telemetry_hook = telemetry_hook
        self._events: Deque[Dict[str, Any]] = deque(maxlen=max_events)
        self._handle: Optional[CFBDSubscriptionHandle] = None
        self._lock = threading.Lock()

    def start_scoreboard_feed(self) -> None:
        if self._handle is not None:
            return

        query = """
        subscription ScoreboardFeed {
          scoreboard {
            gameId
            season
            week
            homeTeam
            awayTeam
            homePoints
            awayPoints
            status
            startDate
          }
        }
        """
        request = GraphQLRequest(query=query, operation_name="ScoreboardFeed")

        handle = self._client.subscribe(
            request=request,
            on_event=self._handle_event,
            on_error=self._handle_error,
            operation_name="ScoreboardFeed",
        )
        self._handle = CFBDSubscriptionHandle(handle)

    def stop(self) -> None:
        if self._handle:
            self._handle.stop()
            self._handle = None

    def _handle_event(self, payload: Dict[str, Any]) -> None:
        scoreboard = payload.get("scoreboard") or []
        timestamp = time.time()
        with self._lock:
            for entry in scoreboard:
                entry = dict(entry)
                entry["received_at"] = timestamp
                self._events.append(entry)

    def _handle_error(self, error: Exception) -> None:  # pragma: no cover - network dependent
        if self._telemetry_hook:
            self._telemetry_hook(
                {
                    "timestamp": time.time(),
                    "client": "graphql_subscription",
                    "operation": "ScoreboardFeed",
                    "outcome": "subscription_error",
                    "detail": str(error),
                }
            )

    def latest_events(self, limit: int = 10) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._events)[-limit:]


__all__ = ["CFBDSubscriptionManager", "CFBDSubscriptionHandle"]
