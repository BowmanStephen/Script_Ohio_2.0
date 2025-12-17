#!/usr/bin/env python3
"""
Simple Prediction API - Dynamic College Football Predictions

This API serves college football predictions dynamically using the Script Ohio 2.0
agent system instead of static JSON files.

Author: Claude Code Assistant
Created: 2025-11-25
Version: 1.0
"""

import json
import logging
import os
import sys
from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict, List, Optional

# Add project root to Python path
project_root = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)  # Go up two levels
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from flask import Flask, abort, jsonify, request
from flask_cors import CORS

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import agent system after setting path
try:
    from agents.analytics_orchestrator import AnalyticsOrchestrator
    from agents.core.agent_framework import AgentRequest, PermissionLevel
except ImportError as e:
    logger.error(f"Failed to import agent system: {e}")
    AnalyticsOrchestrator = None
    PermissionLevel = None
    AgentRequest = None

# Initialize Flask app
app = Flask(__name__)

# CORS configuration: restrict to frontend origin in production
# In development, allow localhost origins; in production, require explicit config
is_production = os.getenv("FLASK_ENV") == "production"
cors_origins_env = os.getenv("CORS_ORIGINS")

if is_production:
    if not cors_origins_env:
        logger.warning(
            "⚠️  CORS_ORIGINS not set in production! Defaulting to empty (no CORS)."
        )
        cors_origins = []
    else:
        cors_origins = cors_origins_env.split(",")
        if "*" in cors_origins:
            raise ValueError(
                "CORS_ORIGINS cannot be '*' in production. "
                "Set specific origins (e.g., CORS_ORIGINS=https://yourdomain.com)"
            )
else:
    # Development: default to localhost origins
    cors_origins = (
        cors_origins_env.split(",")
        if cors_origins_env
        else ["http://localhost:5173", "http://localhost:3000"]
    )
    if "*" in cors_origins:
        logger.warning(
            "⚠️  CORS_ORIGINS='*' in development - this is insecure for production!"
        )

CORS(app, origins=cors_origins)  # Enable CORS for web app

# Initialize agent system
agents_orchestrator = None
model_agent = None


def initialize_agent_system():
    """Initialize the agent system for predictions"""
    global agents_orchestrator, model_agent

    try:
        from agents.analytics_orchestrator import AnalyticsOrchestrator
        from agents.core.agent_framework import PermissionLevel

        logger.info("Initializing agent system...")
        agents_orchestrator = AnalyticsOrchestrator()

        # Get the model engine agent
        model_agent = agents_orchestrator.agent_factory.get_agent(
            "default_model_engine"
        )

        if model_agent:
            logger.info("✅ Agent system initialized successfully")
            logger.info(
                f"Model agent capabilities: {[cap.name for cap in model_agent.capabilities]}"
            )
        else:
            logger.error("❌ Model agent not found")

    except Exception as e:
        logger.error(f"Failed to initialize agent system: {str(e)}")
        model_agent = None


def get_current_week_data():
    """Load current week data for predictions"""
    try:
        # Try enhanced/calibrated predictions first, then fall back to standard
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        web_app_public = os.path.join(project_root, "web_app", "public")

        # Priority order: enhanced calibrated > unified > standard
        prediction_files = [
            os.path.join(web_app_public, "week14_predictions_enhanced_calibrated.json"),
            os.path.join(web_app_public, "week14_predictions_unified.json"),
            os.path.join(web_app_public, "week14_model_predictions.json"),
        ]

        for current_file in prediction_files:
            if os.path.exists(current_file):
                with open(current_file, "r") as f:
                    data = json.load(f)
                logger.info(
                    f"Loaded {len(data)} games from {os.path.basename(current_file)}"
                )
                return data

        logger.warning(f"No predictions file found in {web_app_public}")
        return []

    except Exception as e:
        logger.error(f"Error loading current week data: {str(e)}")
        return []


def predict_single_game(
    home_team: str, away_team: str, model_type: str = "ridge_model_2025"
) -> Dict[str, Any]:
    """Generate prediction for a single game using the agent system"""
    if not model_agent:
        return {
            "error": "Model agent not available",
            "home_team": home_team,
            "away_team": away_team,
            "status": "error",
        }

    try:
        import time

        from agents.core.agent_framework import AgentRequest

        # Create prediction request
        request = AgentRequest(
            request_id=f"api_pred_{int(time.time())}",
            agent_type="model_engine",
            action="predict_game_outcome",
            parameters={
                "home_team": home_team,
                "away_team": away_team,
                "model_type": model_type,
                "include_confidence": True,
            },
            user_context={"role": "api"},
            timestamp=time.time(),
            priority=2,
        )

        # Execute prediction
        from agents.core.agent_framework import PermissionLevel

        response = model_agent.execute_request(request, PermissionLevel.READ_EXECUTE)

        if response.status.value == "completed" and response.result:
            return response.result
        else:
            return {
                "error": response.error_message or "Prediction failed",
                "home_team": home_team,
                "away_team": away_team,
                "status": "error",
            }

    except Exception as e:
        logger.error(f"Error predicting game {home_team} vs {away_team}: {str(e)}")
        return {
            "error": str(e),
            "home_team": home_team,
            "away_team": away_team,
            "status": "error",
        }


