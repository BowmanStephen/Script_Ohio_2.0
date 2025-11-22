#!/usr/bin/env python3
"""
Ensure Latest Data Script
=========================

This script ensures all system components are using the latest data by:
1. Verifying training data includes latest weeks
2. Checking if models need retraining
3. Updating any outdated references
4. Providing clear status report

Usage:
    python3 scripts/ensure_latest_data.py [--week WEEK] [--retrain] [--force]
"""

import os
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import logging
import subprocess

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_training_data_coverage(target_week: int = 13) -> Dict[str, any]:
    """Check if training data includes target week"""
    training_path = PROJECT_ROOT / "model_pack" / "updated_training_data.csv"
    
    if not training_path.exists():
        return {
            'status': 'missing',
            'message': 'Training data file not found'
        }
    
    try:
        df = pd.read_csv(training_path)
        df_2025 = df[df['season'] == 2025]
        
        if len(df_2025) == 0:
            return {
                'status': 'no_2025_data',
                'message': 'No 2025 season data found'
            }
        
        weeks_covered = sorted(df_2025['week'].unique().tolist())
        max_week = max(weeks_covered)
        
        if max_week >= target_week:
            return {
                'status': 'up_to_date',
                'max_week': max_week,
                'weeks_covered': weeks_covered,
                'total_games': len(df_2025),
                'message': f'Training data includes Week {max_week}'
            }
        else:
            return {
                'status': 'outdated',
                'max_week': max_week,
                'target_week': target_week,
                'weeks_covered': weeks_covered,
                'message': f'Training data only goes to Week {max_week}, need Week {target_week}'
            }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Error reading training data: {e}'
        }

def check_model_dates() -> Dict[str, any]:
    """Check if models are newer than training data"""
    training_path = PROJECT_ROOT / "model_pack" / "updated_training_data.csv"
    
    if not training_path.exists():
        return {'status': 'no_data_file'}
    
    training_date = datetime.fromtimestamp(training_path.stat().st_mtime)
    
    models = {
        'ridge': 'ridge_model_2025.joblib',
        'xgb': 'xgb_home_win_model_2025.pkl',
        'fastai': 'fastai_home_win_model_2025.pkl',
        'random_forest': 'random_forest_model_2025.pkl'
    }
    
    result = {
        'training_data_date': training_date.isoformat(),
        'models': {},
        'needs_retrain': []
    }
    
    for name, filename in models.items():
        model_path = PROJECT_ROOT / "model_pack" / filename
        if model_path.exists():
            model_date = datetime.fromtimestamp(model_path.stat().st_mtime)
            is_older = model_date < training_date
            result['models'][name] = {
                'date': model_date.isoformat(),
                'older_than_data': is_older
            }
            if is_older:
                result['needs_retrain'].append(name)
    
    return result

def update_training_data(target_week: int) -> bool:
    """Update training data to include target week"""
    logger.info(f"Updating training data to include Week {target_week}...")
    
    # Check if combine script exists
    combine_script = PROJECT_ROOT / "scripts" / "combine_weeks_5_13_and_retrain.py"
    if combine_script.exists():
        logger.info(f"Running: {combine_script}")
        try:
            result = subprocess.run(
                [sys.executable, str(combine_script)],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                logger.info("✅ Training data updated successfully")
                return True
            else:
                logger.error(f"❌ Update failed: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"❌ Error running update script: {e}")
            return False
    else:
        logger.warning("⚠️  Combine script not found. Manual update may be needed.")
        return False

def retrain_models() -> bool:
    """Retrain all models with latest data"""
    logger.info("Retraining models...")
    
    combine_script = PROJECT_ROOT / "scripts" / "combine_weeks_5_13_and_retrain.py"
    if combine_script.exists():
        try:
            result = subprocess.run(
                [sys.executable, str(combine_script), "--retrain"],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                logger.info("✅ Models retrained successfully")
                return True
            else:
                logger.error(f"❌ Retraining failed: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"❌ Error retraining: {e}")
            return False
    else:
        logger.warning("⚠️  Retraining script not found")
        return False

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Ensure all system components use latest data")
    parser.add_argument('--week', type=int, default=13, help='Target week to ensure coverage')
    parser.add_argument('--retrain', action='store_true', help='Retrain models if needed')
    parser.add_argument('--force', action='store_true', help='Force update even if appears current')
    parser.add_argument('--update-data', action='store_true', help='Update training data if needed')
    
    args = parser.parse_args()
    
    logger.info("=" * 70)
    logger.info("ENSURING LATEST DATA")
    logger.info("=" * 70)
    
    # Check training data
    logger.info("\n1. Checking Training Data Coverage")
    logger.info("-" * 70)
    data_status = check_training_data_coverage(args.week)
    logger.info(f"Status: {data_status['status']}")
    logger.info(f"Message: {data_status.get('message', 'N/A')}")
    
    if data_status['status'] == 'outdated' and args.update_data:
        logger.info("\nUpdating training data...")
        if update_training_data(args.week):
            # Recheck
            data_status = check_training_data_coverage(args.week)
        else:
            logger.error("Failed to update training data")
            return 1
    
    # Check models
    logger.info("\n2. Checking Model Training Dates")
    logger.info("-" * 70)
    model_status = check_model_dates()
    logger.info(f"Training data date: {model_status['training_data_date']}")
    
    for name, info in model_status['models'].items():
        status = "⚠️  OLDER" if info['older_than_data'] else "✅ CURRENT"
        logger.info(f"  {name}: {status} (modified {info['date']})")
    
    if model_status['needs_retrain']:
        logger.warning(f"\n⚠️  Models that may need retraining: {', '.join(model_status['needs_retrain'])}")
        if args.retrain:
            logger.info("\nRetraining models...")
            if not retrain_models():
                logger.error("Failed to retrain models")
                return 1
    else:
        logger.info("\n✅ All models are current")
    
    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("SUMMARY")
    logger.info("=" * 70)
    
    all_good = (
        data_status['status'] == 'up_to_date' and
        len(model_status['needs_retrain']) == 0
    )
    
    if all_good:
        logger.info("✅ System is using latest data")
        logger.info(f"   Training data: Week {data_status.get('max_week', 'N/A')}")
        logger.info("   Models: All current")
        return 0
    else:
        logger.warning("⚠️  Some components may need updating")
        if data_status['status'] != 'up_to_date':
            logger.warning(f"   Training data: {data_status.get('message', 'N/A')}")
        if model_status['needs_retrain']:
            logger.warning(f"   Models: {', '.join(model_status['needs_retrain'])} may need retraining")
        return 1

if __name__ == "__main__":
    sys.exit(main())

