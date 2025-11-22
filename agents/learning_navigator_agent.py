#!/usr/bin/env python3
"""
Learning Navigator Agent - Educational Guidance and Learning Path Navigation

This agent provides educational guidance and learning path navigation for users
who want to learn about college football analytics through the starter_pack notebooks.

Author: Claude Code Assistant
Created: 2025-11-10
Version: 1.0
"""

import os
import time
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

from agents.core.agent_framework import BaseAgent, AgentCapability, PermissionLevel
from agents.core.context_manager import UserRole

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LearningNavigatorAgent(BaseAgent):
    """
    Agent responsible for providing educational guidance and learning path navigation
    for users exploring college football analytics through the starter_pack notebooks.
    """

    def __init__(self, agent_id: str, tool_loader=None):
        super().__init__(
            agent_id=agent_id,
            name="Learning Navigator",
            permission_level=PermissionLevel.READ_EXECUTE,
            tool_loader=tool_loader
        )

        # Learning paths for different user types
        self.learning_paths = {
            UserRole.ANALYST: self._get_analyst_learning_path(),
            UserRole.DATA_SCIENTIST: self._get_data_scientist_learning_path(),
            UserRole.PRODUCTION: self._get_production_learning_path()
        }

        # Notebook metadata cache
        self.notebook_metadata = None
        self._load_notebook_metadata()

    def _define_capabilities(self) -> List[AgentCapability]:
        """Define agent capabilities"""
        return [
            AgentCapability(
                name="guide_learning_path",
                description="Provide learning path guidance based on user skill level",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["load_notebook_metadata", "get_learning_recommendations"],
                data_access=["starter_pack/"],
                execution_time_estimate=2.0
            ),
            AgentCapability(
                name="explain_concepts",
                description="Explain analytics concepts and terminology",
                permission_required=PermissionLevel.READ_ONLY,
                tools_required=[],
                data_access=["starter_pack/"],
                execution_time_estimate=1.0
            ),
            AgentCapability(
                name="recommend_resources",
                description="Recommend additional learning resources",
                permission_required=PermissionLevel.READ_ONLY,
                tools_required=["get_learning_recommendations"],
                data_access=[],
                execution_time_estimate=1.5
            ),
            AgentCapability(
                name="recommend_content",
                description="Recommend learning content and resources",
                permission_required=PermissionLevel.READ_ONLY,
                tools_required=["get_learning_recommendations"],
                data_access=["starter_pack/"],
                execution_time_estimate=1.5
            ),
            AgentCapability(
                name="track_progress",
                description="Track user progress through learning path",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=["load_notebook_metadata"],
                data_access=["starter_pack/"],
                execution_time_estimate=1.0
            ),
            AgentCapability(
                name="bridge_to_model_pack",
                description="Guide users from starter pack concepts to model pack ML features",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["load_notebook_metadata"],
                data_access=["starter_pack/*", "model_pack/updated_training_data.csv", "data/training/weekly/training_data_2025_week*.csv"],
                execution_time_estimate=3.0
            )
        ]

    def _execute_action(self, action: str, parameters: Dict[str, Any],
                       user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent-specific actions"""
        try:
            if action == "guide_learning_path":
                return self._guide_learning_path(parameters, user_context)
            elif action == "explain_concepts":
                return self._explain_concepts(parameters, user_context)
            elif action == "recommend_resources" or action == "recommend_content":
                return self._recommend_resources(parameters, user_context)
            elif action == "track_progress":
                return self._track_progress(parameters, user_context)
            elif action == "bridge_to_model_pack":
                return self._bridge_to_model_pack(parameters, user_context)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}",
                    "error_type": "unknown_action"
                }
        except Exception as e:
            logger.error(f"Error executing action {action}: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "execution_error"
            }

    def _guide_learning_path(self, parameters: Dict[str, Any],
                           user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Provide learning path guidance"""

        # Determine user role and current position
        user_role = user_context.get('detected_role', UserRole.ANALYST)
        current_notebook = parameters.get('current_notebook', None)
        skill_level = parameters.get('skill_level', 'beginner')

        # Get appropriate learning path
        learning_path = self.learning_paths.get(user_role, self.learning_paths[UserRole.ANALYST])

        # Find current position in path
        current_position = 0
        if current_notebook and current_notebook != 'start':
            for i, notebook in enumerate(learning_path):
                if notebook.get('filename', '') == current_notebook:
                    current_position = i
                    break

        # Get current and next notebooks
        current_notebook_info = learning_path[current_position] if current_position < len(learning_path) else None
        next_notebook_info = learning_path[current_position + 1] if current_position + 1 < len(learning_path) else None

        # Generate learning recommendations
        recommendations = self._generate_learning_recommendations(
            current_position, learning_path, skill_level
        )

        return {
            "success": True,
            "user_role": user_role.value if hasattr(user_role, 'value') else str(user_role),
            "current_position": current_position,
            "total_notebooks": len(learning_path),
            "current_notebook": current_notebook_info,
            "next_notebook": next_notebook_info,
            "learning_path": learning_path[:5],  # Return next 5 notebooks
            "recommendations": recommendations,
            "progress_percentage": (current_position / len(learning_path)) * 100 if learning_path else 0
        }

    def _explain_concepts(self, parameters: Dict[str, Any],
                         user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Explain analytics concepts"""

        concepts = parameters.get('concepts', [])
        skill_level = user_context.get('skill_level', 'beginner')

        explanations = {}
        for concept in concepts:
            explanations[concept] = self._get_concept_explanation(concept, skill_level)

        return {
            "success": True,
            "concepts_explained": list(explanations.keys()),
            "explanations": explanations,
            "skill_level": skill_level
        }

    def _recommend_resources(self, parameters: Dict[str, Any],
                           user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Recommend additional learning resources"""

        user_role = user_context.get('detected_role', UserRole.ANALYST)
        current_topic = parameters.get('topic', '')
        skill_level = user_context.get('skill_level', 'beginner')

        resources = self._get_learning_resources(user_role, current_topic, skill_level)

        return {
            "success": True,
            "resources": resources,
            "user_role": user_role.value if hasattr(user_role, 'value') else str(user_role),
            "current_topic": current_topic
        }

    def _track_progress(self, parameters: Dict[str, Any],
                       user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Track user progress through learning path"""

        completed_notebooks = parameters.get('completed_notebooks', [])
        current_notebook = parameters.get('current_notebook', None)

        # Calculate progress metrics
        total_notebooks = len(self.learning_paths.get(UserRole.ANALYST, []))
        completed_count = len(completed_notebooks)
        progress_percentage = (completed_count / total_notebooks) * 100 if total_notebooks > 0 else 0

        # Identify next steps
        next_steps = self._get_next_steps(completed_notebooks, current_notebook)

        return {
            "success": True,
            "completed_notebooks": completed_notebooks,
            "total_notebooks": total_notebooks,
            "completed_count": completed_count,
            "progress_percentage": progress_percentage,
            "next_steps": next_steps,
            "achievement_badges": self._get_achievement_badges(completed_count)
        }

    def _get_analyst_learning_path(self) -> List[Dict[str, Any]]:
        """Get learning path for analyst role"""
        return [
            {
                "title": "Introduction to College Football Data",
                "filename": "01_intro_to_data.ipynb",
                "description": "Learn about available datasets and basic data exploration",
                "estimated_time": "45 minutes",
                "difficulty": "beginner",
                "concepts": ["data exploration", "CSV files", "basic statistics"]
            },
            {
                "title": "Building Simple Rankings",
                "filename": "02_build_simple_rankings.ipynb",
                "description": "Create your first team ranking system",
                "estimated_time": "60 minutes",
                "difficulty": "beginner",
                "concepts": ["rankings", "win-loss records", "strength of schedule"]
            },
            {
                "title": "Team Performance Metrics",
                "filename": "03_metrics_comparison.ipynb",
                "description": "Compare teams using advanced metrics",
                "estimated_time": "75 minutes",
                "difficulty": "intermediate",
                "concepts": ["efficiency metrics", "comparative analysis", "visualization"]
            },
            {
                "title": "Conference Analysis",
                "filename": "04_conference_analysis.ipynb",
                "description": "Analyze conference strength and performance",
                "estimated_time": "90 minutes",
                "difficulty": "intermediate",
                "concepts": ["conference analysis", "statistical comparisons", "data grouping"]
            },
            {
                "title": "Historical Trends",
                "filename": "05_historical_trends.ipynb",
                "description": "Explore historical trends in college football",
                "estimated_time": "120 minutes",
                "difficulty": "intermediate",
                "concepts": ["time series analysis", "historical data", "trend identification"]
            },
            {
                "title": "Season Summaries",
                "filename": "06_season_summaries.ipynb",
                "description": "Create comprehensive season summaries",
                "estimated_time": "90 minutes",
                "difficulty": "intermediate",
                "concepts": ["season analysis", "data aggregation", "report generation"]
            },
            {
                "title": "Team vs Team Matchups",
                "filename": "07_team_vs_team_matchups.ipynb",
                "description": "Analyze head-to-head matchups",
                "estimated_time": "75 minutes",
                "difficulty": "intermediate",
                "concepts": ["matchup analysis", "head-to-head statistics", "comparative metrics"]
            },
            {
                "title": "Advanced Visualizations",
                "filename": "08_advanced_visualizations.ipynb",
                "description": "Create advanced data visualizations",
                "estimated_time": "105 minutes",
                "difficulty": "advanced",
                "concepts": ["advanced plotting", "interactive visualizations", "data storytelling"]
            },
            {
                "title": "Efficiency Dashboards",
                "filename": "09_efficiency_dashboards.ipynb",
                "description": "Build interactive efficiency dashboards",
                "estimated_time": "120 minutes",
                "difficulty": "advanced",
                "concepts": ["dashboard creation", "interactive widgets", "real-time updates"]
            },
            {
                "title": "Conference Championship Analysis",
                "filename": "10_conference_championship_analysis.ipynb",
                "description": "Analyze conference championship scenarios",
                "estimated_time": "90 minutes",
                "difficulty": "advanced",
                "concepts": ["championship scenarios", "tie-breaking rules", "predictive modeling"]
            },
            {
                "title": "Bowl Season Predictions",
                "filename": "11_bowl_season_predictions.ipynb",
                "description": "Make bowl season predictions",
                "estimated_time": "105 minutes",
                "difficulty": "advanced",
                "concepts": ["prediction modeling", "bowl projections", "team selection"]
            },
            {
                "title": "Efficiency Dashboards",
                "filename": "12_efficiency_dashboards.ipynb",
                "description": "Create comprehensive efficiency dashboards",
                "estimated_time": "120 minutes",
                "difficulty": "advanced",
                "concepts": ["comprehensive dashboards", "advanced metrics", "performance tracking"]
            }
        ]

    def _get_data_scientist_learning_path(self) -> List[Dict[str, Any]]:
        """Get learning path for data scientist role"""
        # Similar structure but focused on model_pack notebooks
        return [
            {
                "title": "Linear Regression for Score Prediction",
                "filename": "01_linear_regression_margin.ipynb",
                "description": "Use linear regression to predict score margins",
                "estimated_time": "90 minutes",
                "difficulty": "intermediate",
                "concepts": ["linear regression", "feature engineering", "model evaluation"]
            },
            # ... more model_pack notebooks
        ]

    def _get_production_learning_path(self) -> List[Dict[str, Any]]:
        """Get learning path for production role"""
        return [
            {
                "title": "Quick Start Guide",
                "filename": "quick_start_production.ipynb",
                "description": "Quick start for production users",
                "estimated_time": "30 minutes",
                "difficulty": "beginner",
                "concepts": ["production setup", "model usage", "quick predictions"]
            }
        ]

    def _load_notebook_metadata(self):
        """Load metadata for all notebooks"""
        # In a full implementation, this would scan starter_pack and model_pack directories
        # and load metadata from all notebooks
        self.notebook_metadata = {
            "starter_pack": {
                "total_notebooks": 12,
                "topics": ["data exploration", "rankings", "metrics", "visualization"],
                "difficulty_levels": ["beginner", "intermediate", "advanced"]
            },
            "model_pack": {
                "total_notebooks": 7,
                "topics": ["machine learning", "prediction", "feature engineering"],
                "difficulty_levels": ["intermediate", "advanced"]
            }
        }

    def _generate_learning_recommendations(self, current_position: int,
                                         learning_path: List[Dict[str, Any]],
                                         skill_level: str) -> List[str]:
        """Generate learning recommendations based on current position"""
        recommendations = []

        if current_position == 0:
            recommendations.append("Start with the introduction notebook to understand the data structure")
        elif current_position < len(learning_path) // 3:
            recommendations.append("Focus on understanding basic concepts before moving to advanced topics")
        elif current_position < 2 * len(learning_path) // 3:
            recommendations.append("You're making good progress! Try applying concepts to your own questions")
        else:
            recommendations.append("Advanced topics ahead! Consider exploring model_pack for ML techniques")

        return recommendations

    def _get_concept_explanation(self, concept: str, skill_level: str) -> Dict[str, Any]:
        """Get explanation for a specific concept"""
        explanations = {
            "EPA": {
                "title": "Expected Points Added (EPA)",
                "simple": "EPA measures how many points a team is expected to score on a given play",
                "detailed": "EPA is a metric that quantifies the value of each play by comparing the expected points before and after the play",
                "example": "A 10-yard gain on 1st & 10 might have an EPA of +1.2, while a turnover might have an EPA of -3.5"
            },
            "Success Rate": {
                "title": "Success Rate",
                "simple": "Success rate measures whether a play achieved its goal",
                "detailed": "Success rate is a metric that evaluates whether a play gained enough yards to be considered successful based on down and distance",
                "example": "On 1st & 10, a gain of 4+ yards is considered successful. On 2nd & 8, a gain of 6+ yards is successful."
            }
        }

        return explanations.get(concept, {
            "title": concept,
            "simple": f"Concept explanation for {concept}",
            "detailed": f"Detailed explanation of {concept} for {skill_level} level",
            "example": "Example usage of this concept in college football analytics"
        })

    def _get_learning_resources(self, user_role: UserRole, current_topic: str,
                              skill_level: str) -> List[Dict[str, Any]]:
        """Get recommended learning resources"""
        resources = [
            {
                "type": "documentation",
                "title": "CollegeFootballData.com API Documentation",
                "url": "https://collegefootballdata.com/",
                "description": "Comprehensive API documentation for college football data",
                "difficulty": "intermediate"
            },
            {
                "type": "book",
                "title": "Mathletics",
                "author": "Wayne Winston",
                "description": "Introduction to sports analytics",
                "difficulty": "beginner"
            },
            {
                "type": "website",
                "title": "Sports Analytics Blog",
                "url": "https://www.sportsanalyticsblog.com/",
                "description": "Regular articles on sports analytics topics",
                "difficulty": "intermediate"
            }
        ]

        return resources

    def _get_next_steps(self, completed_notebooks: List[str],
                       current_notebook: Optional[str]) -> List[str]:
        """Get next learning steps"""
        steps = []

        if not completed_notebooks:
            steps.append("Start with '01_intro_to_data.ipynb' to understand the data structure")

        if len(completed_notebooks) >= 3:
            steps.append("Consider exploring some model_pack notebooks for ML techniques")

        if current_notebook and current_notebook.endswith("visualization.ipynb"):
            steps.append("Try creating your own visualizations with different datasets")

        return steps

    def _get_achievement_badges(self, completed_count: int) -> List[Dict[str, Any]]:
        """Get achievement badges based on progress"""
        badges = []

        if completed_count >= 1:
            badges.append({"name": "Getting Started", "icon": "🚀", "description": "Completed first notebook"})

        if completed_count >= 3:
            badges.append({"name": "Data Explorer", "icon": "🔍", "description": "Completed 3 notebooks"})

        if completed_count >= 6:
            badges.append({"name": "Analytics Apprentice", "icon": "📊", "description": "Completed 6 notebooks"})

        if completed_count >= 12:
            badges.append({"name": "Analytics Expert", "icon": "🏆", "description": "Completed all starter notebooks"})

        return badges

    def _bridge_to_model_pack(self, parameters: Dict[str, Any],
                             user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Provide personalized bridge guidance from starter pack to model pack"""
        
        current_notebook = parameters.get("current_notebook", None)
        skill_level = user_context.get('skill_level', 'beginner')
        user_role = user_context.get('detected_role', UserRole.ANALYST)
        
        # Map starter pack notebooks to model pack features and notebooks
        notebook_bridge_map = {
            "05_matchup_predictor.ipynb": {
                "starter_concepts": ["basic prediction", "logistic regression", "feature selection"],
                "model_pack_next": "01_linear_regression_margin.ipynb",
                "feature_connections": {
                    "home_offense_ppa": "home_adjusted_epa",
                    "away_defense_ppa": "away_adjusted_epa_allowed",
                    "successRate_diff": ["home_adjusted_success", "away_adjusted_success"],
                    "ppa_diff": "home_adjusted_epa - away_adjusted_epa_allowed"
                },
                "weekly_data_example": "data/training/weekly/training_data_2025_week01.csv",
                "key_features_to_explore": [
                    "home_adjusted_epa", "away_adjusted_epa",
                    "home_adjusted_success", "away_adjusted_success",
                    "home_elo", "away_elo", "spread"
                ],
                "bridge_steps": [
                    "Load weekly training data to see how basic stats become opponent-adjusted features",
                    "Compare your simple features to the 86-feature ML dataset",
                    "Try the linear regression model in model_pack/01_linear_regression_margin.ipynb"
                ],
                "estimated_time": "30-45 minutes"
            },
            "09_opponent_adjustments.ipynb": {
                "starter_concepts": ["opponent adjustments", "schedule strength", "adjusted metrics"],
                "model_pack_next": "03_xgboost_win_probability.ipynb",
                "feature_connections": {
                    "adj_offense_ppa": "home_adjusted_epa",
                    "adj_defense_ppa": "home_adjusted_epa_allowed",
                    "All adjusted metrics": "86 opponent-adjusted features in training data"
                },
                "weekly_data_example": "data/training/weekly/training_data_2025_week05.csv",
                "key_features_to_explore": [
                    "home_adjusted_epa", "away_adjusted_epa",
                    "home_adjusted_rushing_epa", "home_adjusted_passing_epa",
                    "home_adjusted_explosiveness", "home_adjusted_line_yards",
                    "home_total_havoc_defense", "away_total_havoc_offense"
                ],
                "bridge_steps": [
                    "See how opponent adjustments create all 86 ML features",
                    "Explore weekly training data (Week 5+) for temporal validation",
                    "Try XGBoost model using these adjusted features"
                ],
                "estimated_time": "45-60 minutes"
            },
            "10_srs_adjusted_metrics.ipynb": {
                "starter_concepts": ["SRS adjustments", "strength of schedule", "rating systems"],
                "model_pack_next": "06_shap_interpretability.ipynb",
                "feature_connections": {
                    "SRS ratings": "home_elo, away_elo, home_talent, away_talent",
                    "Strength adjustments": "All opponent-adjusted features"
                },
                "weekly_data_example": "data/training/weekly/training_data_2025_week05.csv",
                "key_features_to_explore": [
                    "home_elo", "away_elo", "home_talent", "away_talent",
                    "spread", "margin"
                ],
                "bridge_steps": [
                    "Understand how SRS concepts feed into Elo and talent ratings",
                    "See feature importance in trained models",
                    "Explore SHAP values to understand model decisions"
                ],
                "estimated_time": "60-90 minutes"
            }
        }
        
        # Get bridge guidance for current notebook or provide general guidance
        if current_notebook and current_notebook in notebook_bridge_map:
            bridge_info = notebook_bridge_map[current_notebook]
        else:
            # General bridge guidance
            bridge_info = {
                "starter_concepts": ["analytics fundamentals"],
                "model_pack_next": "01_linear_regression_margin.ipynb",
                "feature_connections": {
                    "All starter pack metrics": "86 opponent-adjusted features"
                },
                "weekly_data_example": "data/training/weekly/training_data_2025_week01.csv",
                "key_features_to_explore": [
                    "home_adjusted_epa", "away_adjusted_epa",
                    "home_adjusted_success", "away_adjusted_success"
                ],
                "bridge_steps": [
                    "Explore weekly training data to see the 86-feature format",
                    "Understand how starter pack concepts become ML features",
                    "Start with linear regression model in model_pack"
                ],
                "estimated_time": "45-60 minutes"
            }
        
        # Load weekly training data preview if available
        weekly_data_preview = self._preview_weekly_training_data(bridge_info.get("weekly_data_example"))
        
        return {
            "success": True,
            "current_notebook": current_notebook,
            "bridge_info": bridge_info,
            "weekly_data_preview": weekly_data_preview,
            "next_steps": {
                "model_pack_notebook": bridge_info["model_pack_next"],
                "weekly_data_file": bridge_info["weekly_data_example"],
                "features_to_explore": bridge_info["key_features_to_explore"],
                "estimated_time": bridge_info["estimated_time"]
            },
            "agent_usage_example": {
                "python_code": """
from agents.analytics_orchestrator import AnalyticsOrchestrator, AnalyticsRequest

orchestrator = AnalyticsOrchestrator()
request = AnalyticsRequest(
    user_id='your_id',
    query='Bridge me from {current_notebook} to model pack',
    query_type='learning',
    parameters={{'current_notebook': '{current_notebook}'}},
    context_hints={{'role': 'data_scientist', 'skill_level': '{skill_level}'}}
)
response = orchestrator.process_analytics_request(request)
print(response.insights)
""".format(current_notebook=current_notebook or "starter_pack", skill_level=skill_level)
            }
        }
    
    def _preview_weekly_training_data(self, weekly_file_path: str) -> Dict[str, Any]:
        """Preview weekly training data file structure"""
        try:
            import pandas as pd
            from pathlib import Path
            
            # Resolve path relative to project root
            project_root = Path(__file__).resolve().parent.parent
            weekly_file = project_root / weekly_file_path.lstrip("../")
            
            if weekly_file.exists():
                df = pd.read_csv(weekly_file, nrows=3)  # Read first 3 rows for preview
                
                # Categorize features
                feature_categories = {
                    "basic_game_info": [c for c in df.columns if c in ["id", "season", "week", "home_team", "away_team", "neutral_site"]],
                    "strength_metrics": [c for c in df.columns if "elo" in c.lower() or "talent" in c.lower()],
                    "adjusted_epa": [c for c in df.columns if "adjusted_epa" in c],
                    "adjusted_success": [c for c in df.columns if "adjusted_success" in c and "allowed" not in c],
                    "adjusted_explosiveness": [c for c in df.columns if "adjusted" in c and "explosiveness" in c],
                    "havoc_metrics": [c for c in df.columns if "havoc" in c],
                    "points_and_margin": [c for c in df.columns if c in ["home_points", "away_points", "margin", "spread"]]
                }
                
                return {
                    "file_exists": True,
                    "file_path": str(weekly_file),
                    "total_games": len(df) if len(df) > 0 else "Preview only",
                    "total_features": len(df.columns),
                    "feature_categories": {k: len(v) for k, v in feature_categories.items()},
                    "sample_feature_names": list(df.columns[:10]),
                    "all_features": list(df.columns)
                }
            else:
                return {
                    "file_exists": False,
                    "file_path": str(weekly_file),
                    "message": f"Weekly training data file not found: {weekly_file_path}"
                }
        except Exception as e:
            logger.warning(f"Could not preview weekly training data: {e}")
            return {
                "file_exists": False,
                "error": str(e)
            }