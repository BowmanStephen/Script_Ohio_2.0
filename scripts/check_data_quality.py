#!/usr/bin/env python3
"""
Check Data Quality Script

Checks for duplicate games, missing values, and data integrity issues.
Part of Script Ohio 2.0 data validation pipeline.
"""

import pandas as pd
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def check_missing_columns():
    """Check for missing required columns."""
    training_file = project_root / "model_pack" / "updated_training_data.csv"
    
    if not training_file.exists():
        print("❌ Training data file not found")
        return False
    
    try:
        df = pd.read_csv(training_file)
    except Exception as e:
        print(f"❌ Error reading training data: {e}")
        return False
    
    required_columns = [
        'id', 'season', 'week', 'home_team', 'away_team',
        'home_points', 'away_points', 'margin', 'game_key', 'conference_game'
    ]
    
    missing = [col for col in required_columns if col not in df.columns]
    
    if missing:
        print(f"❌ Missing columns: {missing}")
        return False
    
    print("✅ All required columns present")
    return True


def check_duplicate_games():
    """Check for duplicate game IDs."""
    training_file = project_root / "model_pack" / "updated_training_data.csv"
    
    if not training_file.exists():
        print("❌ Training data file not found")
        return False
    
    try:
        df = pd.read_csv(training_file)
    except Exception as e:
        print(f"❌ Error reading training data: {e}")
        return False
    
    duplicates = df[df.duplicated(subset=['id'], keep=False)]
    
    if len(duplicates) > 0:
        print(f"❌ Found {len(duplicates)} duplicate game IDs")
        print("\nDuplicate game details:")
        print(duplicates[['id', 'season', 'week', 'home_team', 'away_team']].head(10))
        if len(duplicates) > 10:
            print(f"  ... and {len(duplicates) - 10} more duplicates")
        return False
    
    print("✅ No duplicate game IDs found")
    return True


def check_missing_values():
    """Check for missing values in critical features."""
    training_file = project_root / "model_pack" / "updated_training_data.csv"
    
    if not training_file.exists():
        print("❌ Training data file not found")
        return False
    
    try:
        df = pd.read_csv(training_file)
    except Exception as e:
        print(f"❌ Error reading training data: {e}")
        return False
    
    critical_features = ['home_elo', 'away_elo', 'home_talent', 'away_talent',
                        'home_points', 'away_points', 'margin']
    
    issues = []
    for feature in critical_features:
        if feature not in df.columns:
            issues.append(f"{feature}: column missing")
            continue
        
        missing = df[feature].isna().sum()
        if missing > 0:
            issues.append(f"{feature}: {missing} missing values ({missing/len(df)*100:.2f}%)")
    
    if issues:
        print("⚠️ Missing values found in critical features:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    
    print("✅ No missing values in critical features")
    return True


def check_talent_ratings():
    """Check talent ratings are within valid range (0-1500)."""
    training_file = project_root / "model_pack" / "updated_training_data.csv"
    
    if not training_file.exists():
        print("❌ Training data file not found")
        return False
    
    try:
        df = pd.read_csv(training_file)
    except Exception as e:
        print(f"❌ Error reading training data: {e}")
        return False
    
    talent_features = ['home_talent', 'away_talent']
    
    issues = []
    for feature in talent_features:
        if feature not in df.columns:
            continue
        
        min_talent = df[feature].min()
        max_talent = df[feature].max()
        
        # Updated range: 0-1500 (was 0-1000)
        if min_talent < 0:
            issues.append(f"{feature}: minimum value {min_talent} below 0")
        
        if max_talent > 1500:
            issues.append(f"{feature}: maximum value {max_talent} above 1500")
        
        if not issues and (min_talent < 0 or max_talent > 1500):
            issues.append(f"{feature}: out of range ({min_talent} to {max_talent})")
    
    if issues:
        print("⚠️ Talent rating range issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    
    print("✅ Talent ratings within valid range (0-1500)")
    return True


def main():
    """Run all data quality checks."""
    print("=" * 80)
    print("DATA QUALITY CHECKS")
    print("=" * 80)
    
    results = []
    
    print("\n1. Checking for missing required columns...")
    results.append(("Missing Columns", check_missing_columns()))
    
    print("\n2. Checking for duplicate game IDs...")
    results.append(("Duplicate Games", check_duplicate_games()))
    
    print("\n3. Checking for missing values...")
    results.append(("Missing Values", check_missing_values()))
    
    print("\n4. Checking talent rating ranges...")
    results.append(("Talent Ratings", check_talent_ratings()))
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    all_passed = True
    for check_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{check_name}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n✅ All data quality checks passed")
    else:
        print("\n❌ Some data quality checks failed")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

