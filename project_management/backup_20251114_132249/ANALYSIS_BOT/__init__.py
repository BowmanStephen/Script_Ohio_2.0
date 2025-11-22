"""
Analysis Bot Package
Multi-agent football analytics system for comprehensive analysis
"""

from .agents.orchestrator_agent import AnalyticsOrchestrator
from .agents.data_acquisition_agent import DataAcquisitionAgent
from .agents.notebook_analyzer_agent import NotebookAnalyzerAgent
from .agents.team_metrics_agent import TeamMetricsAgent
from .agents.power_ranking_agent import PowerRankingAgent
from .agents.matchup_prediction_agent import MatchupPredictionAgent
from .agents.insight_generator_agent import InsightGeneratorAgent
from .agents.report_compiler_agent import ReportCompilerAgent

__version__ = "1.0.0"
__all__ = [
    "AnalyticsOrchestrator",
    "DataAcquisitionAgent", 
    "NotebookAnalyzerAgent",
    "TeamMetricsAgent",
    "PowerRankingAgent",
    "MatchupPredictionAgent",
    "InsightGeneratorAgent",
    "ReportCompilerAgent"
]
