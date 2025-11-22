"""
Report Generator Agent.
Generates weekly analysis reports including SHAP values and interactive dashboards.
"""
import os
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd
import joblib

from agents.core.agent_framework import BaseAgent, AgentCapability, PermissionLevel
from src.visualization.shap_utils import generate_beeswarm_plot, generate_waterfall_plot
from src.visualization.dashboard import create_team_efficiency_dashboard, create_metric_distribution_explorer

logger = logging.getLogger(__name__)

class ReportGeneratorAgent(BaseAgent):
    """
    Agent responsible for generating comprehensive analytics reports.
    """
    
    def __init__(self, week: int, season: int = 2025, agent_id: Optional[str] = None):
        if agent_id is None:
            agent_id = f"report_generator_week{week}"
            
        super().__init__(
            agent_id=agent_id,
            name="Report Generator Agent",
            permission_level=PermissionLevel.READ_EXECUTE_WRITE,
        )
        self.week = week
        self.season = season
        self.output_dir = Path(f"analysis/week{week}")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _define_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                name="generate_weekly_report",
                description="Generate comprehensive weekly report with visualizations",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=["shap_utils", "dashboard_utils"],
                data_access=["analysis/", "model_pack/"],
                execution_time_estimate=20.0
            )
        ]

    def _execute_action(self, action: str, parameters: Dict[str, Any],
                       user_context: Dict[str, Any]) -> Dict[str, Any]:
        if action == "generate_weekly_report":
            return self.generate_weekly_report(parameters, user_context)
        else:
            raise ValueError(f"Unknown action: {action}")

    def execute_task(self, parameters: Dict[str, Any], user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute the primary task of this agent (generating reports)."""
        return self.generate_weekly_report(parameters, user_context or {})

    def generate_weekly_report(self, parameters: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate the weekly report."""
        logger.info(f"Generating weekly report for Week {self.week}")
        generated_files = []
        
        try:
            # 1. Load Data
            stats_path = parameters.get('stats_path')
            data = None
            if stats_path and os.path.exists(stats_path):
                try:
                    data = pd.read_csv(stats_path)
                    logger.info(f"Loaded data from {stats_path}")
                except Exception as e:
                    logger.warning(f"Failed to load stats from {stats_path}: {e}")
            
            # 2. Generate Dashboard
            if data is not None and not data.empty:
                try:
                    # Check for required columns for dashboard
                    if 'offense_ppa' in data.columns and 'defense_ppa' in data.columns:
                        dashboard = create_team_efficiency_dashboard(data)
                        dashboard_path = self.output_dir / "team_efficiency_dashboard.html"
                        dashboard.write_html(str(dashboard_path))
                        generated_files.append(str(dashboard_path))
                        logger.info(f"Generated dashboard: {dashboard_path}")
                except Exception as e:
                    logger.error(f"Dashboard generation failed: {e}")
            
            # 3. Compile HTML report
            report_path = self.output_dir / f"week{self.week}_comprehensive_report.html"
            with open(report_path, "w") as f:
                f.write(f"<html><head><title>Week {self.week} Analysis</title></head><body>")
                f.write(f"<h1>Week {self.week} Analysis Report</h1>")
                f.write("<p>Report generated automatically.</p>")
                
                if generated_files:
                    f.write("<h2>Generated Visualizations</h2><ul>")
                    for file in generated_files:
                        if file != str(report_path):
                            rel_path = os.path.basename(file)
                            f.write(f"<li><a href='{rel_path}'>{rel_path}</a></li>")
                    f.write("</ul>")
                
                f.write("</body></html>")
                
            generated_files.append(str(report_path))
            
            return {
                "status": "success",
                "generated_files": generated_files
            }
            
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
