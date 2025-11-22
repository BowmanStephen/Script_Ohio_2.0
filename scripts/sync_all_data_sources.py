#!/usr/bin/env python3
"""
Sync All Data Sources
=====================

This script ensures all data sources across the system are synchronized:
1. Verifies training data includes latest weeks
2. Updates any outdated data references
3. Checks model training dates
4. Provides comprehensive status report

Usage:
    python3 scripts/sync_all_data_sources.py [--week WEEK] [--retrain] [--dry-run]
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
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(PROJECT_ROOT / 'logs' / 'data_sync.log')
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Main synchronization workflow"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Synchronize all data sources")
    parser.add_argument('--week', type=int, default=13, help='Target week to ensure')
    parser.add_argument('--retrain', action='store_true', help='Retrain models after sync')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    
    args = parser.parse_args()
    
    logger.info("=" * 70)
    logger.info("SYNCHRONIZING ALL DATA SOURCES")
    logger.info("=" * 70)
    
    # Step 1: Run audit
    logger.info("\nStep 1: Running data audit...")
    try:
        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "scripts" / "audit_and_sync_data.py")],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT
        )
        logger.info(result.stdout)
        if result.returncode != 0:
            logger.warning("Audit found issues - see output above")
    except Exception as e:
        logger.error(f"Error running audit: {e}")
    
    # Step 2: Check training data
    logger.info("\nStep 2: Verifying training data...")
    training_path = PROJECT_ROOT / "model_pack" / "updated_training_data.csv"
    
    if not training_path.exists():
        logger.error("❌ Training data file not found!")
        return 1
    
    try:
        df = pd.read_csv(training_path)
        df_2025 = df[df['season'] == 2025]
        weeks_covered = sorted(df_2025['week'].unique().tolist())
        max_week = max(weeks_covered) if weeks_covered else 0
        
        logger.info(f"✅ Training data status:")
        logger.info(f"   Total games: {len(df):,}")
        logger.info(f"   2025 games: {len(df_2025):,}")
        logger.info(f"   Weeks covered: {weeks_covered}")
        logger.info(f"   Latest week: {max_week}")
        
        if max_week < args.week:
            logger.warning(f"⚠️  Training data only goes to Week {max_week}, need Week {args.week}")
            if not args.dry_run:
                logger.info("   Updating training data...")
                # Run update script
                update_script = PROJECT_ROOT / "scripts" / "combine_weeks_5_13_and_retrain.py"
                if update_script.exists():
                    subprocess.run([sys.executable, str(update_script)], cwd=PROJECT_ROOT)
        else:
            logger.info(f"✅ Training data includes Week {args.week}")
            
    except Exception as e:
        logger.error(f"❌ Error checking training data: {e}")
        return 1
    
    # Step 3: Check models
    logger.info("\nStep 3: Verifying models...")
    training_date = datetime.fromtimestamp(training_path.stat().st_mtime)
    
    models = {
        'ridge': 'ridge_model_2025.joblib',
        'xgb': 'xgb_home_win_model_2025.pkl',
        'fastai': 'fastai_home_win_model_2025.pkl',
        'random_forest': 'random_forest_model_2025.pkl'
    }
    
    needs_retrain = []
    for name, filename in models.items():
        model_path = PROJECT_ROOT / "model_pack" / filename
        if model_path.exists():
            model_date = datetime.fromtimestamp(model_path.stat().st_mtime)
            if model_date < training_date:
                needs_retrain.append(name)
                logger.warning(f"⚠️  {name} model is older than training data")
            else:
                logger.info(f"✅ {name} model is current")
        else:
            logger.error(f"❌ {name} model not found")
    
    if needs_retrain and args.retrain and not args.dry_run:
        logger.info(f"\nRetraining models: {', '.join(needs_retrain)}")
        retrain_script = PROJECT_ROOT / "scripts" / "combine_weeks_5_13_and_retrain.py"
        if retrain_script.exists():
            subprocess.run([sys.executable, str(retrain_script)], cwd=PROJECT_ROOT)
    elif needs_retrain:
        logger.warning(f"\n⚠️  Models that may need retraining: {', '.join(needs_retrain)}")
        logger.info("   Run with --retrain to automatically retrain")
    
    # Step 4: Summary
    logger.info("\n" + "=" * 70)
    logger.info("SYNCHRONIZATION COMPLETE")
    logger.info("=" * 70)
    
    all_good = (
        max_week >= args.week and
        len(needs_retrain) == 0
    )
    
    if all_good:
        logger.info("✅ All data sources are synchronized")
    else:
        logger.warning("⚠️  Some components may need attention (see above)")
    
    return 0 if all_good else 1

if __name__ == "__main__":
    sys.exit(main())

