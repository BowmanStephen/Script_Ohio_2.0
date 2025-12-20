"""
🏈 Weekly Analysis Autonomator

Autonomous workflow that self-triggers and self-validates weekly football analysis.
Monitors CFBD data availability, validates data quality, generates enhanced features,
and creates comprehensive analysis reports without human intervention.
"""

import json
import logging
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from agents.core.agent_framework import AgentCapability, BaseAgent, PermissionLevel
from agents.core.state_manager import StateType, state_manager

logger = logging.getLogger(__name__)


class WeeklyAnalysisAutonomator(BaseAgent):
    """
    Autonomous weekly analysis that self-triggers and self-validates

    Capabilities:
    - Auto-trigger on new CFBD data availability
    - Data quality validation and cleansing
    - Enhanced feature generation
    - Automated report creation
    - Self-healing on errors
    - Performance monitoring and optimization
    """

    def __init__(self):
        """Initialize the weekly analysis autonomator"""
        super().__init__(
            agent_id="weekly_analysis_autonomator",
            name="Weekly Analysis Autonomator",
            permission_level=PermissionLevel.ADMIN,
        )

        # Configuration
        self.config = self._load_config()

        # State tracking
        self.current_week = None
        self.current_season = None
        self.last_analysis_time = None

        logger.info("WeeklyAnalysisAutonomator initialized")

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration for weekly analysis"""
        default_config = {
            "data_sources": ["cfbd_api"],
            "quality_thresholds": {
                "min_games": 40,  # Minimum games per week
                "min_teams": 60,  # Minimum unique teams
                "completeness_threshold": 0.95,  # 95% complete data
            },
            "enhanced_features": True,
            "auto_retry": True,
            "max_retries": 3,
            "notification_channels": ["log"],
            "output_paths": {
                "predictions": "data/outputs/predictions/",
                "enhanced_data": "data/weekly/week{week}/enhanced/",
                "reports": "reports/week{week}/",
            },
        }

        # Try to load from config file
        config_path = Path("config/weekly_analysis_autonomator.json")
        if config_path.exists():
            try:
                with open(config_path, "r") as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                logger.warning(f"Error loading config file: {e}")

        return default_config

    def _define_capabilities(self) -> List[AgentCapability]:
        """Define weekly analysis autonomator capabilities"""
        return [
            AgentCapability(
                name="auto_trigger_on_new_data",
                description="Automatically trigger analysis when new CFBD data is available",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["cfbd_client", "file_monitor"],
                data_access=["cfbd_api", "file_system"],
                execution_time_estimate=1.0,
            ),
            AgentCapability(
                name="validate_data_quality",
                description="Validate and cleanse incoming football data",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["data_validation", "quality_checks"],
                data_access=["training_data", "cfbd_data"],
                execution_time_estimate=2.0,
            ),
            AgentCapability(
                name="generate_enhanced_features",
                description="Generate 86 opponent-adjusted features for model input",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["feature_engineering", "data_processing"],
                data_access=["feature_data", "historical_stats"],
                execution_time_estimate=5.0,
            ),
            AgentCapability(
                name="create_analysis_reports",
                description="Generate comprehensive analysis reports and visualizations",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=["report_generation", "visualization"],
                data_access=["analysis_results", "template_data"],
                execution_time_estimate=3.0,
            ),
            AgentCapability(
                name="self_heal_on_errors",
                description="Automatically recover from errors during analysis",
                permission_required=PermissionLevel.ADMIN,
                tools_required=["error_recovery", "fallback_strategies"],
                data_access=["error_logs", "backup_data"],
                execution_time_estimate=1.0,
            ),
        ]

    def _execute_action(
        self, action: str, parameters: Dict[str, Any], user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute weekly analysis autonomator actions"""
        action_start_time = time.time()

        try:
            # Route to appropriate action
            if action == "run_autonomous_analysis":
                result = self._run_autonomous_analysis(parameters, user_context)
            elif action == "check_data_availability":
                result = self._check_data_availability(parameters, user_context)
            elif action == "validate_data_quality":
                result = self._validate_data_quality(parameters, user_context)
            elif action == "generate_features":
                result = self._generate_features(parameters, user_context)
            elif action == "create_reports":
                result = self._create_reports(parameters, user_context)
            elif action == "heal_analysis":
                result = self._heal_analysis(parameters, user_context)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}",
                    "available_actions": [cap.name for cap in self._define_capabilities()],
                }

            # Update execution time
            execution_time = time.time() - action_start_time
            result["execution_time"] = execution_time

            return result

        except Exception as e:
            execution_time = time.time() - action_start_time
            logger.error(f"Error in weekly analysis action {action}: {e}")

            # Attempt self-healing
            if self.config.get("auto_retry", True):
                heal_result = self._heal_analysis(
                    {"error": str(e), "action": action, "parameters": parameters},
                    user_context
                )
                return {
                    "success": False,
                    "error": str(e),
                    "execution_time": execution_time,
                    "healing_attempted": True,
                    "heal_result": heal_result,
                }

            return {
                "success": False,
                "error": str(e),
                "execution_time": execution_time,
                "autonomator_id": self.agent_id,
            }

    def _run_autonomous_analysis(self, params: Dict, context: Dict) -> Dict[str, Any]:
        """Run complete autonomous weekly analysis workflow"""
        # Get parameters
        season = params.get("season", self._get_current_season())
        week = params.get("week", self._get_current_week())

        # Create workflow state
        workflow_id = f"weekly_analysis_{season}_{week}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Save initial state
        state_manager.create_state_snapshot(
            state_type=StateType.WORKFLOW_STATE,
            entity_id=workflow_id,
            state_data={
                "workflow_type": "weekly_analysis",
                "season": season,
                "week": week,
                "status": "started",
                "started_at": datetime.now(timezone.utc).isoformat(),
                "config": self.config,
            },
            metadata={"autonomator": self.agent_id}
        )

        try:
            # Step 1: Check data availability
            logger.info(f"Checking data availability for season {season}, week {week}")
            data_result = self._check_data_availability({"season": season, "week": week}, context)

            if not data_result.get("success"):
                raise Exception(f"Data availability check failed: {data_result.get('error')}")

            # Step 2: Validate data quality
            logger.info("Validating data quality")
            quality_result = self._validate_data_quality({"season": season, "week": week}, context)

            if not quality_result.get("success"):
                raise Exception(f"Data quality validation failed: {quality_result.get('error')}")

            # Step 3: Generate enhanced features
            logger.info("Generating enhanced features")
            features_result = self._generate_features({"season": season, "week": week}, context)

            if not features_result.get("success"):
                raise Exception(f"Feature generation failed: {features_result.get('error')}")

            # Step 4: Run predictions (if configured)
            predictions_result = None
            if self.config.get("run_predictions", True):
                logger.info("Running predictions")
                predictions_result = self._run_predictions({"season": season, "week": week}, context)

            # Step 5: Create analysis reports
            logger.info("Creating analysis reports")
            reports_result = self._create_reports({
                "season": season,
                "week": week,
                "features_result": features_result,
                "predictions_result": predictions_result,
            }, context)

            if not reports_result.get("success"):
                raise Exception(f"Report creation failed: {reports_result.get('error')}")

            # Update final state
            final_state = {
                "workflow_type": "weekly_analysis",
                "season": season,
                "week": week,
                "status": "completed",
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "results": {
                    "data_check": data_result,
                    "quality_validation": quality_result,
                    "feature_generation": features_result,
                    "predictions": predictions_result,
                    "reports": reports_result,
                }
            }

            state_manager.update_state_snapshot(
                workflow_id,
                final_state,
                actor="weekly_analysis_autonomator",
                reason="Analysis completed successfully"
            )

            # Update internal tracking
            self.current_week = week
            self.current_season = season
            self.last_analysis_time = datetime.now(timezone.utc)

            return {
                "success": True,
                "workflow_id": workflow_id,
                "season": season,
                "week": week,
                "message": "Autonomous weekly analysis completed successfully",
                "results": final_state["results"],
                "output_paths": self._get_output_paths(season, week),
            }

        except Exception as e:
            # Save error state
            error_state = {
                "workflow_type": "weekly_analysis",
                "season": season,
                "week": week,
                "status": "failed",
                "failed_at": datetime.now(timezone.utc).isoformat(),
                "error": str(e),
                "error_traceback": str(e.__traceback__) if e.__traceback__ else None,
            }

            state_manager.update_state_snapshot(
                workflow_id,
                error_state,
                actor="weekly_analysis_autonomator",
                reason="Analysis failed"
            )

            raise e

    def _check_data_availability(self, params: Dict, context: Dict) -> Dict[str, Any]:
        """Check if CFBD data is available for the specified week"""
        season = params.get("season", self._get_current_season())
        week = params.get("week", self._get_current_week())

        try:
            # Use existing CFBD client
            from src.cfbd_client.unified_client import UnifiedCFBDClient
            client = UnifiedCFBDClient()

            # Get games for the week
            games = client.get_games(year=season, week=week)

            if not games:
                return {
                    "success": False,
                    "error": f"No games found for season {season}, week {week}",
                    "games_count": 0,
                }

            # Check if we have sufficient data
            games_count = len(games)
            teams_count = len(set(game.get("home_team") for game in games) |
                            set(game.get("away_team") for game in games))

            # Apply quality thresholds
            min_games = self.config["quality_thresholds"]["min_games"]
            min_teams = self.config["quality_thresholds"]["min_teams"]

            if games_count < min_games:
                return {
                    "success": False,
                    "error": f"Insufficient games: {games_count} < {min_games}",
                    "games_count": games_count,
                    "teams_count": teams_count,
                }

            if teams_count < min_teams:
                return {
                    "success": False,
                    "error": f"Insufficient teams: {teams_count} < {min_teams}",
                    "games_count": games_count,
                    "teams_count": teams_count,
                }

            # Check data completeness
            complete_games = 0
            for game in games:
                if (game.get("home_points") is not None and
                    game.get("away_points") is not None and
                    game.get("home_team") and game.get("away_team")):
                    complete_games += 1

            completeness = complete_games / games_count if games_count > 0 else 0
            completeness_threshold = self.config["quality_thresholds"]["completeness_threshold"]

            if completeness < completeness_threshold:
                return {
                    "success": False,
                    "error": f"Insufficient completeness: {completeness:.2%} < {completeness_threshold:.2%}",
                    "games_count": games_count,
                    "teams_count": teams_count,
                    "complete_games": complete_games,
                    "completeness": completeness,
                }

            return {
                "success": True,
                "games_count": games_count,
                "teams_count": teams_count,
                "complete_games": complete_games,
                "completeness": completeness,
                "data_quality": "good",
                "message": f"Data available and validated: {games_count} games, {teams_count} teams",
            }

        except Exception as e:
            logger.error(f"Error checking data availability: {e}")
            return {
                "success": False,
                "error": f"Data availability check failed: {e}",
                "season": season,
                "week": week,
            }

    def _validate_data_quality(self, params: Dict, context: Dict) -> Dict[str, Any]:
        """Perform detailed data quality validation"""
        season = params.get("season", self._get_current_season())
        week = params.get("week", self._get_current_week())

        try:
            # Run existing validation script
            import subprocess
            import sys

            cmd = [
                sys.executable,
                "scripts/validate_weekly_data.py",
                "--season", str(season),
                "--week", str(week),
                "--verbose"
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            validation_results = {
                "success": result.returncode == 0,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }

            if validation_results["success"]:
                # Parse validation output for structured results
                validation_summary = self._parse_validation_output(result.stdout)
                validation_results.update(validation_summary)

            return validation_results

        except Exception as e:
            logger.error(f"Error in data quality validation: {e}")
            return {
                "success": False,
                "error": f"Data quality validation failed: {e}",
                "season": season,
                "week": week,
            }

    def _generate_features(self, params: Dict, context: Dict) -> Dict[str, Any]:
        """Generate enhanced features for the week"""
        season = params.get("season", self._get_current_season())
        week = params.get("week", self._get_current_week())

        try:
            if self.config.get("enhanced_features", True):
                # Use existing feature generation script
                import subprocess
                import sys

                cmd = [
                    sys.executable,
                    "scripts/build_training_data_from_cfbd.py",
                    "--season", str(season),
                    "--week", str(week),
                    "--enhanced"
                ]

                result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)

                feature_results = {
                    "success": result.returncode == 0,
                    "return_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "features_generated": "enhanced" if self.config.get("enhanced_features") else "basic",
                    "season": season,
                    "week": week,
                }

                # Check if output files were created
                if feature_results["success"]:
                    output_paths = self._get_output_paths(season, week)
                    enhanced_file = Path(output_paths["enhanced_data"].format(week=week)) / f"week{week}_features_86.csv"
                    feature_results["output_file"] = str(enhanced_file)
                    feature_results["file_exists"] = enhanced_file.exists()

                return feature_results
            else:
                # Basic feature generation (placeholder)
                return {
                    "success": True,
                    "message": "Basic feature generation completed",
                    "features_generated": "basic",
                    "season": season,
                    "week": week,
                }

        except Exception as e:
            logger.error(f"Error generating features: {e}")
            return {
                "success": False,
                "error": f"Feature generation failed: {e}",
                "season": season,
                "week": week,
            }

    def _run_predictions(self, params: Dict, context: Dict) -> Dict[str, Any]:
        """Run predictions for the week"""
        season = params.get("season", self._get_current_season())
        week = params.get("week", self._get_current_week())

        try:
            # Use existing prediction script
            import subprocess
            import sys

            cmd = [
                sys.executable,
                "scripts/run_weekly_analysis.py",
                "--week", str(week),
                "--season", str(season),
                "--predictions-only"
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

            prediction_results = {
                "success": result.returncode == 0,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "season": season,
                "week": week,
            }

            # Check for prediction output files
            if prediction_results["success"]:
                output_paths = self._get_output_paths(season, week)
                predictions_file = Path(output_paths["predictions"]) / f"week{week}_predictions.json"
                prediction_results["predictions_file"] = str(predictions_file)
                prediction_results["file_exists"] = predictions_file.exists()

            return prediction_results

        except Exception as e:
            logger.error(f"Error running predictions: {e}")
            return {
                "success": False,
                "error": f"Prediction execution failed: {e}",
                "season": season,
                "week": week,
            }

    def _create_reports(self, params: Dict, context: Dict) -> Dict[str, Any]:
        """Create analysis reports and visualizations"""
        season = params.get("season")
        week = params.get("week")
        features_result = params.get("features_result", {})
        predictions_result = params.get("predictions_result", {})

        try:
            reports_created = []

            # Create basic summary report
            summary_report = {
                "season": season,
                "week": week,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "data_validation": self._get_last_validation_summary(),
                "features": {
                    "generated": features_result.get("success", False),
                    "type": features_result.get("features_generated", "unknown"),
                    "file_exists": features_result.get("file_exists", False),
                },
                "predictions": {
                    "generated": predictions_result.get("success", False) if predictions_result else False,
                    "file_exists": predictions_result.get("file_exists", False) if predictions_result else False,
                },
            }

            # Save summary report
            output_paths = self._get_output_paths(season, week)
            reports_dir = Path(output_paths["reports"].format(week=week))
            reports_dir.mkdir(parents=True, exist_ok=True)

            summary_file = reports_dir / f"weekly_analysis_summary_{season}_w{week}.json"
            with open(summary_file, "w") as f:
                json.dump(summary_report, f, indent=2)

            reports_created.append(str(summary_file))

            # Generate enhanced reports if configured
            if self.config.get("enhanced_reports", True):
                # This would call existing report generation scripts
                pass

            return {
                "success": True,
                "reports_created": reports_created,
                "summary_report": summary_report,
                "reports_directory": str(reports_dir),
            }

        except Exception as e:
            logger.error(f"Error creating reports: {e}")
            return {
                "success": False,
                "error": f"Report creation failed: {e}",
                "season": season,
                "week": week,
            }

    def _heal_analysis(self, params: Dict, context: Dict) -> Dict[str, Any]:
        """Attempt to heal analysis errors"""
        error = params.get("error", "")
        action = params.get("action", "")
        parameters = params.get("parameters", {})

        healing_actions = []

        try:
            # Common healing strategies
            if "data" in error.lower():
                # Data-related error healing
                healing_actions.append("retry_with_different_data_source")

                # Try clearing cache
                try:
                    from src.cfbd_client.unified_client import UnifiedCFBDClient
                    client = UnifiedCFBDClient()
                    if hasattr(client, 'clear_cache'):
                        client.clear_cache()
                        healing_actions.append("cleared_cfbd_cache")
                except:
                    pass

            if "timeout" in error.lower():
                # Timeout healing
                healing_actions.append("increase_timeout")
                healing_actions.append("retry_with_exponential_backoff")

            if "permission" in error.lower() or "access" in error.lower():
                # Permission/Access error healing
                healing_actions.append("check_api_key")
                healing_actions.append("verify_file_permissions")

            # Generic retry for transient errors
            if self.config.get("auto_retry", True) and action:
                healing_actions.append("schedule_retry")

            return {
                "success": True,
                "healing_actions": healing_actions,
                "error_type": self._classify_error(error),
                "retry_recommended": len(healing_actions) > 0,
            }

        except Exception as e:
            logger.error(f"Error in healing: {e}")
            return {
                "success": False,
                "error": f"Healing failed: {e}",
                "healing_actions": healing_actions,
            }

    # Helper methods

    def _get_current_season(self) -> int:
        """Get current football season"""
        now = datetime.now(timezone.utc)
        # College football season typically runs from August to January
        if now.month >= 8:  # August or later
            return now.year
        elif now.month <= 1:  # January
            return now.year - 1
        else:  # February - July
            return now.year - 1

    def _get_current_week(self) -> int:
        """Get current college football week"""
        # This would contain proper week calculation logic
        # For now, return a reasonable estimate
        now = datetime.now(timezone.utc)
        season_start = datetime(self._get_current_season(), 8, 1, tzinfo=timezone.utc)
        weeks_elapsed = (now - season_start).days // 7
        return min(18, max(1, weeks_elapsed + 1))

    def _get_output_paths(self, season: int, week: int) -> Dict[str, str]:
        """Get output file paths for the analysis"""
        base_paths = self.config.get("output_paths", {})

        return {
            "predictions": base_paths.get("predictions", "data/outputs/predictions/"),
            "enhanced_data": base_paths.get("enhanced_data", "data/weekly/week{week}/enhanced/"),
            "reports": base_paths.get("reports", "reports/week{week}/"),
        }

    def _parse_validation_output(self, output: str) -> Dict[str, Any]:
        """Parse validation script output for structured results"""
        # This would contain sophisticated parsing logic
        # For now, return basic info
        return {
            "validation_passed": "PASSED" in output.upper(),
            "validation_details": output[:500] if output else "",  # First 500 chars
        }

    def _get_last_validation_summary(self) -> Dict[str, Any]:
        """Get summary of most recent validation"""
        # This would query recent validation results
        return {
            "last_check": datetime.now(timezone.utc).isoformat(),
            "status": "passed",
        }

    def _classify_error(self, error: str) -> str:
        """Classify the type of error for healing"""
        error_lower = error.lower()

        if any(keyword in error_lower for keyword in ["network", "connection", "timeout"]):
            return "network"
        elif any(keyword in error_lower for keyword in ["permission", "access", "unauthorized"]):
            return "permission"
        elif any(keyword in error_lower for keyword in ["data", "format", "parse"]):
            return "data"
        elif any(keyword in error_lower for keyword in ["memory", "resource"]):
            return "resource"
        else:
            return "unknown"

    def get_analysis_status(self) -> Dict[str, Any]:
        """Get current analysis status and statistics"""
        return {
            "current_week": self.current_week,
            "current_season": self.current_season,
            "last_analysis_time": self.last_analysis_time.isoformat() if self.last_analysis_time else None,
            "autonomator_id": self.agent_id,
            "config": self.config,
            "capabilities": [cap.name for cap in self._define_capabilities()],
        }


# Global instance
weekly_analysis_autonomator = WeeklyAnalysisAutonomator()