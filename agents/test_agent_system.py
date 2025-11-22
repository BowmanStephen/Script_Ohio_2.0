#!/usr/bin/env python3
"""Modern smoke tests for the Script Ohio 2.0 agent stack."""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.append(str(REPO_ROOT))

from agents.analytics_orchestrator import AnalyticsOrchestrator, AnalyticsRequest
from agents.core.agent_framework import (
    AgentCapability,
    AgentRequest,
    AgentStatus,
    BaseAgent,
    PermissionLevel,
)


_ORCHESTRATOR = None


def get_orchestrator() -> AnalyticsOrchestrator:
    """Lazily instantiate the production orchestrator once."""
    global _ORCHESTRATOR
    if _ORCHESTRATOR is None:
        _ORCHESTRATOR = AnalyticsOrchestrator()
    return _ORCHESTRATOR


def test_base_agent() -> bool:
    """Validate BaseAgent contract with execution estimates."""

    class DemoAgent(BaseAgent):
        def __init__(self):
            super().__init__(
                agent_id="demo_agent",
                name="Demo Agent",
                permission_level=PermissionLevel.READ_EXECUTE,
            )

        def _define_capabilities(self) -> List[AgentCapability]:
            return [
                AgentCapability(
                    name="test_action",
                    description="Simple smoke-test action",
                    permission_required=PermissionLevel.READ_EXECUTE,
                    tools_required=["diagnostics"],
                    data_access=["tests/"],
                    execution_time_estimate=0.1,
                )
            ]

        def _execute_action(self, action, parameters, user_context):
            if action == "test_action":
                return {"status": "success", "echo": parameters}
            raise ValueError(f"Unknown action: {action}")

    agent = DemoAgent()
    request = AgentRequest(
        request_id="demo-request",
        agent_type="demo",  # Derived from DemoAgent -> "demo"
        action="test_action",
        parameters={"payload": 42},
        user_context={"user_id": "tester"},
        timestamp=time.time(),
    )

    response = agent.execute_request(request, PermissionLevel.READ_EXECUTE)

    ok = response.status == AgentStatus.COMPLETED and response.result["status"] == "success"
    print("✅ BaseAgent smoke test" if ok else "❌ BaseAgent smoke test failed")
    return ok


def test_analytics_orchestrator() -> bool:
    """Send a representative request through the orchestrator."""
    orchestrator = get_orchestrator()
    request = AnalyticsRequest(
        user_id="test_user",
        query="Predict Ohio State vs Michigan",
        query_type="prediction",
        parameters={"home_team": "Ohio State", "away_team": "Michigan"},
        context_hints={"role": "analyst"},
    )
    response = orchestrator.process_analytics_request(request)
    ok = response.status in {"success", "partial_success"}
    print("✅ Orchestrator request" if ok else "❌ Orchestrator request failed")
    return ok


def test_production_agents() -> bool:
    """Ensure every production agent exposes valid capabilities."""
    orchestrator = get_orchestrator()
    statuses: List[Tuple[str, bool]] = []

    for agent in orchestrator.agent_factory.agents.values():
        caps = agent.capabilities
        has_estimates = all(getattr(cap, "execution_time_estimate", 0) > 0 for cap in caps)
        statuses.append((agent.name, bool(caps) and has_estimates))

    all_ok = all(status for _, status in statuses)
    for name, status in statuses:
        symbol = "✅" if status else "❌"
        print(f"{symbol} Capabilities defined for {name}")
    return all_ok


def run_all_tests() -> bool:
    print("🚀 Starting Agent System Smoke Tests")
    print("=" * 50)

    tests = [
        ("BaseAgent", test_base_agent),
        ("AnalyticsOrchestrator", test_analytics_orchestrator),
        ("Production Agents", test_production_agents),
    ]

    results = []
    for name, func in tests:
        try:
            result = func()
        except Exception as exc:  # pylint: disable=broad-except
            print(f"❌ {name} raised an exception: {exc}")
            result = False
        results.append((name, result))

    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)

    for name, result in results:
        print(f"{name:<25} {'✅ PASSED' if result else '❌ FAILED'}")

    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\nOverall: {passed}/{total} passed")

    os.makedirs("logs", exist_ok=True)
    with open("logs/agent_smoke_tests.json", "w") as handle:
        json.dump(
            {
                "timestamp": datetime.now().isoformat(),
                "results": [
                    {"name": name, "passed": result}
                    for name, result in results
                ],
            },
            handle,
            indent=2,
        )

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
