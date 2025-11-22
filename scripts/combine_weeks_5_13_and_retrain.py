#!/usr/bin/env python3
"""
Combine Weeks 5-13 Data and Retrain Models
===========================================

This script:
1. Combines all week-specific training data files (week05-week13) from canonical location (data/training/weekly/)
2. Optionally includes weeks 1-4 if they are missing from training data
3. Fetches game outcomes from CFBD API or existing data
4. Merges with existing updated_training_data.csv
5. Retrains Ridge, XGBoost, and FastAI models with the updated dataset

Usage:
    python3 scripts/combine_weeks_5_13_and_retrain.py [--include-weeks-1-4]

Options:
    --include-weeks-1-4: Include weeks 1-4 in combination (if missing from training data)

Author: Script Ohio 2.0
Date: 2025-11-19
Updated: 2025-11-19 - Added support for all weeks 1-13
"""

import os
import sys
import pandas as pd
import numpy as np
import shutil
import time
import argparse
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import path utilities
from model_pack.utils.path_utils import get_weekly_training_file

# Try to import CFBD for fetching game outcomes
try:
    from cfbd import Configuration, ApiClient
    from cfbd import GamesApi
    CFBD_AVAILABLE = True
except ImportError:
    CFBD_AVAILABLE = False
    print("Warning: CFBD API not available. Will try to use existing game data.")

