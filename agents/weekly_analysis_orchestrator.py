"""
Weekly Analysis Orchestrator
Coordinates weekly analysis agents for comprehensive matchup analysis and predictions
"""

import os
import logging
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional

from agents.core.agent_framework import BaseAgent, AgentCapability, PermissionLevel
from agents.weekly_matchup_analysis_agent import WeeklyMatchupAnalysisAgent
from agents.weekly_model_validation_agent import WeeklyModelValidationAgent
from agents.weekly_prediction_generation_agent import WeeklyPredictionGenerationAgent
from agents.report_generator_agent import ReportGeneratorAgent

# Import feature validation utilities
try:
    from config.model_features import validate_features, RIDGE_FEATURES, XGB_FEATURES, get_model_features
except ImportError:
    try:
        from model_features import validate_features, RIDGE_FEATURES, XGB_FEATURES, get_model_features
    except ImportError:
        logger.warning("Could not import feature validation utilities")
        validate_features = None
        RIDGE_FEATURES = []
        XGB_FEATURES = []
        get_model_features = None

logger = logging.getLogger(__name__)


class WeeklyAnalysisOrchestrator(BaseAgent):
    """
    Orchestrator that coordinates weekly analysis agents for comprehensive
    matchup analysis, model validation, and prediction generation
    """

    def __init__(self, week: int, season: int = 2025, agent_id: Optional[str] = None):
        self.week = week
        self.season = season
        
        if agent_id is None:
            agent_id = f"week{week}_analysis_orchestrator"
        
        super().__init__(
            agent_id=agent_id,
            name=f"Week {week} Analysis Orchestrator",
            permission_level=PermissionLevel.ADMIN,
        )
        self.agent_description = f"Coordinates Week {week} analysis agents for comprehensive matchup analysis."

        # Initialize specialized agents
        self.matchup_agent = WeeklyMatchupAnalysisAgent(week=week, season=season)
        self.validation_agent = WeeklyModelValidationAgent(week=week, season=season)
        self.prediction_agent = WeeklyPredictionGenerationAgent(week=week, season=season)
        self.report_agent = ReportGeneratorAgent(week=week, season=season)

    def _define_capabilities(self) -> List[AgentCapability]:
        """Define orchestrator capabilities"""
        return [
            AgentCapability(
                name="run_weekly_analysis",
                description=f"Run complete Week {self.week} analysis pipeline",
                permission_required=PermissionLevel.ADMIN,
                tools_required=["matchup_analysis", "model_validation", "prediction_generation"],
                data_access=["data/", "analysis/", "predictions/", "model_pack/"],
                execution_time_estimate=30.0,
            ),
            AgentCapability(
                name="validate_models",
                description=f"Validate models for Week {self.week}",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=["model_validation"],
                data_access=["model_pack/", "data/"],
                execution_time_estimate=12.0,
            ),
            AgentCapability(
                name="generate_predictions",
                description=f"Generate predictions for Week {self.week}",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=["prediction_generation"],
                data_access=["data/", "model_pack/", "predictions/"],
                execution_time_estimate=15.0,
            ),
        ]

    def _execute_action(self, action: str, parameters: Dict[str, Any],
                       user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute orchestrator actions"""
        if action == "run_weekly_analysis":
            return self.run_complete_analysis(parameters, user_context)
        elif action == "validate_models":
            return self.validate_models(parameters, user_context)
        elif action == "generate_predictions":
            return self.generate_predictions(parameters, user_context)
        else:
            raise ValueError(f"Unknown action: {action}")

    def _validate_features_for_models(self, features_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate that features match model expectations.
        
        Args:
            features_df: DataFrame with features to validate
            
        Returns:
            Dictionary with validation results
        """
        validation_result = {
            'is_valid': True,
            'warnings': [],
            'errors': [],
            'missing_ridge': [],
            'missing_xgb': [],
            'feature_count': len(features_df.columns),
            'expected_ridge_count': len(RIDGE_FEATURES) if RIDGE_FEATURES else 0,
            'expected_xgb_count': len(XGB_FEATURES) if XGB_FEATURES else 0,
        }
        
        if features_df.empty:
            validation_result['is_valid'] = False
            validation_result['errors'].append("Features DataFrame is empty")
            return validation_result
        
        available_features = set(features_df.columns)
        
        # Validate Ridge features
        if RIDGE_FEATURES:
            missing_ridge = [f for f in RIDGE_FEATURES if f not in available_features]
            if missing_ridge:
                validation_result['missing_ridge'] = missing_ridge
                validation_result['warnings'].append(
                    f"Missing {len(missing_ridge)} Ridge model features: {missing_ridge[:5]}"
                    + (f" (and {len(missing_ridge) - 5} more)" if len(missing_ridge) > 5 else "")
                )
                # Don't fail on missing features, just warn (some may be optional)
        
        # Validate XGB features
        if XGB_FEATURES:
            missing_xgb = [f for f in XGB_FEATURES if f not in available_features]
            if missing_xgb:
                validation_result['missing_xgb'] = missing_xgb
                validation_result['warnings'].append(
                    f"Missing {len(missing_xgb)} XGBoost model features: {missing_xgb[:5]}"
                    + (f" (and {len(missing_xgb) - 5} more)" if len(missing_xgb) > 5 else "")
                )
        
        # Check feature count (expected ~86 features)
        expected_count = 86
        if len(features_df.columns) < expected_count:
            validation_result['warnings'].append(
                f"Feature count ({len(features_df.columns)}) is less than expected ({expected_count})"
            )
        elif len(features_df.columns) > expected_count + 10:
            validation_result['warnings'].append(
                f"Feature count ({len(features_df.columns)}) is significantly higher than expected ({expected_count})"
            )
        
        # Check for critical missing features (common to both models)
        if RIDGE_FEATURES and XGB_FEATURES:
            shared_features = set(RIDGE_FEATURES) & set(XGB_FEATURES)
            missing_shared = [f for f in shared_features if f not in available_features]
            if missing_shared:
                validation_result['errors'].append(
                    f"Missing critical shared features: {missing_shared[:10]}"
                )
                validation_result['is_valid'] = False
        
        # Check data types - features should be numeric
        numeric_count = len(features_df.select_dtypes(include=['number']).columns)
        if numeric_count < len(features_df.columns) * 0.9:  # 90% should be numeric
            validation_result['warnings'].append(
                f"Only {numeric_count}/{len(features_df.columns)} features are numeric"
            )
        
        return validation_result

    def run_complete_analysis(self, parameters: Dict[str, Any] = None,
                             user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Run complete weekly analysis pipeline:
        1. Model validation
        2. Matchup analysis
        3. Prediction generation
        """
        try:
            logger.info(f"Starting Week {self.week} complete analysis pipeline")

            results = {
                'week': self.week,
                'season': self.season,
                'start_time': datetime.now().isoformat(),
                'steps_completed': [],
                'steps_failed': [],
                'final_status': 'in_progress'
            }

            # Step 1: Validate models
            logger.info(f"Step 1: Validating models for Week {self.week}")
            try:
                validation_result = self.validation_agent.execute_task({})
                results['validation'] = validation_result
                results['steps_completed'].append('model_validation')
                logger.info(f"Model validation completed: {validation_result.get('status', 'unknown')}")
            except Exception as e:
                logger.error(f"Model validation failed: {e}")
                results['validation'] = {'status': 'error', 'error': str(e)}
                results['steps_failed'].append('model_validation')

            # Step 2: Run matchup analysis
            logger.info(f"Step 2: Running matchup analysis for Week {self.week}")
            try:
                matchup_result = self.matchup_agent.execute_task({})
                results['matchup_analysis'] = matchup_result
                results['steps_completed'].append('matchup_analysis')
                logger.info(f"Matchup analysis completed: {matchup_result.get('status', 'unknown')}")
            except Exception as e:
                logger.error(f"Matchup analysis failed: {e}")
                results['matchup_analysis'] = {'status': 'error', 'error': str(e)}
                results['steps_failed'].append('matchup_analysis')

            # Step 2.5: Validate features before predictions
            logger.info(f"Step 2.5: Validating features for model compatibility")
            try:
                # Load weekly data to validate features
                from model_pack.utils.path_utils import get_weekly_enhanced_file
                enhanced_path = get_weekly_enhanced_file(self.week, self.season)
                if enhanced_path and enhanced_path.exists():
                    features_df = pd.read_csv(enhanced_path)
                    feature_validation = self._validate_features_for_models(features_df)
                    results['feature_validation'] = feature_validation
                    
                    if feature_validation['warnings']:
                        for warning in feature_validation['warnings']:
                            logger.warning(f"⚠️  Feature validation warning: {warning}")
                    
                    if not feature_validation['is_valid']:
                        error_msg = "Feature validation failed. Critical features missing."
                        logger.error(f"❌ {error_msg}")
                        for error in feature_validation['errors']:
                            logger.error(f"   - {error}")
                        # Don't fail the pipeline, but log the issue
                        results['feature_validation_warnings'] = feature_validation['warnings']
                        results['feature_validation_errors'] = feature_validation['errors']
                    else:
                        logger.info("✅ Feature validation passed")
                else:
                    logger.warning(f"⚠️  Could not find enhanced features file at {enhanced_path}")
            except Exception as e:
                logger.warning(f"⚠️  Feature validation check failed (non-fatal): {e}")
                # Don't fail the pipeline on validation errors, just log

            # Step 3: Generate predictions
            logger.info(f"Step 3: Generating predictions for Week {self.week}")
            try:
                prediction_result = self.prediction_agent.execute_task({})
                results['predictions'] = prediction_result
                results['steps_completed'].append('prediction_generation')
                logger.info(f"Prediction generation completed: {prediction_result.get('status', 'unknown')}")
            except Exception as e:
                logger.error(f"Prediction generation failed: {e}")
                results['predictions'] = {'status': 'error', 'error': str(e)}
                results['steps_failed'].append('prediction_generation')

            # Step 4: Generate report
            logger.info(f"Step 4: Generating comprehensive report for Week {self.week}")
            try:
                report_result = self.report_agent.execute_task({"stats_path": results.get("matchup_analysis", {}).get("output_path")})
                results['report'] = report_result
                results['steps_completed'].append('report_generation')
                logger.info(f"Report generation completed: {report_result.get('status', 'unknown')}")
            except Exception as e:
                logger.error(f"Report generation failed: {e}")
                results['report'] = {'status': 'error', 'error': str(e)}
                results['steps_failed'].append('report_generation')

            # Determine final status
            if len(results['steps_failed']) == 0:
                results['final_status'] = 'success'
            elif len(results['steps_completed']) > 0:
                results['final_status'] = 'partial_success'
            else:
                results['final_status'] = 'failed'

            results['end_time'] = datetime.now().isoformat()
            results['completion_rate'] = len(results['steps_completed']) / 3.0

            logger.info(f"Week {self.week} analysis pipeline completed: {results['final_status']}")
            return results

        except Exception as e:
            logger.error(f"Week {self.week} analysis pipeline failed: {e}")
            return {
                'week': self.week,
                'season': self.season,
                'final_status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def validate_models(self, parameters: Dict[str, Any] = None,
                       user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Run model validation for the week"""
        return self.validation_agent.execute_task(parameters or {})

    def generate_predictions(self, parameters: Dict[str, Any] = None,
                            user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate predictions for the week"""
        return self.prediction_agent.execute_task(parameters or {})

    def analyze_matchups(self, parameters: Dict[str, Any] = None,
                        user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Run matchup analysis for the week"""
        return self.matchup_agent.execute_task(parameters or {})


# Example usage
if __name__ == "__main__":
    orchestrator = WeeklyAnalysisOrchestrator(week=13, season=2025)
    
    result = orchestrator.run_complete_analysis()
    print(f"Week 13 Analysis Result: {result}")

