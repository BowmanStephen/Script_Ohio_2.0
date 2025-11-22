#!/usr/bin/env python3
"""
Meta-Orchestrator Agent for 2025 Football Analytics
Coordinates all specialized agents for comprehensive analysis
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from agents.core.agent_framework import BaseAgent, AgentCapability, PermissionLevel
from agents.core.context_manager import ContextManager, UserRole

class AnalyticsOrchestrator(BaseAgent):
    """
    Top-level orchestrator managing the entire football analytics workflow
    Coordinates all specialized agents for comprehensive analysis
    """
    
    def __init__(self, agent_id: str = "orchestrator_2025"):
        super().__init__(
            agent_id=agent_id,
            name="Analytics Orchestrator 2025",
            permission_level=PermissionLevel.ADMIN,
            description="Coordinates all football analytics agents for comprehensive reporting"
        )
        
        # Initialize context manager
        self.context_manager = ContextManager()
        
        # Initialize specialized agents
        self.agents = {}
        self.workflow_state = {
            "phase": "initialization",
            "agents_status": {},
            "data_timestamp": None,
            "analysis_timestamp": None,
            "completed_tasks": [],
            "errors": []
        }
        
    def _define_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                name="workflow_orchestration",
                description="Manages complete analytics workflow with specialized agents",
                required_tools=["file_management", "process_management", "json_export", "logging"]
            ),
            AgentCapability(
                name="quality_control",
                description="Ensures all agents meet quality standards and validates results"
            ),
            AgentCapability(
                name="output_synthesis",
                description="Compiles multi-agent results into comprehensive actionable reports"
            ),
            AgentCapability(
                name="optimization_monitoring",
                description="Monitors and optimizes agent performance and resource usage"
            )
        ]
    
    def execute_comprehensive_analysis(self, start_date: str = "2025-01-01") -> Dict[str, Any]:
        """
        Execute complete 2025 football analytics workflow
        """
        print("🚀 Starting Comprehensive 2025 Football Analytics Workflow")
        print("=" * 60)
        
        # Initialize workflow
        self.workflow_state = {
            "phase": "initialization",
            "agents_status": {},
            "data_timestamp": datetime.now().isoformat(),
            "analysis_timestamp": None,
            "completed_tasks": [],
            "errors": []
        }
        
        # Step 1: Data Acquisition
        print("\n📊 Step 1: Data Acquisition")
        print("-" * 40)
        try:
            from data_acquisition_agent import DataAcquisitionAgent
            data_agent = DataAcquisitionAgent()
            data_result = data_agent.acquire_2025_data()
            if not data_result["success"]:
                raise Exception(f"Data acquisition failed: {data_result['error']}")
            
            self.workflow_state["completed_tasks"].append("data_acquisition")
            print(f"✅ Data acquired successfully: {data_result['games_count']} games")
            
        except Exception as e:
            self.workflow_state["errors"].append(f"Data acquisition failed: {str(e)}")
            print(f"❌ Data acquisition failed: {e}")
            return {"success": False, "error": str(e)}
        
        # Step 2: Notebook Analysis
        print("\n📓 Step 2: Notebook Analysis")
        print("-" * 40)
        try:
            from notebook_analyzer_agent import NotebookAnalyzerAgent
            notebook_agent = NotebookAnalyzerAgent()
            notebook_results = notebook_agent.analyze_all_notebooks()
            self.workflow_state["completed_tasks"].append("notebook_analysis")
            print(f"✅ Notebook analysis completed: {len(notebook_results)} notebooks processed")
            
        except Exception as e:
            self.workflow_state["errors"].append(f"Notebook analysis failed: {str(e)}")
            print(f"❌ Notebook analysis failed: {e}")
            return {"success": False, "error": str(e)}
        
        # Step 3: Team Metrics Calculation
        print("\n🏈 Step 3: Team Metrics Calculation")
        print("-" * 40)
        try:
            from team_metrics_agent import TeamMetricsAgent
            metrics_agent = TeamMetricsAgent()
            metrics_result = metrics_agent.calculate_comprehensive_metrics()
            self.workflow_state["completed_tasks"].append("team_metrics")
            print(f"✅ Team metrics calculated: {len(metrics_result['team_metrics'])} teams")
            
        except Exception as e:
            self.workflow_state["errors"].append(f"Team metrics calculation failed: {str(e)}")
            print(f"❌ Team metrics calculation failed: {e}")
            return {"success": False, "error": str(e)}
        
        # Step 4: Power Rankings
        print("\n🏆 Step 4: Power Rankings Generation")
        print("-" * 40)
        try:
            from power_ranking_agent import PowerRankingAgent
            ranking_agent = PowerRankingAgent()
            rankings_result = ranking_agent.generate_power_rankings()
            self.workflow_state["completed_tasks"].append("power_rankings")
            print(f"✅ Power rankings generated: {len(rankings_result['rankings'])} ranked teams")
            
        except Exception as e:
            self.workflow_state["errors"].append(f"Power ranking generation failed: {str(e)}")
            print(f"❌ Power ranking generation failed: {e}")
            return {"success": False, "error": str(e)}
        
        # Step 5: Matchup Predictions
        print("\n🎯 Step 5: Matchup Predictions")
        print("-" * 40)
        try:
            from matchup_prediction_agent import MatchupPredictionAgent
            matchup_agent = MatchupPredictionAgent()
            matchup_result = matchup_agent.generate_matchup_predictions()
            self.workflow_state["completed_tasks"].append("matchup_predictions")
            print(f"✅ Matchup predictions generated: {len(matchup_result['predictions'])} matchups")
            
        except Exception as e:
            self.workflow_state["errors"].append(f"Matchup prediction failed: {str(e)}")
            print(f"❌ Matchup prediction failed: {e}")
            return {"success": False, "error": str(e)}
        
        # Step 6: Insight Generation
        print("\n💡 Step 6: Insight Generation")
        print("-" * 40)
        try:
            from insight_generator_agent import InsightGeneratorAgent
            insight_agent = InsightGeneratorAgent()
            insights_result = insight_agent.generate_actionable_insights()
            self.workflow_state["completed_tasks"].append("insight_generation")
            print(f"✅ Insights generated: {len(insights_result['insights'])} actionable insights")
            
        except Exception as e:
            self.workflow_state["errors"].append(f"Insight generation failed: {str(e)}")
            print(f"❌ Insight generation failed: {e}")
            return {"success": False, "error": str(e)}
        
        # Step 7: Report Compilation
        print("\n📝 Step 7: Report Compilation")
        print("-" * 40)
        try:
            from report_compiler_agent import ReportCompilerAgent
            report_agent = ReportCompilerAgent()
            report_result = report_agent.compile_comprehensive_report()
            self.workflow_state["completed_tasks"].append("report_compilation")
            print(f"✅ Report compiled: {report_result['filename']}")
            
        except Exception as e:
            self.workflow_state["errors"].append(f"Report compilation failed: {str(e)}")
            print(f"❌ Report compilation failed: {e}")
            return {"success": False, "error": str(e)}
        
        # Final workflow completion
        self.workflow_state["phase"] = "completed"
        self.workflow_state["analysis_timestamp"] = datetime.now().isoformat()
        
        print("\n🎉 Comprehensive Analysis Complete!")
        print("=" * 60)
        print(f"✅ Completed Tasks: {len(self.workflow_state['completed_tasks'])}/7")
        print(f"⚠️ Errors: {len(self.workflow_state['errors'])}")
        
        # Generate final summary
        summary = {
            "success": True,
            "workflow_state": self.workflow_state,
            "timestamp": datetime.now().isoformat(),
            "agents_status": {agent: "completed" for agent in self.agents.keys()},
            "output_files": [f"reports/comprehensive_2025_report_{datetime.now().strftime('%Y%m%d')}.md"]
        }
        
        return summary
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """Get current workflow status"""
        return {
            "phase": self.workflow_state["phase"],
            "completed_tasks": self.workflow_state["completed_tasks"],
            "errors": self.workflow_state["errors"],
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    orchestrator = AnalyticsOrchestrator()
    result = orchestrator.execute_comprehensive_analysis()
    print(json.dumps(result, indent=2))
