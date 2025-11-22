#!/usr/bin/env python3
"""
Complete 2025 Data Migration Script
Merges real 2025 data from starter pack with model pack training data
Author: Claude Code Assistant
Date: 2025-11-13
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataMigration2025:
    """Handle migration of complete 2025 data from starter pack to model pack"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.starter_pack_path = self.project_root.parent / 'starter_pack/data/games.csv'
        self.training_data_path = self.project_root / 'updated_training_data.csv'
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.backup_path = self.project_root / f'updated_training_data_backup_{timestamp}.csv'
        self.output_path = self.project_root / 'updated_training_data.csv'

    def create_backup(self):
        """Create backup of existing training data"""
        logger.info("Creating backup of existing training data...")
        if self.training_data_path.exists():
            df_backup = pd.read_csv(self.training_data_path)
            df_backup.to_csv(self.backup_path, index=False)
            logger.info(f"✅ Backup created: {self.backup_path}")
            return True
        else:
            logger.error("❌ Training data file not found")
            return False

    def load_starter_pack_2025(self):
        """Load 2025 games from starter pack"""
        logger.info("Loading 2025 data from starter pack...")

        if not self.starter_pack_path.exists():
            logger.error(f"❌ Starter pack not found: {self.starter_pack_path}")
            return None

        # Load starter pack data
        df_starter = pd.read_csv(self.starter_pack_path, low_memory=False)
        df_2025_starter = df_starter[df_starter['season'] == 2025].copy()

        logger.info(f"✅ Loaded {len(df_2025_starter):,} 2025 games from starter pack")
        logger.info(f"✅ Week range: {df_2025_starter['week'].min()} - {df_2025_starter['week'].max()}")

        return df_2025_starter

    def load_existing_training_data(self):
        """Load existing training data"""
        logger.info("Loading existing training data...")

        if not self.training_data_path.exists():
            logger.error(f"❌ Training data not found: {self.training_data_path}")
            return None

        df_training = pd.read_csv(self.training_data_path)
        logger.info(f"✅ Loaded {len(df_training):,} total games from training data")

        # Separate 2025 and historical data
        df_2025_existing = df_training[df_training['season'] == 2025].copy()
        df_historical = df_training[df_training['season'] < 2025].copy()

        logger.info(f"✅ Historical games (pre-2025): {len(df_historical):,}")
        logger.info(f"✅ Existing 2025 games: {len(df_2025_existing):,}")

        return df_historical, df_2025_existing

    def create_game_identifier(self, df):
        """Create unique game identifier for matching"""
        df['game_key'] = df['season'].astype(str) + '_' + \
                         df['week'].astype(str) + '_' + \
                         df['home_team'].str.replace(' ', '_') + '_' + \
                         df['away_team'].str.replace(' ', '_')
        return df

    def find_new_games(self, starter_2025, existing_2025):
        """Find games in starter pack that are not in existing training data"""
        logger.info("Identifying new games to add...")

        # Create game identifiers
        starter_2025 = self.create_game_identifier(starter_2025)
        existing_2025 = self.create_game_identifier(existing_2025)

        # Find new games
        existing_keys = set(existing_2025['game_key'])
        new_games_mask = ~starter_2025['game_key'].isin(existing_keys)
        new_games = starter_2025[new_games_mask].copy()

        logger.info(f"✅ Found {len(new_games):,} new games to add")

        # Show week breakdown of new games
        week_counts = new_games['week'].value_counts().sort_index()
        logger.info("New games by week:")
        for week, count in week_counts.items():
            logger.info(f"   Week {week}: +{count} games")

        return new_games

    def create_feature_template(self, existing_2025):
        """Create feature template based on existing 2025 data structure"""
        logger.info("Creating feature template...")

        # Get all columns from existing data
        template_columns = list(existing_2025.columns)

        # Create template DataFrame
        template_df = pd.DataFrame(columns=template_columns)

        logger.info(f"✅ Template created with {len(template_columns)} columns")
        logger.info(f"Sample columns: {template_columns[:10]}")

        return template_df, template_columns

    def map_basic_features(self, new_games, existing_2025):
        """Map basic features from starter pack to training data format"""
        logger.info("Mapping basic features...")

        # Basic column mapping
        column_mapping = {
            'id': 'id',
            'season': 'season',
            'week': 'week',
            'start_date': 'start_date',
            'home_team': 'home_team',
            'away_team': 'away_team',
            'neutral_site': 'neutral_site',
            'conference_game': 'conference_game'
        }

        # Create mapped DataFrame
        mapped_games = pd.DataFrame()

        # Map available columns
        for starter_col, training_col in column_mapping.items():
            if starter_col in new_games.columns:
                mapped_games[training_col] = new_games[starter_col]
            else:
                mapped_games[training_col] = None

        # Add missing columns with default values
        feature_template = self.create_feature_template(existing_2025)[1]
        for col in feature_template:
            if col not in mapped_games.columns:
                mapped_games[col] = np.nan  # Will be filled later

        logger.info(f"✅ Mapped basic features for {len(mapped_games)} games")
        return mapped_games

    def estimate_missing_features(self, mapped_games, existing_2025):
        """Estimate missing features using patterns from existing data"""
        logger.info("Estimating missing features...")

        # For now, use simple estimations based on existing patterns
        # This is a simplified approach - could be enhanced with more sophisticated methods

        # Estimate basic stats based on team averages from existing data
        team_stats = {}

        # Calculate team averages from existing 2025 data
        for team in set(existing_2025['home_team'].unique()) | set(existing_2025['away_team'].unique()):
            home_games = existing_2025[existing_2025['home_team'] == team]
            away_games = existing_2025[existing_2025['away_team'] == team]

            if len(home_games) > 0 or len(away_games) > 0:
                team_stats[team] = {
                    'home_elo': home_games['home_elo'].mean() if len(home_games) > 0 else 1500,
                    'away_elo': away_games['away_elo'].mean() if len(away_games) > 0 else 1500,
                    'home_talent': home_games['home_talent'].mean() if len(home_games) > 0 else 0,
                    'away_talent': away_games['away_talent'].mean() if len(away_games) > 0 else 0,
                }

        # Apply estimations to new games
        for idx, game in mapped_games.iterrows():
            home_team = game['home_team']
            away_team = game['away_team']

            # Use team averages or defaults
            if home_team in team_stats:
                mapped_games.loc[idx, 'home_elo'] = team_stats[home_team]['home_elo']
                mapped_games.loc[idx, 'home_talent'] = team_stats[home_team]['home_talent']

            if away_team in team_stats:
                mapped_games.loc[idx, 'away_elo'] = team_stats[away_team]['away_elo']
                mapped_games.loc[idx, 'away_talent'] = team_stats[away_team]['away_talent']

        # Fill remaining missing values with reasonable defaults
        default_values = {
            'season_type': 'regular',
            'home_conference': 'Unknown',
            'away_conference': 'Unknown',
            'home_elo': 1500,
            'away_elo': 1500,
            'home_talent': 0,
            'away_talent': 0,
        }

        for col, default_val in default_values.items():
            if col in mapped_games.columns:
                mapped_games[col] = mapped_games[col].fillna(default_val)

        logger.info("✅ Missing features estimated")
        return mapped_games

    def merge_datasets(self, df_historical, df_2025_existing, new_games_processed):
        """Merge historical, existing 2025, and new 2025 data"""
        logger.info("Merging datasets...")

        # Combine all datasets
        final_df = pd.concat([df_historical, df_2025_existing, new_games_processed], ignore_index=True)

        logger.info(f"✅ Final dataset size: {len(final_df):,} games")
        logger.info(f"✅ Historical (pre-2025): {len(df_historical):,}")
        logger.info(f"✅ Existing 2025: {len(df_2025_existing):,}")
        logger.info(f"✅ New 2025: {len(new_games_processed):,}")

        # Verify data integrity
        final_2025 = final_df[final_df['season'] == 2025]
        logger.info(f"✅ Total 2025 games in final dataset: {len(final_2025):,}")

        # Week distribution for 2025
        week_counts = final_2025['week'].value_counts().sort_index()
        logger.info("2025 Week distribution:")
        for week, count in week_counts.items():
            logger.info(f"   Week {week}: {count} games")

        return final_df

    def save_updated_data(self, final_df):
        """Save updated training data"""
        logger.info("Saving updated training data...")

        final_df.to_csv(self.output_path, index=False)
        logger.info(f"✅ Updated training data saved to: {self.output_path}")

        # Verify save
        verify_df = pd.read_csv(self.output_path)
        logger.info(f"✅ Verification: {len(verify_df):,} games in saved file")

        return True

    def validate_migration(self, final_df):
        """Validate migration results"""
        logger.info("Validating migration results...")

        # Key validation checks
        validation_results = {
            'total_games': len(final_df),
            'historical_games': len(final_df[final_df['season'] < 2025]),
            'total_2025_games': len(final_df[final_df['season'] == 2025]),
            'week_12_games': len(final_df[(final_df['season'] == 2025) & (final_df['week'] == 12)]),
            'columns': len(final_df.columns),
            'missing_values': final_df.isnull().sum().sum(),
        }

        # Check for Ohio State vs UCLA specifically
        osu_ucla = final_df[
            (final_df['season'] == 2025) & (final_df['week'] == 12) &
            ((final_df['home_team'].str.contains('Ohio State', case=False, na=False)) &
             (final_df['away_team'].str.contains('UCLA', case=False, na=False))) |
            ((final_df['away_team'].str.contains('Ohio State', case=False, na=False)) &
             (final_df['home_team'].str.contains('UCLA', case=False, na=False)))
        ]

        validation_results['osu_ucla_games'] = len(osu_ucla)

        logger.info("📊 Migration Validation Results:")
        for key, value in validation_results.items():
            logger.info(f"   {key}: {value:,}")

        # Success criteria
        success = (
            validation_results['total_2025_games'] >= 1500 and  # Near complete 2025 data
            validation_results['week_12_games'] >= 100 and      # Week 12 games present
            validation_results['osu_ucla_games'] >= 1          # Ohio State vs UCLA present
        )

        if success:
            logger.info("✅ Migration validation PASSED")
        else:
            logger.error("❌ Migration validation FAILED")

        return success, validation_results

    def run_migration(self):
        """Run complete migration process"""
        logger.info("🚀 Starting 2025 Data Migration...")

        try:
            # Step 1: Create backup
            if not self.create_backup():
                return False

            # Step 2: Load data
            starter_2025 = self.load_starter_pack_2025()
            if starter_2025 is None:
                return False

            df_historical, df_2025_existing = self.load_existing_training_data()
            if df_historical is None:
                return False

            # Step 3: Find new games
            new_games = self.find_new_games(starter_2025, df_2025_existing)

            if len(new_games) == 0:
                logger.info("✅ No new games to add - dataset already complete")
                return True

            # Step 4: Process new games
            mapped_games = self.map_basic_features(new_games, df_2025_existing)
            processed_games = self.estimate_missing_features(mapped_games, df_2025_existing)

            # Step 5: Merge datasets
            final_df = self.merge_datasets(df_historical, df_2025_existing, processed_games)

            # Step 6: Save updated data
            self.save_updated_data(final_df)

            # Step 7: Validate migration
            success, validation_results = self.validate_migration(final_df)

            if success:
                logger.info("🎉 2025 Data Migration COMPLETED SUCCESSFULLY!")
                return True
            else:
                logger.error("❌ Migration failed validation")
                return False

        except Exception as e:
            logger.error(f"❌ Migration failed with error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """Main execution function"""
    migration = DataMigration2025()
    success = migration.run_migration()

    if success:
        print("\\n✅ Migration completed successfully!")
        print("Your model pack now has complete 2025 data from the starter pack.")
    else:
        print("\\n❌ Migration failed. Check logs for details.")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())