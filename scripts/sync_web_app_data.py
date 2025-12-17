#!/usr/bin/env python3
"""
Sync latest predictions and models to web app

This script copies the latest prediction files from predictions/week14/
to web_app/public/ and ensures the API can access the latest models.
"""

import csv
import json
import os
import shutil
from pathlib import Path
from typing import Any, Dict, List

# Project root
PROJECT_ROOT = Path(__file__).parent.parent
PREDICTIONS_DIR = PROJECT_ROOT / "predictions" / "week14"
BOWLS_PREDICTIONS = PROJECT_ROOT / "predictions" / "bowls_2025_predictions.json"
WEB_APP_PUBLIC = PROJECT_ROOT / "web_app" / "public"
MODEL_PACK = PROJECT_ROOT / "model_pack"


def copy_file_if_exists(source: Path, dest: Path, description: str) -> bool:
    """Copy a file if it exists, creating destination directory if needed"""
    if not source.exists():
        print(f"⚠️  {description} not found: {source}")
        return False

    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest)
    print(f"✅ Copied {description}: {dest.name}")
    return True


def convert_bowls_predictions_schema(source_path: Path, dest_path: Path) -> bool:
    """Convert bowls predictions JSON to web app compatible schema"""
    if not source_path.exists():
        print(f"⚠️  Bowls predictions not found: {source_path}")
        return False

    try:
        with open(source_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Convert schema to match web app expectations
        web_app_data = []
        for game in data.get("games", []):
            web_game = {
                "game_id": game.get("id"),
                "season": data.get("season", 2025),
                "week": None,  # Bowl games don't have weeks
                "home_team": game.get("home_team"),
                "away_team": game.get("away_team"),
                "start_date": game.get("date"),
                "home_conference": None,  # Not in bowls data
                "away_conference": None,  # Not in bowls data
                "spread": None,  # Not in bowls data
                "ridge_predicted_margin": game.get("predicted_margin"),
                "predicted_margin": game.get("predicted_margin"),
                "ridge_home_win_probability": game.get("home_win_prob"),
                "xgb_home_win_probability": game.get("home_win_prob"),  # Use same value
                "fastai_home_win_probability": 0.0,  # Not available
                "ensemble_margin": game.get("predicted_margin"),
                "ensemble_home_win_probability": game.get("home_win_prob"),
                "ensemble_away_win_probability": 1 - game.get("home_win_prob", 0.5),
                "ensemble_confidence": abs(game.get("home_win_prob", 0.5) - 0.5) * 2,
                "models_used": "ridge,xgb",  # Based on model info
                "model_agreement": "high",  # Default
                "home_win_probability": game.get("home_win_prob"),
                "away_win_probability": 1 - game.get("home_win_prob", 0.5),
                "predicted_winner": game.get("home_team")
                if game.get("home_win_prob", 0.5) > 0.5
                else game.get("away_team"),
            }
            web_app_data.append(web_game)

        # Create output with web app structure
        output_data = {
            "generated_at": data.get("generated_at"),
            "model": data.get("model", {}),
            "season": data.get("season", 2025),
            "predictions_type": "bowls",
            "games": web_app_data,
        }

        with open(dest_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2)

        print(
            f"✅ Converted bowls predictions to web app schema: {dest_path.name} ({len(web_app_data)} games)"
        )
        return True
    except Exception as e:
        print(f"❌ Error converting bowls predictions: {e}")
        return False


def convert_csv_to_json(csv_path: Path, json_path: Path) -> bool:
    """Convert CSV predictions to JSON format for web app"""
    if not csv_path.exists():
        return False

    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            data = list(reader)

        # Convert numeric strings to numbers where appropriate
        for row in data:
            for key, value in row.items():
                if value == "":
                    continue
                # Try to convert to number
                try:
                    if "." in value:
                        row[key] = float(value)
                    else:
                        row[key] = int(value)
                except ValueError:
                    pass  # Keep as string

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        print(f"✅ Converted CSV to JSON: {json_path.name} ({len(data)} games)")
        return True
    except Exception as e:
        print(f"❌ Error converting {csv_path.name} to JSON: {e}")
        return False


def sync_predictions():
    """Sync prediction files to web app"""
    print("\n📊 Syncing prediction files...")

    # Primary prediction files
    files_to_sync = [
        (
            "week14_model_predictions.json",
            "week14_model_predictions.json",
            "Model predictions (JSON)",
        ),
        (
            "week14_model_predictions.csv",
            "week14_model_predictions.csv",
            "Model predictions (CSV)",
        ),
        ("week14_ats_full_table.csv", "week14_ats_full_table.csv", "ATS full table"),
    ]

    for source_name, dest_name, description in files_to_sync:
        source = PREDICTIONS_DIR / source_name
        dest = WEB_APP_PUBLIC / dest_name
        copy_file_if_exists(source, dest, description)

    # Sync bowls predictions with schema conversion
    print("\n🏆 Syncing bowls predictions...")
    bowls_dest = WEB_APP_PUBLIC / "bowls_2025_predictions.json"
    if convert_bowls_predictions_schema(BOWLS_PREDICTIONS, bowls_dest):
        print("✅ Bowls predictions synced successfully")
    else:
        print("⚠️  Bowls predictions sync failed")

    # Enhanced/calibrated predictions (optional, for future use)
    enhanced_files = [
        (
            "week14_predictions_enhanced_calibrated.csv",
            "week14_predictions_enhanced_calibrated.csv",
            "Enhanced calibrated predictions",
        ),
        (
            "week14_predictions_unified.json",
            "week14_predictions_unified.json",
            "Unified predictions",
        ),
    ]

    for source_name, dest_name, description in enhanced_files:
        source = PREDICTIONS_DIR / source_name
        dest = WEB_APP_PUBLIC / dest_name
        if copy_file_if_exists(source, dest, description):
            # Also convert CSV to JSON if needed
            if source_name.endswith(".csv"):
                json_name = dest_name.replace(".csv", ".json")
                json_path = WEB_APP_PUBLIC / json_name
                convert_csv_to_json(source, json_path)

    # ATS data JSON (convert from CSV if JSON doesn't exist)
    ats_csv = WEB_APP_PUBLIC / "week14_ats_full_table.csv"
    ats_json = WEB_APP_PUBLIC / "week14_ats_data.json"

    if ats_csv.exists() and not ats_json.exists():
        print("📝 Converting ATS CSV to JSON...")
        convert_csv_to_json(ats_csv, ats_json)


def verify_models():
    """Verify that model files exist and are accessible"""
    print("\n🤖 Verifying model files...")

    models = [
        ("ridge_model_2025.joblib", "Ridge Regression"),
        ("xgb_home_win_model_2025.pkl", "XGBoost"),
        ("fastai_home_win_model_2025.pkl", "FastAI"),
    ]

    all_present = True
    for model_file, model_name in models:
        model_path = MODEL_PACK / model_file
        if model_path.exists():
            size_mb = model_path.stat().st_size / (1024 * 1024)
            print(f"✅ {model_name}: {model_file} ({size_mb:.2f} MB)")
        else:
            print(f"❌ {model_name}: {model_file} NOT FOUND")
            all_present = False

    return all_present


def update_api_config():
    """Update API configuration to use latest predictions"""
    print("\n🔧 Checking API configuration...")

    api_file = PROJECT_ROOT / "api" / "prediction_api.py"
    if not api_file.exists():
        print("⚠️  API file not found, skipping update")
        return

    # Check if bowls API endpoint was added
    with open(api_file, "r", encoding="utf-8") as f:
        content = f.read()

    if "/api/predictions/bowls" in content:
        print("✅ API already configured with bowls predictions endpoint")
    else:
        print("⚠️  API may need bowls endpoint update - check manually")

    # Check if predictions files exist
    if (WEB_APP_PUBLIC / "week14_model_predictions.json").exists():
        print("✅ Week 14 predictions file exists")
    if (WEB_APP_PUBLIC / "bowls_2025_predictions.json").exists():
        print("✅ Bowls predictions file exists")


def main():
    """Main sync function"""
    print("🚀 Syncing web app data and models...")
    print(f"📁 Project root: {PROJECT_ROOT}")
    print(f"📁 Predictions source: {PREDICTIONS_DIR}")
    print(f"📁 Web app public: {WEB_APP_PUBLIC}")

    # Sync predictions
    sync_predictions()

    # Verify models
    models_ok = verify_models()

    # Update API config
    update_api_config()

    print("\n" + "=" * 60)
    if models_ok:
        print("✅ Sync complete! All models verified.")
    else:
        print("⚠️  Sync complete, but some models are missing.")
    print("=" * 60)
    print("\n📝 Next steps:")
    print("  1. Restart the API server if running")
    print("  2. Refresh the web app to see new data")
    print("  3. Check web_app/public/ for updated files")


if __name__ == "__main__":
    main()
