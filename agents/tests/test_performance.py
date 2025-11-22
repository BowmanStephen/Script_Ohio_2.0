"""Lightweight performance benchmarks for the Script Ohio 2.0 orchestrator."""

import time

import pytest

from agents.analytics_orchestrator import AnalyticsRequest


@pytest.mark.performance
@pytest.mark.parametrize(
    "query,query_type,max_seconds",
    [
        ("Recommend notebooks for beginners", "learning", 3.0),
        ("Predict Ohio State vs Michigan", "prediction", 5.0),
    ],
)
def test_response_time(orchestrator, query, query_type, max_seconds):
    request = AnalyticsRequest(
        user_id="performance_test",
        query=query,
        query_type=query_type,
        parameters={"home_team": "Ohio State", "away_team": "Michigan"} if query_type == "prediction" else {},
        context_hints={},
    )

    start = time.perf_counter()
    response = orchestrator.process_analytics_request(request)
    elapsed = time.perf_counter() - start

    assert response.status in {"success", "partial_success"}
    assert elapsed < max_seconds, f"{query_type} request took {elapsed:.2f}s (limit {max_seconds:.2f}s)"
