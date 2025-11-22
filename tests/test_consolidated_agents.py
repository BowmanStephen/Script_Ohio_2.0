from __future__ import annotations

from collections import deque
from typing import Any, Dict

import pytest

from agents.cfbd_integration_agent import CFBDIntegrationAgent
from agents.quality_assurance_agent import QualityAssuranceAgent


class FakeProvider:
    def get_team_snapshot(self, team: str, season: int, week: int | None = None) -> Dict[str, Any]:
        return {
            "team": team,
            "season": season,
            "week": week,
            "games": [
                {
                    "opponent": "michigan",
                    "home_points": 35,
                    "away_points": 28,
                }
            ],
        }

    def get_games(self, year: int, week: int | None = None, team: str | None = None) -> list:
        return [{
            "opponent": "michigan",
            "home_points": 35,
            "away_points": 28,
            "week": 12
        }]

    def get_ratings(self, year: int, week: int | None = None) -> list:
        return [{"team": "Ohio State", "rating": 90.0}]

    def get_stats(self, year: int, team: str | None = None) -> list:
        return [{"category": "offense", "stat": "total_yards", "value": 500}]

    def get_team_talent(self, year: int) -> list:
        return [{"school": "Ohio State", "talent": 95.0}]


class FakeLiveFeed:
    def latest_events(self, limit: int = 5):
        return [
            {
                "homeTeam": "Ohio State",
                "homePoints": 14,
                "awayTeam": "Michigan State",
                "awayPoints": 3,
                "status": "Q2",
            }
        ][:limit]


def test_cfbd_integration_agent_snapshot():
    agent = CFBDIntegrationAgent("cfbd_test", cfbd_client=FakeProvider())
    result = agent._execute_action(
        "team_snapshot",
        {"team": "Ohio State", "season": 2025, "week": 12},
        {},
    )
    assert result["status"] == "success"
    assert result["snapshot"]["team"] == "Ohio State"


def test_cfbd_integration_agent_live_scoreboard():
    agent = CFBDIntegrationAgent(
        "cfbd_test",
        cfbd_client=FakeProvider(),
        live_feed_provider=FakeLiveFeed(),
    )
    result = agent._execute_action("live_scoreboard", {"limit": 1}, {})
    assert result["status"] == "success"
    assert len(result["events"]) == 1


def test_quality_assurance_agent_health_check():
    telemetry = deque(
        [
            {"outcome": "success", "latency_ms": 120},
            {"outcome": "success", "latency_ms": 80},
            {"outcome": "subscription_error"},
        ],
        maxlen=200,
    )
    agent = QualityAssuranceAgent("qa_test", telemetry_events=telemetry)
    summary = agent._execute_action("cfbd_health_check", {}, {})
    assert summary["total_events"] == 3
    assert summary["status_counts"].get("success") == 2
    recent = agent._execute_action("cfbd_recent_events", {"limit": 2}, {})
    assert len(recent["events"]) == 2
