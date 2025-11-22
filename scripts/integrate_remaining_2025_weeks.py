#!/usr/bin/env python3.13
"""
Script Ohio 2.0 - Complete 2025 Missing Weeks Integration

Integrate remaining weeks 13, 14, and 16 from starter pack to complete the 2025 dataset.
This will bring the total 2025 games from 637 to ~800+ for complete season coverage.

Author: Data Integration Specialist Agent
Created: 2025-11-18
Version: 1.0.0
"""

import logging
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import sys
import os
import time

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from src.data_sources import CFBDRESTDataSource, CFBDClientConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def fetch_game_scores_from_api(rest_ds, year, week, game_id, home_team, away_team):
    """Fetch scores for a specific game from CFBD API.
    
    Args:
        rest_ds: CFBD REST data source client
        year: Season year
        week: Week number
        game_id: Game ID to match
        home_team: Home team name
        away_team: Away team name
        
    Returns:
        Tuple of (home_points, away_points) or (None, None) if not found
    """
    try:
        # Fetch all games for this week
        games = rest_ds.fetch_games(year=year, week=week, season_type="regular")
        
        if not games:
            return None, None
            
        # Try to find matching game by ID first, then by team names
        for game in games:
            if game.get('id') == game_id:
                return game.get('home_points'), game.get('away_points')
            
            # Fallback: match by team names (normalize spaces/case)
            game_home = str(game.get('home_team', '')).strip().lower()
            game_away = str(game.get('away_team', '')).strip().lower()
            expected_home = str(home_team).strip().lower()
            expected_away = str(away_team).strip().lower()
            
            if game_home == expected_home and game_away == expected_away:
                return game.get('home_points'), game.get('away_points')
                
        return None, None
        
    except Exception as e:
        logger.warning(f"Failed to fetch scores from API for game {game_id}: {e}")
        return None, None


