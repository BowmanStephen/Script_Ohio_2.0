"""Integration tests for the Script Ohio 2.0 agent system."""

import pytest

from agents.analytics_orchestrator import AnalyticsRequest


@pytest.mark.integration
@pytest.mark.parametrize(
    "query,query_type,context",
    [
        ("Guide me from beginner to advanced analytics", "learning", {"skill_level": "beginner"}),
        ("Predict all week 12 games", "prediction", {"role": "data_scientist", "week": 12}),
        ("Analyze Big Ten performance and recommend next steps", "analysis", {"role": "analyst"}),
    ],
)
def test_end_to_end_flows(orchestrator, query, query_type, context):
    request = AnalyticsRequest(
        user_id="integration_test",
        query=query,
        query_type=query_type,
        parameters={},
        context_hints=context,
    )

    response = orchestrator.process_analytics_request(request)

    assert response.status in {"success", "partial_success"}
    assert response.execution_time >= 0


def test_multi_agent_collaboration(orchestrator):
    request = AnalyticsRequest(
        user_id="integration_test",
        query="Create a workflow that fetches data and runs predictions",
        query_type="workflow",
        parameters={},
        context_hints={"role": "production"},
    )

    response = orchestrator.process_analytics_request(request)

    assert response.status in {"success", "partial_success"}
    assert len(response.metadata.get("agents_used", [])) >= 1


def test_conversational_follow_up(orchestrator):
    first_request = AnalyticsRequest(
        user_id="integration_convo",
        query="Explain expected points added",
        query_type="conversation",
        parameters={},
        context_hints={"skill_level": "beginner"},
    )
    response = orchestrator.process_analytics_request(first_request)
    assert response.status in {"success", "partial_success"}

    follow_up = AnalyticsRequest(
        user_id="integration_convo",
        query="Give me a follow-up drill",
        query_type="conversation",
        parameters={},
        context_hints={"skill_level": "beginner"},
    )
    follow_response = orchestrator.process_analytics_request(follow_up)
    assert follow_response.status in {"success", "partial_success"}
