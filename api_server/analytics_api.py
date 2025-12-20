#!/usr/bin/env python3
"""
Analytics API Server
===================

Provides API endpoints for:
- External model analysis data
- Enhanced predictions with advanced features
- Real-time analytics and insights
- Model performance comparisons

This complements the bowl API with advanced analytics capabilities.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, request
from flask_cors import CORS

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Global cache for analysis data
ANALYSIS_CACHE = {}
LAST_CACHE_UPDATE = None
CACHE_DURATION_MINUTES = 30  # Refresh cache every 30 minutes


def load_analysis_data():
    """Load external model analysis data from latest file"""
    global ANALYSIS_CACHE, LAST_CACHE_UPDATE

    try:
        # Look for the latest analysis file
        analysis_dir = PROJECT_ROOT / "data" / "outputs" / "analysis"

        if not analysis_dir.exists():
            print("❌ Analysis directory not found")
            return None

        # Find the latest external model analysis file
        analysis_files = list(analysis_dir.glob("external_model_analysis_*.json"))
        if not analysis_files:
            print("❌ No external model analysis files found")
            return None

        # Sort by modification time and get the latest
        latest_file = max(analysis_files, key=lambda f: f.stat().st_mtime)

        print(f"📊 Loading analysis data from: {latest_file}")

        with open(latest_file, "r") as f:
            analysis_data = json.load(f)

        # Process the data for API consumption
        processed_data = {
            "models": [],
            "insights": {},
            "recommendations": {},
            "visualization_data": analysis_data.get("visualization_data", {}),
            "key_findings": analysis_data.get("key_findings", {}),
            "generated_at": analysis_data.get("generated_at"),
            "total_models_analyzed": analysis_data.get("total_models", 0),
        }

        # Process external models
        external_models = analysis_data.get("external_models", {})
        for model_id, model_data in external_models.items():
            processed_data["models"].append(
                {
                    "name": model_data["name"],
                    "straightUpAccuracy": model_data["accuracy_straight_up"],
                    "vsSpreadAccuracy": model_data["accuracy_vs_spread"],
                    "methodology": model_data["methodology"],
                    "researchConfidence": model_data["research_confidence"],
                    "isScriptOhio": "script_ohio" in model_id,
                    "dataSources": model_data.get("data_sources", []),
                    "updateFrequency": model_data.get("update_frequency", "Unknown"),
                    "coverage": model_data.get("coverage", "Unknown"),
                }
            )

        # Sort by straight-up accuracy (highest first)
        processed_data["models"].sort(
            key=lambda x: x["straightUpAccuracy"], reverse=True
        )

        # Add rankings
        for i, model in enumerate(processed_data["models"], 1):
            model["ranking"] = i

        # Extract Script Ohio specific insights
        script_ohio_models = [m for m in processed_data["models"] if m["isScriptOhio"]]
        if script_ohio_models:
            best_script_ohio = script_ohio_models[0]
            top_model = processed_data["models"][0]

            processed_data["insights"] = {
                "gapToLeader": round(
                    top_model["straightUpAccuracy"]
                    - best_script_ohio["straightUpAccuracy"],
                    1,
                ),
                "improvementNeeded": round(
                    top_model["straightUpAccuracy"]
                    - best_script_ohio["straightUpAccuracy"]
                    + 0.3,
                    1,
                ),  # Add small buffer
                "keyAdvantages": [
                    "Comprehensive feature set with 86 opponent-adjusted features",
                    "Robust validation framework with iron-clad verification",
                    "Multiple model ensemble approach reducing bias",
                    "Real-time CFBD API integration",
                ],
                "mainChallenges": [
                    "Feature engineering complexity",
                    "CFBD API limitations for advanced metrics",
                    "Data access constraints for some advanced features",
                ],
            }

        # Extract recommendations
        key_findings = analysis_data.get("key_findings", {})
        if "competitive_analysis" in key_findings:
            competitive_analysis = key_findings["competitive_analysis"]
            processed_data["recommendations"] = {
                "immediate": competitive_analysis.get("immediate_improvements", []),
                "medium": competitive_analysis.get("medium_term_enhancements", []),
                "long": competitive_analysis.get("long_term_research", []),
            }

        ANALYSIS_CACHE = processed_data
        LAST_CACHE_UPDATE = datetime.now()

        print(
            f"✅ Analysis data loaded and cached: {len(processed_data['models'])} models"
        )
        return processed_data

    except Exception as e:
        print(f"❌ Error loading analysis data: {e}")
        return None


def load_enhanced_predictions():
    """Load enhanced predictions with advanced features"""
    try:
        # Look for the latest enhanced predictions file
        predictions_dir = PROJECT_ROOT / "predictions"

        if not predictions_dir.exists():
            return None

        # Look for working enhanced predictions first, then regular enhanced
        enhanced_files = list(
            predictions_dir.glob("working_enhanced_bowl_predictions_*.json")
        )
        if not enhanced_files:
            enhanced_files = list(
                predictions_dir.glob("enhanced_bowl_predictions_*.json")
            )

        if not enhanced_files:
            return None

        # Sort by modification time and get the latest
        latest_file = max(enhanced_files, key=lambda f: f.stat().st_mtime)

        print(f"🎯 Loading enhanced predictions from: {latest_file}")

        with open(latest_file, "r") as f:
            predictions_data = json.load(f)

        return predictions_data

    except Exception as e:
        print(f"❌ Error loading enhanced predictions: {e}")
        return None


def should_refresh_cache():
    """Check if cache should be refreshed"""
    if LAST_CACHE_UPDATE is None:
        return True

    elapsed = datetime.now() - LAST_CACHE_UPDATE
    return elapsed.total_seconds() > (CACHE_DURATION_MINUTES * 60)


@app.route("/api/external-model-analysis", methods=["GET"])
def get_external_model_analysis():
    """Get external model analysis and comparison data"""

    # Refresh cache if needed
    if should_refresh_cache() or not ANALYSIS_CACHE:
        analysis_data = load_analysis_data()
        if not analysis_data:
            return (
                jsonify(
                    {
                        "error": "Unable to load analysis data",
                        "message": "External model analysis file not found or corrupted",
                    }
                ),
                500,
            )

    # Add cache timestamp
    response_data = ANALYSIS_CACHE.copy()
    response_data["cached_at"] = (
        LAST_CACHE_UPDATE.isoformat() if LAST_CACHE_UPDATE else None
    )

    return jsonify(response_data)


@app.route("/api/enhanced-bowl-predictions", methods=["GET"])
def get_enhanced_bowl_predictions():
    """Get enhanced bowl predictions with advanced CFBD features"""

    try:
        predictions_data = load_enhanced_predictions()

        if not predictions_data:
            # Fallback to regular predictions if enhanced not available
            regular_predictions_file = (
                PROJECT_ROOT / "predictions" / "fbs_bowl_predictions_latest.json"
            )
            if regular_predictions_file.exists():
                with open(regular_predictions_file, "r") as f:
                    predictions_data = json.load(f)
                predictions_data["enhancement_method"] = "standard_predictions"
            else:
                return (
                    jsonify(
                        {
                            "error": "Unable to load predictions",
                            "message": "No prediction files found",
                        }
                    ),
                    500,
                )

        return jsonify(predictions_data)

    except Exception as e:
        return (
            jsonify(
                {"error": "Failed to load enhanced predictions", "message": str(e)}
            ),
            500,
        )


@app.route("/api/analytics-summary", methods=["GET"])
def get_analytics_summary():
    """Get a comprehensive analytics summary"""

    try:
        # Get analysis data
        if should_refresh_cache() or not ANALYSIS_CACHE:
            load_analysis_data()

        if not ANALYSIS_CACHE:
            return jsonify({"error": "Analysis data not available"}), 500

        # Get predictions data
        predictions_data = load_enhanced_predictions() or load_enhanced_predictions()

        # Create summary
        summary = {
            "model_performance": {
                "total_models": ANALYSIS_CACHE.get("total_models_analyzed", 0),
                "script_ohio_ranking": None,
                "top_model": None,
                "gap_to_leader": 0,
            },
            "prediction_coverage": {
                "total_games": (
                    len(predictions_data.get("games", [])) if predictions_data else 0
                ),
                "enhanced_features_available": False,
                "latest_prediction_date": None,
            },
            "system_health": {
                "cache_status": "fresh" if not should_refresh_cache() else "stale",
                "last_cache_update": (
                    LAST_CACHE_UPDATE.isoformat() if LAST_CACHE_UPDATE else None
                ),
                "data_sources": ANALYSIS_CACHE.get("visualization_data", {}).get(
                    "data_sources", []
                ),
            },
            "key_metrics": {
                "script_ohio_accuracy": 0,
                "industry_leader_accuracy": 0,
                "competitive_gap": 0,
            },
        }

        # Find Script Ohio ranking
        script_ohio_models = [
            m for m in ANALYSIS_CACHE.get("models", []) if m["isScriptOhio"]
        ]
        if script_ohio_models:
            best_script_ohio = min(script_ohio_models, key=lambda x: x["ranking"])
            summary["model_performance"]["script_ohio_ranking"] = best_script_ohio[
                "ranking"
            ]
            summary["key_metrics"]["script_ohio_accuracy"] = best_script_ohio[
                "straightUpAccuracy"
            ]

        # Get top model info
        if ANALYSIS_CACHE.get("models"):
            top_model = ANALYSIS_CACHE["models"][0]
            summary["model_performance"]["top_model"] = top_model["name"]
            summary["key_metrics"]["industry_leader_accuracy"] = top_model[
                "straightUpAccuracy"
            ]

            if script_ohio_models:
                summary["key_metrics"]["competitive_gap"] = (
                    top_model["straightUpAccuracy"]
                    - best_script_ohio["straightUpAccuracy"]
                )

        # Enhanced features check
        if predictions_data:
            games = predictions_data.get("games", [])
            if (
                games
                and games[0].get("working_advanced_features")
                or games[0].get("advanced_features")
            ):
                summary["prediction_coverage"]["enhanced_features_available"] = True

            # Get latest prediction date
            if games:
                dates = [game.get("date") for game in games if game.get("date")]
                if dates:
                    summary["prediction_coverage"]["latest_prediction_date"] = max(
                        dates
                    )

        return jsonify(summary)

    except Exception as e:
        return (
            jsonify(
                {"error": "Failed to generate analytics summary", "message": str(e)}
            ),
            500,
        )


@app.route("/api/refresh-cache", methods=["POST"])
def refresh_cache():
    """Force refresh of analytics cache"""
    try:
        global ANALYSIS_CACHE, LAST_CACHE_UPDATE

        # Clear cache
        ANALYSIS_CACHE = None
        LAST_CACHE_UPDATE = None

        # Reload data
        analysis_data = load_analysis_data()

        if analysis_data:
            return jsonify(
                {
                    "success": True,
                    "message": "Cache refreshed successfully",
                    "models_loaded": len(analysis_data.get("models", [])),
                    "cached_at": (
                        LAST_CACHE_UPDATE.isoformat() if LAST_CACHE_UPDATE else None
                    ),
                }
            )
        else:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "Failed to refresh cache - no data available",
                    }
                ),
                500,
            )

    except Exception as e:
        return (
            jsonify({"success": False, "message": f"Cache refresh failed: {str(e)}"}),
            500,
        )


@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify(
        {
            "status": "healthy",
            "service": "Analytics API",
            "timestamp": datetime.now().isoformat(),
            "cache_status": "loaded" if ANALYSIS_CACHE else "empty",
            "last_update": LAST_CACHE_UPDATE.isoformat() if LAST_CACHE_UPDATE else None,
        }
    )


if __name__ == "__main__":
    print("🚀 Starting Analytics API Server...")
    print("=" * 50)

    # Preload analysis data
    print("📊 Preloading analysis data...")
    analysis_data = load_analysis_data()

    if analysis_data:
        print(f"✅ Preloaded {len(analysis_data.get('models', []))} models")

        # Show Script Ohio rankings
        script_ohio_models = [
            m for m in analysis_data.get("models", []) if m["isScriptOhio"]
        ]
        if script_ohio_models:
            print("🏈 Script Ohio Model Rankings:")
            for model in script_ohio_models:
                print(
                    f"  • {model['name']}: #{model['ranking']} ({model['straightUpAccuracy']}%)"
                )
    else:
        print("⚠️  Could not preload analysis data")

    print("=" * 50)
    print("🌐 Analytics API available at: http://localhost:5002")
    print("📊 Endpoints:")
    print("  • GET /api/external-model-analysis - Model comparison data")
    print("  • GET /api/enhanced-bowl-predictions - Enhanced predictions")
    print("  • GET /api/analytics-summary - Comprehensive summary")
    print("  • POST /api/refresh-cache - Force cache refresh")
    print("  • GET /api/health - Health check")

    # Run on port 5002 to avoid conflicts with bowl API
    app.run(host="0.0.0.0", port=5002, debug=True)
