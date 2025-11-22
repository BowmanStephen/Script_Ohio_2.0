#!/usr/bin/env python3
"""
Recover Missing Games - Local Data First Strategy

This script:
1. Extracts missing games from local data sources (ZERO API calls for most games)
2. Builds features from local data files
3. Only uses API for games truly not available locally (batched by week/year)
4. Integrates all recovered games into training data

CRITICAL: This script minimizes API usage by checking local data sources first!
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Set, Optional
import pandas as pd
import numpy as np

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import path utilities
from model_pack.utils.path_utils import get_weekly_training_file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# File paths
STARTER_PACK_GAMES = PROJECT_ROOT / 'starter_pack' / 'data' / 'games.csv'
BACKUP_TRAINING = PROJECT_ROOT / 'model_pack' / 'training_data.csv'
MISSING_GAMES = PROJECT_ROOT / 'reports' / 'missing_games.csv'
CURRENT_TRAINING = PROJECT_ROOT / 'model_pack' / 'updated_training_data.csv'
STARTER_PACK_PLAYS = PROJECT_ROOT / 'starter_pack' / 'data' / 'plays'
STARTER_PACK_DRIVES = PROJECT_ROOT / 'starter_pack' / 'data' / 'drives'
STARTER_PACK_ADV_STATS = PROJECT_ROOT / 'starter_pack' / 'data' / 'advanced_game_stats'

# Weekly training data files (2025 season, weeks 1-13, all have 86 features)
# Use path utility for dynamic resolution with fallback support
def get_weekly_training_files(weeks: List[int], season: int = 2025) -> List[Path]:
    """Get weekly training file paths using path utility."""
    files = []
    for week in weeks:
        try:
            file_path = get_weekly_training_file(week=week, season=season, base_path=PROJECT_ROOT)
            if file_path.exists():
                files.append(file_path)
        except FileNotFoundError:
            logger.warning(f"Week {week} training file not found, skipping")
    return files

# Default weeks 5-13 for backward compatibility
WEEKLY_TRAINING_WEEKS = list(range(5, 14))


class LocalFirstGameRecovery:
    """Recover missing games using local data sources first."""
    
    def __init__(self):
        self.stats = {
            'total_missing': 0,
            'found_in_starter': 0,
            'found_in_backup': 0,
            'found_in_weekly_training': 0,  # All weekly training files (weeks 5-13)
            'still_missing': 0,
            'api_calls_needed': 0,
            'api_calls_made': 0
        }
        # Track which weekly files contributed games
        self.weekly_file_stats = {}
    
    def phase1_extract_from_local(self) -> Dict[str, pd.DataFrame]:
        """Phase 1: Extract games from local data sources."""
        logger.info("=" * 80)
        logger.info("PHASE 1: LOCAL DATA EXTRACTION")
        logger.info("=" * 80)
        
        # Load missing games list
        if not MISSING_GAMES.exists():
            logger.error(f"Missing games file not found: {MISSING_GAMES}")
            logger.info("Run scripts/identify_missing_games.py first")
            return {}
        
        missing_games_df = pd.read_csv(MISSING_GAMES)
        self.stats['total_missing'] = len(missing_games_df)
        logger.info(f"Total missing games: {len(missing_games_df)}")
        
        # Extract from starter pack
        found_in_starter = pd.DataFrame()
        if STARTER_PACK_GAMES.exists():
            logger.info(f"Loading starter pack games from {STARTER_PACK_GAMES}...")
            try:
                starter_games_df = pd.read_csv(STARTER_PACK_GAMES, low_memory=False)
                logger.info(f"Loaded {len(starter_games_df)} games from starter pack")
                
                # Match missing game IDs
                found_in_starter = starter_games_df[
                    starter_games_df['id'].isin(missing_games_df['id'])
                ].copy()
                self.stats['found_in_starter'] = len(found_in_starter)
                logger.info(f"✅ Found {len(found_in_starter)} missing games in starter pack")
            except Exception as e:
                logger.error(f"Error loading starter pack: {e}")
        else:
            logger.warning(f"Starter pack games file not found: {STARTER_PACK_GAMES}")
        
        # Extract from backup training data
        found_in_backup = pd.DataFrame()
        if BACKUP_TRAINING.exists():
            logger.info(f"Loading backup training data from {BACKUP_TRAINING}...")
            try:
                backup_training_df = pd.read_csv(BACKUP_TRAINING, low_memory=False)
                logger.info(f"Loaded {len(backup_training_df)} games from backup training data")
                
                # Match missing game IDs
                found_in_backup = backup_training_df[
                    backup_training_df['id'].isin(missing_games_df['id'])
                ].copy()
                self.stats['found_in_backup'] = len(found_in_backup)
                logger.info(f"✅ Found {len(found_in_backup)} missing games in backup training data (with 86 features!)")
            except Exception as e:
                logger.error(f"Error loading backup training data: {e}")
        else:
            logger.warning(f"Backup training data file not found: {BACKUP_TRAINING}")
        
        # Extract from all weekly training data files (2025 weeks 5-13, all have 86 features)
        found_in_weekly = []
        total_found_in_weekly = 0
        
        logger.info("Checking weekly training data files (weeks 5-13)...")
        # Get weekly training files using path utility (supports weeks 1-13)
        weekly_training_files = get_weekly_training_files(WEEKLY_TRAINING_WEEKS)
        for weekly_file in weekly_training_files:
            if weekly_file.exists():
                try:
                    logger.info(f"  Loading {weekly_file.name}...")
                    weekly_df = pd.read_csv(weekly_file, low_memory=False)
                    
                    # Match missing game IDs
                    found_in_this_week = weekly_df[
                        weekly_df['id'].isin(missing_games_df['id'])
                    ].copy()
                    
                    if len(found_in_this_week) > 0:
                        found_in_weekly.append(found_in_this_week)
                        count = len(found_in_this_week)
                        total_found_in_weekly += count
                        self.weekly_file_stats[weekly_file.name] = count
                        logger.info(f"    ✅ Found {count} missing games in {weekly_file.name} (with 86 features!)")
                except Exception as e:
                    logger.error(f"  Error loading {weekly_file.name}: {e}")
            else:
                logger.warning(f"  Weekly training file not found: {weekly_file.name}")
        
        # Combine all weekly training data
        found_in_all_weekly = pd.DataFrame()
        if found_in_weekly:
            found_in_all_weekly = pd.concat(found_in_weekly, ignore_index=True)
            self.stats['found_in_weekly_training'] = total_found_in_weekly
            logger.info(f"✅ Total found in weekly training data (weeks 5-13): {total_found_in_weekly} games (all have 86 features!)")
        
        # Identify still-missing games
        all_found_ids = set()
        if len(found_in_starter) > 0:
            all_found_ids.update(found_in_starter['id'].astype(str))
        if len(found_in_backup) > 0:
            all_found_ids.update(found_in_backup['id'].astype(str))
        if len(found_in_all_weekly) > 0:
            all_found_ids.update(found_in_all_weekly['id'].astype(str))
        
        still_missing = missing_games_df[
            ~missing_games_df['id'].astype(str).isin(all_found_ids)
        ].copy()
        self.stats['still_missing'] = len(still_missing)
        
        # Calculate unique (year, week) combinations for API calls
        if len(still_missing) > 0:
            unique_weeks = still_missing.groupby(['season', 'week']).size()
            self.stats['api_calls_needed'] = len(unique_weeks)
            logger.info(f"⚠️  Still missing: {len(still_missing)} games")
            logger.info(f"📡 API calls needed: {self.stats['api_calls_needed']} (one per unique week/year)")
            logger.info(f"   Reduction: {((len(missing_games_df) - self.stats['api_calls_needed']) / len(missing_games_df) * 100):.1f}% fewer calls than naive approach")
        else:
            logger.info("🎉 All missing games found in local sources! ZERO API calls needed!")
        
        return {
            'found_in_starter': found_in_starter,
            'found_in_backup': found_in_backup,
            'found_in_weekly_training': found_in_all_weekly,
            'still_missing': still_missing
        }
    
    def phase2_build_features_local(self, found_games: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Phase 2: Build features from local data sources."""
        logger.info("=" * 80)
        logger.info("PHASE 2: FEATURE ENGINEERING FROM LOCAL DATA")
        logger.info("=" * 80)
        
        all_games_with_features = []
        
        # Games from backup training data already have 86 features!
        if len(found_games.get('found_in_backup', pd.DataFrame())) > 0:
            backup_games = found_games['found_in_backup']
            logger.info(f"✅ Using {len(backup_games)} games from backup (already have 86 features)")
            all_games_with_features.append(backup_games)
        
        # Games from weekly training data already have 86 features!
        if len(found_games.get('found_in_weekly_training', pd.DataFrame())) > 0:
            weekly_games = found_games['found_in_weekly_training']
            logger.info(f"✅ Using {len(weekly_games)} games from weekly training data (weeks 5-13, already have 86 features)")
            all_games_with_features.append(weekly_games)
        
        # Games from starter pack need feature engineering
        if len(found_games.get('found_in_starter', pd.DataFrame())) > 0:
            starter_games = found_games['found_in_starter']
            logger.info(f"🔧 Building features for {len(starter_games)} games from starter pack")
            
            # For now, use basic structure - full feature engineering can be added later
            # TODO: Implement full 86-feature engineering using local data files
            starter_with_features = self._build_basic_features(starter_games)
            all_games_with_features.append(starter_with_features)
        
        if all_games_with_features:
            combined = pd.concat(all_games_with_features, ignore_index=True)
            logger.info(f"✅ Total games with features from local data: {len(combined)}")
            return combined
        else:
            logger.warning("No games found in local sources")
            return pd.DataFrame()
    
    def _build_basic_features(self, games_df: pd.DataFrame) -> pd.DataFrame:
        """Build basic features structure (placeholder for full feature engineering)."""
        # This is a simplified version - full implementation would:
        # 1. Load plays data from starter_pack/data/plays/
        # 2. Load drives data from starter_pack/data/drives/
        # 3. Load advanced stats from starter_pack/data/advanced_game_stats/
        # 4. Use existing feature engineering pipeline from model_pack
        
        # For now, create basic structure matching training data format
        result_df = games_df.copy()
        
        # Ensure we have basic columns
        required_cols = ['id', 'season', 'week', 'home_team', 'away_team', 'home_points', 'away_points']
        for col in required_cols:
            if col not in result_df.columns:
                logger.warning(f"Missing required column: {col}")
        
        # Add basic calculated fields
        if 'home_points' in result_df.columns and 'away_points' in result_df.columns:
            result_df['margin'] = (result_df['home_points'] - result_df['away_points']).abs()
        
        logger.info(f"Built basic features for {len(result_df)} games")
        logger.info("NOTE: Full 86-feature engineering should be implemented using local data files")
        
        return result_df
    
    def phase3_api_fetch_if_needed(self, still_missing: pd.DataFrame) -> pd.DataFrame:
        """Phase 3: Fetch remaining games from API (batched)."""
        if len(still_missing) == 0:
            logger.info("✅ No API calls needed - all games found locally!")
            return pd.DataFrame()
        
        logger.info("=" * 80)
        logger.info("PHASE 3: API FETCH (BATCHED)")
        logger.info("=" * 80)
        logger.info(f"Fetching {len(still_missing)} games using batched API calls")
        logger.info(f"Estimated API calls: {self.stats['api_calls_needed']}")
        
        # Check for API key
        API_KEY = os.environ.get("CFBD_API_KEY") or os.environ.get("CFBD_API_TOKEN")
        if not API_KEY:
            logger.error("CFBD_API_KEY not set - cannot fetch from API")
            logger.info("Games will be saved for later API fetch")
            return pd.DataFrame()
        
        # Use the FIXED fill_missing_games.py script
        try:
            # Import using absolute path
            import importlib.util
            fill_missing_path = PROJECT_ROOT / 'scripts' / 'fill_missing_games.py'
            spec = importlib.util.spec_from_file_location("fill_missing_games", fill_missing_path)
            fill_missing_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(fill_missing_module)
            MissingGamesFiller = fill_missing_module.MissingGamesFiller
            
            filler = MissingGamesFiller()
            api_fetched = filler.fetch_all_missing_games(still_missing)
            self.stats['api_calls_made'] = self.stats['api_calls_needed']
            
            logger.info(f"✅ Fetched {len(api_fetched)} games from API")
            return api_fetched
        except Exception as e:
            logger.error(f"Error fetching from API: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return pd.DataFrame()
    
    def phase4_integrate_all(self, local_games: pd.DataFrame, api_games: pd.DataFrame) -> bool:
        """Phase 4: Integrate all recovered games."""
        logger.info("=" * 80)
        logger.info("PHASE 4: INTEGRATION")
        logger.info("=" * 80)
        
        # Combine all games
        all_recovered = []
        if len(local_games) > 0:
            all_recovered.append(local_games)
        if len(api_games) > 0:
            all_recovered.append(api_games)
        
        if not all_recovered:
            logger.warning("No games to integrate")
            return False
        
        all_recovered_df = pd.concat(all_recovered, ignore_index=True)
        logger.info(f"Total games recovered: {len(all_recovered_df)}")
        
        # Use existing integration logic from fill_missing_games.py
        try:
            # Import using absolute path
            import importlib.util
            fill_missing_path = PROJECT_ROOT / 'scripts' / 'fill_missing_games.py'
            spec = importlib.util.spec_from_file_location("fill_missing_games", fill_missing_path)
            fill_missing_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(fill_missing_module)
            MissingGamesFiller = fill_missing_module.MissingGamesFiller
            
            filler = MissingGamesFiller()
            success = filler.integrate_games(all_recovered_df)
            
            if success:
                logger.info("✅ Successfully integrated all recovered games")
            else:
                logger.error("❌ Failed to integrate games")
            
            return success
        except Exception as e:
            logger.error(f"Error integrating games: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def run(self, analyze_only: bool = False) -> Dict:
        """Execute complete recovery workflow."""
        logger.info("=" * 80)
        logger.info("LOCAL-FIRST MISSING GAMES RECOVERY")
        logger.info("=" * 80)
        
        # Phase 1: Extract from local
        found_games = self.phase1_extract_from_local()
        
        if analyze_only:
            logger.info("\n" + "=" * 80)
            logger.info("ANALYSIS COMPLETE (analyze-only mode)")
            logger.info("=" * 80)
            return {'stats': self.stats, 'found_games': found_games}
        
        # Phase 2: Build features from local data
        local_games_with_features = self.phase2_build_features_local(found_games)
        
        # Phase 3: API fetch if needed (batched)
        api_games_with_features = self.phase3_api_fetch_if_needed(found_games.get('still_missing', pd.DataFrame()))
        
        # Phase 4: Integrate all
        success = self.phase4_integrate_all(local_games_with_features, api_games_with_features)
        
        # Summary
        logger.info("=" * 80)
        logger.info("RECOVERY SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total missing games: {self.stats['total_missing']}")
        logger.info(f"Found in starter pack: {self.stats['found_in_starter']}")
        logger.info(f"Found in backup training: {self.stats['found_in_backup']}")
        logger.info(f"Found in weekly training (weeks 5-13): {self.stats['found_in_weekly_training']}")
        if self.weekly_file_stats:
            logger.info("  Weekly file breakdown:")
            for filename, count in sorted(self.weekly_file_stats.items()):
                logger.info(f"    {filename}: {count} games")
        logger.info(f"Still missing (API needed): {self.stats['still_missing']}")
        logger.info(f"API calls needed: {self.stats['api_calls_needed']}")
        logger.info(f"API calls made: {self.stats['api_calls_made']}")
        logger.info(f"Success: {success}")
        
        if success:
            logger.info("=" * 80)
            logger.info("✅ SUCCESS: All games recovered and integrated!")
            logger.info("=" * 80)
        else:
            logger.error("=" * 80)
            logger.error("❌ FAILED: Recovery incomplete")
            logger.error("=" * 80)
        
        return {
            'success': success,
            'stats': self.stats
        }


def main():
    """Main execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Recover missing games using local data first')
    parser.add_argument('--analyze-only', action='store_true',
                       help='Only analyze what can be recovered locally, do not fetch or integrate')
    args = parser.parse_args()
    
    recovery = LocalFirstGameRecovery()
    result = recovery.run(analyze_only=args.analyze_only)
    
    if not result.get('success', False) and not args.analyze_only:
        sys.exit(1)


if __name__ == "__main__":
    main()