# Validated API Request Models
try:
    from pydantic import BaseModel, Field, ValidationError

    class PredictionRequest(BaseModel):
        home_team: str = Field(..., description="Name of the home team")
        away_team: str = Field(..., description="Name of the away team")
        model_type: str = Field(
            "ridge_model_2025", description="Model to use for prediction"
        )

except ImportError:
    # Fallback if pydantic not available (should be installed)
    BaseModel = object
    logger.warning("Pydantic not found, validation disabled")


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify(
        {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "agent_system": model_agent is not None,
            "version": "1.0",
        }
    )


@app.route("/api/predict", methods=["GET", "POST"])
def predict_game():
    """Predict outcome for a single game"""

    # Handle both GET and POST
    if request.method == "GET":
        home_team = request.args.get("home_team")
        away_team = request.args.get("away_team")
        model_type = request.args.get("model_type", "ridge_model_2025")

        if not home_team or not away_team:
            return jsonify(
                {
                    "error": "Both home_team and away_team are required",
                    "example": "GET /api/predict?home_team=Ohio%20State&away_team=Michigan",
                }
            ), 400

    else:  # POST
        data = request.get_json() or {}
        try:
            # Validate with Pydantic if available
            if BaseModel != object:
                pred_request = PredictionRequest(**data)
                home_team = pred_request.home_team
                away_team = pred_request.away_team
                model_type = pred_request.model_type
            else:
                home_team = data.get("home_team")
                away_team = data.get("away_team")
                model_type = data.get("model_type", "ridge_model_2025")

                if not home_team or not away_team:
                    raise ValueError("Both home_team and away_team are required")

        except (ValueError, ValidationError) as e:
            return jsonify(
                {
                    "error": str(e),
                    "example": {"home_team": "Ohio State", "away_team": "Michigan"},
                }
            ), 400

    logger.info(f"Prediction request: {home_team} vs {away_team} using {model_type}")

    # Generate prediction
    prediction = predict_single_game(home_team, away_team, model_type)

    # Add metadata
    prediction["api_metadata"] = {
        "timestamp": datetime.now().isoformat(),
        "model_type": model_type,
        "request_source": "api",
    }

    return jsonify(prediction)


@app.route("/api/predictions/week/<int:week>", methods=["GET"])
def get_week_predictions(week):
    """Get predictions for all games in a week"""

    # Try to load existing data first
    existing_data = get_current_week_data()

    if not existing_data:
        return jsonify(
            {
                "error": f"No data available for week {week}",
                "message": "Static predictions file not found",
            }
        ), 404

    logger.info(f"Returning {len(existing_data)} predictions for week {week}")

    # Add API metadata
    response = {
        "week": week,
        "season": 2025,
        "total_games": len(existing_data),
        "predictions": existing_data,
        "api_metadata": {
            "timestamp": datetime.now().isoformat(),
            "source": "static_file_with_live_api_capability",
            "note": "Data loaded from static file with live API capability available",
        },
    }

    return jsonify(response)


@app.route("/api/predictions/bowls", methods=["GET"])
def get_bowls_predictions():
    """Get predictions for all bowl games"""

    try:
        # Load bowls predictions from the synced file
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        bowls_file = os.path.join(
            project_root, "web_app", "public", "bowls_2025_predictions.json"
        )

        if not os.path.exists(bowls_file):
            return jsonify(
                {
                    "error": "Bowl predictions not found",
                    "message": "Run sync_web_app_data.py to generate bowl predictions",
                }
            ), 404

        with open(bowls_file, "r") as f:
            bowls_data = json.load(f)

        # Extract games list
        games = bowls_data.get("games", [])

        logger.info(f"Returning {len(games)} bowl predictions")

        # Add API metadata
        response = {
            "season": bowls_data.get("season", 2025),
            "predictions_type": "bowls",
            "total_games": len(games),
            "model_info": bowls_data.get("model", {}),
            "generated_at": bowls_data.get("generated_at"),
            "predictions": games,
            "api_metadata": {
                "timestamp": datetime.now().isoformat(),
                "source": "bowl_predictions_json",
                "note": "Bowl game predictions from Ridge + XGBoost ensemble",
            },
        }

        return jsonify(response)

    except Exception as e:
        logger.error(f"Error loading bowl predictions: {str(e)}")
        return jsonify(
            {"error": "Failed to load bowl predictions", "message": str(e)}
        ), 500