# Set up logging
log_dir = PROJECT_ROOT / 'logs'
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'combine_weeks_retrain.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class WeekDataCombiner:
    """Combine week-specific training data files and prepare for model retraining"""
    
    def __init__(self, project_root: Path = PROJECT_ROOT, include_weeks_1_4: bool = False):
        self.project_root = project_root
        self.include_weeks_1_4 = include_weeks_1_4
        
        # Base week files (weeks 5-13)
        self.week_files = [
            'training_data_2025_week05.csv',
            'training_data_2025_week06.csv',
            'training_data_2025_week07.csv',
            'training_data_2025_week08.csv',
            'training_data_2025_week09.csv',
            'training_data_2025_week10.csv',
            'training_data_2025_week11.csv',
            'training_data_2025_week12.csv',
            'training_data_2025_week13.csv'
        ]
        
        # Add weeks 1-4 if requested
        if include_weeks_1_4:
            weeks_1_4 = [
                'training_data_2025_week01.csv',
                'training_data_2025_week02.csv',
                'training_data_2025_week03.csv',
                'training_data_2025_week04.csv'
            ]
            self.week_files = weeks_1_4 + self.week_files
        
        self.combined_data = None
        self.cfbd_client = None
    
    def check_missing_weeks(self) -> List[int]:
        """Check which weeks are missing from training data."""
        training_path = self.project_root / 'model_pack' / 'updated_training_data.csv'
        if not training_path.exists():
            return list(range(1, 14))  # All weeks missing if no training data
        
        try:
            df = pd.read_csv(training_path, low_memory=False)
            df_2025 = df[df['season'] == 2025]
            weeks_present = set(df_2025['week'].dropna().unique().tolist())
            expected_weeks = set(range(1, 14))
            missing = sorted(list(expected_weeks - weeks_present))
            return missing
        except Exception as e:
            logger.warning(f"Could not check missing weeks: {e}")
            return []
        
    def setup_cfbd_client(self) -> bool:
        """Set up CFBD API client if API key is available"""
        if not CFBD_AVAILABLE:
            return False
            
        api_key = os.environ.get('CFBD_API_KEY')
        if not api_key:
            logger.warning("CFBD_API_KEY not found in environment. Will use existing data only.")
            return False
            
        try:
            configuration = Configuration()
            configuration.api_key['Authorization'] = f"Bearer {api_key}"
            configuration.api_key_prefix['Authorization'] = 'Bearer'
            configuration.host = "https://api.collegefootballdata.com"
            
            self.cfbd_client = GamesApi(ApiClient(configuration))
            logger.info("✅ CFBD API client initialized")
            return True
        except Exception as e:
            logger.warning(f"Failed to initialize CFBD client: {e}")
            return False
    
    def load_week_files(self) -> pd.DataFrame:
        """Load and combine all week-specific training data files"""
        logger.info("📂 Loading week-specific training data files...")
        
        all_weeks = []
        loaded_files = []
        missing_files = []
        
        for week_file in self.week_files:
            # Extract week number from filename (e.g., "training_data_2025_week05.csv" -> 5)
            try:
                week_num = int(week_file.split('week')[1].split('.')[0])
                # Use path utility with fallback search
                file_path = get_weekly_training_file(week=week_num, season=2025, base_path=self.project_root)
            except (ValueError, FileNotFoundError) as e:
                # File not found in any location - log and skip
                missing_files.append(week_file)
                logger.warning(f"⚠️  File not found: {week_file} ({e})")
                logger.debug(f"   Searched locations: data/training/weekly/, data/weekly_training/, root")
                continue
                
            try:
                df = pd.read_csv(file_path, low_memory=False)
                # Remove empty rows
                df = df.dropna(how='all')
                if len(df) > 0:
                    # Validate column count (should have 86 features + metadata)
                    if len(df.columns) < 80:
                        logger.warning(f"⚠️  {week_file} has fewer columns than expected: {len(df.columns)}")
                    
                    all_weeks.append(df)
                    loaded_files.append(week_file)
                    logger.info(f"  ✅ Loaded {week_file}: {len(df)} games, {len(df.columns)} columns")
                else:
                    logger.warning(f"  ⚠️  {week_file} is empty")
            except Exception as e:
                logger.error(f"  ❌ Error loading {week_file}: {e}")
                continue
        
        if not all_weeks:
            raise ValueError("No week files could be loaded!")
        
        if missing_files:
            logger.warning(f"⚠️  {len(missing_files)} files not found: {', '.join(missing_files)}")
        
        # Combine all weeks
        logger.info(f"📊 Combining {len(all_weeks)} week files...")
        combined = pd.concat(all_weeks, ignore_index=True)
        
        # Remove duplicates based on game ID
        initial_count = len(combined)
        if 'id' in combined.columns:
            combined = combined.drop_duplicates(subset=['id'], keep='last')
            duplicates_removed = initial_count - len(combined)
            if duplicates_removed > 0:
                logger.info(f"  Removed {duplicates_removed} duplicate games")
        else:
            logger.warning("⚠️  'id' column not found - cannot remove duplicates")
        
        logger.info(f"✅ Combined {len(combined)} unique games from {len(loaded_files)} week files")
        logger.info(f"   Columns: {len(combined.columns)}")
        
        self.combined_data = combined
        return combined
    
    def fetch_game_outcomes_cfbd(self, game_ids: List[int]) -> Dict[int, Dict]:
        """Fetch game outcomes from CFBD API with rate limiting"""
        if not self.cfbd_client:
            return {}
        
        outcomes = {}
        logger.info(f"📡 Fetching outcomes for {len(game_ids)} games from CFBD API...")
        
        try:
            # Fetch all 2025 games (more efficient than individual requests)
            time.sleep(0.17)  # Rate limiting: 6 req/sec
            games = self.cfbd_client.get_games(year=2025)
            
            # Create lookup dictionary
            game_lookup = {game.id: game for game in games if game.id in game_ids}
            
            # Extract outcomes
            for game_id in game_ids:
                if game_id in game_lookup:
                    game = game_lookup[game_id]
                    outcomes[game_id] = {
                        'home_points': game.home_points if game.home_points is not None else None,
                        'away_points': game.away_points if game.away_points is not None else None,
                        'completed': getattr(game, 'completed', False)
                    }
            
            logger.info(f"✅ Fetched outcomes for {len(outcomes)} games from CFBD API")
            return outcomes
            
        except Exception as e:
            logger.warning(f"⚠️  Error fetching from CFBD API: {e}")
            return {}
    
    def merge_outcomes_from_existing(self, df: pd.DataFrame) -> pd.DataFrame:
        """Merge game outcomes from existing training data"""
        existing_data_path = self.project_root / 'model_pack' / 'updated_training_data.csv'
        
        if not existing_data_path.exists():
            logger.info("  📂 No existing training data found for outcome merging")
            return df
        
        logger.info("  📂 Checking existing training data for outcomes...")
        try:
            existing_df = pd.read_csv(existing_data_path, low_memory=False)
            
            if 'id' not in existing_df.columns:
                logger.warning("  ⚠️  Existing data missing 'id' column")
                return df
            
            if 'home_points' not in existing_df.columns or 'away_points' not in existing_df.columns:
                logger.warning("  ⚠️  Existing data missing outcome columns")
                return df
            
            # Filter to games with outcomes
            existing_outcomes = existing_df[
                existing_df['id'].notna() & 
                existing_df['home_points'].notna() & 
                existing_df['away_points'].notna()
            ][['id', 'home_points', 'away_points']].copy()
            
            if len(existing_outcomes) == 0:
                logger.warning("  ⚠️  No outcomes found in existing data")
                return df
            
            # Merge outcomes
            initial_missing = df['home_points'].isna().sum() if 'home_points' in df.columns else len(df)
            
            if 'home_points' not in df.columns:
                df['home_points'] = np.nan
                df['away_points'] = np.nan
            
            # Merge on id
            df = df.merge(
                existing_outcomes,
                on='id',
                how='left',
                suffixes=('', '_existing')
            )
            
            # Fill missing values from existing data
            if 'home_points_existing' in df.columns:
                df['home_points'] = df['home_points'].fillna(df['home_points_existing'])
                df['away_points'] = df['away_points'].fillna(df['away_points_existing'])
                df = df.drop(columns=['home_points_existing', 'away_points_existing'])
            
            outcomes_added = initial_missing - df['home_points'].isna().sum()
            logger.info(f"  ✅ Merged outcomes from existing data: {outcomes_added} games")
            
        except Exception as e:
            logger.warning(f"  ⚠️  Error reading existing data: {e}")
        
        return df
    
    def add_game_outcomes(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add game outcomes (home_points, away_points, margin) to the dataframe"""
        logger.info("🎯 Adding game outcomes to training data...")
        
        df = df.copy()
        
        # Check if outcomes already exist
        has_outcomes = 'home_points' in df.columns and 'away_points' in df.columns
        missing_outcomes = df['home_points'].isna().any() if has_outcomes else True
        
        if has_outcomes and not missing_outcomes:
            logger.info("  ✅ Game outcomes already present in data")
            if 'margin' not in df.columns:
                df['margin'] = df['home_points'] - df['away_points']
            return df
        
        # Try to fetch from CFBD API first
        if self.cfbd_client and 'id' in df.columns:
            game_ids = df['id'].dropna().unique().tolist()
            outcomes = self.fetch_game_outcomes_cfbd(game_ids)
            
            # Merge outcomes
            if outcomes:
                for idx, row in df.iterrows():
                    game_id = row.get('id')
                    if game_id in outcomes:
                        outcome = outcomes[game_id]
                        if outcome['home_points'] is not None and outcome['away_points'] is not None:
                            if 'home_points' not in df.columns:
                                df['home_points'] = np.nan
                                df['away_points'] = np.nan
                            df.at[idx, 'home_points'] = outcome['home_points']
                            df.at[idx, 'away_points'] = outcome['away_points']
        
        # Try to merge from existing training data
        df = self.merge_outcomes_from_existing(df)
        
        # Calculate margin
        if 'home_points' in df.columns and 'away_points' in df.columns:
            df['margin'] = df['home_points'] - df['away_points']
            games_with_outcomes = df['margin'].notna().sum()
            logger.info(f"  ✅ Calculated margin for {games_with_outcomes} games ({games_with_outcomes/len(df)*100:.1f}%)")
        else:
            logger.warning("  ⚠️  Could not add game outcomes. Models will need outcomes for training.")
        
        return df
    
    def combine_with_existing_data(self, week_data: pd.DataFrame) -> pd.DataFrame:
        """Merge week data with existing updated_training_data.csv"""
        existing_path = self.project_root / 'model_pack' / 'updated_training_data.csv'
        
        if not existing_path.exists():
            logger.info("📝 No existing training data found. Using week data only.")
            return week_data
        
        logger.info("📝 Merging with existing training data...")
        try:
            existing_df = pd.read_csv(existing_path, low_memory=False)
            logger.info(f"  Loaded existing data: {len(existing_df)} games")
            
            # Combine dataframes
            combined = pd.concat([existing_df, week_data], ignore_index=True)
            
            # Remove duplicates based on game ID
            initial_count = len(combined)
            if 'id' in combined.columns:
                combined = combined.drop_duplicates(subset=['id'], keep='last')
                duplicates_removed = initial_count - len(combined)
                if duplicates_removed > 0:
                    logger.info(f"  Removed {duplicates_removed} duplicate games")
            else:
                logger.warning("  ⚠️  'id' column not found - cannot remove duplicates")
            
            logger.info(f"✅ Combined dataset: {len(combined)} total games")
            
            # Show season breakdown
            if 'season' in combined.columns:
                season_counts = combined['season'].value_counts().sort_index()
                logger.info("  Season breakdown:")
                for season, count in season_counts.items():
                    logger.info(f"    {season}: {count} games")
            
            return combined
            
        except Exception as e:
            logger.error(f"❌ Error merging with existing data: {e}")
            import traceback
            traceback.print_exc()
            return week_data
    
    def save_combined_data(self, df: pd.DataFrame, output_path: Optional[Path] = None) -> Path:
        """Save combined training data with backup of existing file"""
        if output_path is None:
            output_path = self.project_root / 'model_pack' / 'updated_training_data.csv'
        
        # Backup existing file
        if output_path.exists():
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = output_path.with_suffix('.csv.backup_' + timestamp)
            try:
                shutil.copy2(output_path, backup_path)
                logger.info(f"📦 Backed up existing file to {backup_path.name}")
            except Exception as e:
                logger.warning(f"⚠️  Could not backup existing file: {e}")
        
        # Save combined data
        try:
            df.to_csv(output_path, index=False)
            logger.info(f"💾 Saved combined training data: {output_path}")
            logger.info(f"   Total games: {len(df)}")
            logger.info(f"   Columns: {len(df.columns)}")
            
            # Show outcome statistics
            if 'home_points' in df.columns and 'away_points' in df.columns:
                games_with_outcomes = df['home_points'].notna().sum()
                logger.info(f"   Games with outcomes: {games_with_outcomes} ({games_with_outcomes/len(df)*100:.1f}%)")
            
            return output_path
        except Exception as e:
            logger.error(f"❌ Error saving combined data: {e}")
            raise
    
    def backup_models(self) -> None:
        """Backup existing model files before retraining"""
        model_dir = self.project_root / 'model_pack'
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        model_files = [
            'ridge_model_2025.joblib',
            'xgb_home_win_model_2025.pkl',
            'fastai_home_win_model_2025.pkl'
        ]
        
        for model_file in model_files:
            model_path = model_dir / model_file
            if model_path.exists():
                backup_path = model_path.with_suffix(model_path.suffix + '.backup_' + timestamp)
                try:
                    shutil.copy2(model_path, backup_path)
                    logger.info(f"📦 Backed up {model_file} to {backup_path.name}")
                except Exception as e:
                    logger.warning(f"⚠️  Could not backup {model_file}: {e}")


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Combine weeks 5-13 data and retrain models')
    parser.add_argument('--include-weeks-1-4', action='store_true',
                       help='Include weeks 1-4 in combination (if missing from training data)')
    args = parser.parse_args()
    
    logger.info("=" * 70)
    logger.info("COMBINING WEEK 5-13 DATA AND RETRAINING MODELS")
    logger.info("=" * 70)
    logger.info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Initialize combiner
        combiner = WeekDataCombiner(include_weeks_1_4=args.include_weeks_1_4)
        
        # Check for missing weeks
        missing_weeks = combiner.check_missing_weeks()
        if missing_weeks:
            logger.info(f"📊 Missing weeks detected: {missing_weeks}")
            if 13 in missing_weeks:
                logger.info("  → Week 13 will be integrated")
            if any(w in [1, 2, 3, 4] for w in missing_weeks) and not args.include_weeks_1_4:
                logger.warning("  ⚠️  Weeks 1-4 are missing. Use --include-weeks-1-4 to add them.")
        else:
            logger.info("✅ All weeks 1-13 are present in training data")
        
        # Setup CFBD client (optional)
        combiner.setup_cfbd_client()
        
        # Step 1: Load week files
        logger.info("\n" + "=" * 70)
        logger.info("STEP 1: LOAD WEEK FILES")
        logger.info("=" * 70)
        try:
            week_data = combiner.load_week_files()
        except Exception as e:
            logger.error(f"❌ Failed to load week files: {e}")
            import traceback
            traceback.print_exc()
            return 1
        
        # Step 2: Add game outcomes
        logger.info("\n" + "=" * 70)
        logger.info("STEP 2: ADD GAME OUTCOMES")
        logger.info("=" * 70)
        week_data = combiner.add_game_outcomes(week_data)
        
        # Step 3: Merge with existing data
        logger.info("\n" + "=" * 70)
        logger.info("STEP 3: MERGE WITH EXISTING DATA")
        logger.info("=" * 70)
        combined_data = combiner.combine_with_existing_data(week_data)
        
        # Step 4: Save combined data
        logger.info("\n" + "=" * 70)
        logger.info("STEP 4: SAVE COMBINED DATA")
        logger.info("=" * 70)
        output_path = combiner.save_combined_data(combined_data)
        
        # Step 5: Backup existing models
        logger.info("\n" + "=" * 70)
        logger.info("STEP 5: BACKUP EXISTING MODELS")
        logger.info("=" * 70)
        combiner.backup_models()
        
        # Step 6: Retrain models
        logger.info("\n" + "=" * 70)
        logger.info("STEP 6: RETRAIN MODELS")
        logger.info("=" * 70)
        
        try:
            # Import model training agent
            sys.path.insert(0, str(PROJECT_ROOT / 'model_pack'))
            from model_training_agent import ModelTrainingAgent
            
            # Initialize trainer with combined data path
            trainer = ModelTrainingAgent(data_path=str(output_path))
            
            # Run complete training pipeline
            trainer.run_complete_training_pipeline()
            
            logger.info("\n" + "=" * 70)
            logger.info("✅ MODEL RETRAINING COMPLETED SUCCESSFULLY!")
            logger.info("=" * 70)
            logger.info(f"📁 Models saved in: {PROJECT_ROOT / 'model_pack'}")
            logger.info(f"📊 Performance reports generated")
            logger.info(f"📝 Log file: {log_dir / 'combine_weeks_retrain.log'}")
            
        except Exception as e:
            logger.error(f"❌ Error during model retraining: {e}")
            import traceback
            traceback.print_exc()
            return 1
        
        logger.info(f"\n✅ Complete! End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        return 0
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())

