#!/usr/bin/env python3
"""
Comprehensive verification script for 2025 season data completeness.

This script verifies:
- Which weeks (1-13) are present in updated_training_data.csv
- Game counts per week for 2025 season
- Schema consistency (86 features expected)
- Data quality checks
- Outputs JSON report with week-by-week status
"""

import pandas as pd
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TRAINING_DATA_PATH = PROJECT_ROOT / 'model_pack' / 'updated_training_data.csv'
WEEKLY_TRAINING_DIR = PROJECT_ROOT / 'data' / 'weekly_training'
OUTPUT_REPORT_PATH = PROJECT_ROOT / 'reports' / '2025_data_completeness_report.json'


def verify_2025_data_completeness() -> Dict[str, Any]:
    """Verify 2025 season data completeness and generate report."""
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'training_data_file': str(TRAINING_DATA_PATH),
        'weekly_training_dir': str(WEEKLY_TRAINING_DIR),
        'status': 'unknown',
        'weeks_status': {},
        'summary': {},
        'issues': [],
        'recommendations': []
    }
    
    # Check if training data file exists
    if not TRAINING_DATA_PATH.exists():
        report['status'] = 'error'
        report['issues'].append(f"Training data file not found: {TRAINING_DATA_PATH}")
        return report
    
    # Load training data
    try:
        df = pd.read_csv(TRAINING_DATA_PATH, low_memory=False)
        report['summary']['total_games'] = len(df)
        report['summary']['total_columns'] = len(df.columns)
    except Exception as e:
        report['status'] = 'error'
        report['issues'].append(f"Error reading training data: {str(e)}")
        return report
    
    # Check 2025 season data
    df_2025 = df[df['season'] == 2025].copy()
    report['summary']['2025_games'] = len(df_2025)
    
    if len(df_2025) == 0:
        report['status'] = 'error'
        report['issues'].append("No 2025 season data found in training data")
        return report
    
    # Check week coverage (1-13)
    expected_weeks = list(range(1, 14))  # Weeks 1-13
    weeks_present = sorted(df_2025['week'].dropna().unique().tolist())
    missing_weeks = set(expected_weeks) - set(weeks_present)
    
    # Check each week
    for week in expected_weeks:
        week_data = df_2025[df_2025['week'] == week]
        week_file = WEEKLY_TRAINING_DIR / f'training_data_2025_week{week:02d}.csv'
        
        week_status = {
            'week': week,
            'present_in_training_data': week in weeks_present,
            'games_count': len(week_data),
            'weekly_file_exists': week_file.exists(),
            'has_outcomes': False,
            'missing_features': [],
            'data_quality_issues': []
        }
        
        if week in weeks_present:
            # Check for game outcomes
            if 'home_points' in week_data.columns and 'away_points' in week_data.columns:
                games_with_outcomes = week_data[
                    week_data['home_points'].notna() & 
                    week_data['away_points'].notna()
                ]
                week_status['has_outcomes'] = len(games_with_outcomes) > 0
                week_status['games_with_outcomes'] = len(games_with_outcomes)
            
            # Check for missing values in critical columns
            critical_cols = ['home_team', 'away_team', 'home_elo', 'away_elo', 
                           'home_talent', 'away_talent']
            for col in critical_cols:
                if col in week_data.columns:
                    missing_count = week_data[col].isna().sum()
                    if missing_count > 0:
                        week_status['data_quality_issues'].append(
                            f"{col}: {missing_count} missing values"
                        )
        
        # Check weekly file if it exists
        if week_file.exists():
            try:
                weekly_df = pd.read_csv(week_file, low_memory=False)
                week_status['weekly_file_games'] = len(weekly_df)
                week_status['weekly_file_columns'] = len(weekly_df.columns)
                
                # Check if weekly file matches training data schema
                if week in weeks_present:
                    if len(weekly_df.columns) != len(df.columns):
                        week_status['data_quality_issues'].append(
                            f"Weekly file has {len(weekly_df.columns)} columns, "
                            f"training data has {len(df.columns)} columns"
                        )
            except Exception as e:
                week_status['data_quality_issues'].append(
                    f"Error reading weekly file: {str(e)}"
                )
        else:
            if week in weeks_present:
                week_status['data_quality_issues'].append(
                    "Weekly file missing but data present in training data"
                )
        
        report['weeks_status'][f'week_{week}'] = week_status
    
    # Schema validation
    expected_feature_count = 86
    if len(df.columns) != expected_feature_count:
        report['issues'].append(
            f"Expected {expected_feature_count} features, found {len(df.columns)} columns"
        )
        report['recommendations'].append(
            "Verify schema matches expected 86-feature structure"
        )
    
    # Check for required columns
    required_columns = ['id', 'season', 'week', 'home_team', 'away_team']
    missing_required = [col for col in required_columns if col not in df.columns]
    if missing_required:
        report['issues'].append(f"Missing required columns: {missing_required}")
    
    # Overall status
    if missing_weeks:
        report['status'] = 'incomplete'
        report['issues'].append(f"Missing weeks: {sorted(missing_weeks)}")
        report['recommendations'].append(
            f"Integrate missing weeks {sorted(missing_weeks)} into training data"
        )
    else:
        report['status'] = 'complete'
    
    # Summary statistics
    report['summary']['weeks_present'] = weeks_present
    report['summary']['weeks_missing'] = sorted(missing_weeks)
    report['summary']['total_weeks_expected'] = len(expected_weeks)
    report['summary']['total_weeks_present'] = len(weeks_present)
    
    # Game counts by week
    report['summary']['game_counts_by_week'] = {
        week: len(df_2025[df_2025['week'] == week])
        for week in expected_weeks
    }
    
    # Save report
    OUTPUT_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_REPORT_PATH, 'w') as f:
        json.dump(report, f, indent=2)
    
    return report