@app.route("/api/models", methods=["GET"])
def get_available_models():
    """Get list of available prediction models"""

    if not model_agent:
        return jsonify(
            {"error": "Model agent not available", "available_models": []}
        ), 503

    # Known models from the system
    models = [
        {
            "name": "ridge_model_2025",
            "display_name": "Ridge Regression",
            "type": "regression",
            "description": "Linear regression model with ridge regularization",
        },
        {
            "name": "xgb_home_win_model_2025",
            "display_name": "XGBoost",
            "type": "classification",
            "description": "Gradient boosted trees for win probability",
        },
        {
            "name": "fastai_home_win_model_2025",
            "display_name": "FastAI Neural Network",
            "type": "neural_network",
            "description": "Deep learning model using FastAI framework",
        },
        {
            "name": "random_forest_model_2025",
            "display_name": "Random Forest",
            "type": "ensemble",
            "description": "Random forest ensemble model",
        },
    ]

    return jsonify(
        {
            "available_models": models,
            "agent_capabilities": [cap.name for cap in model_agent.capabilities],
            "timestamp": datetime.now().isoformat(),
        }
    )


@app.route("/api/stats", methods=["GET"])
def get_system_stats():
    """Get system statistics and agent info"""

    stats = {
        "system_status": "running",
        "agent_system": {
            "initialized": agents_orchestrator is not None,
            "model_agent_available": model_agent is not None,
            "registered_agents": len(agents_orchestrator.agent_factory.agent_registry)
            if agents_orchestrator
            else 0,
            "active_agents": len(agents_orchestrator.agent_factory.agents)
            if agents_orchestrator
            else 0,
        },
        "api_info": {
            "version": "1.0",
            "endpoints": [
                "GET /health - Health check",
                "GET|POST /api/predict - Single game prediction",
                "GET /api/predictions/week/<week> - Weekly predictions",
                "GET /api/models - Available models",
                "GET /api/stats - System stats",
                "GET /api/cfbd/scoreboard - CFBD scoreboard data",
                "GET /api/cfbd/games - CFBD games data",
                "GET /api/cfbd/advanced-stats - CFBD advanced statistics",
                "GET /api/cfbd/media - CFBD game media",
                "GET /api/cfbd/calendar - CFBD calendar",
                "GET /api/cfbd/box-score - CFBD box score",
                "GET /api/cfbd/matchup - Team matchup",
                "GET /api/cfbd/roster - Team roster",
                "GET /api/cfbd/win-probabilities - Win probabilities",
                "GET /api/cfbd/recruiting - Recruiting data",
            ],
        },
        "timestamp": datetime.now().isoformat(),
    }

    return jsonify(stats)


@app.route("/api/cfbd/games", methods=["GET"])
def api_cfbd_games():
    """Proxy CFBD games endpoint - secure BFF pattern (no API keys exposed)"""
    try:
        from src.cfbd_client.unified_client import UnifiedCFBDClient

        year = request.args.get("year", type=int)
        week = request.args.get("week", type=int)
        season_type = request.args.get("season_type", "regular")
        team = request.args.get("team", type=str)

        if not year:
            return jsonify(
                {"status": "error", "message": "year parameter is required"}
            ), 400

        # Use unified client (CFBD_API_KEY from backend env, never exposed)
        client = UnifiedCFBDClient()
        games = client.get_games(
            year=year, week=week, season_type=season_type, team=team
        )

        return jsonify(
            {
                "status": "success",
                "data": games,
                "count": len(games),
                "year": year,
                "week": week,
            }
        )
    except Exception as e:
        logger.error(f"CFBD games proxy error: {e}")
        return jsonify({"status": "error", "message": "Failed to fetch games"}), 500


