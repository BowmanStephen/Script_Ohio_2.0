"""
Week 12 Model Validation Agent (Backward Compatibility Wrapper)
Thin wrapper around WeeklyModelValidationAgent for Week 12
"""

from typing import Dict, Any
from agents.weekly_model_validation_agent import WeeklyModelValidationAgent
from agents.core.agent_framework import BaseAgent, AgentCapability, PermissionLevel


class Week12ModelValidationAgent(BaseAgent):
    """
    Backward compatibility wrapper for Week 12 model validation.
    Delegates to WeeklyModelValidationAgent with week=12.
    """

    def __init__(self, agent_id: str = "week12_model_validation_agent", tool_loader=None):
        # Create weekly agent first (before super().__init__ calls _define_capabilities)
        self._weekly_agent = WeeklyModelValidationAgent(week=12, season=2025, agent_id=agent_id, tool_loader=tool_loader)
        
        super().__init__(
            agent_id=agent_id,
            name="Week 12 Model Validation Agent",
            permission_level=PermissionLevel.READ_EXECUTE_WRITE,
            tool_loader=tool_loader,
        )
        self.agent_description = "Validates Week 12 ML models and data compatibility."

    def _define_capabilities(self):
        """Delegate capabilities to weekly agent"""
        return self._weekly_agent._define_capabilities()

    def _execute_action(self, action: str, parameters: Dict[str, Any],
                      user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Delegate action execution to weekly agent"""
        return self._weekly_agent._execute_action(action, parameters, user_context)

    def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Delegate task execution to weekly agent"""
        return self._weekly_agent.execute_task(task_data)


# Example usage
if __name__ == "__main__":
    agent = Week12ModelValidationAgent()

    task_data = {
        'operation': 'validate_models',
        'target_week': 12,
        'season': 2025,
        'validation_comprehensive': True
    }

    result = agent.execute_task(task_data)
    print(f"Model Validation Result: {result}")