def main():
    """Main integration function for remaining 2025 weeks"""
    logger.info("🚀 Starting integration of remaining 2025 weeks (13, 14, 16)")
    logger.info("="  * 80)
    
    # Initialize CFBD client for fetching missing scores
    api_key = os.environ.get('CFBD_API_KEY')
    if not api_key:
        logger.warning("⚠️ CFBD_API_KEY not found. Will not be able to fetch missing scores from API.")
        rest_ds = None
    else:
        try:
            rest_ds = CFBDRESTDataSource(config=CFBDClientConfig(api_key=api_key))
            logger.info("✅ CFBD API client initialized for score fetching")
        except Exception as e:
            logger.warning(f"⚠️ Failed to initialize CFBD client: {e}. Will not fetch missing scores.")
            rest_ds = None

    # File paths
    starter_data_path = Path("starter_pack/data/2025_games.csv")
    training_data_path = Path("model_pack/updated_training_data.csv")
    output_path = Path("model_pack/updated_training_data_complete.csv")

    # Check files exist
    if not starter_data_path.exists():
        logger.error(f"❌ Starter data not found: {starter_data_path}")
        return False

    if not training_data_path.exists():
        logger.error(f"❌ Training data not found: {training_data_path}")
        return False

    logger.info("📁 Loading datasets...")

    # Load datasets
    try:
        starter_df = pd.read_csv(starter_data_path)
        training_df = pd.read_csv(training_data_path)
        
        # Load 2025 game stats to fix missing scores
        game_stats_path = Path("starter_pack/data/game_stats/2025.csv")
        if game_stats_path.exists():
            logger.info(f"✅ Loaded 2025 game stats from {game_stats_path}")
            game_stats_df = pd.read_csv(game_stats_path)
            
            # Create score mapping: game_id -> {home_points, away_points}
            score_map = {}
            for _, row in game_stats_df.iterrows():
                gid = row['game_id']
                if gid not in score_map:
                    score_map[gid] = {}
                
                if row['home_away'] == 'home':
                    score_map[gid]['home_points'] = row['points']
                else:
                    score_map[gid]['away_points'] = row['points']
            
            # Update starter_df with scores from stats
            updated_count = 0
            for idx, row in starter_df.iterrows():
                if row['season'] == 2025 and (pd.isna(row.get('home_points')) or pd.isna(row.get('away_points'))):
                    gid = row['id']
                    if gid in score_map:
                        scores = score_map[gid]
                        if 'home_points' in scores and 'away_points' in scores:
                            starter_df.at[idx, 'home_points'] = scores['home_points']
                            starter_df.at[idx, 'away_points'] = scores['away_points']
                            updated_count += 1
            
            logger.info(f"✅ Repaired scores for {updated_count} games using game_stats")
        else:
            logger.warning(f"⚠️ Game stats file not found at {game_stats_path}. Cannot repair missing scores.")

        logger.info(f"✅ Loaded starter data: {len(starter_df)} games")
        logger.info(f"✅ Loaded training data: {len(training_df)} games")

    except Exception as e:
        logger.error(f"❌ Error loading data: {str(e)}")
        return False

    # Filter to 2025 season
    starter_2025 = starter_df[starter_df['season'] == 2025].copy()
    training_2025 = training_df[training_df['season'] == 2025].copy()

    logger.info(f"📊 2025 Data Summary:")
    logger.info(f"  Starter pack 2025: {len(starter_2025)} games")
    logger.info(f"  Training data 2025: {len(training_2025)} games")

    # Analyze week coverage
    starter_weeks = sorted(starter_2025['week'].unique())
    training_weeks = sorted(training_2025['week'].unique())

    logger.info(f"  Starter weeks: {starter_weeks}")
    logger.info(f"  Training weeks: {training_weeks}")

    # Find missing weeks
    missing_weeks = [week for week in starter_weeks if week not in training_weeks]
    logger.info(f"  Missing weeks to integrate: {missing_weeks}")

    # Check week 12 completeness
    if 12 in starter_weeks and 12 in training_weeks:
        starter_week12_count = len(starter_2025[starter_2025['week'] == 12])
        training_week12_count = len(training_2025[training_2025['week'] == 12])

        logger.info(f"  Week 12 - Starter: {starter_week12_count}, Training: {training_week12_count}")

        if starter_week12_count > training_week12_count:
            missing_week12 = starter_week12_count - training_week12_count
            logger.info(f"  ⚠️  Missing {missing_week12} week 12 games to complete the week")

    # Filter missing weeks data
    missing_data_list = []

    for week in missing_weeks:
        week_data = starter_2025[starter_2025['week'] == week].copy()
        logger.info(f"  Week {week}: {len(week_data)} games available")
        missing_data_list.append(week_data)

    if missing_data_list:
        missing_games_df = pd.concat(missing_data_list, ignore_index=True)
        logger.info(f"📋 Total missing games to integrate: {len(missing_games_df)}")
    else:
        logger.info("✅ No missing weeks found!")
        return True

    # Prepare missing games for training data format
    logger.info("🔧 Preparing missing games for training data format...")

    # Get training data schema
    training_columns = training_df.columns.tolist()
    logger.info(f"📊 Training data has {len(training_columns)} columns")

    # Create template for missing games
    missing_games_processed = []
    api_fetched_count = 0
    skipped_future_games = 0

    for _, game in missing_games_df.iterrows():
        home_points = game.get('home_points')
        away_points = game.get('away_points')
        
        # Check if scores are missing
        if pd.isna(home_points) or pd.isna(away_points):
            # Try to fetch from API if client is available
            if rest_ds is not None:
                game_id = game.get('id')
                week = game.get('week')
                home_team = game.get('home_team', game.get('home', 'Unknown'))
                away_team = game.get('away_team', game.get('away', 'Unknown'))
                
                logger.info(f"🔍 Fetching scores from API for {home_team} vs {away_team} (Week {week}, ID: {game_id})")
                
                api_home_points, api_away_points = fetch_game_scores_from_api(
                    rest_ds, 2025, week, game_id, home_team, away_team
                )
                
                # If we got valid scores from API, use them
                if api_home_points is not None and api_away_points is not None:
                    home_points = api_home_points
                    away_points = api_away_points
                    api_fetched_count += 1
                    logger.info(f"✅ Fetched scores from API: {home_team} {home_points} - {away_points} {away_team}")
                    time.sleep(0.2)  # Rate limiting
                else:
                    # Game not found or not completed yet - skip it
                    logger.warning(f"⚠️ Skipping game {home_team} vs {away_team} (Week {week}) - no scores available (likely future game)")
                    skipped_future_games += 1
                    continue
            else:
                # No API client - skip game
                logger.warning(f"⚠️ Skipping game {game.get('home_team')} vs {game.get('away_team')} (Week {game.get('week')}) due to missing scores (no API client).")
                skipped_future_games += 1
                continue

        # Create row with all required columns
        processed_game = {}

        # Map basic fields
        for col in training_columns:
            if col in game.index:
                processed_game[col] = game[col]
            else:
                # Set default/missing values for required fields
                if col == 'id':
                    processed_game[col] = game.get('id', f"missing_{len(missing_games_processed)}")
                elif col in ['season', 'season_type']:
                    processed_game[col] = 2025
                elif col == 'neutral_site':
                    processed_game[col] = game.get('neutral_site', False)
                elif col in ['home_team', 'away_team']:
                    processed_game[col] = game.get(col.replace('_team', ''), 'Unknown')
                elif col in ['home_conference', 'away_conference']:
                    processed_game[col] = 'FBS'  # Default
                elif col in ['home_elo', 'away_elo']:
                    processed_game[col] = 1500.0  # Default Elo
                elif col in ['home_talent', 'away_talent']:
                    processed_game[col] = 0.0  # Default talent
                elif col == 'home_points':
                    # Use the fetched or existing score (no fallback to 0)
                    processed_game[col] = home_points
                elif col == 'away_points':
                    # Use the fetched or existing score (no fallback to 0)
                    processed_game[col] = away_points
                elif col == 'margin':
                    processed_game[col] = home_points - away_points
                elif col == 'spread':
                    processed_game[col] = 0.0
                elif col == 'game_key':
                    home_team = game.get('home_team', 'Unknown')
                    away_team = game.get('away_team', 'Unknown')
                    week = game.get('week', 1)
                    processed_game[col] = f"2025_{week}_{home_team}_{away_team}".replace(' ', '_')
                elif col == 'conference_game':
                    home_conf = game.get('home_conference', 'FBS')
                    away_conf = game.get('away_conference', 'FBS')
                    processed_game[col] = int(home_conf == away_conf and home_conf != 'FBS')
                else:
                    # For advanced metrics, use NaN or 0.0
                    if 'epa' in col.lower() or 'yards' in col.lower() or 'success' in col.lower():
                        processed_game[col] = np.nan
                    else:
                        processed_game[col] = 0.0

        missing_games_processed.append(processed_game)

    # Convert to DataFrame
    if not missing_games_processed:
        logger.warning("⚠️ All missing games were skipped due to missing scores. No new games to integrate.")
        logger.info(f"📊 API Fetch Summary: {api_fetched_count} scores fetched, {skipped_future_games} future games skipped")
        # Create empty DF with correct columns to allow script to proceed (or just return)
        missing_games_df_processed = pd.DataFrame(columns=training_columns)
    else:
        missing_games_df_processed = pd.DataFrame(missing_games_processed)
        # Ensure all columns match training data
        missing_games_df_processed = missing_games_df_processed[training_columns]

    logger.info(f"✅ Processed {len(missing_games_df_processed)} missing games")
    logger.info(f"📊 API Fetch Summary: {api_fetched_count} scores fetched from API, {skipped_future_games} future games skipped")

    # Show week breakdown
    for week in sorted(missing_games_df_processed['week'].unique()):
        week_count = len(missing_games_df_processed[missing_games_df_processed['week'] == week])
        logger.info(f"  Week {week}: {week_count} games")

    # Combine with existing training data
    logger.info("🔗 Combining with existing training data...")

    # Create backup
    backup_path = training_data_path.with_suffix('.csv.backup_remaining_weeks')
    training_df.to_csv(backup_path, index=False)
    logger.info(f"💾 Backup saved to: {backup_path}")

    # Combine datasets
    combined_df = pd.concat([training_df, missing_games_df_processed], ignore_index=True)

    logger.info(f"📊 Combined dataset:")
    logger.info(f"  Total games: {len(combined_df)}")
    logger.info(f"  Games before: {len(training_df)}")
    logger.info(f"  Games added: {len(missing_games_df_processed)}")

    # Verify 2025 coverage
    combined_2025 = combined_df[combined_df['season'] == 2025]
    combined_weeks = sorted(combined_2025['week'].unique())
    logger.info(f"  2025 weeks after integration: {combined_weeks}")

    for week in combined_weeks:
        week_count = len(combined_2025[combined_2025['week'] == week])
        logger.info(f"    Week {week}: {week_count} games")

    # Save updated dataset
    logger.info("💾 Saving updated training data...")
    combined_df.to_csv(output_path, index=False)
    logger.info(f"✅ Updated training data saved to: {output_path}")

    # Also update the main file
    combined_df.to_csv(training_data_path, index=False)
    logger.info(f"✅ Original training data updated in place")

    # Generate summary report
    report = {
        "integration_timestamp": datetime.now().isoformat(),
        "source_files": {
            "starter_data": str(starter_data_path),
            "training_data_before": str(training_data_path),
            "backup_created": str(backup_path)
        },
        "integration_summary": {
            "games_before": len(training_df),
            "games_after": len(combined_df),
            "games_added": len(missing_games_df_processed),
            "missing_weeks_integrated": missing_weeks
        },
        "2025_coverage": {
            "weeks_before": training_weeks,
            "weeks_after": combined_weeks,
            "games_2025_before": len(training_2025),
            "games_2025_after": len(combined_2025)
        },
        "data_quality": {
            "columns_count": len(combined_df.columns),
            "missing_values_before": training_df.isnull().sum().sum(),
            "missing_values_after": combined_df.isnull().sum().sum(),
            "schema_consistent": list(combined_df.columns) == training_columns
        }
    }

    # Save report
    report_path = Path("logs/remaining_weeks_integration_report.json")
    report_path.parent.mkdir(exist_ok=True)

    import json
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)

    logger.info(f"📊 Integration report saved to: {report_path}")

    # Success message
    logger.info("=" * 80)
    logger.info("🎉 REMAINING WEEKS INTEGRATION COMPLETED SUCCESSFULLY!")
    logger.info("=" * 80)
    logger.info(f"📈 Results:")
    logger.info(f"  ✅ Integrated {len(missing_games_df_processed)} missing games")
    logger.info(f"  ✅ Total dataset now has {len(combined_df)} games")
    logger.info(f"  ✅ 2025 coverage now includes weeks: {combined_weeks}")
    logger.info(f"  ✅ Schema consistency maintained: {len(combined_df.columns)} columns")

    logger.info("\n📋 Next Steps:")
    logger.info("  1. Run model retraining with complete dataset")
    logger.info("  2. Validate advanced metrics for new weeks")
    logger.info("  3. Test agent system with updated data")
    logger.info("  4. Update educational notebooks if needed")

    return True

if __name__ == "__main__":
    success = main()
    if success:
        logger.info("\n🚀 Integration completed successfully!")
        sys.exit(0)
    else:
        logger.error("\n❌ Integration failed!")
        sys.exit(1)