def print_report_summary(report: Dict[str, Any]):
    """Print a human-readable summary of the verification report."""
    print("=" * 80)
    print("2025 DATA COMPLETENESS VERIFICATION REPORT")
    print("=" * 80)
    print(f"Timestamp: {report['timestamp']}")
    print(f"Status: {report['status'].upper()}")
    print()
    
    print("SUMMARY:")
    print(f"  Total games in training data: {report['summary']['total_games']}")
    print(f"  2025 season games: {report['summary']['2025_games']}")
    print(f"  Weeks present: {report['summary']['total_weeks_present']}/{report['summary']['total_weeks_expected']}")
    print(f"  Weeks missing: {report['summary']['weeks_missing']}")
    print()
    
    print("WEEK-BY-WEEK STATUS:")
    for week in range(1, 14):
        week_key = f'week_{week}'
        if week_key in report['weeks_status']:
            status = report['weeks_status'][week_key]
            present = "✓" if status['present_in_training_data'] else "✗"
            games = status['games_count']
            file_exists = "✓" if status['weekly_file_exists'] else "✗"
            outcomes = "✓" if status.get('has_outcomes', False) else "✗"
            
            print(f"  Week {week:2d}: {present} | Games: {games:3d} | File: {file_exists} | Outcomes: {outcomes}")
            
            if status['data_quality_issues']:
                for issue in status['data_quality_issues']:
                    print(f"           ⚠️  {issue}")
    
    if report['issues']:
        print()
        print("ISSUES FOUND:")
        for issue in report['issues']:
            print(f"  ⚠️  {issue}")
    
    if report['recommendations']:
        print()
        print("RECOMMENDATIONS:")
        for rec in report['recommendations']:
            print(f"  → {rec}")
    
    print()
    print(f"Full report saved to: {OUTPUT_REPORT_PATH}")
    print("=" * 80)


if __name__ == "__main__":
    report = verify_2025_data_completeness()
    print_report_summary(report)
    
    # Exit with error code if status is not complete
    if report['status'] != 'complete':
        sys.exit(1)
    sys.exit(0)

