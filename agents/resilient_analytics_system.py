#!/usr/bin/env python3
"""
Resilient Analytics System
Integrates comprehensive error handling with the football analytics platform

This system provides:
- Circuit breakers to prevent cascade failures
- Intelligent retry mechanisms for transient failures
- Fallback systems for graceful degradation
- Comprehensive error classification and handling
- Automatic recovery and self-healing
"""

import time
import random
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from core.error_handling import (
    ErrorHandler, ErrorSeverity, ErrorCategory, RetryConfig, CircuitBreakerConfig,
    error_handler, circuit_breaker, retry, handle_errors, fallback_for, safe_execute
)

logger = logging.getLogger("resilient_analytics")

class ResilientDataLoader:
    """
    Data loader with comprehensive error handling
    Demonstrates circuit breakers, retries, and fallbacks
    """

    def __init__(self):
        # Circuit breaker for data loading
        data_circuit_config = CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=30.0
        )

        # Retry configuration for transient failures
        retry_config = RetryConfig(
            max_attempts=3,
            base_delay=1.0,
            max_delay=10.0
        )

        # Register circuit breaker
        error_handler.register_circuit_breaker("data_loader", data_circuit_config)

        # Simulate data availability
        self.data_sources = {
            "primary": True,    # Whether primary source is available
            "secondary": True,  # Whether secondary source is available
            "cache": True       # Whether cache is available
        }

    @circuit_breaker("data_loader")
    @retry()
    @handle_errors("DataLoading", ErrorSeverity.MEDIUM, "Unable to load data. Using cached version.")
    def load_team_data(self, season: str) -> Dict[str, Any]:
        """Load team data with comprehensive error handling"""

        # Simulate occasional failures
        if not self.data_sources["primary"]:
            raise ConnectionError("Primary data source unavailable")

        # Simulate network issues
        if random.random() < 0.2:  # 20% chance of failure
            raise TimeoutError("Network timeout while loading data")

        # Simulate successful load
        return {
            "season": season,
            "teams": 130,
            "games": 890,
            "source": "primary",
            "loaded_at": datetime.now().isoformat()
        }

    @fallback_for("load_team_data", priority=1)
    def load_team_data_fallback_secondary(self, season: str, **kwargs) -> Dict[str, Any]:
        """Fallback to secondary data source"""
        if not self.data_sources["secondary"]:
            raise ConnectionError("Secondary data source also unavailable")

        return {
            "season": season,
            "teams": 125,  # Slightly different data
            "games": 875,
            "source": "secondary",
            "loaded_at": datetime.now().isoformat(),
            "warning": "Using secondary data source"
        }

    @fallback_for("load_team_data", priority=2)
    def load_team_data_fallback_cache(self, season: str, **kwargs) -> Dict[str, Any]:
        """Fallback to cached data"""
        if not self.data_sources["cache"]:
            raise FileNotFoundError("No cached data available")

        return {
            "season": season,
            "teams": 118,  # Older cached data
            "games": 850,
            "source": "cache",
            "loaded_at": datetime.now().isoformat(),
            "warning": "Using cached data (may be outdated)"
        }

    @fallback_for("load_team_data", priority=3)
    def load_team_data_fallback_mock(self, season: str, **kwargs) -> Dict[str, Any]:
        """Ultimate fallback to mock data"""
        return {
            "season": season,
            "teams": 120,
            "games": 800,
            "source": "mock",
            "loaded_at": datetime.now().isoformat(),
            "warning": "Using mock data for demonstration"
        }

