#!/usr/bin/env python3
"""
Validate prediction files for Next.js web app

This script validates that prediction files exist and are properly formatted
for the Next.js web app. The new web app reads directly from predictions/ and
data/outputs/ directories, so no file copying is needed.

Usage:
    python scripts/sync_web_app_data.py --week 14 --season 2025
    python scripts/sync_web_app_data.py --week 15  # defaults to season 2025
    python scripts/sync_web_app_data.py --bowls-only  # only validate bowl predictions
"""

import argparse
import csv
import json
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent.parent
MODEL_PACK = PROJECT_ROOT / "model_pack"


def validate_weekly_predictions(week: int, season: int = 2025) -> bool:
    """Validate that weekly prediction files exist and are readable"""
    predictions_dir = PROJECT_ROOT / "predictions" / f"week{week}"

    if not predictions_dir.exists():
        print(
            f"⚠️  Week {week} predictions directory not found: {predictions_dir}"
        )
        return False

    expected_files = [
        f"week{week}_model_predictions.json",
        f"week{week}_model_predictions.csv",
    ]

    all_exist = True
    for filename in expected_files:
        filepath = predictions_dir / filename
        if filepath.exists():
            try:
                # Validate JSON structure
                if filename.endswith(".json"):
                    with open(filepath, "r") as f:
                        data = json.load(f)
                    count = len(data) if isinstance(data, list) else "valid"
                    print(f"✅ {filename}: {count} predictions")
                else:
                    # Validate CSV structure
                    with open(filepath, "r") as f:
                        reader = csv.DictReader(f)
                        row_count = sum(1 for _ in reader)
                    print(f"✅ {filename}: {row_count} predictions")
            except Exception as e:
                print(f"❌ {filename}: Invalid format - {e}")
                all_exist = False
        else:
            print(f"⚠️  {filename}: Not found")
            all_exist = False

    return all_exist


def validate_bowl_predictions(season: int = 2025) -> bool:
    """Validate that bowl prediction files exist"""
    bowls_dir = (
        PROJECT_ROOT
        / "data"
        / "outputs"
        / "predictions"
        / str(season)
        / "bowl_season"
    )

    if not bowls_dir.exists():
        print(f"⚠️  Bowl predictions directory not found: {bowls_dir}")
        return False

    # Check for any bowl prediction JSON files
    json_files = list(bowls_dir.glob("bowls_*.json"))
    json_files = [f for f in json_files if "backup" not in f.name]

    if not json_files:
        print(f"⚠️  No bowl prediction files found in {bowls_dir}")
        return False

    # Validate latest file
    latest_file = max(json_files, key=lambda f: f.stat().st_mtime)
    try:
        with open(latest_file, "r") as f:
            data = json.load(f)
        games_count = len(data.get("games", []))
        print(f"✅ Bowl predictions: {latest_file.name} ({games_count} games)")
        return True
    except Exception as e:
        print(f"❌ {latest_file.name}: Invalid format - {e}")
        return False


def validate_analytics() -> bool:
    """Validate that analytics files exist"""
    analysis_dir = PROJECT_ROOT / "data" / "outputs" / "analysis"

    if not analysis_dir.exists():
        print(f"⚠️  Analytics directory not found: {analysis_dir}")
        return False

    analysis_files = list(analysis_dir.glob("external_model_analysis_*.json"))

    if not analysis_files:
        print(
            f"⚠️  No external model analysis files found in {analysis_dir}"
        )
        return False

    latest_file = max(analysis_files, key=lambda f: f.stat().st_mtime)
    try:
        with open(latest_file, "r") as f:
            data = json.load(f)
        models_count = len(data.get("external_models", {}))
        print(
            f"✅ External model analysis: {latest_file.name} ({models_count} models)"
        )
        return True
    except Exception as e:
        print(f"❌ {latest_file.name}: Invalid format - {e}")
        return False


def verify_models() -> bool:
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


def main():
    """Main sync/validation function"""
    parser = argparse.ArgumentParser(
        description="Validate prediction files for Next.js web app"
    )
    parser.add_argument(
        "--week",
        type=int,
        help="Week number to validate (default: 14)",
        default=14,
    )
    parser.add_argument(
        "--season",
        type=int,
        help="Season year (default: 2025)",
        default=2025,
    )
    parser.add_argument(
        "--bowls-only",
        action="store_true",
        help="Only validate bowl predictions",
    )
    parser.add_argument(
        "--analytics-only",
        action="store_true",
        help="Only validate analytics files",
    )

    args = parser.parse_args()

    print("🚀 Validating web app data sources...")
    print(f"📁 Project root: {PROJECT_ROOT}")
    print(f"📁 Season: {args.season}")

    results = {"weekly": True, "bowls": True, "analytics": True, "models": True}

    if args.bowls_only:
        results["bowls"] = validate_bowl_predictions(args.season)
    elif args.analytics_only:
        results["analytics"] = validate_analytics()
    else:
        # Validate weekly predictions
        print(f"\n📊 Validating Week {args.week} predictions...")
        results["weekly"] = validate_weekly_predictions(args.week, args.season)

        # Validate bowl predictions
        print(f"\n🏆 Validating Bowl Season {args.season} predictions...")
        results["bowls"] = validate_bowl_predictions(args.season)

        # Validate analytics
        print("\n📈 Validating analytics files...")
        results["analytics"] = validate_analytics()

        # Verify models
        print("\n🤖 Verifying model files...")
        results["models"] = verify_models()

    print("\n" + "=" * 60)
    all_passed = all(results.values())
    if all_passed:
        print("✅ All validations passed!")
    else:
        print("⚠️  Some validations failed:")
        for key, value in results.items():
            status = "✅" if value else "❌"
            print(f"  {status} {key}")
    print("=" * 60)

    print("\n📝 Note:")
    print("  The new Next.js web app reads directly from predictions/ and")
    print("  data/outputs/ directories. No file copying needed!")
    print(f"  Access weekly predictions at: /week/{args.week}")


if __name__ == "__main__":
    main()
