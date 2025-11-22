#!/usr/bin/env python3
"""
Weekly Analysis Preparation Script
Fetches weekly data, validates previous week results, and prepares for weekly analysis
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
from typing import Dict, Any
import pandas as pd
import json
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def check_cfbd_api_key() -> bool:
    """Check if CFBD API key is set"""
    api_key = os.environ.get('CFBD_API_KEY')
    if not api_key:
        print("⚠️  CFBD_API_KEY environment variable not set")
        print("   Set it with: export CFBD_API_KEY=your_key_here")
        return False
    return True


def fetch_week_schedule(week: int, season: int, api_key: str) -> Dict[str, Any]:
    """Fetch weekly game schedule from CFBD API"""
    print(f"📡 Fetching Week {week} game schedule from CFBD API...")
    
    try:
        from project_management.TOOLS_AND_CONFIG.fetch_future_week import fetch_week_data
        
        result = fetch_week_data(season=season, week=week, api_key=api_key)
        print(f"✅ Fetched {result['fetched_games']} Week {week} games")
        print(f"   Total games in system: {result['total_games']}")
        return result
    except Exception as e:
        print(f"❌ Error fetching Week {week} schedule: {e}")
        return {'error': str(e)}


def validate_previous_week_results(week: int, season: int) -> Dict[str, Any]:
    """Validate that previous week results are in training data"""
    previous_week = week - 1
    print(f"\n🔍 Validating Week {previous_week} results in training data...")
    
    try:
        training_path = project_root / "model_pack" / "updated_training_data.csv"
        if not training_path.exists():
            print("⚠️  Training data file not found")
            return {'status': 'warning', 'message': 'Training data file not found'}
        
        training_df = pd.read_csv(training_path)
        prev_week_games = training_df[(training_df['season'] == season) & (training_df['week'] == previous_week)]
        
        if len(prev_week_games) == 0:
            print(f"⚠️  No Week {previous_week} {season} games found in training data")
            print(f"   You may need to update training data with Week {previous_week} results")
            return {
                'status': 'warning',
                'previous_week_games_found': 0,
                'message': f'Week {previous_week} results not yet in training data'
            }
        else:
            print(f"✅ Found {len(prev_week_games)} Week {previous_week} {season} games in training data")
            return {
                'status': 'success',
                'previous_week_games_found': len(prev_week_games),
                'total_training_games': len(training_df)
            }
    except Exception as e:
        print(f"❌ Error validating Week {previous_week} results: {e}")
        return {'status': 'error', 'error': str(e)}


def check_model_files() -> Dict[str, Any]:
    """Check that model files exist and are recent"""
    print("\n🔍 Checking model files...")
    
    model_files = {
        'ridge': project_root / "model_pack" / "ridge_model_2025.joblib",
        'xgb': project_root / "model_pack" / "xgb_home_win_model_2025.pkl",
        'fastai': project_root / "model_pack" / "fastai_home_win_model_2025.pkl"
    }
    
    results = {}
    for model_name, model_path in model_files.items():
        if model_path.exists():
            mtime = datetime.fromtimestamp(model_path.stat().st_mtime)
            age_days = (datetime.now() - mtime).days
            results[model_name] = {
                'exists': True,
                'last_modified': mtime.isoformat(),
                'age_days': age_days,
                'status': 'recent' if age_days < 30 else 'old'
            }
            print(f"✅ {model_name}: Found (modified {age_days} days ago)")
        else:
            results[model_name] = {'exists': False, 'status': 'missing'}
            print(f"⚠️  {model_name}: Not found")
    
    return results


def create_week_directories(week: int) -> bool:
    """Create weekly directory structure"""
    print(f"\n📁 Creating Week {week} directory structure...")
    
    # Import path utilities for canonical paths
    from model_pack.utils.path_utils import get_weekly_enhanced_dir, ensure_directory_exists
    
    # Use canonical directory path
    enhanced_dir = get_weekly_enhanced_dir(week)
    ensure_directory_exists(enhanced_dir)
    
    directories = [
        enhanced_dir,
        project_root / "analysis" / f"week{week}",
        project_root / "predictions" / f"week{week}",
        project_root / "validation" / f"week{week}"
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created/verified: {directory}")
    
    return True


def check_week_data_availability(week: int) -> Dict[str, Any]:
    """Check if weekly data files exist"""
    print(f"\n🔍 Checking Week {week} data availability...")
    
    # Import path utilities for canonical paths
    from model_pack.utils.path_utils import get_weekly_enhanced_file
    
    try:
        features_path = get_weekly_enhanced_file(week, 'features')
    except FileNotFoundError:
        features_path = None
    
    try:
        games_path = get_weekly_enhanced_file(week, 'games')
    except FileNotFoundError:
        games_path = None
    
    data_files = {
        'games': project_root / "starter_pack" / "data" / "2025_games.csv",
        'features': features_path,
        'enhanced_games': games_path
    }
    
    results = {}
    for file_type, file_path in data_files.items():
        if file_path is not None and file_path.exists():
            results[file_type] = {'exists': True, 'path': str(file_path)}
            print(f"✅ {file_type}: Found at {file_path}")
        else:
            results[file_type] = {'exists': False, 'path': str(file_path) if file_path else 'None'}
            print(f"⚠️  {file_type}: Not found" + (f" (expected at {file_path})" if file_path else ""))
    
    return results


def suggest_next_steps(week: int, season: int, validation_results: Dict[str, Any], 
                       model_results: Dict[str, Any],
                       data_results: Dict[str, Any]) -> None:
    """Suggest next steps based on validation results"""
    previous_week = week - 1
    print("\n📋 Recommended Next Steps:")
    print("=" * 60)
    
    # Check if previous week results need to be added
    if validation_results.get('previous_week_games_found', 0) == 0:
        print(f"\n1. Update training data with Week {previous_week} results:")
        print(f"   python project_management/core_tools/data_workflows.py refresh-training --max-week {week}")
    
    # Check if models need retraining
    old_models = [name for name, info in model_results.items() 
                  if info.get('status') == 'old']
    if old_models:
        print(f"\n2. Retrain models (some are >30 days old):")
        print("   python config/retrain_fixed_models.py")
        print("   python project_management/core_tools/data_workflows.py train-fastai")
    
    # Check if weekly data needs to be generated
    if not data_results.get('features', {}).get('exists'):
        print(f"\n3. Generate Week {week} features (run feature generation pipeline or CFBD integration)")
    
    if not data_results.get('enhanced_games', {}).get('exists'):
        print(f"\n4. Generate enhanced Week {week} games data")
    
    print(f"\n5. Run Week {week} analysis:")
    print("   from agents.weekly_analysis_orchestrator import WeeklyAnalysisOrchestrator")
    print(f"   orchestrator = WeeklyAnalysisOrchestrator(week={week}, season={season})")
    print("   result = orchestrator.run_complete_analysis()")
    
    print("\n" + "=" * 60)


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description="Prepare weekly analysis")
    parser.add_argument('--week', type=int, default=13,
                       help='Week number to prepare (default: 13)')
    parser.add_argument('--season', type=int, default=2025,
                       help='Season year (default: 2025)')
    parser.add_argument('--skip-fetch', action='store_true',
                       help='Skip fetching weekly schedule from CFBD')
    parser.add_argument('--skip-validation', action='store_true',
                       help='Skip previous week validation check')
    args = parser.parse_args()
    
    week = args.week
    season = args.season
    
    print("=" * 60)
    print(f"Week {week} Analysis Preparation - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Step 1: Check CFBD API key
    has_api_key = check_cfbd_api_key()
    
    # Step 2: Fetch weekly schedule (if API key available and not skipped)
    if has_api_key and not args.skip_fetch:
        fetch_result = fetch_week_schedule(week, season, os.environ['CFBD_API_KEY'])
    else:
        print(f"\n⏭️  Skipping Week {week} schedule fetch")
        fetch_result = {'skipped': True}
    
    # Step 3: Validate previous week results
    if not args.skip_validation:
        validation_results = validate_previous_week_results(week, season)
    else:
        print(f"\n⏭️  Skipping Week {week-1} validation")
        validation_results = {'skipped': True}
    
    # Step 4: Check model files
    model_results = check_model_files()
    
    # Step 5: Create directories
    create_week_directories(week)
    
    # Step 6: Check data availability
    data_results = check_week_data_availability(week)
    
    # Step 7: Suggest next steps
    suggest_next_steps(week, season, validation_results, model_results, data_results)
    
    print(f"\n✅ Week {week} preparation check complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())

