#!/usr/bin/env python3
"""
Sync All Data Sources
=====================

This script ensures all data sources across the system are synchronized:
1. Audits master training data + weekly inputs
2. Integrates missing weekly/postseason files into the master dataset
3. Checks model training dates vs data dates
4. Optionally retrains models

Usage:
    python3 scripts/sync_all_data_sources.py [--season SEASON] [--week WEEK|auto] [--retrain] [--dry-run]
"""

import os
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime
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
    parser.add_argument('--season', type=int, default=2025, help='Target season (default: 2025)')
    parser.add_argument(
        '--week',
        type=str,
        default="auto",
        help="Target week to ensure, or 'auto' to infer from weekly files",
    )
    parser.add_argument('--retrain', action='store_true', help='Retrain models after sync')
    parser.add_argument(
        '--skip-fastai',
        action='store_true',
        help='Skip FastAI retraining (recommended unless fastai is installed)',
    )
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
        df_season = df[df['season'] == int(args.season)]
        weeks_covered = sorted(df_season['week'].dropna().unique().tolist())
        max_week = max(weeks_covered) if weeks_covered else 0
        
        logger.info(f"✅ Training data status:")
        logger.info(f"   Total games: {len(df):,}")
        logger.info(f"   {args.season} games: {len(df_season):,}")
        logger.info(f"   Weeks covered: {weeks_covered}")
        logger.info(f"   Latest week: {max_week}")

        # Determine target week from canonical weekly files (auto) or argument.
        if str(args.week).lower() == "auto":
            weekly_dir = PROJECT_ROOT / "data" / "training" / "weekly"
            week_files = sorted(weekly_dir.glob(f"training_data_{int(args.season)}_week*.csv"))
            detected_weeks: list[int] = []
            for path in week_files:
                try:
                    detected_weeks.append(int(path.stem.split("week")[-1]))
                except Exception:
                    continue
            target_week = max(detected_weeks) if detected_weeks else max_week
        else:
            target_week = int(args.week)

        if max_week < target_week:
            logger.warning(
                f"⚠️  Master training data only goes to Week {max_week}, "
                f"but weekly inputs go to Week {target_week}"
            )
        else:
            logger.info(f"✅ Training data includes Week {target_week}")

        # Check if master dataset contains the game IDs present in weekly/postseason inputs.
        weekly_inputs_dir = PROJECT_ROOT / "data" / "training" / "weekly"
        input_paths = sorted(
            weekly_inputs_dir.glob(f"training_data_{int(args.season)}_week*.csv")
        )
        postseason_path = weekly_inputs_dir / f"training_data_{int(args.season)}_postseason.csv"
        if postseason_path.exists():
            input_paths.append(postseason_path)

        if input_paths and "id" in df.columns:
            master_ids = set(df['id'].dropna().astype(int).tolist())
            missing_weeks: set[int] = set()
            missing_postseason = False

            for path in input_paths:
                try:
                    in_df = pd.read_csv(path, usecols=['id', 'week'], low_memory=False)
                except Exception:
                    continue
                in_ids = set(in_df['id'].dropna().astype(int).tolist())
                if not in_ids:
                    continue
                if in_ids - master_ids:
                    if "postseason" in path.name:
                        missing_postseason = True
                    else:
                        missing_weeks.update(
                            in_df['week'].dropna().astype(int).unique().tolist()
                        )

            if missing_weeks or missing_postseason:
                parts = []
                if missing_weeks:
                    parts.append(f"weeks {sorted(missing_weeks)}")
                if missing_postseason:
                    parts.append("postseason")
                logger.warning(f"⚠️  Master dataset missing IDs from: {', '.join(parts)}")

                if not args.dry_run:
                    integrate_script = PROJECT_ROOT / "scripts" / "integrate_weekly_files.py"
                    week_arg = ",".join(str(w) for w in sorted(missing_weeks)) or str(target_week)
                    cmd = [
                        sys.executable,
                        str(integrate_script),
                        "--season",
                        str(int(args.season)),
                        "--weeks",
                        week_arg,
                    ]
                    if missing_postseason:
                        cmd.append("--include-postseason")
                    logger.info("Integrating weekly inputs into master dataset...")
                    subprocess.run(cmd, cwd=PROJECT_ROOT, check=False)
            else:
                logger.info("✅ Master dataset already contains all weekly/postseason IDs")
            
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
        retrain_script = PROJECT_ROOT / "scripts" / "retrain_models_current.py"
        if retrain_script.exists():
            cmd = [sys.executable, str(retrain_script)]
            if args.skip_fastai:
                cmd.append("--skip-fastai")
            subprocess.run(cmd, cwd=PROJECT_ROOT)
    elif needs_retrain:
        logger.warning(f"\n⚠️  Models that may need retraining: {', '.join(needs_retrain)}")
        logger.info("   Run with --retrain to automatically retrain")
    
    # Step 4: Summary
    logger.info("\n" + "=" * 70)
    logger.info("SYNCHRONIZATION COMPLETE")
    logger.info("=" * 70)
    
    all_good = (
        max_week >= (int(args.week) if str(args.week).lower() != "auto" else max_week) and
        len(needs_retrain) == 0
    )
    
    if all_good:
        logger.info("✅ All data sources are synchronized")
    else:
        logger.warning("⚠️  Some components may need attention (see above)")
    
    return 0 if all_good else 1

if __name__ == "__main__":
    sys.exit(main())
