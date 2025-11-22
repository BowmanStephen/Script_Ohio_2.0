import pandas as pd
import pytest

from agents.insight_generator_agent import InsightGeneratorAgent
from agents.workflow_automator_agent import WorkflowAutomatorAgent


class _StubRestSource:
    def __init__(self, games):
        self._games = games

    def fetch_games(self, **kwargs):
        return self._games

    def fetch_lines(self, **kwargs):
        return [{"gameId": 123, "spread": -6.5}]


class _StubEngineer:
    def prepare_games_frame(self, games, source="rest"):
        return pd.DataFrame(
            [
                {
                    "id": 123,
                    "season": 2025,
                    "season_type": "regular",
                    "week": 1,
                    "home_team": "Ohio State",
                    "home_conference": "Big Ten",
                    "home_points": 31,
                    "away_team": "Michigan",
                    "away_conference": "Big Ten",
                    "away_points": 24,
                    "margin": 7.0,
                    "game_key": "2025_1_Ohio State_Michigan",
                }
            ]
        )

    def merge_spreads(self, df, lines):
        df = df.copy()
        df["spread"] = -6.5
        return df

    def build_feature_frame(self, df):
        df = df.copy()
        df["conference_game"] = True
        return df


class _StubGraphQLClient:
    def fetch_team_talent(self, **kwargs):
        return {"teamTalent": [{"team": {"school": "Ohio State"}, "talent": 945}]}

    def fetch_recruits(self, **kwargs):
        return {"recruit": [{"name": "Five Star QB"}]}


@pytest.fixture
def _games_payload():
    return [
        {
            "id": 123,
            "season": 2025,
            "seasonType": "regular",
            "week": 1,
            "homeTeam": "Ohio State",
            "homePoints": 31,
            "awayTeam": "Michigan",
            "awayPoints": 24,
        }
    ]


def test_insight_generator_cfbd_analysis(monkeypatch, _games_payload):
    monkeypatch.setattr("agents.insight_generator_agent.CFBDDataProvider", None)
    agent = InsightGeneratorAgent("test_insight")

    stub_rest = _StubRestSource(_games_payload)
    stub_engineer = _StubEngineer()
    monkeypatch.setattr(agent, "_get_rest_data_source", lambda host: stub_rest)
    monkeypatch.setattr(agent, "_get_feature_engineer", lambda season: stub_engineer)
    monkeypatch.setattr(agent, "_summarize_feature_frame", lambda frame: {"avg_margin": 7.0})

    response = agent._perform_cfbd_real_time_analysis({"season": 2025}, {"detected_role": "analyst"})
    assert response["success"] is True
    assert response["summary"]["avg_margin"] == 7.0
    assert response["games_returned"] == 1


def test_insight_generator_graphql_scan(monkeypatch):
    monkeypatch.setattr("agents.insight_generator_agent.CFBDDataProvider", None)
    agent = InsightGeneratorAgent("test_insight_graphql")
    monkeypatch.setattr(agent, "_get_graphql_client", lambda: _StubGraphQLClient())

    response = agent._execute_graphql_trend_scan({"season": 2025, "limit": 5}, {"detected_role": "analyst"})
    assert response["success"] is True
    assert response["talent_sample"][0]["team"] == "Ohio State"


def test_workflow_automator_cfbd_pipeline(monkeypatch, _games_payload):
    monkeypatch.setattr("agents.workflow_automator_agent.CFBDDataProvider", None)
    agent = WorkflowAutomatorAgent("wf_auto")

    stub_rest = _StubRestSource(_games_payload)
    stub_engineer = _StubEngineer()
    monkeypatch.setattr(agent, "_get_rest_data_source", lambda host: stub_rest)
    monkeypatch.setattr(agent, "_get_feature_engineer", lambda season: stub_engineer)
    monkeypatch.setattr(agent, "_run_ridge_predictions", lambda frame: [{"game_key": "abc", "predicted_margin": 3.2}])
    monkeypatch.setattr(agent, "_fetch_graphql_summary", lambda season, limit: {"available": True})

    response = agent._execute_cfbd_pipeline({"season": 2025}, {"detected_role": "analyst"})
    assert response["success"] is True
    assert response["games_processed"] == 1
    assert response["predictions"][0]["predicted_margin"] == 3.2

