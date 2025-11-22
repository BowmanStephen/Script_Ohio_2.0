import time

from agents.core.agent_framework import AgentRequest, AgentStatus, PermissionLevel
from agents.learning_navigator_agent import LearningNavigatorAgent


def _request(action: str, params: dict) -> AgentRequest:
    return AgentRequest(
        request_id=f"test_{action}",
        agent_type="learning_navigator",
        action=action,
        parameters=params,
        user_context={"role": "analyst", "user_id": "pytest"},
        timestamp=time.time(),
        priority=1,
    )


action_parameters = {
    "guide_learning_path": {"skill_level": "beginner"},
    "explain_concepts": {"topic": "expected points added"},
    "recommend_resources": {"topic": "data exploration"},
    "recommend_content": {"query": "learn about EPA"},
    "track_progress": {"completed": ["01_intro.ipynb"]},
}


def test_capabilities_have_estimates():
    agent = LearningNavigatorAgent(agent_id="pytest_learning")
    assert agent.capabilities, "Agent should expose capabilities"
    for capability in agent.capabilities:
        assert capability.execution_time_estimate > 0


def test_actions_execute_successfully():
    agent = LearningNavigatorAgent(agent_id="pytest_learning")
    for capability in agent.capabilities:
        params = action_parameters.get(capability.name, {"skill_level": "beginner"})
        req = _request(capability.name, params)
        response = agent.execute_request(req, PermissionLevel.READ_EXECUTE)
        assert response.status == AgentStatus.COMPLETED
