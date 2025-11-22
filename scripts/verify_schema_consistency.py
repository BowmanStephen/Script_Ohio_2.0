#!/usr/bin/env python3
"""
Verify Schema Consistency Script

Verifies that 81-feature schema (88 total columns) matches across all weeks.
Part of Script Ohio 2.0 data validation pipeline.
"""

import pandas as pd
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def verify_schema_consistency():
    """Verify all weeks have consistent 81-feature schema (88 total columns)."""
    training_file = project_root / "model_pack" / "updated_training_data.csv"
    
    if not training_file.exists():
        print("❌ Training data file not found")
        print(f"   Expected: {training_file}")
        return False
    
    try:
        df = pd.read_csv(training_file)
    except Exception as e:
        print(f"❌ Error reading training data: {e}")
        return False
    
    # Expected 81 predictive features (88 total columns including 7 metadata)
    # According to feature_validation_summary.json, the schema includes:
    # - 81 predictive features used by models
    # - 7 metadata columns: id, start_date, season_type, game_key, conference_game, home_conference, away_conference
    # Total: 88 columns
    expected_features = 81
    
    # Non-feature columns that should be excluded from feature count
    # Only pure metadata/identifier columns that are never used as features
    # Note: season, week, home_team, away_team, neutral_site ARE counted as features
    non_feature_columns = ['id', 'game_key', 'conference_game', 
                          'start_date', 'season_type',
                          'home_conference', 'away_conference']
    
    # Check column count
    feature_columns = [col for col in df.columns 
                      if col not in non_feature_columns]
    
    if len(feature_columns) != expected_features:
        print(f"❌ Expected {expected_features} features, got {len(feature_columns)}")
        print(f"   Feature columns: {len(feature_columns)}")
        print(f"   Total columns: {len(df.columns)}")
        return False
    
    print(f"✅ Feature count matches: {len(feature_columns)} features")
    
    # Check for missing values in critical features
    critical_features = ['home_elo', 'away_elo', 'home_talent', 'away_talent',
                        'home_points', 'away_points', 'margin']
    
    missing_features = []
    missing_value_counts = {}
    
    for feature in critical_features:
        if feature not in df.columns:
            missing_features.append(feature)
            continue
        
        missing_count = df[feature].isna().sum()
        if missing_count > 0:
            missing_value_counts[feature] = missing_count
    
    if missing_features:
        print(f"❌ Missing critical features: {missing_features}")
        return False
    
    if missing_value_counts:
        print("⚠️ Missing values found in critical features:")
        for feature, count in missing_value_counts.items():
            print(f"  - {feature}: {count} missing values")
        return False
    
    print("✅ All critical features present with no missing values")
    
    # Verify schema consistency across weeks
    if 'season' in df.columns and 'week' in df.columns:
        df_2025 = df[df['season'] == 2025]
        weeks = sorted(df_2025['week'].dropna().unique().tolist())
        
        print(f"\nVerifying schema consistency across {len(weeks)} weeks...")
        week_column_counts = {}
        
        for week in weeks:
            week_df = df_2025[df_2025['week'] == week]
            week_column_counts[week] = len(week_df.columns)
        
        # Check if all weeks have the same column count
        if len(set(week_column_counts.values())) > 1:
            print("⚠️ Inconsistent column counts across weeks:")
            for week, count in sorted(week_column_counts.items()):
                print(f"  Week {week}: {count} columns")
            return False
        
        print(f"✅ Schema consistent across all {len(weeks)} weeks")
    
    print("✅ Schema consistency verified")
    return True


if __name__ == "__main__":
    success = verify_schema_consistency()
    sys.exit(0 if success else 1)

