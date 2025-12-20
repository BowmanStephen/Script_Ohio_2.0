"""
🏈 Game Day Prediction Autonomator

Real-time prediction updates on game days:
- Monitor live game data and line movements
- Update predictions dynamically based on new information
- Generate instant alerts for significant changes
- Track prediction accuracy throughout game day
- Automatic publishing of updated predictions
"""

import json
import logging
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from agents.core.agent_framework import AgentCapability, BaseAgent, PermissionLevel
from agents.core.state_manager import StateType, state_manager

logger = logging.getLogger(__name__)


class GameDayPredictionAutonomator(BaseAgent):
    """
    Real-time prediction updates on game days

    Capabilities:
    - Live data monitoring for game day updates
    - Dynamic prediction updates based on line movements
    - Real-time accuracy tracking and validation
    - Automatic publishing of updated predictions
    - Alert generation for significant changes
    """

    def __init__(self):
        """Initialize the game day prediction autonomator"""
        super().__init__(
            agent_id="gameday_prediction_autonomator",
            name="Game Day Prediction Autonomator",
            permission_level=PermissionLevel.ADMIN,
        )

        # Configuration
        self.config = self._load_config()

        # Game day state
        self.active_games = {}
        self.prediction_history = []
        self.last_update_time = None

        # Alert thresholds
        self.alert_history = []

        logger.info("GameDayPredictionAutonomator initialized")

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration for game day predictions"""
        default_config = {
            "monitoring": {
                "update_frequency_minutes": 15,  # Check for updates every 15 minutes
                "game_start_buffer_hours": 2,  # Start monitoring 2 hours before first game
                "game_end_buffer_hours": 2,  # Stop monitoring 2 hours after last game
                "live_data_sources": ["cfbd_api", "espn_api"],
            },
            "predictions": {
                "update_threshold": 0.05,  # Update prediction if change > 5%
                "confidence_threshold": 0.6,  # Minimum confidence for publishing
                "ensemble_weight_adjustment": True,
                "line_movement_sensitivity": 0.02,  # Trigger on 2% line movement
            },
            "alerts": {
                "significant_prediction_change": 0.10,  # Alert on 10% prediction change
                "upset_probability": 0.25,  # Alert when upset probability > 25%
                "high_confidence_prediction": 0.85,  # Alert when confidence > 85%
                "line_movement_threshold": 0.03,  # Alert on 3% line movement
            },
            "publishing": {
                "auto_publish": True,
                "webhook_endpoints": [],
                "file_outputs": ["web_app/data/live_predictions.json"],
                "social_media": False,
            },
            "storage": {
                "predictions_dir": "data/outputs/predictions/live/",
                "game_data_dir": "data/live/game_days/",
                "alert_log": "project_management/gameday_alerts.json",
            },
            "validation": {
                "real_time_accuracy": True,
                "track_prediction_changes": True,
                "save_intermediate_states": True,
            },
        }

        # Try to load from config file
        config_path = Path("config/gameday_prediction_autonomator.json")
        if config_path.exists():
            try:
                with open(config_path, "r") as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                logger.warning(f"Error loading config file: {e}")

        return default_config

    def _define_capabilities(self) -> List[AgentCapability]:
        """Define game day prediction autonomator capabilities"""
        return [
            AgentCapability(
                name="live_data_monitoring",
                description="Monitor live game data and updates",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["data_fetcher", "change_detector"],
                data_access=["live_game_data", "score_updates"],
                execution_time_estimate=1.0,
            ),
            AgentCapability(
                name="real_time_prediction_updates",
                description="Update predictions dynamically based on new information",
                permission_required=PermissionLevel.ADMIN,
                tools_required=["prediction_engine", "model_inference"],
                data_access=["game_data", "model_weights"],
                execution_time_estimate=2.0,
            ),
            AgentCapability(
                name="line_movement_analysis",
                description="Analyze and respond to betting line movements",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["line_tracker", "movement_analyzer"],
                data_access=["betting_lines", "market_data"],
                execution_time_estimate=1.5,
            ),
            AgentCapability(
                name="automatic_publishing",
                description="Publish updated predictions automatically",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=["publisher", "webhook_manager"],
                data_access=["prediction_data", "publishing_endpoints"],
                execution_time_estimate=1.0,
            ),
            AgentCapability(
                name="alert_generation",
                description="Generate alerts for significant prediction changes",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["alert_engine", "notification_manager"],
                data_access=["alert_history", "threshold_config"],
                execution_time_estimate=0.5,
            ),
            AgentCapability(
                name="accuracy_tracking",
                description="Track prediction accuracy in real-time",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["accuracy_tracker", "result_validator"],
                data_access=["prediction_results", "actual_outcomes"],
                execution_time_estimate=1.0,
            ),
        ]

    def _execute_action(
        self, action: str, parameters: Dict[str, Any], user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute game day prediction autonomator actions"""
        action_start_time = time.time()

        try:
            # Route to appropriate action
            if action == "monitor_gameday_predictions":
                result = self._monitor_gameday_predictions(parameters, user_context)
            elif action == "update_live_predictions":
                result = self._update_live_predictions(parameters, user_context)
            elif action == "analyze_line_movements":
                result = self._analyze_line_movements(parameters, user_context)
            elif action == "publish_updates":
                result = self._publish_updates(parameters, user_context)
            elif action == "generate_alerts":
                result = self._generate_alerts(parameters, user_context)
            elif action == "track_accuracy":
                result = self._track_accuracy(parameters, user_context)
            elif action == "run_gameday_cycle":
                result = self._run_gameday_cycle(parameters, user_context)
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
            logger.error(f"Error in gameday prediction action {action}: {e}")

            return {
                "success": False,
                "error": str(e),
                "execution_time": execution_time,
                "autonomator_id": self.agent_id,
            }

    def _monitor_gameday_predictions(self, params: Dict, context: Dict) -> Dict[str, Any]:
        """Monitor game day predictions and check for updates"""
        date = params.get("date", datetime.now(timezone.utc).date().isoformat())

        try:
            # Get games for the specified date
            games = self._get_games_for_date(date)

            if not games:
                return {
                    "success": True,
                    "message": f"No games found for {date}",
                    "games_count": 0,
                    "date": date,
                }

            # Check which games are active or upcoming
            active_games = self._identify_active_games(games, date)
            self.active_games = {game["id"]: game for game in active_games}

            monitoring_results = {
                "date": date,
                "total_games": len(games),
                "active_games": len(active_games),
                "game_statuses": {},
                "update_needed": False,
            }

            # Check each game for update needs
            for game in active_games:
                game_id = game["id"]
                game_status = self._get_game_status(game)
                monitoring_results["game_statuses"][game_id] = game_status

                # Determine if predictions need updating
                needs_update = self._check_update_needed(game, game_status)
                if needs_update:
                    monitoring_results["update_needed"] = True

            # Save monitoring state
            self.last_update_time = datetime.now(timezone.utc)

            return {
                "success": True,
                "monitoring_results": monitoring_results,
                "active_games": self.active_games,
                "next_check": self._get_next_check_time(),
            }

        except Exception as e:
            logger.error(f"Error monitoring gameday predictions: {e}")
            return {
                "success": False,
                "error": f"Game day monitoring failed: {e}",
                "date": date,
            }

    def _update_live_predictions(self, params: Dict, context: Dict) -> Dict[str, Any]:
        """Update predictions for live games"""
        game_ids = params.get("game_ids", list(self.active_games.keys()))
        force_update = params.get("force_update", False)

        try:
            update_results = {}
            significant_changes = []

            for game_id in game_ids:
                if game_id not in self.active_games:
                    continue

                game = self.active_games[game_id]
                logger.info(f"Updating predictions for game {game_id}: {game.get('home_team')} vs {game.get('away_team')}")

                # Get current game data
                current_data = self._get_current_game_data(game_id)

                # Get previous predictions
                previous_predictions = self._get_previous_predictions(game_id)

                # Generate updated predictions
                new_predictions = self._generate_updated_predictions(game, current_data, previous_predictions)

                # Compare with previous predictions
                changes = self._compare_predictions(previous_predictions, new_predictions)

                if self._is_significant_change(changes) or force_update:
                    significant_changes.append({
                        "game_id": game_id,
                        "game": f"{game.get('home_team')} vs {game.get('away_team')}",
                        "changes": changes,
                        "old_predictions": previous_predictions,
                        "new_predictions": new_predictions,
                    })

                # Save updated predictions
                self._save_predictions(game_id, new_predictions)

                update_results[game_id] = {
                    "success": True,
                    "predictions_updated": True,
                    "changes": changes,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

            # Generate alerts for significant changes
            if significant_changes:
                alert_result = self._generate_alerts({
                    "type": "significant_prediction_changes",
                    "changes": significant_changes,
                }, context)

            return {
                "success": True,
                "update_results": update_results,
                "games_updated": len(update_results),
                "significant_changes": len(significant_changes),
                "alert_generated": alert_result.get("success", False),
            }

        except Exception as e:
            logger.error(f"Error updating live predictions: {e}")
            return {
                "success": False,
                "error": f"Prediction update failed: {e}",
                "game_ids": game_ids,
            }

    def _analyze_line_movements(self, params: Dict, context: Dict) -> Dict[str, Any]:
        """Analyze line movements and update predictions accordingly"""
        game_ids = params.get("game_ids", list(self.active_games.keys()))

        try:
            movement_analysis = {}

            for game_id in game_ids:
                if game_id not in self.active_games:
                    continue

                game = self.active_games[game_id]

                # Get current and historical lines
                current_lines = self._get_current_lines(game_id)
                historical_lines = self._get_historical_lines(game_id)

                if not current_lines or not historical_lines:
                    movement_analysis[game_id] = {
                        "status": "insufficient_data",
                        "message": "Line data not available",
                    }
                    continue

                # Analyze movement
                line_change = self._calculate_line_change(historical_lines, current_lines)
                movement_significance = self._assess_movement_significance(line_change)

                movement_analysis[game_id] = {
                    "current_line": current_lines,
                    "line_change": line_change,
                    "significance": movement_significance,
                    "recommendation": self._get_line_movement_recommendation(line_change, movement_significance),
                }

                # Update predictions if significant movement
                if movement_significance["level"] in ["high", "critical"]:
                    logger.info(f"Significant line movement for game {game_id}: {line_change}")

                    # Adjust predictions based on line movement
                    adjusted_predictions = self._adjust_predictions_for_line_movement(
                        game_id, line_change, movement_significance
                    )

                    movement_analysis[game_id]["predictions_adjusted"] = True
                    movement_analysis[game_id]["adjusted_predictions"] = adjusted_predictions

            return {
                "success": True,
                "movement_analysis": movement_analysis,
                "games_analyzed": len(movement_analysis),
                "significant_movements": len([
                    g for g in movement_analysis.values()
                    if g.get("significance", {}).get("level") in ["high", "critical"]
                ]),
            }

        except Exception as e:
            logger.error(f"Error analyzing line movements: {e}")
            return {
                "success": False,
                "error": f"Line movement analysis failed: {e}",
                "game_ids": game_ids,
            }

    def _publish_updates(self, params: Dict, context: Dict) -> Dict[str, Any]:
        """Publish updated predictions to configured endpoints"""
        update_data = params.get("update_data", {})
        channels = params.get("channels", self.config["publishing"]["file_outputs"])

        try:
            publishing_results = {}

            # Save to file outputs
            if "file_outputs" in channels:
                file_results = self._publish_to_files(update_data)
                publishing_results["file_outputs"] = file_results

            # Send webhook notifications
            if "webhook_endpoints" in channels:
                webhook_results = self._send_webhooks(update_data)
                publishing_results["webhooks"] = webhook_results

            # Social media updates (if configured)
            if "social_media" in channels and self.config["publishing"]["social_media"]:
                social_results = self._publish_to_social_media(update_data)
                publishing_results["social_media"] = social_results

            return {
                "success": True,
                "publishing_results": publishing_results,
                "channels_used": channels,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Error publishing updates: {e}")
            return {
                "success": False,
                "error": f"Publishing failed: {e}",
                "channels": channels,
            }

    def _generate_alerts(self, params: Dict, context: Dict) -> Dict[str, Any]:
        """Generate alerts for significant prediction changes"""
        alert_type = params.get("type", "prediction_change")
        alert_data = params.get("changes", [])

        try:
            generated_alerts = []

            if alert_type == "significant_prediction_changes":
                for change in alert_data:
                    alert = self._create_prediction_change_alert(change)
                    if alert:
                        generated_alerts.append(alert)

            elif alert_type == "upset_probability":
                alert = self._create_upset_probability_alert(alert_data)
                if alert:
                    generated_alerts.append(alert)

            elif alert_type == "high_confidence":
                alert = self._create_high_confidence_alert(alert_data)
                if alert:
                    generated_alerts.append(alert)

            # Save alerts to log
            self._save_alerts(generated_alerts)

            # Send notifications if configured
            notification_results = self._send_alert_notifications(generated_alerts)

            return {
                "success": True,
                "alerts_generated": len(generated_alerts),
                "alerts": generated_alerts,
                "notifications_sent": notification_results.get("sent_count", 0),
            }

        except Exception as e:
            logger.error(f"Error generating alerts: {e}")
            return {
                "success": False,
                "error": f"Alert generation failed: {e}",
                "alert_type": alert_type,
            }

    def _track_accuracy(self, params: Dict, context: Dict) -> Dict[str, Any]:
        """Track prediction accuracy in real-time"""
        try:
            # Get recent game results
            recent_results = self._get_recent_game_results()

            accuracy_metrics = {
                "total_predictions": 0,
                "correct_predictions": 0,
                "overall_accuracy": 0.0,
                "accuracy_by_confidence": {
                    "high": {"correct": 0, "total": 0, "accuracy": 0.0},
                    "medium": {"correct": 0, "total": 0, "accuracy": 0.0},
                    "low": {"correct": 0, "total": 0, "accuracy": 0.0},
                },
                "recent_trend": "stable",
            }

            # Compare predictions with actual results
            for result in recent_results:
                prediction = self._get_prediction_for_game(result["game_id"])
                if prediction:
                    accuracy_metrics["total_predictions"] += 1

                    # Check if prediction was correct
                    correct = self._evaluate_prediction_correctness(prediction, result)
                    if correct:
                        accuracy_metrics["correct_predictions"] += 1

                    # Track by confidence level
                    confidence = prediction.get("confidence", 0.5)
                    confidence_bucket = "high" if confidence > 0.75 else "medium" if confidence > 0.5 else "low"

                    accuracy_metrics["accuracy_by_confidence"][confidence_bucket]["total"] += 1
                    if correct:
                        accuracy_metrics["accuracy_by_confidence"][confidence_bucket]["correct"] += 1

            # Calculate accuracies
            if accuracy_metrics["total_predictions"] > 0:
                accuracy_metrics["overall_accuracy"] = (
                    accuracy_metrics["correct_predictions"] / accuracy_metrics["total_predictions"]
                )

            for bucket in accuracy_metrics["accuracy_by_confidence"].values():
                if bucket["total"] > 0:
                    bucket["accuracy"] = bucket["correct"] / bucket["total"]

            # Calculate trend
            if len(self.prediction_history) >= 2:
                recent_accuracy = self.prediction_history[-1].get("accuracy", 0)
                previous_accuracy = self.prediction_history[-2].get("accuracy", 0)

                if recent_accuracy > previous_accuracy + 0.05:
                    accuracy_metrics["recent_trend"] = "improving"
                elif recent_accuracy < previous_accuracy - 0.05:
                    accuracy_metrics["recent_trend"] = "declining"
                else:
                    accuracy_metrics["recent_trend"] = "stable"

            # Save to history
            self.prediction_history.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "accuracy": accuracy_metrics["overall_accuracy"],
                "total_predictions": accuracy_metrics["total_predictions"],
            })

            # Keep only last 50 entries
            if len(self.prediction_history) > 50:
                self.prediction_history = self.prediction_history[-50]

            return {
                "success": True,
                "accuracy_metrics": accuracy_metrics,
                "tracking_period": "last_7_days",
                "history_entries": len(self.prediction_history),
            }

        except Exception as e:
            logger.error(f"Error tracking accuracy: {e}")
            return {
                "success": False,
                "error": f"Accuracy tracking failed: {e}",
            }

    def _run_gameday_cycle(self, params: Dict, context: Dict) -> Dict[str, Any]:
        """Run complete game day prediction cycle"""
        date = params.get("date", datetime.now(timezone.utc).date().isoformat())

        try:
            cycle_results = {}

            # Step 1: Monitor games
            logger.info(f"Starting game day cycle for {date}")
            monitoring_result = self._monitor_gameday_predictions({"date": date}, context)
            cycle_results["monitoring"] = monitoring_result

            if not monitoring_result.get("success"):
                return {
                    "success": False,
                    "error": "Monitoring failed, aborting cycle",
                    "cycle_results": cycle_results,
                }

            # Step 2: Check for updates
            if monitoring_result.get("monitoring_results", {}).get("update_needed"):
                logger.info("Updates needed, proceeding with prediction updates")
                update_result = self._update_live_predictions({}, context)
                cycle_results["predictions"] = update_result

                # Step 3: Analyze line movements
                line_result = self._analyze_line_movements({}, context)
                cycle_results["line_movements"] = line_result

                # Step 4: Publish updates
                if update_result.get("significant_changes", 0) > 0:
                    publish_result = self._publish_updates({
                        "update_data": {
                            "predictions": update_result.get("update_results"),
                            "line_movements": line_result.get("movement_analysis"),
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                    }, context)
                    cycle_results["publishing"] = publish_result

            # Step 5: Track accuracy
            accuracy_result = self._track_accuracy({}, context)
            cycle_results["accuracy"] = accuracy_result

            return {
                "success": True,
                "cycle_results": cycle_results,
                "date": date,
                "games_monitored": len(self.active_games),
                "updates_generated": cycle_results.get("predictions", {}).get("significant_changes", 0),
                "cycle_time": "completed",
            }

        except Exception as e:
            logger.error(f"Error in game day cycle: {e}")
            return {
                "success": False,
                "error": f"Game day cycle failed: {e}",
                "date": date,
                "partial_results": cycle_results,
            }

    # Helper methods

    def _get_games_for_date(self, date: str) -> List[Dict]:
        """Get games scheduled for a specific date"""
        try:
            from src.cfbd_client.unified_client import UnifiedCFBDClient
            client = UnifiedCFBDClient()

            # Convert date string to year and week
            # This would need proper date-to-week conversion
            year = int(date.split("-")[0])  # Simple extraction
            week = self._get_week_from_date(date)

            games = client.get_games(year=year, week=week)

            # Filter games for the specific date
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
            date_games = [
                game for game in games
                if datetime.fromisoformat(game["start_date"].replace("Z", "+00:00")).date() == target_date
            ]

            return date_games

        except Exception as e:
            logger.error(f"Error getting games for date {date}: {e}")
            return []

    def _get_week_from_date(self, date: str) -> int:
        """Convert date to college football week (simplified)"""
        # This would contain proper date-to-week conversion logic
        # For now, estimate based on day of year
        dt = datetime.strptime(date, "%Y-%m-%d")
        day_of_year = (dt - datetime(dt.year, 1, 1)).days
        return min(18, max(1, (day_of_year - 240) // 7 + 1))  # Rough estimate

    def _identify_active_games(self, games: List[Dict], date: str) -> List[Dict]:
        """Identify games that are active or about to start"""
        current_time = datetime.now(timezone.utc)
        active_games = []

        for game in games:
            game_time = datetime.fromisoformat(game["start_date"].replace("Z", "+00:00"))

            # Games within buffer hours (2 hours before to 2 hours after)
            buffer_hours = self.config["monitoring"]["game_end_buffer_hours"]
            time_diff = abs((current_time - game_time).total_seconds()) / 3600

            if time_diff <= buffer_hours + 4:  # 4 hours game duration
                active_games.append(game)

        return active_games

    def _get_game_status(self, game: Dict) -> Dict[str, Any]:
        """Get current status of a game"""
        current_time = datetime.now(timezone.utc)
        game_time = datetime.fromisoformat(game["start_date"].replace("Z", "+00:00"))

        status = {
            "game_id": game["id"],
            "scheduled_time": game_time.isoformat(),
            "current_time": current_time.isoformat(),
            "time_to_game": (game_time - current_time).total_seconds() / 3600,  # hours
            "status": "scheduled",
        }

        if game["home_points"] is not None and game["away_points"] is not None:
            status["status"] = "completed"
        elif current_time >= game_time:
            status["status"] = "in_progress"
        elif (game_time - current_time).total_seconds() / 3600 <= 2:
            status["status"] = "pre_game"

        return status

    def _check_update_needed(self, game: Dict, game_status: Dict) -> bool:
        """Check if predictions need updating for a game"""
        # Update needed for games in pre-game, in-progress, or recently completed
        return game_status["status"] in ["pre_game", "in_progress", "completed"]

    def _get_next_check_time(self) -> str:
        """Get time for next monitoring check"""
        next_check = datetime.now(timezone.utc) + timedelta(
            minutes=self.config["monitoring"]["update_frequency_minutes"]
        )
        return next_check.isoformat()

    def _get_current_game_data(self, game_id: str) -> Dict[str, Any]:
        """Get current data for a specific game"""
        try:
            from src.cfbd_client.unified_client import UnifiedCFBDClient
            client = UnifiedCFBDClient()

            # Get current game data
            game_data = client.get_game(game_id)

            # Add live data if available
            live_data = self._get_live_game_data(game_id)
            if live_data:
                game_data.update(live_data)

            return game_data

        except Exception as e:
            logger.error(f"Error getting current game data for {game_id}: {e}")
            return {}

    def _get_live_game_data(self, game_id: str) -> Optional[Dict]:
        """Get live game data (play-by-play, scores, etc.)"""
        # This would integrate with live data sources
        # For now, return None
        return None

    def _get_previous_predictions(self, game_id: str) -> Dict[str, Any]:
        """Get previously stored predictions for a game"""
        try:
            prediction_file = Path(self.config["storage"]["predictions_dir"]) / f"{game_id}_predictions.json"
            if prediction_file.exists():
                with open(prediction_file, "r") as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error getting previous predictions for {game_id}: {e}")
            return {}

    def _generate_updated_predictions(self, game: Dict, current_data: Dict, previous_predictions: Dict) -> Dict[str, Any]:
        """Generate updated predictions based on current game data"""
        try:
            # Use existing model prediction infrastructure
            from src.models.execution.engine import ModelExecutionEngine

            engine = ModelExecutionEngine()

            # Prepare input data for prediction
            input_data = {
                "home_team": game["home_team"],
                "away_team": game["away_team"],
                "home_score": current_data.get("home_points", 0),
                "away_score": current_data.get("away_points", 0),
                "time_remaining": self._calculate_time_remaining(current_data),
                "quarter": current_data.get("quarter", 1),
                "possession": current_data.get("possession", "home"),  # Would get from live data
            }

            # Get predictions from all models
            predictions = {}
            for model_name in ["ridge", "xgboost", "fastai"]:
                if hasattr(engine, f"_{model_name}"):
                    model = getattr(engine, f"_{model_name}")
                    prediction = model.predict([input_data])
                    predictions[model_name] = prediction[0] if prediction else 0.5

            # Calculate ensemble prediction
            weights = self.config["models"]
            ensemble_prediction = (
                predictions["ridge"] * weights["ridge_regression"]["weight"] +
                predictions["xgboost"] * weights["xgboost"]["weight"] +
                predictions["fastai"] * weights["fastai"]["weight"]
            )

            # Calculate confidence based on model agreement
            model_values = list(predictions.values())
            confidence = 1.0 - (max(model_values) - min(model_values))  # Higher when models agree

            return {
                "predictions": predictions,
                "ensemble_prediction": ensemble_prediction,
                "confidence": max(0.0, min(1.0, confidence)),
                "home_win_probability": ensemble_prediction,
                "away_win_probability": 1.0 - ensemble_prediction,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "game_id": game["id"],
            }

        except Exception as e:
            logger.error(f"Error generating updated predictions: {e}")
            return previous_predictions  # Fallback to previous

    def _calculate_time_remaining(self, game_data: Dict) -> int:
        """Calculate remaining time in seconds"""
        # This would calculate based on quarter, time left, etc.
        # For now, return default
        return 1800  # 30 minutes default

    def _compare_predictions(self, old: Dict, new: Dict) -> Dict[str, Any]:
        """Compare old and new predictions"""
        try:
            old_ensemble = old.get("ensemble_prediction", 0.5)
            new_ensemble = new.get("ensemble_prediction", 0.5)

            change = new_ensemble - old_ensemble
            change_percent = abs(change / old_ensemble) if old_ensemble > 0 else 0

            return {
                "old_prediction": old_ensemble,
                "new_prediction": new_ensemble,
                "change": change,
                "change_percent": change_percent,
                "significant": change_percent > self.config["predictions"]["update_threshold"],
            }

        except Exception as e:
            logger.error(f"Error comparing predictions: {e}")
            return {"error": str(e)}

    def _is_significant_change(self, changes: Dict) -> bool:
        """Check if prediction change is significant"""
        if "error" in changes:
            return False
        return changes.get("significant", False) or changes.get("change_percent", 0) > 0.05

    def _save_predictions(self, game_id: str, predictions: Dict):
        """Save predictions to file"""
        try:
            predictions_dir = Path(self.config["storage"]["predictions_dir"])
            predictions_dir.mkdir(parents=True, exist_ok=True)

            prediction_file = predictions_dir / f"{game_id}_predictions.json"
            with open(prediction_file, "w") as f:
                json.dump(predictions, f, indent=2)

        except Exception as e:
            logger.error(f"Error saving predictions for {game_id}: {e}")

    def _get_current_lines(self, game_id: str) -> Optional[Dict]:
        """Get current betting lines for a game"""
        try:
            # This would integrate with betting data sources
            # For now, return simulated data
            return {
                "spread": -7.5,
                "moneyline": {"home": -280, "away": 220},
                "total": 48.5,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        except:
            return None

    def _get_historical_lines(self, game_id: str) -> Optional[Dict]:
        """Get historical betting lines for comparison"""
        try:
            # This would get opening lines or lines from previous time
            # For now, return simulated historical data
            return {
                "spread": -6.5,
                "moneyline": {"home": -250, "away": 200},
                "total": 47.5,
                "timestamp": (datetime.now(timezone.utc) - timedelta(hours=6)).isoformat(),
            }
        except:
            return None

    def _calculate_line_change(self, historical: Dict, current: Dict) -> Dict[str, Any]:
        """Calculate changes between historical and current lines"""
        try:
            changes = {}

            # Spread change
            if historical.get("spread") and current.get("spread"):
                spread_change = current["spread"] - historical["spread"]
                changes["spread"] = {
                    "old": historical["spread"],
                    "new": current["spread"],
                    "change": spread_change,
                    "change_percent": abs(spread_change / abs(historical["spread"])) if historical["spread"] != 0 else 0,
                }

            # Total change
            if historical.get("total") and current.get("total"):
                total_change = current["total"] - historical["total"]
                changes["total"] = {
                    "old": historical["total"],
                    "new": current["total"],
                    "change": total_change,
                    "change_percent": abs(total_change / historical["total"]) if historical["total"] != 0 else 0,
                }

            # Moneyline change (more complex)
            if historical.get("moneyline") and current.get("moneyline"):
                ml_old = historical["moneyline"]
                ml_new = current["moneyline"]
                changes["moneyline"] = {
                    "old": ml_old,
                    "new": ml_new,
                    "home_change": ml_new["home"] - ml_old["home"] if isinstance(ml_new, dict) else 0,
                    "away_change": ml_new["away"] - ml_old["away"] if isinstance(ml_new, dict) else 0,
                }

            return changes

        except Exception as e:
            logger.error(f"Error calculating line change: {e}")
            return {"error": str(e)}

    def _assess_movement_significance(self, line_change: Dict) -> Dict[str, Any]:
        """Assess significance of line movement"""
        try:
            max_change_percent = 0
            significant_changes = []

            for line_type, change_data in line_change.items():
                if line_type == "error":
                    continue

                change_percent = change_data.get("change_percent", 0)
                max_change_percent = max(max_change_percent, change_percent)

                threshold = self.config["alerts"]["line_movement_threshold"]
                if change_percent > threshold:
                    significant_changes.append(line_type)

            if max_change_percent > 0.05:
                level = "critical"
            elif max_change_percent > 0.03:
                level = "high"
            elif max_change_percent > 0.01:
                level = "medium"
            else:
                level = "low"

            return {
                "max_change_percent": max_change_percent,
                "level": level,
                "significant_changes": significant_changes,
            }

        except Exception as e:
            logger.error(f"Error assessing movement significance: {e}")
            return {"level": "unknown", "error": str(e)}

    def _get_line_movement_recommendation(self, line_change: Dict, significance: Dict) -> str:
        """Get recommendation based on line movement"""
        level = significance.get("level", "low")

        if level == "critical":
            return "Update predictions immediately - significant line movement detected"
        elif level == "high":
            return "Consider prediction adjustments - notable line movement"
        elif level == "medium":
            return "Monitor for additional changes"
        else:
            return "No action needed"

    def _adjust_predictions_for_line_movement(self, game_id: str, line_change: Dict, significance: Dict) -> Dict[str, Any]:
        """Adjust predictions based on line movements"""
        try:
            current_predictions = self._get_previous_predictions(game_id)

            if not current_predictions:
                return {"error": "No current predictions to adjust"}

            # Get line movement factor
            spread_change = line_change.get("spread", {}).get("change", 0)
            adjustment_factor = 1.0

            # Adjust predictions based on line movement
            if abs(spread_change) > 0:
                # Positive spread change means favorite is more favored
                adjustment_factor = 1.0 + (spread_change * 0.01)  # Simple linear adjustment

            # Apply adjustment to ensemble prediction
            old_prediction = current_predictions.get("ensemble_prediction", 0.5)

            # Keep within [0.1, 0.9] range
            adjusted_prediction = max(0.1, min(0.9, old_prediction * adjustment_factor))

            current_predictions["ensemble_prediction"] = adjusted_prediction
            current_predictions["home_win_probability"] = adjusted_prediction
            current_predictions["away_win_probability"] = 1.0 - adjusted_prediction
            current_predictions["line_adjusted"] = True
            current_predictions["adjustment_factor"] = adjustment_factor
            current_predictions["line_movement"] = line_change

            return current_predictions

        except Exception as e:
            logger.error(f"Error adjusting predictions for line movement: {e}")
            return {"error": str(e)}

    def _publish_to_files(self, update_data: Dict) -> Dict[str, Any]:
        """Publish updates to file outputs"""
        try:
            file_results = {}

            for file_path in self.config["publishing"]["file_outputs"]:
                output_path = Path(file_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)

                with open(output_path, "w") as f:
                    json.dump(update_data, f, indent=2)

                file_results[file_path] = {
                    "success": True,
                    "path": str(output_path),
                    "size": output_path.stat().st_size,
                }

            return file_results

        except Exception as e:
            logger.error(f"Error publishing to files: {e}")
            return {"error": str(e)}

    def _send_webhooks(self, update_data: Dict) -> Dict[str, Any]:
        """Send webhook notifications"""
        # This would send notifications to webhook endpoints
        # For now, return empty result
        return {"webhooks_sent": 0, "endpoints": []}

    def _publish_to_social_media(self, update_data: Dict) -> Dict[str, Any]:
        """Publish updates to social media"""
        # This would integrate with social media APIs
        # For now, return empty result
        return {"social_posts": 0, "platforms": []}

    def _create_prediction_change_alert(self, change: Dict) -> Optional[Dict]:
        """Create alert for prediction change"""
        try:
            if not self._meets_alert_threshold(change.get("changes", {}), "prediction_change"):
                return None

            return {
                "type": "prediction_change",
                "severity": "medium",
                "game_id": change["game_id"],
                "game": change["game"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "details": {
                    "old_prediction": change["old_predictions"]["ensemble_prediction"],
                    "new_prediction": change["new_predictions"]["ensemble_prediction"],
                    "change_percent": change["changes"]["change_percent"],
                    "confidence": change["new_predictions"]["confidence"],
                },
                "message": f"Significant prediction change for {change['game']}: "
                           f"{change['old_predictions']['ensemble_prediction']:.2f} → "
                           f"{change['new_predictions']['ensemble_prediction']:.2f}",
            }

        except Exception as e:
            logger.error(f"Error creating prediction change alert: {e}")
            return None

    def _meets_alert_threshold(self, changes: Dict, alert_type: str) -> bool:
        """Check if changes meet alert threshold"""
        if alert_type == "prediction_change":
            threshold = self.config["alerts"]["significant_prediction_change"]
            return changes.get("change_percent", 0) > threshold

        return False

    def _save_alerts(self, alerts: List[Dict]):
        """Save alerts to log file"""
        try:
            alert_log_path = Path(self.config["storage"]["alert_log"])
            alert_log_path.parent.mkdir(parents=True, exist_ok=True)

            # Load existing alerts
            existing_alerts = []
            if alert_log_path.exists():
                with open(alert_log_path, "r") as f:
                    existing_alerts = json.load(f)

            # Add new alerts
            existing_alerts.extend(alerts)

            # Keep only last 1000 alerts
            existing_alerts = existing_alerts[-1000:]

            # Save updated alerts
            with open(alert_log_path, "w") as f:
                json.dump(existing_alerts, f, indent=2)

            # Update internal alert history
            self.alert_history.extend(alerts)
            if len(self.alert_history) > 100:
                self.alert_history = self.alert_history[-100:]

        except Exception as e:
            logger.error(f"Error saving alerts: {e}")

    def _send_alert_notifications(self, alerts: List[Dict]) -> Dict[str, Any]:
        """Send alert notifications"""
        # This would integrate with notification systems
        # For now, return empty result
        return {"sent_count": len(alerts), "channels": ["log"]}

    def _get_recent_game_results(self) -> List[Dict]:
        """Get recent game results for accuracy tracking"""
        # This would query actual game results
        # For now, return empty list
        return []

    def _get_prediction_for_game(self, game_id: str) -> Optional[Dict]:
        """Get stored prediction for a specific game"""
        return self._get_previous_predictions(game_id)

    def _evaluate_prediction_correctness(self, prediction: Dict, result: Dict) -> bool:
        """Evaluate if a prediction was correct"""
        try:
            predicted_winner = prediction.get("ensemble_prediction", 0.5) > 0.5
            actual_winner = result.get("home_points", 0) > result.get("away_points", 0)

            return predicted_winner == actual_winner

        except Exception as e:
            logger.error(f"Error evaluating prediction correctness: {e}")
            return False

    def get_gameday_status(self) -> Dict[str, Any]:
        """Get current game day prediction status"""
        return {
            "autonomator_id": self.agent_id,
            "active_games_count": len(self.active_games),
            "last_update_time": self.last_update_time.isoformat() if self.last_update_time else None,
            "prediction_history_entries": len(self.prediction_history),
            "alert_history_entries": len(self.alert_history),
            "config": self.config,
            "capabilities": [cap.name for cap in self._define_capabilities()],
        }


# Global instance
gameday_prediction_autonomator = GameDayPredictionAutonomator()