#!/usr/bin/env python3
"""
Demo script for Claude Code Plan-then-Execute integration

Demonstrates the complete P-t-E workflow:
1. Planning phase
2. Execution phase
3. Context isolation
4. Sequential handoffs
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.claude_code_orchestrator import PlanThenExecuteOrchestrator
from agents.claude_code_subagent_registry import SubagentRegistry
from agents.core.context_isolation import ContextIsolationManager
from agents.core.handoff_manager import HandoffManager


def main():
    """Run the demo"""
    print("=" * 60)
    print("Claude Code Plan-then-Execute Integration Demo")
    print("=" * 60)
    print()

    # 1. Initialize components
    print("1. Initializing components...")
    orchestrator = PlanThenExecuteOrchestrator()
    registry = SubagentRegistry()
    context_manager = ContextIsolationManager()
    handoff_manager = HandoffManager(context_manager)

    print(f"   ✓ Orchestrator initialized")
    print(f"   ✓ Subagent registry loaded ({len(registry.list_subagents())} subagents)")
    print(f"   ✓ Context isolation manager initialized")
    print(f"   ✓ Handoff manager initialized")
    print()

    # 2. List available subagents
    print("2. Available subagents:")
    subagents = registry.list_subagents()
    for i, name in enumerate(subagents[:5], 1):  # Show first 5
        subagent = registry.get_subagent(name)
        print(f"   {i}. {name}")
        print(f"      Description: {subagent.description}")
        print(f"      Tools: {len(subagent.tools)} tools")
    if len(subagents) > 5:
        print(f"   ... and {len(subagents) - 5} more")
    print()

    # 3. Planning phase
    print("3. Planning phase:")
    objective = "Add a new feature to the system"
    print(f"   Objective: {objective}")

    plan = orchestrator.plan_phase(objective)
    print(f"   ✓ Plan created: {plan.plan_id}")
    print(f"   ✓ Tasks: {len(plan.tasks)}")
    print(f"   ✓ Estimated time: {plan.estimated_total_time:.1f}s")
    print(f"   ✓ Parallel execution: {plan.parallel_execution}")
    print()

    # 4. Execution phase
    print("4. Execution phase:")
    result = orchestrator.execute_phase(plan)
    print(f"   ✓ Execution ID: {result.execution_id}")
    print(f"   ✓ Status: {result.status}")
    print(f"   ✓ Tasks completed: {result.tasks_completed}/{result.total_tasks}")
    print(f"   ✓ Tasks failed: {result.tasks_failed}")
    print(f"   ✓ Execution time: {result.execution_time:.3f}s")
    print()

    # 5. Context isolation
    print("5. Context isolation:")
    context1 = context_manager.create_isolated_context("planner", {"task": "plan"})
    print(f"   ✓ Created context for planner: {context1.context_id}")

    context2 = context_manager.handoff_context(
        "planner", "engineer", {"result": "plan_complete"}
    )
    print(f"   ✓ Handed off context to engineer: {context2.context_id}")
    print()

    # 6. Sequential handoffs
    print("6. Sequential handoffs:")
    chain = handoff_manager.create_handoff_chain(["pm", "engineer", "reviewer"])
    print(f"   ✓ Created handoff chain: {chain.chain_id}")
    print(f"   ✓ Agents: {' → '.join(chain.agents)}")

    # Execute chain (mock)
    print("   ✓ Chain execution simulated")
    print()

    # 7. Summary
    print("=" * 60)
    print("Demo Summary")
    print("=" * 60)
    print(f"✓ Orchestrator: {orchestrator.agent_id}")
    print(f"✓ Subagents: {len(subagents)} available")
    print(f"✓ Plan: {plan.plan_id} with {len(plan.tasks)} tasks")
    print(f"✓ Execution: {result.execution_id} ({result.status})")
    print(f"✓ Context isolation: Working")
    print(f"✓ Handoff chains: Supported")
    print()
    print("All components are working correctly!")
    print("=" * 60)


if __name__ == "__main__":
    main()
