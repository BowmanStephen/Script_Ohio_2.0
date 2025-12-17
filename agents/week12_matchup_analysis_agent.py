"""
Week 12 Matchup Analysis Agent (Backward Compatibility Wrapper)
Thin wrapper around WeeklyMatchupAnalysisAgent for Week 12
"""

from typing import Dict, Any
from agents.weekly_matchup_analysis_agent import WeeklyMatchupAnalysisAgent
from agents.core.agent_framework import BaseAgent, AgentCapability, PermissionLevel


class Week12MatchupAnalysisAgent(BaseAgent):
    """
    Backward compatibility wrapper for Week 12 matchup analysis.
    Delegates to WeeklyMatchupAnalysisAgent with week=12.
    """

    def __init__(self, agent_id: str = "week12_matchup_analysis", tool_loader=None):
        # Create weekly agent first (before super().__init__ calls _define_capabilities)
        self._weekly_agent = WeeklyMatchupAnalysisAgent(week=12, season=2025, agent_id=agent_id)
        
        super().__init__(
            agent_id=agent_id,
            name="Week 12 Matchup Analysis Agent",
            permission_level=PermissionLevel.READ_EXECUTE_WRITE,
            tool_loader=tool_loader,
        )
        self.agent_description = "Analyzes Week 12 matchups and produces strategic insights."

        # Delegate missing attributes to wrapped agent for compatibility
        self.role = getattr(self._weekly_agent, 'role', "Matchup Analysis Specialist")
        self.context_manager = getattr(self._weekly_agent, 'context_manager', None)
        self.analysis_weights = getattr(self._weekly_agent, 'analysis_weights', {})
        self.permissions = getattr(self._weekly_agent, 'permissions', ["READ_WRITE"])
        self.tools = getattr(self._weekly_agent, 'tools', ["data_analyzer"])

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

    def _load_week12_matchups(self):
        """Load Week 12 matchups data"""
        import pandas as pd
        # This will be mocked in tests to return sample data
        return pd.read_csv("data/week12_matchups.csv")


# Example usage
if __name__ == "__main__":
    agent = Week12MatchupAnalysisAgent()

    task_data = {
        'operation': 'analyze_matchups',
        'target_week': 12,
        'season': 2025,
        'analysis_depth': 'comprehensive'
    }

    result = agent.execute_task(task_data)
    print(f"Matchup Analysis Result: {result}")
