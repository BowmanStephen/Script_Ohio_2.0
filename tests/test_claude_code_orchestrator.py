"""
Tests for Claude Code Plan-then-Execute Orchestrator
"""

import pytest
from agents.claude_code_orchestrator import PlanThenExecuteOrchestrator


class TestPlanThenExecuteOrchestrator:
    """Test suite for PlanThenExecuteOrchestrator"""

    def setup_method(self):
        """Set up test fixtures"""
        self.orchestrator = PlanThenExecuteOrchestrator()

    def test_orchestrator_initialization(self):
        """Test orchestrator initialization"""
        assert self.orchestrator.agent_id == "claude_code_orchestrator"
        assert self.orchestrator.subagent_registry is not None
        assert self.orchestrator.plan_generator is not None
        assert self.orchestrator.task_delegator is not None

    def test_plan_phase(self):
        """Test planning phase"""
        objective = "Add feature X"
        plan = self.orchestrator.plan_phase(objective)

        assert plan is not None
        assert plan.objective == objective
        assert len(plan.tasks) > 0
        assert plan.plan_id is not None

    def test_plan_validation(self):
        """Test plan validation"""
        plan = self.orchestrator.plan_phase("Test objective")
        errors = plan.validate()

        assert isinstance(errors, list)
        # Plan should be valid
        assert len(errors) == 0

    def test_execute_phase(self):
        """Test execution phase"""
        plan = self.orchestrator.plan_phase("Test execution")
        result = self.orchestrator.execute_phase(plan)

        assert result is not None
        assert result.execution_id is not None
        assert result.plan_id == plan.plan_id
        assert result.status in ["success", "failed", "partial"]

    def test_plan_and_execute(self):
        """Test complete plan-and-execute workflow"""
        result = self.orchestrator._plan_and_execute(
            {"objective": "Test complete workflow"}, {}
        )

        assert result is not None
        assert "plan" in result
        assert "execution" in result

    def test_capabilities(self):
        """Test orchestrator capabilities"""
        capabilities = self.orchestrator._define_capabilities()

        assert len(capabilities) > 0
        capability_names = [cap.name for cap in capabilities]
        assert "plan_phase" in capability_names
        assert "execute_phase" in capability_names
        assert "plan_and_execute" in capability_names
