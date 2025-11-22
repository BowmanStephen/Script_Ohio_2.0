#!/usr/bin/env python3
"""
Check if starter pack data is ready for model pack and notebook usage.

This script verifies:
1. Starter pack data exists and is complete
2. Data can be migrated to model pack format
3. Training data integration is possible
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DATA_DIR = PROJECT_ROOT / "starter_pack" / "data"
MODEL_PACK_DIR = PROJECT_ROOT / "model_pack"
YEAR = 2025
START_WEEK = 1
END_WEEK = 12


def check_starter_pack_data():
    """Check starter pack data availability."""
    print("=" * 80)
    print("STEP 1: Checking Starter Pack Data")
    print("=" * 80)

    issues = []
    warnings = []

    # Check games.csv
    games_file = DATA_DIR / "games.csv"
    if not games_file.exists():
        issues.append("❌ games.csv not found")
        return issues, warnings

    try:
        df = pd.read_csv(games_file, low_memory=False)
        df_2025 = df[df["season"] == YEAR] if "season" in df.columns else pd.DataFrame()

        if len(df_2025) == 0:
            issues.append("❌ No 2025 games found in games.csv")
            return issues, warnings

        df_2025_weeks = df_2025[
            (df_2025["week"] >= START_WEEK) & (df_2025["week"] <= END_WEEK)
        ] if "week" in df_2025.columns else pd.DataFrame()

        games_with_scores = df_2025_weeks["home_points"].notna().sum() if "home_points" in df_2025_weeks.columns else 0
        total_games = len(df_2025_weeks)

        print(f"✅ Found {len(df_2025)} total 2025 games")
        print(f"✅ Found {total_games} games in weeks {START_WEEK}-{END_WEEK}")
        print(f"{'✅' if games_with_scores > 0 else '⚠️'} {games_with_scores}/{total_games} games have scores")

        if games_with_scores == 0:
            warnings.append(
                f"⚠️  No games with scores in weeks {START_WEEK}-{END_WEEK}. "
                "This is normal for future games, but completed games should have scores."
            )

        # Check other required files
        required_files = {
            "advanced_game_stats": DATA_DIR / "advanced_game_stats" / f"{YEAR}.csv",
            "advanced_season_stats": DATA_DIR / "advanced_season_stats" / f"{YEAR}.csv",
            "drives": DATA_DIR / "drives" / f"drives_{YEAR}.csv",
        }

        for name, path in required_files.items():
            if path.exists():
                print(f"✅ {name} exists")
            else:
                issues.append(f"❌ {name} not found: {path}")

    except Exception as e:
        issues.append(f"❌ Error reading games.csv: {e}")

    return issues, warnings


def check_migration_readiness():
    """Check if data can be migrated to model pack format."""
    print("\n" + "=" * 80)
    print("STEP 2: Checking Migration Readiness")
    print("=" * 80)

    issues = []
    warnings = []

    # Check if migration script exists
    migration_script = PROJECT_ROOT / "model_pack" / "migrate_starter_pack_data.py"
    if not migration_script.exists():
        issues.append("❌ Migration script not found: migrate_starter_pack_data.py")
        return issues, warnings

    print("✅ Migration script exists")

    # Check if already migrated
    migrated_file = MODEL_PACK_DIR / f"{YEAR}_weeks1-12_migrated.csv"
    if migrated_file.exists():
        try:
            df = pd.read_csv(migrated_file)
            print(f"✅ Migration file exists: {len(df)} records")
            if len(df) > 0:
                print(f"   Columns: {len(df.columns)}")
                if "game_key" in df.columns:
                    print(f"   Unique games: {df['game_key'].nunique()}")
        except Exception as e:
            warnings.append(f"⚠️  Error reading migration file: {e}")
    else:
        warnings.append(
            f"⚠️  Migration file not found. Run migration to create: {migrated_file.name}"
        )

    return issues, warnings


def check_training_data_integration():
    """Check if data can be integrated into training data."""
    print("\n" + "=" * 80)
    print("STEP 3: Checking Training Data Integration")
    print("=" * 80)

    issues = []
    warnings = []

    # Check training data file
    training_data = MODEL_PACK_DIR / "updated_training_data.csv"
    if not training_data.exists():
        issues.append("❌ Training data file not found: updated_training_data.csv")
        return issues, warnings

    try:
        df = pd.read_csv(training_data, nrows=5)
        print(f"✅ Training data exists: {len(df.columns)} columns")
        print(f"   Sample columns: {list(df.columns[:10])}")

        # Check if 2025 data already exists
        df_full = pd.read_csv(training_data, low_memory=False)
        df_2025 = df_full[df_full["season"] == YEAR] if "season" in df_full.columns else pd.DataFrame()

        if len(df_2025) > 0:
            weeks = sorted(df_2025["week"].unique()) if "week" in df_2025.columns else []
            print(f"✅ Training data already contains {len(df_2025)} 2025 games")
            print(f"   Weeks present: {weeks[:10]}")
            if set(range(START_WEEK, END_WEEK + 1)).issubset(set(weeks)):
                print(f"✅ Weeks {START_WEEK}-{END_WEEK} are already in training data")
            else:
                missing = set(range(START_WEEK, END_WEEK + 1)) - set(weeks)
                warnings.append(f"⚠️  Missing weeks in training data: {sorted(missing)}")
        else:
            warnings.append("⚠️  No 2025 data in training data yet. Migration needed.")

    except Exception as e:
        issues.append(f"❌ Error reading training data: {e}")

    return issues, warnings


def main():
    """Run all checks."""
    print("=" * 80)
    print("MODEL PACK & NOTEBOOK READINESS CHECK")
    print(f"Year: {YEAR}, Weeks: {START_WEEK}-{END_WEEK}")
    print("=" * 80)

    all_issues = []
    all_warnings = []

    # Run checks
    issues, warnings = check_starter_pack_data()
    all_issues.extend(issues)
    all_warnings.extend(warnings)

    issues, warnings = check_migration_readiness()
    all_issues.extend(issues)
    all_warnings.extend(warnings)

    issues, warnings = check_training_data_integration()
    all_issues.extend(issues)
    all_warnings.extend(warnings)

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    if all_issues:
        print(f"\n❌ Issues Found ({len(all_issues)}):")
        for issue in all_issues:
            print(f"  {issue}")
    else:
        print("\n✅ No critical issues found")

    if all_warnings:
        print(f"\n⚠️  Warnings ({len(all_warnings)}):")
        for warning in all_warnings:
            print(f"  {warning}")
    else:
        print("\n✅ No warnings")

    # Overall status
    if all_issues:
        print("\n❌ STATUS: NOT READY - Issues must be resolved")
        return 1
    elif all_warnings:
        print("\n⚠️  STATUS: READY WITH WARNINGS - Data can be used but review warnings")
        return 0
    else:
        print("\n✅ STATUS: READY - Data is ready for model pack and notebooks")
        return 0


if __name__ == "__main__":
    sys.exit(main())

