from __future__ import annotations

import pandas as pd

from cfbd_client.data_provider import CFBDDataProvider


class DummyGraphQL:
    def __init__(self):
        self.calls = 0

    def query(self, request):
        self.calls += 1
        return {
            "adjustedTeamMetrics": [
                {
                    "team": request.variables["team"],
                    "year": request.variables["season"],
                    "rating": 10.5,
                    "offense": 6.2,
                    "defense": 4.3,
                }
            ]
        }


def _games_df():
    return pd.DataFrame(
        [
            {
                "id": 1,
                "home_team": "ohio_state",
                "away_team": "michigan",
                "home_points": 30,
                "away_points": 27,
                "week": 12,
                "season": 2025,
            }
        ]
    )


def _ratings_df():
    return pd.DataFrame(
        [
            {
                "team": "ohio_state",
                "conference": "big_ten",
                "rating_type": "sp+",
                "rating_value": 28.4,
                "fetched_at": "2025-11-12",
            }
        ]
    )


def _predictions_df():
    return pd.DataFrame(
        [
            {
                "team": "ohio_state",
                "opponent": "michigan",
                "predicted_margin": 6.5,
                "win_probability": 0.62,
                "is_home": True,
                "fetched_at": "2025-11-12",
            }
        ]
    )


def test_team_snapshot_uses_live_data(monkeypatch):
    dummy_graphql = DummyGraphQL()
    provider = CFBDDataProvider(cfbd_client=object(), graphql_client=dummy_graphql)

    monkeypatch.setattr("cfbd_client.data_provider.fetch_games", lambda *_, **__: _games_df())
    monkeypatch.setattr("cfbd_client.data_provider.fetch_ratings", lambda *_, **__: _ratings_df())
    monkeypatch.setattr(
        "cfbd_client.data_provider.fetch_predicted_points",
        lambda *_, **__: _predictions_df(),
    )

    snapshot = provider.get_team_snapshot(team="ohio_state", season=2025, week=12)

    assert snapshot["recent_games"][0]["home_points"] == 30
    assert snapshot["ratings"][0]["rating_value"] == 28.4
    assert snapshot["predicted_points"][0]["win_probability"] == 0.62
    assert snapshot["adjusted_metrics"]["rating"] == 10.5


def test_adjusted_metric_cache(monkeypatch):
    dummy_graphql = DummyGraphQL()
    provider = CFBDDataProvider(cfbd_client=object(), graphql_client=dummy_graphql)

    monkeypatch.setattr("cfbd_client.data_provider.fetch_games", lambda *_, **__: _games_df())
    monkeypatch.setattr("cfbd_client.data_provider.fetch_ratings", lambda *_, **__: _ratings_df())
    monkeypatch.setattr(
        "cfbd_client.data_provider.fetch_predicted_points",
        lambda *_, **__: _predictions_df(),
    )

    provider.get_adjusted_team_metrics(team="ohio_state", season=2025)
    provider.get_adjusted_team_metrics(team="ohio_state", season=2025)

    assert dummy_graphql.calls == 1
