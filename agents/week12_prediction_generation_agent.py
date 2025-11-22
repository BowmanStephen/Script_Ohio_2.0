"""
Week 12 Prediction Generation Agent (Backward Compatibility Wrapper)
Thin wrapper around WeeklyPredictionGenerationAgent for Week 12
"""

from typing import Dict, Any
from agents.weekly_prediction_generation_agent import WeeklyPredictionGenerationAgent
from agents.core.agent_framework import BaseAgent, AgentCapability, PermissionLevel


class Week12PredictionGenerationAgent(BaseAgent):
    """
    Backward compatibility wrapper for Week 12 prediction generation.
    Delegates to WeeklyPredictionGenerationAgent with week=12.
    """

    def __init__(self, agent_id: str = "week12_prediction_generation_agent",
                 name: str = "Week12PredictionGenerationAgent", tool_loader=None):
        # Create weekly agent first (before super().__init__ calls _define_capabilities)
        self._weekly_agent = WeeklyPredictionGenerationAgent(week=12, season=2025, agent_id=agent_id, name=name, tool_loader=tool_loader)
        
        permission_level = PermissionLevel.READ_EXECUTE_WRITE
        super().__init__(agent_id, name, permission_level, tool_loader)

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
    agent = Week12PredictionGenerationAgent()

    task_data = {
        'operation': 'generate_predictions',
        'target_week': 12,
        'season': 2025,
        'use_ensemble': True,
        'generate_explanations': True
    }

    result = agent.execute_task(task_data)
    print(f"Prediction Generation Result: {result}")
