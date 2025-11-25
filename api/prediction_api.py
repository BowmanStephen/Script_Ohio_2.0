#!/usr/bin/env python3
"""
Simple Prediction API - Dynamic College Football Predictions

This API serves college football predictions dynamically using the Script Ohio 2.0
agent system instead of static JSON files.

Author: Claude Code Assistant
Created: 2025-11-25
Version: 1.0
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import asdict

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Go up two levels
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from flask import Flask, jsonify, request, abort
from flask_cors import CORS

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import agent system after setting path
try:
    from agents.analytics_orchestrator import AnalyticsOrchestrator
    from agents.core.agent_framework import PermissionLevel, AgentRequest
except ImportError as e:
    logger.error(f"Failed to import agent system: {e}")
    AnalyticsOrchestrator = None
    PermissionLevel = None
    AgentRequest = None

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for web app

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
        model_agent = agents_orchestrator.agent_factory.get_agent('default_model_engine')

        if model_agent:
            logger.info("✅ Agent system initialized successfully")
            logger.info(f"Model agent capabilities: {[cap.name for cap in model_agent.capabilities]}")
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
                with open(current_file, 'r') as f:
                    data = json.load(f)
                logger.info(f"Loaded {len(data)} games from {os.path.basename(current_file)}")
                return data
        
        logger.warning(f"No predictions file found in {web_app_public}")
        return []

    except Exception as e:
        logger.error(f"Error loading current week data: {str(e)}")
        return []

def predict_single_game(home_team: str, away_team: str, model_type: str = 'ridge_model_2025') -> Dict[str, Any]:
    """Generate prediction for a single game using the agent system"""
    if not model_agent:
        return {
            "error": "Model agent not available",
            "home_team": home_team,
            "away_team": away_team,
            "status": "error"
        }

    try:
        from agents.core.agent_framework import AgentRequest
        import time

        # Create prediction request
        request = AgentRequest(
            request_id=f'api_pred_{int(time.time())}',
            agent_type='model_engine',
            action='predict_game_outcome',
            parameters={
                'home_team': home_team,
                'away_team': away_team,
                'model_type': model_type,
                'include_confidence': True
            },
            user_context={'role': 'api'},
            timestamp=time.time(),
            priority=2
        )

        # Execute prediction
        from agents.core.agent_framework import PermissionLevel
        response = model_agent.execute_request(request, PermissionLevel.READ_EXECUTE)

        if response.status.value == 'completed' and response.result:
            return response.result
        else:
            return {
                "error": response.error_message or "Prediction failed",
                "home_team": home_team,
                "away_team": away_team,
                "status": "error"
            }

    except Exception as e:
        logger.error(f"Error predicting game {home_team} vs {away_team}: {str(e)}")
        return {
            "error": str(e),
            "home_team": home_team,
            "away_team": away_team,
            "status": "error"
        }

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "agent_system": model_agent is not None,
        "version": "1.0"
    })

@app.route('/api/predict', methods=['GET', 'POST'])
def predict_game():
    """Predict outcome for a single game"""

    # Handle both GET and POST
    if request.method == 'GET':
        home_team = request.args.get('home_team')
        away_team = request.args.get('away_team')
        model_type = request.args.get('model_type', 'ridge_model_2025')
    else:  # POST
        data = request.get_json() or {}
        home_team = data.get('home_team')
        away_team = data.get('away_team')
        model_type = data.get('model_type', 'ridge_model_2025')

    if not home_team or not away_team:
        return jsonify({
            "error": "Both home_team and away_team are required",
            "example": "GET /api/predict?home_team=Ohio%20State&away_team=Michigan"
        }), 400

    logger.info(f"Prediction request: {home_team} vs {away_team} using {model_type}")

    # Generate prediction
    prediction = predict_single_game(home_team, away_team, model_type)

    # Add metadata
    prediction['api_metadata'] = {
        "timestamp": datetime.now().isoformat(),
        "model_type": model_type,
        "request_source": "api"
    }

    return jsonify(prediction)

@app.route('/api/predictions/week/<int:week>', methods=['GET'])
def get_week_predictions(week):
    """Get predictions for all games in a week"""

    # Try to load existing data first
    existing_data = get_current_week_data()

    if not existing_data:
        return jsonify({
            "error": f"No data available for week {week}",
            "message": "Static predictions file not found"
        }), 404

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
            "note": "Data loaded from static file with live API capability available"
        }
    }

    return jsonify(response)

@app.route('/api/models', methods=['GET'])
def get_available_models():
    """Get list of available prediction models"""

    if not model_agent:
        return jsonify({
            "error": "Model agent not available",
            "available_models": []
        }), 503

    # Known models from the system
    models = [
        {
            "name": "ridge_model_2025",
            "display_name": "Ridge Regression",
            "type": "regression",
            "description": "Linear regression model with ridge regularization"
        },
        {
            "name": "xgb_home_win_model_2025",
            "display_name": "XGBoost",
            "type": "classification",
            "description": "Gradient boosted trees for win probability"
        },
        {
            "name": "fastai_home_win_model_2025",
            "display_name": "FastAI Neural Network",
            "type": "neural_network",
            "description": "Deep learning model using FastAI framework"
        },
        {
            "name": "random_forest_model_2025",
            "display_name": "Random Forest",
            "type": "ensemble",
            "description": "Random forest ensemble model"
        }
    ]

    return jsonify({
        "available_models": models,
        "agent_capabilities": [cap.name for cap in model_agent.capabilities],
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/stats', methods=['GET'])
def get_system_stats():
    """Get system statistics and agent info"""

    stats = {
        "system_status": "running",
        "agent_system": {
            "initialized": agents_orchestrator is not None,
            "model_agent_available": model_agent is not None,
            "registered_agents": len(agents_orchestrator.agent_factory.agent_registry) if agents_orchestrator else 0,
            "active_agents": len(agents_orchestrator.agent_factory.agents) if agents_orchestrator else 0
        },
        "api_info": {
            "version": "1.0",
            "endpoints": [
                "GET /health - Health check",
                "GET|POST /api/predict - Single game prediction",
                "GET /api/predictions/week/<week> - Weekly predictions",
                "GET /api/models - Available models",
                "GET /api/stats - System stats"
            ]
        },
        "timestamp": datetime.now().isoformat()
    }

    return jsonify(stats)

# Initialize agent system on startup
initialize_agent_system()

if __name__ == '__main__':
    # Run the Flask app
    logger.info("Starting Prediction API Server...")
    logger.info("Available endpoints:")
    logger.info("  GET  http://localhost:5000/health")
    logger.info("  GET  http://localhost:5000/api/predict?home_team=Ohio%20State&away_team=Michigan")
    logger.info("  POST http://localhost:5000/api/predict")
    logger.info("  GET  http://localhost:5000/api/predictions/week/14")
    logger.info("  GET  http://localhost:5000/api/models")
    logger.info("  GET  http://localhost:5000/api/stats")

    port = int(os.environ.get('FLASK_PORT', 5001))  # Use 5001 to avoid conflicts
    app.run(
        host='0.0.0.0',
        port=port,
        debug=True
    )