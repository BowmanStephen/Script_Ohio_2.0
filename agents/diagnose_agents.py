#!/usr/bin/env python3
"""
Comprehensive Agent Diagnostic Tool

Tests each agent individually to identify which work and which need debugging.
"""

import json
import sys
import time
import traceback
from pathlib import Path
from typing import Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.append(str(REPO_ROOT))

from agents.analytics_orchestrator import AnalyticsOrchestrator
from agents.core.agent_framework import AgentRequest, AgentStatus, PermissionLevel


class AgentDiagnostic:
    """Diagnostic tool for testing agents"""

    def __init__(self):
        self.orchestrator = AnalyticsOrchestrator()
        self.results: List[Dict] = []

    def test_agent_initialization(self, agent_id: str) -> Tuple[bool, str]:
        """Test if agent can be initialized"""
        try:
            agent = self.orchestrator.agent_factory.agents.get(agent_id)
            if agent is None:
                return False, f"Agent {agent_id} not found in factory"
            if not hasattr(agent, "capabilities"):
                return False, f"Agent {agent_id} missing capabilities"
            if not agent.capabilities:
                return False, f"Agent {agent_id} has no capabilities defined"
            return True, f"Agent {agent_id} initialized with {len(agent.capabilities)} capabilities"
        except Exception as e:
            return False, f"Initialization error: {str(e)}"

    def test_agent_capability(self, agent_id: str, capability_name: str) -> Tuple[bool, str, Dict]:
        """Test a specific capability of an agent"""
        try:
            agent = self.orchestrator.agent_factory.agents.get(agent_id)
            if agent is None:
                return False, f"Agent {agent_id} not found", {}

            # Find the capability
            capability = None
            for cap in agent.capabilities:
                if cap.name == capability_name:
                    capability = cap
                    break

            if capability is None:
                return False, f"Capability {capability_name} not found", {}

            # Get the correct agent_type from the agent class name
            # The agent derives its type from its class name
            agent_type_from_class = agent.__class__.__name__.replace("Agent", "").lower()
            # Apply the same transformations as BaseAgent.can_handle_request
            if "learning" in agent_type_from_class and "navigator" in agent_type_from_class:
                agent_type_from_class = "learning_navigator"
            elif "model" in agent_type_from_class and "execution" in agent_type_from_class and "engine" in agent_type_from_class:
                agent_type_from_class = "model_engine"
            elif "insight" in agent_type_from_class and "generator" in agent_type_from_class:
                agent_type_from_class = "insight_generator"
            elif "workflow" in agent_type_from_class and "automator" in agent_type_from_class:
                agent_type_from_class = "workflow_automator"
            elif "conversational" in agent_type_from_class and "ai" in agent_type_from_class:
                agent_type_from_class = "conversational_ai"
            elif "weekly" in agent_type_from_class and "analysis" in agent_type_from_class and "orchestrator" in agent_type_from_class:
                agent_type_from_class = "weekly_analysis_orchestrator"
            elif "weekly" in agent_type_from_class and "prediction" in agent_type_from_class and "generation" in agent_type_from_class:
                agent_type_from_class = "weekly_prediction_generation"
            elif "weekly" in agent_type_from_class and "matchup" in agent_type_from_class and "analysis" in agent_type_from_class:
                agent_type_from_class = "weekly_matchup_analysis"
            elif "weekly" in agent_type_from_class and "model" in agent_type_from_class and "validation" in agent_type_from_class:
                agent_type_from_class = "weekly_model_validation"
            elif "cfbd" in agent_type_from_class and "integration" in agent_type_from_class:
                agent_type_from_class = "cfbd_integration"
            elif "quality" in agent_type_from_class and "assurance" in agent_type_from_class:
                agent_type_from_class = "quality_assurance"
            elif "postseason" in agent_type_from_class and "projection" in agent_type_from_class:
                agent_type_from_class = "postseason_projection"
            
            # Create a test request
            request = AgentRequest(
                request_id=f"test_{int(time.time())}",
                agent_type=agent_type_from_class,
                action=capability_name,
                parameters={},
                user_context={"user_id": "diagnostic_tool"},
                timestamp=time.time(),
            )

            # Execute the request
            start_time = time.time()
            response = agent.execute_request(request, PermissionLevel.READ_EXECUTE)
            execution_time = time.time() - start_time

            success = response.status == AgentStatus.COMPLETED
            error_msg = response.error_message if response.error_message else ""

            return (
                success,
                f"Capability {capability_name}: {response.status.value}",
                {
                    "execution_time": execution_time,
                    "error": error_msg,
                    "result_keys": list(response.result.keys()) if response.result and isinstance(response.result, dict) else [],
                },
            )
        except Exception as e:
            return False, f"Execution error: {str(e)}", {"traceback": traceback.format_exc()}

    def test_all_agents(self):
        """Test all registered agents"""
        print("🔍 Agent Diagnostic Tool")
        print("=" * 80)
        print()

        # Get all registered agents
        agents = self.orchestrator.agent_factory.agents
        print(f"Found {len(agents)} registered agents\n")

        working_agents = []
        broken_agents = []
        partial_agents = []

        for agent_id, agent in agents.items():
            print(f"Testing: {agent_id}")
            print(f"  Type: {agent.__class__.__name__}")
            print(f"  Name: {agent.name}")

            # Test initialization
            init_ok, init_msg = self.test_agent_initialization(agent_id)
            print(f"  Initialization: {'✅' if init_ok else '❌'} {init_msg}")

            if not init_ok:
                broken_agents.append({
                    "agent_id": agent_id,
                    "agent_name": agent.name,
                    "agent_type": agent.__class__.__name__,
                    "status": "BROKEN",
                    "issue": init_msg,
                    "capabilities": [],
                })
                print()
                continue

            # Test each capability
            capability_results = []
            all_caps_work = True
            some_caps_work = False

            for cap in agent.capabilities:
                cap_ok, cap_msg, cap_data = self.test_agent_capability(agent_id, cap.name)
                capability_results.append({
                    "name": cap.name,
                    "status": "WORKING" if cap_ok else "BROKEN",
                    "message": cap_msg,
                    "data": cap_data,
                })
                if cap_ok:
                    some_caps_work = True
                else:
                    all_caps_work = False
                print(f"    Capability '{cap.name}': {'✅' if cap_ok else '❌'} {cap_msg}")

            # Categorize agent
            if all_caps_work:
                working_agents.append({
                    "agent_id": agent_id,
                    "agent_name": agent.name,
                    "agent_type": agent.__class__.__name__,
                    "status": "WORKING",
                    "capabilities": capability_results,
                })
            elif some_caps_work:
                partial_agents.append({
                    "agent_id": agent_id,
                    "agent_name": agent.name,
                    "agent_type": agent.__class__.__name__,
                    "status": "PARTIAL",
                    "capabilities": capability_results,
                })
            else:
                broken_agents.append({
                    "agent_id": agent_id,
                    "agent_name": agent.name,
                    "agent_type": agent.__class__.__name__,
                    "status": "BROKEN",
                    "capabilities": capability_results,
                })

            print()

        # Summary
        print("=" * 80)
        print("📊 DIAGNOSTIC SUMMARY")
        print("=" * 80)
        print()

        print(f"✅ WORKING AGENTS ({len(working_agents)}):")
        for agent in working_agents:
            print(f"  - {agent['agent_id']} ({agent['agent_name']})")
            print(f"    Type: {agent['agent_type']}")
            print(f"    Capabilities: {len([c for c in agent['capabilities'] if c['status'] == 'WORKING'])}/{len(agent['capabilities'])} working")
        print()

        if partial_agents:
            print(f"⚠️  PARTIAL AGENTS ({len(partial_agents)}):")
            for agent in partial_agents:
                print(f"  - {agent['agent_id']} ({agent['agent_name']})")
                print(f"    Type: {agent['agent_type']}")
                working_caps = [c for c in agent['capabilities'] if c['status'] == 'WORKING']
                broken_caps = [c for c in agent['capabilities'] if c['status'] == 'BROKEN']
                print(f"    Working: {[c['name'] for c in working_caps]}")
                print(f"    Broken: {[c['name'] for c in broken_caps]}")
            print()

        if broken_agents:
            print(f"❌ BROKEN AGENTS ({len(broken_agents)}):")
            for agent in broken_agents:
                print(f"  - {agent['agent_id']} ({agent['agent_name']})")
                print(f"    Type: {agent['agent_type']}")
                if 'issue' in agent:
                    print(f"    Issue: {agent['issue']}")
                else:
                    broken_caps = [c for c in agent['capabilities'] if c['status'] == 'BROKEN']
                    if broken_caps:
                        print(f"    Broken capabilities: {[c['name'] for c in broken_caps]}")
            print()

        # Save results
        results = {
            "timestamp": time.time(),
            "working": working_agents,
            "partial": partial_agents,
            "broken": broken_agents,
            "summary": {
                "total_agents": len(agents),
                "working": len(working_agents),
                "partial": len(partial_agents),
                "broken": len(broken_agents),
            },
        }

        output_file = REPO_ROOT / "agents" / "diagnostic_results.json"
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)

        print(f"📄 Detailed results saved to: {output_file}")
        print()

        return results


if __name__ == "__main__":
    diagnostic = AgentDiagnostic()
    results = diagnostic.test_all_agents()
    sys.exit(0 if results["summary"]["broken"] == 0 else 1)
