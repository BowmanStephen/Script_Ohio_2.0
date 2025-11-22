from __future__ import annotations

from typing import Any, Dict

import pytest

from agents.system import cfbd_subscription_manager as manager_module


class FakeHandle:
    def __init__(self) -> None:
        self.stopped = False

    def stop(self) -> None:
        self.stopped = True


class FakeClient:
    def __init__(self, telemetry_hook=None) -> None:
        self.telemetry_hook = telemetry_hook
        self.on_event = None
        self.on_error = None

    def subscribe(self, request, on_event, on_error, operation_name: str = "ScoreboardFeed") -> FakeHandle:
        self.on_event = on_event
        self.on_error = on_error
        return FakeHandle()


class FakeRequest:
    def __init__(self, query: str, operation_name: str) -> None:
        self.query = query
        self.operation_name = operation_name


@pytest.fixture(autouse=True)
def patch_graphql(monkeypatch):
    monkeypatch.setattr(manager_module, "GraphQLSubscriptionClient", FakeClient)
    monkeypatch.setattr(manager_module, "GraphQLRequest", FakeRequest)


def test_subscription_manager_collects_events():
    mgr = manager_module.CFBDSubscriptionManager()
    mgr.start_scoreboard_feed()
    sample_event: Dict[str, Any] = {
        "scoreboard": [
            {
                "gameId": 1,
                "homeTeam": "Ohio State",
                "awayTeam": "Michigan",
                "homePoints": 21,
                "awayPoints": 14,
                "status": "Q3",
            }
        ]
    }
    mgr._handle_event(sample_event)
    events = mgr.latest_events(limit=1)
    assert len(events) == 1
    assert events[0]["homeTeam"] == "Ohio State"


def test_subscription_manager_stop():
    mgr = manager_module.CFBDSubscriptionManager()
    mgr.start_scoreboard_feed()
    assert mgr._handle is not None
    handle = mgr._handle
    mgr.stop()
    assert handle is not None and handle._handle.stopped