class ResilientModelEngine:
    """
    ML model engine with comprehensive error handling
    Demonstrates model fallbacks and degraded service
    """

    def __init__(self):
        self.models_available = {
            "primary": True,    # Main XGBoost model
            "backup": True,     # Backup Ridge model
            "simple": True      # Simple statistical model
        }

        # Circuit breaker for model inference
        model_circuit_config = CircuitBreakerConfig(
            failure_threshold=5,
            recovery_timeout=60.0
        )

        error_handler.register_circuit_breaker("model_engine", model_circuit_config)

    @circuit_breaker("model_engine")
    @handle_errors("ModelInference", ErrorSeverity.HIGH, "Prediction unavailable. Using fallback model.")
    def predict_game_outcome(self, home_team: str, away_team: str, features: Dict[str, Any]) -> Dict[str, Any]:
        """Predict game outcome with error handling"""

        if not self.models_available["primary"]:
            raise RuntimeError("Primary model unavailable")

        # Simulate model loading issues
        if random.random() < 0.15:  # 15% chance of failure
            raise RuntimeError("Model loading failed")

        # Simulate successful prediction
        return {
            "home_team": home_team,
            "away_team": away_team,
            "home_win_probability": round(random.uniform(0.3, 0.8), 3),
            "predicted_margin": round(random.uniform(-10, 10), 1),
            "confidence": round(random.uniform(0.6, 0.9), 3),
            "model_used": "primary_xgboost",
            "features_used": len(features)
        }

    @fallback_for("predict_game_outcome", priority=1)
    def predict_game_outcome_backup_model(self, home_team: str, away_team: str, features: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Fallback to backup model"""
        if not self.models_available["backup"]:
            raise RuntimeError("Backup model also unavailable")

        return {
            "home_team": home_team,
            "away_team": away_team,
            "home_win_probability": round(random.uniform(0.25, 0.75), 3),
            "predicted_margin": round(random.uniform(-8, 8), 1),
            "confidence": round(random.uniform(0.5, 0.8), 3),
            "model_used": "backup_ridge",
            "features_used": min(len(features), 10),  # Backup uses fewer features
            "warning": "Using backup model with reduced accuracy"
        }

    @fallback_for("predict_game_outcome", priority=2)
    def predict_game_outcome_simple_model(self, home_team: str, away_team: str, features: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Fallback to simple statistical model"""
        if not self.models_available["simple"]:
            raise RuntimeError("All models unavailable")

        # Simple prediction based on basic statistics
        home_advantage = 0.55  # Home team advantage

        return {
            "home_team": home_team,
            "away_team": away_team,
            "home_win_probability": home_advantage,
            "predicted_margin": 3.0,  # Average home advantage
            "confidence": 0.65,
            "model_used": "simple_statistical",
            "features_used": 0,  # No features used
            "warning": "Using simple statistical model"
        }

class ResilientAnalyticsAgent:
    """
    Analytics agent with comprehensive error handling
    Demonstrates graceful degradation and error recovery
    """

    def __init__(self, agent_id: str, data_loader: ResilientDataLoader, model_engine: ResilientModelEngine):
        self.agent_id = agent_id
        self.data_loader = data_loader
        self.model_engine = model_engine

        # Track performance and errors
        self.analysis_results = []

    def analyze_team_performance(self, team_name: str, season: str) -> Dict[str, Any]:
        """
        Analyze team performance with comprehensive error handling
        Demonstrates multi-layer error handling and graceful degradation
        """

        analysis_start = time.time()
        error_count = 0

        try:
            # Step 1: Load data with fallbacks
            logger.info(f"Loading data for {team_name} {season}")
            team_data = safe_execute(
                self.data_loader.load_team_data,
                season,
                default_value={"teams": 0, "games": 0}
            )

            if not team_data:
                raise RuntimeError("Failed to load any data")

            # Step 2: Perform basic analysis (always succeeds)
            basic_analysis = {
                "team": team_name,
                "season": season,
                "data_quality": "good" if team_data.get("source") != "mock" else "limited",
                "total_teams": team_data.get("teams", 0),
                "total_games": team_data.get("games", 0),
                "analysis_timestamp": datetime.now().isoformat()
            }

            # Step 3: Try advanced analysis with model predictions
            try:
                logger.info(f"Running model predictions for {team_name}")

                # Create mock features
                features = {
                    "offensive_efficiency": round(random.uniform(0.3, 0.8), 3),
                    "defensive_efficiency": round(random.uniform(0.2, 0.7), 3),
                    "talent_differential": round(random.uniform(-5, 5), 2)
                }

                prediction = self.model_engine.predict_game_outcome(
                    home_team=team_name,
                    away_team="Opponent",
                    features=features
                )

                advanced_analysis = {
                    "prediction_confidence": prediction.get("confidence", 0.5),
                    "model_used": prediction.get("model_used", "unknown"),
                    "features_analyzed": len(features),
                    "prediction_available": True
                }

            except Exception as e:
                logger.warning(f"Model prediction failed: {str(e)}")
                advanced_analysis = {
                    "prediction_confidence": 0.0,
                    "model_used": "none",
                    "features_analyzed": 0,
                    "prediction_available": False,
                    "error": str(e)
                }
                error_count += 1

            # Step 4: Combine results
            analysis_time = time.time() - analysis_start

            final_result = {
                **basic_analysis,
                **advanced_analysis,
                "agent_id": self.agent_id,
                "analysis_time_seconds": round(analysis_time, 3),
                "errors_encountered": error_count,
                "analysis_success": error_count == 0,
                "degraded_service": error_count > 0
            }

            # Record the analysis
            self.analysis_results.append({
                "timestamp": datetime.now().isoformat(),
                "team": team_name,
                "success": error_count == 0,
                "errors": error_count,
                "analysis_time": analysis_time
            })

            logger.info(f"Analysis completed for {team_name}: {'SUCCESS' if error_count == 0 else 'DEGRADED'}")
            return final_result

        except Exception as e:
            # Ultimate fallback - minimal information
            logger.error(f"Complete analysis failure for {team_name}: {str(e)}")

            error_report = ErrorHandler.create_error_report(
                error=e,
                error_type="CompleteAnalysisFailure",
                severity=ErrorSeverity.HIGH,
                context={
                    "agent_id": self.agent_id,
                    "team": team_name,
                    "season": season
                },
                user_facing_message=f"Unable to complete analysis for {team_name}. Please try again later."
            )

            error_handler.handle_error(error_report)

            return {
                "team": team_name,
                "season": season,
                "agent_id": self.agent_id,
                "analysis_success": False,
                "errors_encountered": 1,
                "analysis_time_seconds": round(time.time() - analysis_start, 3),
                "error_message": "Analysis failed completely",
                "user_facing_message": "Analysis temporarily unavailable"
            }

    def get_agent_metrics(self) -> Dict[str, Any]:
        """Get agent performance and error metrics"""
        if not self.analysis_results:
            return {"message": "No analyses performed yet"}

        total_analyses = len(self.analysis_results)
        successful_analyses = sum(1 for r in self.analysis_results if r["success"])
        failed_analyses = total_analyses - successful_analyses
        avg_analysis_time = sum(r["analysis_time"] for r in self.analysis_results) / total_analyses

        return {
            "agent_id": self.agent_id,
            "total_analyses": total_analyses,
            "successful_analyses": successful_analyses,
            "failed_analyses": failed_analyses,
            "success_rate": round(successful_analyses / total_analyses, 3),
            "average_analysis_time": round(avg_analysis_time, 3),
            "error_metrics": error_handler.get_error_metrics()
        }

def demo_resilient_analytics():
    """Demonstrate resilient analytics capabilities"""
    print("🛡️ Resilient Analytics Demo")
    print("=" * 60)
    print("Implementing Comprehensive Error Handling and Recovery")
    print("=" * 60)

    # Create resilient components
    print(f"\n🔧 Initializing Resilient Components")
    data_loader = ResilientDataLoader()
    model_engine = ResilientModelEngine()
    analytics_agent = ResilientAnalyticsAgent("resilient_analyst_001", data_loader, model_engine)

    # Test data loading with failures
    print(f"\n📊 Testing Data Loading with Error Handling")

    # Simulate primary source failure
    print(f"   Testing with primary source unavailable...")
    # Get sample teams from data
    from src.utils.data import get_teams_from_data, get_current_season
    teams = get_teams_from_data(limit=5)
    current_season = get_current_season()
    sample_team1 = teams[0] if teams else "Sample Team 1"
    sample_team2 = teams[1] if len(teams) > 1 else "Sample Team 2"
    
    data_loader.data_sources["primary"] = False

    result1 = analytics_agent.analyze_team_performance(sample_team1, str(current_season))
    print(f"   Result: {'SUCCESS' if result1['analysis_success'] else 'DEGRADED'}")
    print(f"   Data source: {result1.get('data_quality', 'unknown')}")
    print(f"   Errors: {result1['errors_encountered']}")

    # Test model engine failures
    print(f"\n🤖 Testing Model Engine with Failures")

    # Restore primary data but simulate model issues
    data_loader.data_sources["primary"] = True
    model_engine.models_available["primary"] = False

    result2 = analytics_agent.analyze_team_performance(sample_team2, str(current_season))
    print(f"   Result: {'SUCCESS' if result2['analysis_success'] else 'DEGRADED'}")
    print(f"   Model used: {result2.get('model_used', 'none')}")
    print(f"   Prediction available: {result2.get('prediction_available', False)}")

    # Test complete system resilience
    print(f"\n⚡ Testing Complete System Resilience")

    # Simulate multiple failures
    data_loader.data_sources["primary"] = False
    data_loader.data_sources["secondary"] = False
    model_engine.models_available["primary"] = False
    model_engine.models_available["backup"] = False

    sample_team3 = teams[2] if len(teams) > 2 else "Sample Team 3"
    sample_team4 = teams[3] if len(teams) > 3 else "Sample Team 4"
    
    result3 = analytics_agent.analyze_team_performance(sample_team3, str(current_season))
    print(f"   Result: {'SUCCESS' if result3['analysis_success'] else 'DEGRADED'}")
    print(f"   System still functional: {result3['agent_id'] in result3}")
    print(f"   Errors handled gracefully: {result3['errors_encountered']}")

    # Test recovery
    print(f"\n🔄 Testing System Recovery")

    # Restore all services
    data_loader.data_sources = {"primary": True, "secondary": True, "cache": True}
    model_engine.models_available = {"primary": True, "backup": True, "simple": True}

    result4 = analytics_agent.analyze_team_performance(sample_team4, str(current_season))
    print(f"   Result: {'SUCCESS' if result4['analysis_success'] else 'DEGRADED'}")
    print(f"   Full functionality restored: {result4['errors_encountered'] == 0}")
    print(f"   Analysis time: {result4['analysis_time_seconds']}s")

    # Get comprehensive metrics
    print(f"\n📊 System Performance Metrics")
    agent_metrics = analytics_agent.get_agent_metrics()

    print(f"   Total analyses: {agent_metrics['total_analyses']}")
    print(f"   Success rate: {agent_metrics['success_rate']:.1%}")
    print(f"   Average analysis time: {agent_metrics['average_analysis_time']}s")

    # Get error handling metrics
    error_metrics = agent_metrics.get('error_metrics', {})
    print(f"\n🛡️ Error Handling Metrics")
    if error_metrics:
        print(f"   Total errors handled: {error_metrics.get('total_errors', 0)}")
        print(f"   Recovery rate: {error_metrics.get('recovery_rate', 0):.1%}")
        print(f"   Active circuit breakers: {len(error_metrics.get('circuit_breakers', {}))}")
        print(f"   Fallback strategies: {error_metrics.get('fallback_metrics', {}).get('registered_fallbacks', 0)}")

    print(f"\n✅ Resilient Analytics Demo Complete!")
    print(f"✅ Circuit breakers: Preventing cascade failures")
    print(f"✅ Retry mechanisms: Handling transient failures")
    print(f"✅ Fallback systems: Graceful degradation")
    print(f"✅ Error classification: Intelligent error handling")
    print(f"✅ Automatic recovery: Self-healing capabilities")

if __name__ == "__main__":
    demo_resilient_analytics()