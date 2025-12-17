from agents.analytics_orchestrator import AnalyticsRequest


def test_learning_request(orchestrator):
    request = AnalyticsRequest(
        user_id="pytest_user",
        query="Guide me through the starter pack",
        query_type="learning",
        parameters={},
        context_hints={"skill_level": "beginner"},
    )

    response = orchestrator.process_analytics_request(request)
    assert response.status in {"success", "partial_success"}
    assert response.insights


def test_agent_registry_contains_defaults(orchestrator):
    agent_types = set(orchestrator.agent_factory.agent_registry.keys())
    # Minimum expected core agents for a healthy orchestrator
    # Note: conversational_ai and workflow_automator are optional in the
    # current architecture and may be disabled in some environments.
    required_core = {"learning_navigator", "model_engine", "insight_generator"}
    assert required_core.issubset(agent_types)