@app.route("/api/cfbd/scoreboard", methods=["GET"])
def api_cfbd_scoreboard():
    """Proxy CFBD scoreboard endpoint - secure BFF pattern (no API keys exposed)"""
    try:
        from src.cfbd_client.unified_client import UnifiedCFBDClient

        year = request.args.get("year", type=int) or 2025
        week = request.args.get("week", type=int)
        season_type = request.args.get("season_type", "regular")
        team = request.args.get("team", type=str)
        use_graphql = request.args.get("use_graphql", "true").lower() == "true"

        # Use unified client (CFBD_API_KEY from backend env, never exposed)
        client = UnifiedCFBDClient()

        # Try GraphQL if requested, available, and week is present (GraphQL scoreboard needs week usually, or inefficient)
        data = None
        source = "rest"

        if use_graphql:
            # Note: get_scoreboard_graphql returns {'data': {'game': [...]}} structure from GQL
            gql_result = client.get_scoreboard_graphql(year=year, week=week)
            if gql_result and "data" in gql_result:
                data = gql_result["data"].get("game", [])
                source = "graphql"

        # Fallback to REST
        if data is None:
            data = client.get_games(
                year=year, week=week, season_type=season_type, team=team
            )
            source = "rest"

        return jsonify(
            {
                "status": "success",
                "data": data or [],
                "count": len(data) if data else 0,
                "year": year,
                "week": week,
                "season_type": season_type,
                "source": source,
            }
        )
    except Exception as e:
        logger.error(f"CFBD scoreboard proxy error: {e}")
        return jsonify(
            {"status": "error", "message": "Failed to fetch scoreboard"}
        ), 500


@app.route("/api/cfbd/ratings", methods=["GET"])
def api_cfbd_ratings():
    """Proxy CFBD ratings endpoint - secure BFF pattern"""
    try:
        from src.cfbd_client.unified_client import UnifiedCFBDClient

        year = request.args.get("year", type=int)
        week = request.args.get("week", type=int)

        if not year:
            return jsonify(
                {"status": "error", "message": "year parameter is required"}
            ), 400

        # Use unified client (CFBD_API_KEY from backend env, never exposed)
        client = UnifiedCFBDClient()
        ratings = client.get_ratings(year=year, week=week)

        return jsonify(
            {
                "status": "success",
                "data": ratings,
                "count": len(ratings),
                "year": year,
                "week": week,
            }
        )
    except Exception as e:
        logger.error(f"CFBD ratings proxy error: {e}")
        return jsonify({"status": "error", "message": "Failed to fetch ratings"}), 500


@app.route("/api/cfbd/advanced-stats", methods=["GET"])
def api_cfbd_advanced_stats():
    """Proxy CFBD advanced stats endpoint - secure BFF pattern"""
    try:
        from src.cfbd_client.unified_client import UnifiedCFBDClient

        year = request.args.get("year", type=int)
        team = request.args.get("team", type=str)

        if not year:
            return jsonify(
                {"status": "error", "message": "year parameter is required"}
            ), 400

        # Use unified client (CFBD_API_KEY from backend env, never exposed)
        client = UnifiedCFBDClient()
        stats = client.get_advanced_stats(year=year, team=team)

        return jsonify(
            {
                "status": "success",
                "data": stats or [],
                "count": len(stats) if stats else 0,
                "year": year,
                "team": team,
            }
        )
    except Exception as e:
        logger.error(f"CFBD advanced stats proxy error: {e}")
        return jsonify(
            {"status": "error", "message": "Failed to fetch advanced stats"}
        ), 500


@app.route("/api/cfbd/media", methods=["GET"])
def api_cfbd_media():
    """Proxy CFBD game media endpoint"""
    try:
        from src.cfbd_client.unified_client import UnifiedCFBDClient

        year = request.args.get("year", type=int) or 2025
        week = request.args.get("week", type=int)
        team = request.args.get("team", type=str)
        conference = request.args.get("conference", type=str)

        client = UnifiedCFBDClient()
        media = client.get_game_media(
            year=year, week=week, team=team, conference=conference
        )

        return jsonify(
            {"status": "success", "data": media, "count": len(media), "year": year}
        )
    except Exception as e:
        logger.error(f"CFBD media proxy error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/cfbd/calendar", methods=["GET"])
def api_cfbd_calendar():
    """Proxy CFBD calendar endpoint"""
    try:
        from src.cfbd_client.unified_client import UnifiedCFBDClient

        year = request.args.get("year", type=int) or 2025

        client = UnifiedCFBDClient()
        calendar = client.get_calendar(year=year)

        return jsonify(
            {
                "status": "success",
                "data": calendar,
                "count": len(calendar),
                "year": year,
            }
        )
    except Exception as e:
        logger.error(f"CFBD calendar proxy error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/cfbd/box-score", methods=["GET"])
