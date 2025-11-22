#!/usr/bin/env python3
"""
Modern Agent System Demonstration

This script showcases the production-ready `AnalyticsOrchestrator` and the five
primary agents (learning navigator, model engine, insight generator, workflow
automator, conversational AI).
"""

import json
import os
import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.append(str(REPO_ROOT))

from agents.analytics_orchestrator import AnalyticsOrchestrator, AnalyticsRequest


def _print_response(label: str, response) -> None:
    """Pretty-print orchestrator responses."""
    print(f"\n=== {label} ===")
    print(f"Status: {response.status}")
    print(f"Execution Time: {response.execution_time:.2f}s")
    if response.error_message:
        print(f"Error: {response.error_message}")
        return
    if response.insights:
        print("Insights:")
        for insight in response.insights[:3]:
            print(f"  - {insight}")
    if response.results:
        print("Result keys:", list(response.results.keys()))


def build_request(user_id: str, query: str, query_type: str,
                  parameters: Dict, context_hints: Dict) -> AnalyticsRequest:
    """Helper to create consistent requests."""
    return AnalyticsRequest(
        user_id=user_id,
        query=query,
        query_type=query_type,
        parameters=parameters,
        context_hints=context_hints,
    )


def demo_requests() -> List[AnalyticsRequest]:
    """Sample requests that exercise each production agent."""
    return [
        build_request(
            "demo_user",
            "Guide me through the starter pack notebooks",
            "learning",
            {},
            {"skill_level": "beginner"},
        ),
        build_request(
            "demo_user",
            "Predict Ohio State vs Michigan",
            "prediction",
            {"home_team": "Ohio State", "away_team": "Michigan"},
            {"role": "analyst"},
        ),
        build_request(
            "demo_user",
            "Analyze Big Ten offensive efficiency",
            "analysis",
            {"analysis_type": "performance", "conference": "Big Ten"},
            {"role": "data_scientist"},
        ),
        build_request(
            "demo_user",
            "Create a workflow that fetches data and runs predictions",
            "workflow",
            {"workflow_name": "weekly_prediction"},
            {"role": "production"},
        ),
        build_request(
            "demo_user",
            "Explain expected points added in simple terms",
            "conversation",
            {},
            {"skill_level": "beginner"},
        ),
    ]


def run_demo() -> bool:
    """Run the orchestrator demonstration."""
    print("🚀 SCRIPT OHIO 2.0 - MODERN AGENT SYSTEM DEMO")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")

    orchestrator = AnalyticsOrchestrator()
    scenarios = demo_requests()
    successes = 0

    for idx, request in enumerate(scenarios, 1):
        response = orchestrator.process_analytics_request(request)
        _print_response(f"Scenario {idx}: {request.query_type}", response)
        if response.status in {"success", "partial_success"}:
            successes += 1

    print("\n=== SUMMARY ===")
    print(f"Completed {successes}/{len(scenarios)} scenarios successfully.")
    print("Agent types available:", sorted(orchestrator.agent_factory.agent_registry.keys()))
    print("Agent instances created:", sorted(orchestrator.agent_factory.agents.keys()))

    # Persist raw responses for debugging/reference
    demo_log = {
        "timestamp": datetime.now().isoformat(),
        "scenarios": [asdict(r) for r in scenarios],
        "agent_types": sorted(orchestrator.agent_factory.agent_registry.keys()),
        "agent_instances": sorted(orchestrator.agent_factory.agents.keys()),
    }
    os.makedirs("logs", exist_ok=True)
    log_path = "logs/modern_demo_log.json"
    with open(log_path, "w") as f:
        json.dump(demo_log, f, indent=2)
    print(f"📁 Demo metadata saved to {log_path}")

    return successes == len(scenarios)


if __name__ == "__main__":
    success = run_demo()
    exit(0 if success else 1)