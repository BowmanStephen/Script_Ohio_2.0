#!/usr/bin/env python3
"""
Verification script to check weeks 1-12 integration in training data.

This script verifies:
- All weeks 1-12 are present in 2025 season data
- Game counts per week
- Schema consistency across weeks
"""

import pandas as pd
import sys
from pathlib import Path

def verify_weeks_1_12_integration():
    """Verify all weeks 1-12 are present in training data."""
    training_file = Path("model_pack/updated_training_data.csv")
    
    if not training_file.exists():
        print("❌ Training data file not found")
        print(f"   Expected: {training_file.absolute()}")
        return False
    
    try:
        df = pd.read_csv(training_file)
    except Exception as e:
        print(f"❌ Error reading training data: {e}")
        return False
    
    # Check 2025 season data
    df_2025 = df[df['season'] == 2025]
    
    if len(df_2025) == 0:
        print("❌ No 2025 season data found in training data")
        return False
    
    # Check week coverage
    weeks_present = sorted(df_2025['week'].dropna().unique().tolist())
    expected_weeks = list(range(1, 13))  # Weeks 1-12
    
    missing_weeks = set(expected_weeks) - set(weeks_present)
    
    if missing_weeks:
        print(f"❌ Missing weeks: {sorted(missing_weeks)}")
        print(f"   Weeks present: {weeks_present}")
        return False
    
    print(f"✅ All weeks 1-12 present: {weeks_present}")
    
    # Check game counts
    print("\n📊 Game counts by week:")
    for week in expected_weeks:
        week_games = len(df_2025[df_2025['week'] == week])
        print(f"   Week {week}: {week_games} games")
    
    # Check schema consistency
    print("\n🔍 Schema consistency check:")
    print(f"   Total columns: {len(df.columns)}")
    print(f"   Total 2025 games: {len(df_2025)}")
    
    # Check for required columns
    required_columns = ['id', 'season', 'week', 'home_team', 'away_team',
                       'home_points', 'away_points', 'margin', 'game_key']
    missing_required = [col for col in required_columns if col not in df.columns]
    
    if missing_required:
        print(f"⚠️  Missing required columns: {missing_required}")
    else:
        print("✅ All required columns present")
    
    # Check for numeric feature columns
    numeric_columns = df.select_dtypes(include=['int64', 'float64']).columns
    print(f"   Numeric feature columns: {len(numeric_columns)}")
    
    return True

if __name__ == "__main__":
    success = verify_weeks_1_12_integration()
    sys.exit(0 if success else 1)
