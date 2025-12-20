#!/usr/bin/env python3
"""
FBS Bowl Game API Server

Provides API endpoints for FBS-only bowl game data and analytics.
Uses real prediction data with all 4 models: Ridge, XGBoost, FastAI, Ensemble.
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

from flask import Flask, jsonify, request
from flask_cors import CORS

# Add project root to Python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173", "http://localhost:3000"])


# Load real FBS bowl predictions
def load_fbs_bowl_predictions():
    """Load the most recent FBS-only bowl predictions"""
    try:
        # Try latest file first
        latest_file = PROJECT_ROOT / "predictions" / "fbs_bowl_predictions_latest.json"
        if latest_file.exists():
            with open(latest_file, "r") as f:
                return json.load(f)

        # Fallback to timestamped files
        predictions_dir = PROJECT_ROOT / "predictions"
        if predictions_dir.exists():
            fbs_files = [
                f
                for f in predictions_dir.glob("fbs_bowl_predictions_*.json")
                if f.name != "fbs_bowl_predictions_latest.json"
            ]
            if fbs_files:
                latest = sorted(fbs_files, key=lambda x: x.stat().st_mtime)[-1]
                with open(latest, "r") as f:
                    return json.load(f)

        # Fallback to legacy file
        legacy_file = PROJECT_ROOT / "predictions" / "bowls_2025_predictions.json"
        if legacy_file.exists():
            with open(legacy_file, "r") as f:
                return json.load(f)

        return None
    except Exception as e:
        print(f"Error loading predictions: {e}")
        return None


# Load predictions at startup
BOWL_PREDICTIONS = load_fbs_bowl_predictions()
print(
    f"Loaded {len(BOWL_PREDICTIONS.get('games', []))} FBS bowl predictions"
    if BOWL_PREDICTIONS
    else "Using fallback data"
)


# API Endpoints
@app.route("/")
def index():
    """API health check"""
    return jsonify(
        {
            "status": "healthy",
            "service": "FBS Bowl Prediction API",
            "version": "2.0",
            "data_source": "FBS-only predictions with Ridge, XGBoost, FastAI, Ensemble models",
            "total_games": (
                len(BOWL_PREDICTIONS.get("games", [])) if BOWL_PREDICTIONS else 0
            ),
            "last_updated": (
                BOWL_PREDICTIONS.get("generated_at") if BOWL_PREDICTIONS else None
            ),
        }
    )


@app.route("/api/bowl-games")
def get_bowl_games():
    """Get all FBS bowl game predictions"""
    if not BOWL_PREDICTIONS:
        return (
            jsonify(
                {
                    "success": False,
                    "error": "No prediction data available",
                    "message": "Please generate predictions first using scripts/generate_fbs_bowl_predictions.py",
                }
            ),
            500,
        )

    games = BOWL_PREDICTIONS.get("games", [])

    # Transform to match frontend expectations
    formatted_games = []
    for game in games:
        # Use ensemble predictions as primary
        ensemble = game.get("ensemble_predictions", {})
        summary = game.get("summary", {})

        formatted_game = {
            "id": game.get("id"),
            "date": game.get("date"),
            "home_team": game.get("home_team"),
            "away_team": game.get("away_team"),
            "bowl_name": game.get("bowl_name"),
            "stadium": game.get("stadium"),
            "location": game.get("location"),
            "conference": game.get("conference"),
            # Primary ensemble predictions
            "home_win_prob": ensemble.get("home_win_probability", 0.5),
            "away_win_prob": ensemble.get("away_win_probability", 0.5),
            "predicted_margin": ensemble.get("predicted_margin", 0),
            "predicted_winner": summary.get("predicted_winner"),
            "confidence": ensemble.get("confidence_score", 0.5),
            # Additional model details
            "model_details": {
                "ridge": {
                    "margin": game.get("ridge_predictions", {}).get("predicted_margin"),
                    "probability": game.get("ridge_predictions", {}).get(
                        "home_win_probability"
                    ),
                },
                "xgb": {
                    "margin": game.get("xgb_predictions", {}).get("predicted_margin"),
                    "probability": game.get("xgb_predictions", {}).get(
                        "home_win_probability"
                    ),
                },
                "fastai": {
                    "margin": game.get("fastai_predictions", {}).get(
                        "predicted_margin"
                    ),
                    "probability": game.get("fastai_predictions", {}).get(
                        "home_win_probability"
                    ),
                },
            },
        }

        formatted_games.append(formatted_game)

    return jsonify(
        {
            "success": True,
            "data": {
                "games": formatted_games,
                "total_count": len(formatted_games),
                "season": BOWL_PREDICTIONS.get("season", 2025),
                "generated_at": BOWL_PREDICTIONS.get("generated_at"),
                "model_info": BOWL_PREDICTIONS.get("models_used", {}),
                "data_quality": BOWL_PREDICTIONS.get("data_quality", {}),
            },
        }
    )


@app.route("/api/model-comparisons")
def get_model_comparisons():
    """Get detailed model comparison data for all games"""
    if not BOWL_PREDICTIONS:
        return jsonify({"success": False, "error": "No prediction data available"}), 500

    games = BOWL_PREDICTIONS.get("games", [])
    comparisons = []

    for game in games:
        comparison = {
            "game_id": game.get("id"),
            "bowl_name": game.get("bowl_name"),
            "home_team": game.get("home_team"),
            "away_team": game.get("away_team"),
            # Individual model predictions
            "ridge_prediction": {
                "margin": game.get("ridge_predictions", {}).get("predicted_margin", 0),
                "home_win_probability": game.get("ridge_predictions", {}).get(
                    "home_win_probability", 0.5
                ),
            },
            "xgb_prediction": {
                "margin": game.get("xgb_predictions", {}).get("predicted_margin", 0),
                "home_win_probability": game.get("xgb_predictions", {}).get(
                    "home_win_probability", 0.5
                ),
            },
            "fastai_prediction": {
                "margin": game.get("fastai_predictions", {}).get("predicted_margin", 0),
                "home_win_probability": game.get("fastai_predictions", {}).get(
                    "home_win_probability", 0.5
                ),
            },
            "ensemble_prediction": {
                "margin": game.get("ensemble_predictions", {}).get(
                    "predicted_margin", 0
                ),
                "home_win_probability": game.get("ensemble_predictions", {}).get(
                    "home_win_probability", 0.5
                ),
                "confidence": game.get("ensemble_predictions", {}).get(
                    "confidence_score", 0.5
                ),
            },
        }

        comparisons.append(comparison)

    return jsonify(
        {
            "success": True,
            "data": {
                "comparisons": comparisons,
                "total_games": len(comparisons),
                "model_info": BOWL_PREDICTIONS.get("models_used", {}),
            },
        }
    )


@app.route("/api/analytics")
def get_analytics():
    """Get analytics and statistics about the predictions"""
    if not BOWL_PREDICTIONS:
        return jsonify({"success": False, "error": "No prediction data available"}), 500

    games = BOWL_PREDICTIONS.get("games", [])

    # Calculate statistics
    margins = [
        game.get("ensemble_predictions", {}).get("predicted_margin", 0)
        for game in games
    ]
    confidences = [
        game.get("ensemble_predictions", {}).get("confidence_score", 0)
        for game in games
    ]

    avg_margin = sum(margins) / len(margins) if margins else 0
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0

    high_confidence_games = sum(1 for c in confidences if c > 0.8)
    home_team_favorites = sum(
        1
        for game in games
        if game.get("ensemble_predictions", {}).get("home_win_probability", 0.5) > 0.5
    )

    return jsonify(
        {
            "success": True,
            "data": {
                "total_games": len(games),
                "average_predicted_margin": round(avg_margin, 2),
                "average_confidence": round(avg_confidence, 3),
                "high_confidence_games": high_confidence_games,
                "high_confidence_percentage": (
                    round(high_confidence_games / len(games) * 100, 1) if games else 0
                ),
                "home_team_favorites": home_team_favorites,
                "home_team_favorite_percentage": (
                    round(home_team_favorites / len(games) * 100, 1) if games else 0
                ),
                "model_details": BOWL_PREDICTIONS.get("models_used", {}),
                "data_quality": BOWL_PREDICTIONS.get("data_quality", {}),
                "generated_at": BOWL_PREDICTIONS.get("generated_at"),
            },
        }
    )


@app.route("/api/refresh")
def refresh_predictions():
    """Reload predictions from files"""
    try:
        global BOWL_PREDICTIONS
        BOWL_PREDICTIONS = load_fbs_bowl_predictions()

        if BOWL_PREDICTIONS:
            return jsonify(
                {
                    "success": True,
                    "message": f"Refreshed {len(BOWL_PREDICTIONS.get('games', []))} predictions",
                    "generated_at": BOWL_PREDICTIONS.get("generated_at"),
                }
            )
        else:
            return (
                jsonify({"success": False, "error": "No prediction files found"}),
                404,
            )

    except Exception as e:
        return jsonify({"success": False, "error": f"Refresh failed: {str(e)}"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5002))
    debug = os.environ.get("DEBUG", "False").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