def api_cfbd_box_score():
    """Proxy CFBD box score endpoint"""
    try:
        from src.cfbd_client.unified_client import UnifiedCFBDClient

        game_id = request.args.get("game_id", type=int)

        if not game_id:
            return jsonify({"status": "error", "message": "game_id required"}), 400

        client = UnifiedCFBDClient()
        box = client.get_box_score(game_id=game_id)

        return jsonify({"status": "success", "data": box})
    except Exception as e:
        logger.error(f"CFBD box score proxy error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/cfbd/matchup", methods=["GET"])
def api_cfbd_matchup():
    """Proxy CFBD matchup endpoint"""
    try:
        from src.cfbd_client.unified_client import UnifiedCFBDClient

        team1 = request.args.get("team1", type=str)
        team2 = request.args.get("team2", type=str)
        min_year = request.args.get("min_year", type=int)
        max_year = request.args.get("max_year", type=int)

        if not team1 or not team2:
            return jsonify(
                {"status": "error", "message": "team1 and team2 required"}
            ), 400

        client = UnifiedCFBDClient()
        matchup = client.get_team_matchup(
            team1=team1, team2=team2, min_year=min_year, max_year=max_year
        )

        return jsonify(
            {"status": "success", "data": matchup, "team1": team1, "team2": team2}
        )
    except Exception as e:
        logger.error(f"CFBD matchup proxy error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/cfbd/roster", methods=["GET"])
def api_cfbd_roster():
    """Proxy CFBD roster endpoint"""
    try:
        from src.cfbd_client.unified_client import UnifiedCFBDClient

        year = request.args.get("year", type=int) or 2025
        team = request.args.get("team", type=str)

        if not team:
            return jsonify({"status": "error", "message": "team required"}), 400

        client = UnifiedCFBDClient()
        roster = client.get_roster(year=year, team=team)

        return jsonify(
            {
                "status": "success",
                "data": roster,
                "count": len(roster),
                "year": year,
                "team": team,
            }
        )
    except Exception as e:
        logger.error(f"CFBD roster proxy error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/cfbd/win-probabilities", methods=["GET"])
def api_cfbd_win_probs():
    """Proxy CFBD win probabilities endpoint"""
    try:
        from src.cfbd_client.unified_client import UnifiedCFBDClient

        year = request.args.get("year", type=int) or 2025
        week = request.args.get("week", type=int)
        team = request.args.get("team", type=str)

        client = UnifiedCFBDClient()
        probs = client.get_win_probabilities(year=year, week=week, team=team)

        return jsonify(
            {"status": "success", "data": probs, "count": len(probs), "year": year}
        )
    except Exception as e:
        logger.error(f"CFBD win probs proxy error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/cfbd/recruiting", methods=["GET"])
def api_cfbd_recruiting():
    """Proxy CFBD recruiting endpoint (supports optional GraphQL)"""
    try:
        from src.cfbd_client.unified_client import UnifiedCFBDClient

        year = request.args.get("year", type=int) or 2025
        team = request.args.get("team", type=str)
        use_graphql = request.args.get("use_graphql", "true").lower() == "true"

        client = UnifiedCFBDClient()

        # Try GraphQL if requested and available
        data = None
        source = "rest"

        if use_graphql:
            data = client.get_recruiting_graphql(year=year, team=team)
            if data:
                source = "graphql"

        # Fallback to REST
        if not data:
            data = client.get_recruiting(year=year, team=team)
            source = "rest"

        return jsonify(
            {
                "status": "success",
                "data": data,
                "source": source,
                "year": year,
                "team": team,
            }
        )
    except Exception as e:
        logger.error(f"CFBD recruiting proxy error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# Initialize agent system on startup (skip during testing)
if os.environ.get("FLASK_TESTING") != "true":
    initialize_agent_system()

if __name__ == "__main__":
    # Run the Flask app
    logger.info("Starting Prediction API Server...")
    logger.info("Available endpoints:")
    logger.info("  GET  http://localhost:5000/health")
    logger.info(
        "  GET  http://localhost:5000/api/predict?home_team=Ohio%20State&away_team=Michigan"
    )
    logger.info("  POST http://localhost:5000/api/predict")
    logger.info("  GET  http://localhost:5000/api/predictions/week/14")
    logger.info("  GET  http://localhost:5000/api/models")
    logger.info("  GET  http://localhost:5000/api/stats")
    logger.info("  GET  http://localhost:5000/api/cfbd/scoreboard?year=2025&week=12")
    logger.info("  GET  http://localhost:5000/api/cfbd/advanced-stats?year=2025")

    port = int(os.environ.get("FLASK_PORT", 5001))  # Use 5001 to avoid conflicts
    app.run(host="0.0.0.0", port=port, debug=True)
