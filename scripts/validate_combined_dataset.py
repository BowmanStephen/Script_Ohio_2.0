#!/usr/bin/env python3
"""
Comprehensive validation of combined training dataset.

Validates:
- Total game count
- All 86 features present
- Missing values in critical columns
- Game outcomes availability
- Schema consistency
- Data quality metrics
"""

import pandas as pd
import sys
from pathlib import Path
from typing import Dict, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TRAINING_DATA_PATH = PROJECT_ROOT / 'model_pack' / 'updated_training_data.csv'


def validate_combined_dataset() -> Dict[str, any]:
    """Run comprehensive validation on combined dataset."""
    
    results = {
        'status': 'unknown',
        'issues': [],
        'warnings': [],
        'metrics': {},
        'validation_passed': False
    }
    
    # Check if file exists
    if not TRAINING_DATA_PATH.exists():
        results['status'] = 'error'
        results['issues'].append(f"Training data file not found: {TRAINING_DATA_PATH}")
        return results
    
    # Load data
    try:
        df = pd.read_csv(TRAINING_DATA_PATH, low_memory=False)
        results['metrics']['total_games'] = len(df)
        results['metrics']['total_columns'] = len(df.columns)
    except Exception as e:
        results['status'] = 'error'
        results['issues'].append(f"Error reading training data: {str(e)}")
        return results
    
    # Validate feature count (expected 86)
    expected_features = 86
    if len(df.columns) != expected_features:
        results['warnings'].append(
            f"Column count mismatch: Expected {expected_features}, found {len(df.columns)}"
        )
    
    # Check required columns
    required_columns = ['id', 'season', 'week', 'home_team', 'away_team', 
                       'home_elo', 'away_elo', 'home_talent', 'away_talent']
    missing_required = [col for col in required_columns if col not in df.columns]
    if missing_required:
        results['issues'].append(f"Missing required columns: {missing_required}")
    
    # Check 2025 season data
    df_2025 = df[df['season'] == 2025].copy()
    results['metrics']['2025_games'] = len(df_2025)
    
    # Check week coverage
    weeks_2025 = sorted(df_2025['week'].dropna().unique().tolist())
    expected_weeks = list(range(1, 14))
    missing_weeks = set(expected_weeks) - set(weeks_2025)
    
    if missing_weeks:
        results['issues'].append(f"Missing weeks in 2025 data: {sorted(missing_weeks)}")
    else:
        results['metrics']['weeks_1_13_complete'] = True
    
    # Check for missing values in critical columns
    critical_columns = ['home_team', 'away_team', 'home_elo', 'away_elo', 
                       'home_talent', 'away_talent']
    missing_values_summary = {}
    for col in critical_columns:
        if col in df.columns:
            missing_count = df[col].isna().sum()
            if missing_count > 0:
                missing_values_summary[col] = missing_count
                results['warnings'].append(
                    f"Missing values in {col}: {missing_count} ({missing_count/len(df)*100:.1f}%)"
                )
    
    results['metrics']['missing_values'] = missing_values_summary
    
    # Check game outcomes
    if 'home_points' in df.columns and 'away_points' in df.columns:
        games_with_outcomes = df[
            df['home_points'].notna() & df['away_points'].notna()
        ]
        results['metrics']['games_with_outcomes'] = len(games_with_outcomes)
        results['metrics']['outcomes_percentage'] = len(games_with_outcomes) / len(df) * 100
        
        # Check 2025 outcomes
        df_2025_with_outcomes = df_2025[
            df_2025['home_points'].notna() & df_2025['away_points'].notna()
        ]
        results['metrics']['2025_games_with_outcomes'] = len(df_2025_with_outcomes)
        results['metrics']['2025_outcomes_percentage'] = len(df_2025_with_outcomes) / len(df_2025) * 100 if len(df_2025) > 0 else 0
    else:
        results['warnings'].append("Game outcome columns (home_points, away_points) not found")
    
    # Check for duplicates
    if 'id' in df.columns:
        duplicates = df.duplicated(subset=['id'], keep=False)
        duplicate_count = duplicates.sum()
        if duplicate_count > 0:
            results['warnings'].append(f"Found {duplicate_count} duplicate game IDs")
        results['metrics']['duplicate_games'] = duplicate_count
    
    # Season breakdown
    season_counts = df['season'].value_counts().sort_index().to_dict()
    results['metrics']['season_breakdown'] = season_counts
    
    # Data type validation
    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
    results['metrics']['numeric_columns'] = len(numeric_cols)
    
    # Overall status
    if results['issues']:
        results['status'] = 'failed'
        results['validation_passed'] = False
    elif results['warnings']:
        results['status'] = 'warning'
        results['validation_passed'] = True
    else:
        results['status'] = 'passed'
        results['validation_passed'] = True
    
    return results


def print_validation_results(results: Dict[str, any]):
    """Print validation results in human-readable format."""
    print("=" * 80)
    print("COMBINED DATASET VALIDATION REPORT")
    print("=" * 80)
    print(f"Status: {results['status'].upper()}")
    print()
    
    print("METRICS:")
    metrics = results['metrics']
    print(f"  Total games: {metrics.get('total_games', 'N/A')}")
    print(f"  Total columns: {metrics.get('total_columns', 'N/A')}")
    print(f"  2025 season games: {metrics.get('2025_games', 'N/A')}")
    
    if metrics.get('weeks_1_13_complete'):
        print("  ✅ All weeks 1-13 present")
    
    if 'games_with_outcomes' in metrics:
        print(f"  Games with outcomes: {metrics['games_with_outcomes']} ({metrics.get('outcomes_percentage', 0):.1f}%)")
        print(f"  2025 games with outcomes: {metrics.get('2025_games_with_outcomes', 0)} ({metrics.get('2025_outcomes_percentage', 0):.1f}%)")
    
    if 'season_breakdown' in metrics:
        print("\n  Season breakdown:")
        for season, count in sorted(metrics['season_breakdown'].items()):
            print(f"    {season}: {count} games")
    
    if results['issues']:
        print("\nISSUES:")
        for issue in results['issues']:
            print(f"  ❌ {issue}")
    
    if results['warnings']:
        print("\nWARNINGS:")
        for warning in results['warnings']:
            print(f"  ⚠️  {warning}")
    
    print()
    if results['validation_passed']:
        print("✅ VALIDATION PASSED")
    else:
        print("❌ VALIDATION FAILED")
    print("=" * 80)


if __name__ == "__main__":
    results = validate_combined_dataset()
    print_validation_results(results)
    
    sys.exit(0 if results['validation_passed'] else 1)

