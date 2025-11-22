#!/usr/bin/env python3
"""
Integrate Weeks 1-12 Data and Retrain All Models
=================================================

This script orchestrates the complete data integration and model retraining pipeline:
1. Migrates weeks 1-11 from starter pack data to training format
2. Transforms week12 enhanced data to match training data schema
3. Merges all weeks 1-12 into updated_training_data.csv
4. Retrains Ridge, XGBoost, and FastAI models with the updated dataset

Author: Script Ohio 2.0 Integration Pipeline
Date: 2025-11-14
"""

import json
import logging
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd
import numpy as np

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import required modules
from model_pack.migrate_starter_pack_data import StarterPackDataMigrator
from core_tools.data_workflows import TrainingDataExtender
from model_pack.model_training_agent import ModelTrainingAgent

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(PROJECT_ROOT / 'logs' / 'weeks_1_12_integration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def transform_week12_data(
    features_path: Path,
    games_path: Path,
    training_data_path: Path,
    output_path: Path
) -> bool:
    """
    Transform week12 enhanced data to match training data format.
    
    Args:
        features_path: Path to week12_features_86.csv
        games_path: Path to week12_enhanced_games.csv
        training_data_path: Path to updated_training_data.csv (for schema reference)
        output_path: Path to save transformed week12 data
        
    Returns:
        True if successful, False otherwise
    """
    logger.info("=" * 80)
    logger.info("TRANSFORMING WEEK12 ENHANCED DATA")
    logger.info("=" * 80)
    
    try:
        # Load training data to get schema
        logger.info(f"Loading training data schema from: {training_data_path}")
        training_df = pd.read_csv(training_data_path, nrows=1)
        training_columns = list(training_df.columns)
        logger.info(f"Training data has {len(training_columns)} columns")
        
        # Load week12 features
        logger.info(f"Loading week12 features from: {features_path}")
        features_df = pd.read_csv(features_path)
        logger.info(f"Loaded {len(features_df)} games with {len(features_df.columns)} feature columns")
        
        # Load week12 games metadata
        logger.info(f"Loading week12 games metadata from: {games_path}")
        games_df = pd.read_csv(games_path)
        logger.info(f"Loaded {len(games_df)} games with metadata")
        
        # Merge features and games on game_id
        # The features file has game_id, games file has id
        logger.info("Merging features and games data...")
        
        # Rename id to game_id in games_df for merging
        games_df = games_df.rename(columns={'id': 'game_id'})
        
        # Check for duplicate columns before merge
        feature_cols = set(features_df.columns)
        game_cols = set(games_df.columns)
        overlap = feature_cols & game_cols - {'game_id'}
        if overlap:
            logger.info(f"Columns in both datasets (will use games_df values): {overlap}")
            # Drop overlapping columns from features_df (except game_id) since games_df has the authoritative metadata
            features_df_clean = features_df.drop(columns=[col for col in overlap if col in features_df.columns])
        else:
            features_df_clean = features_df
        
        # Merge on game_id - use suffixes to handle any remaining duplicates
        merged_df = features_df_clean.merge(
            games_df[['game_id', 'season', 'week', 'season_type', 'home_team', 'away_team', 
                     'home_points', 'away_points', 'game_date']],
            on='game_id',
            how='inner',
            suffixes=('_features', '_games')
        )
        
        # If suffixes were added, prefer the _games version for metadata columns
        for col in ['home_team', 'away_team']:
            if f'{col}_games' in merged_df.columns:
                merged_df[col] = merged_df[f'{col}_games']
                merged_df = merged_df.drop(columns=[f'{col}_games'])
            if f'{col}_features' in merged_df.columns:
                merged_df = merged_df.drop(columns=[f'{col}_features'])
        
        logger.info(f"Merged data: {len(merged_df)} games")
        logger.info(f"Merged columns: {list(merged_df.columns)[:10]}... (showing first 10)")
        
        # Extract features from JSON if needed (from enhanced_features column)
        # The features are already in the features_df, so we mainly need metadata
        
        # Create a base dataframe with required columns matching training data format
        logger.info("Building training data format...")
        
        # Start with metadata columns
        week12_training = pd.DataFrame()
        
        # Map game_id to id
        week12_training['id'] = merged_df['game_id']
        
        # Map game_date to start_date
        week12_training['start_date'] = pd.to_datetime(merged_df['game_date']).dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Add season and week
        week12_training['season'] = merged_df['season']
        week12_training['season_type'] = merged_df['season_type']
        week12_training['week'] = merged_df['week']
        
        # Add neutral_site (default to False for now)
        week12_training['neutral_site'] = False
        
        # Add teams
        week12_training['home_team'] = merged_df['home_team']
        week12_training['away_team'] = merged_df['away_team']
        
        # Add conferences (we'll need to infer or use defaults)
        # For now, set to empty and let the migration process handle it
        week12_training['home_conference'] = ''
        week12_training['away_conference'] = ''
        
        # Add Elo ratings (will need to be populated from historical data or defaults)
        week12_training['home_elo'] = np.nan
        week12_training['away_elo'] = np.nan
        
        # Add talent scores from features
        week12_training['home_talent'] = merged_df['home_talent']
        week12_training['away_talent'] = merged_df['away_talent']
        
        # Add points
        week12_training['home_points'] = merged_df['home_points'].fillna(0).astype(float)
        week12_training['away_points'] = merged_df['away_points'].fillna(0).astype(float)
        
        # Calculate margin
        week12_training['margin'] = week12_training['home_points'] - week12_training['away_points']
        
        # Add spread (default to NaN if not available)
        week12_training['spread'] = np.nan
        
        # Now add all the feature columns from features_df
        # Exclude columns we've already added
        feature_cols_to_add = [col for col in features_df.columns 
                              if col not in ['game_id', 'home_team', 'away_team', 
                                           'home_talent', 'away_talent']]
        
        # Map feature columns to training data format
        # The training data has specific column names for features
        # We need to map the week12 features to match
        
        # Get the feature columns from training data (excluding metadata)
        metadata_cols = ['id', 'start_date', 'season', 'season_type', 'week', 'neutral_site',
                        'home_team', 'home_conference', 'home_elo', 'home_talent',
                        'away_team', 'away_conference', 'away_talent', 'away_elo',
                        'home_points', 'away_points', 'margin', 'spread', 'game_key', 'conference_game']
        
        training_feature_cols = [col for col in training_columns if col not in metadata_cols]
        
        # Add feature columns from week12 features
        # Map the feature columns from week12 to training format
        for col in training_feature_cols:
            if col in merged_df.columns:
                week12_training[col] = merged_df[col]
            elif col in features_df.columns:
                week12_training[col] = features_df[col]
            else:
                # Fill missing features with NaN
                week12_training[col] = np.nan
                logger.warning(f"Feature column {col} not found in week12 data, filling with NaN")
        
        # Add game_key
        week12_training['game_key'] = (
            week12_training['season'].astype(str) + '_' +
            week12_training['week'].astype(str) + '_' +
            week12_training['home_team'] + '_' +
            week12_training['away_team']
        )
        
        # Add conference_game (default to False)
        week12_training['conference_game'] = False
        
        # Reorder columns to match training data
        week12_training = week12_training[training_columns]
        
        # Ensure data types match (handle type conversion errors gracefully)
        for col in week12_training.columns:
            if col in training_df.columns:
                try:
                    target_dtype = training_df[col].dtype
                    # Handle object/string types specially
                    if target_dtype == 'object':
                        week12_training[col] = week12_training[col].astype(str)
                    else:
                        # For numeric types, convert to numeric first, then to target type
                        week12_training[col] = pd.to_numeric(week12_training[col], errors='coerce')
                        week12_training[col] = week12_training[col].astype(target_dtype)
                except Exception as e:
                    logger.warning(f"Could not convert column {col} to {training_df[col].dtype}: {e}")
                    # Keep original type if conversion fails
        
        # Save transformed data
        logger.info(f"Saving transformed week12 data to: {output_path}")
        week12_training.to_csv(output_path, index=False)
        
        logger.info(f"✅ Week12 transformation complete: {len(week12_training)} games, {len(week12_training.columns)} columns")
        logger.info(f"   Week12 games: {week12_training['week'].unique()}")
        logger.info(f"   Season: {week12_training['season'].unique()}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error transforming week12 data: {str(e)}")
        traceback.print_exc()
        return False


def migrate_weeks_1_11(output_path: Optional[Path] = None) -> Optional[Path]:
    """
    Migrate weeks 1-11 from starter pack data.
    
    Args:
        output_path: Optional custom output path
        
    Returns:
        Path to migrated file, or None if failed
    """
    logger.info("=" * 80)
    logger.info("MIGRATING WEEKS 1-11 FROM STARTER PACK")
    logger.info("=" * 80)
    
    try:
        # Create migrator
        migrator = StarterPackDataMigrator()
        
        # Modify migrator to filter to weeks 1-11 only
        # We'll need to override the apply_week_filter method or filter after migration
        # For now, let's run migration and then filter
        
        logger.info("Running starter pack migration...")
        success = migrator.run_migration()
        
        if not success:
            logger.error("❌ Starter pack migration failed")
            return None
        
        # Load the migrated data and filter to weeks 1-11
        logger.info(f"Loading migrated data from: {migrator.output_file}")
        migrated_df = pd.read_csv(migrator.output_file, low_memory=False)
        
        logger.info(f"Total migrated games: {len(migrated_df)}")
        logger.info(f"Weeks in migrated data: {sorted(migrated_df['week'].unique())}")
        
        # Filter to weeks 1-11
        weeks_1_11 = migrated_df[migrated_df['week'] <= 11].copy()
        logger.info(f"Weeks 1-11 games: {len(weeks_1_11)}")
        
        # Save filtered data
        if output_path is None:
            output_path = PROJECT_ROOT / 'model_pack' / '2025_starter_pack_migrated_weeks_1_11.csv'
        
        weeks_1_11.to_csv(output_path, index=False)
        logger.info(f"✅ Weeks 1-11 migration complete: {len(weeks_1_11)} games saved to {output_path}")
        
        return output_path
        
    except Exception as e:
        logger.error(f"❌ Error migrating weeks 1-11: {str(e)}")
        traceback.print_exc()
        return None


def main():
    """Main execution function."""
    logger.info("=" * 80)
    logger.info("WEEKS 1-12 DATA INTEGRATION AND MODEL RETRAINING PIPELINE")
    logger.info("=" * 80)
    logger.info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    summary = {
        'start_time': datetime.now().isoformat(),
        'steps_completed': [],
        'errors': [],
        'final_stats': {}
    }
    
    try:
        # Define paths
        week12_features_path = PROJECT_ROOT / 'data' / 'week12' / 'enhanced' / 'week12_features_86.csv'
        week12_games_path = PROJECT_ROOT / 'data' / 'week12' / 'enhanced' / 'week12_enhanced_games.csv'
        training_data_path = PROJECT_ROOT / 'model_pack' / 'updated_training_data.csv'
        week12_output_path = PROJECT_ROOT / 'model_pack' / '2025_week12_migrated.csv'
        weeks_1_11_output_path = PROJECT_ROOT / 'model_pack' / '2025_starter_pack_migrated_weeks_1_11.csv'
        
        # Step 1: Migrate weeks 1-11
        logger.info("\n" + "=" * 80)
        logger.info("STEP 1: MIGRATE WEEKS 1-11")
        logger.info("=" * 80)
        weeks_1_11_path = migrate_weeks_1_11(weeks_1_11_output_path)
        if weeks_1_11_path is None:
            raise RuntimeError("Failed to migrate weeks 1-11")
        summary['steps_completed'].append('migrate_weeks_1_11')
        
        # Step 2: Transform week12 data
        logger.info("\n" + "=" * 80)
        logger.info("STEP 2: TRANSFORM WEEK12 DATA")
        logger.info("=" * 80)
        if not week12_features_path.exists():
            raise FileNotFoundError(f"Week12 features not found: {week12_features_path}")
        if not week12_games_path.exists():
            raise FileNotFoundError(f"Week12 games not found: {week12_games_path}")
        if not training_data_path.exists():
            raise FileNotFoundError(f"Training data not found: {training_data_path}")
        
        week12_success = transform_week12_data(
            week12_features_path,
            week12_games_path,
            training_data_path,
            week12_output_path
        )
        if not week12_success:
            raise RuntimeError("Failed to transform week12 data")
        summary['steps_completed'].append('transform_week12')
        
        # Step 3: Merge weeks 1-11 into training data
        logger.info("\n" + "=" * 80)
        logger.info("STEP 3: MERGE WEEKS 1-11 INTO TRAINING DATA")
        logger.info("=" * 80)
        extender = TrainingDataExtender()
        merge_result_1 = extender.extend(weeks_1_11_path)
        logger.info(f"✅ Merged weeks 1-11: {merge_result_1['rows_added']} games added")
        logger.info(f"   Total games now: {merge_result_1['rows_after']}")
        summary['steps_completed'].append('merge_weeks_1_11')
        summary['merge_weeks_1_11'] = merge_result_1
        
        # Step 4: Merge week12 into training data
        logger.info("\n" + "=" * 80)
        logger.info("STEP 4: MERGE WEEK12 INTO TRAINING DATA")
        logger.info("=" * 80)
        merge_result_2 = extender.extend(week12_output_path)
        logger.info(f"✅ Merged week12: {merge_result_2['rows_added']} games added")
        logger.info(f"   Total games now: {merge_result_2['rows_after']}")
        summary['steps_completed'].append('merge_week12')
        summary['merge_week12'] = merge_result_2
        
        # Step 5: Validate final dataset
        logger.info("\n" + "=" * 80)
        logger.info("STEP 5: VALIDATE FINAL DATASET")
        logger.info("=" * 80)
        final_df = pd.read_csv(training_data_path, low_memory=False)
        logger.info(f"Final dataset: {len(final_df)} total games")
        logger.info(f"2025 season games: {len(final_df[final_df['season'] == 2025])}")
        
        week_distribution = final_df[final_df['season'] == 2025]['week'].value_counts().sort_index()
        logger.info("Week distribution for 2025:")
        for week, count in week_distribution.items():
            logger.info(f"  Week {week}: {count} games")
        
        # Count games with scores
        games_with_scores = final_df[
            (final_df['home_points'].notna()) & 
            (final_df['away_points'].notna()) &
            ((final_df['home_points'] > 0) | (final_df['away_points'] > 0))
        ]
        logger.info(f"Games with actual scores: {len(games_with_scores)}")
        logger.info(f"Games without scores (future games): {len(final_df) - len(games_with_scores)}")
        
        summary['final_stats'] = {
            'total_games': len(final_df),
            '2025_games': len(final_df[final_df['season'] == 2025]),
            'games_with_scores': len(games_with_scores),
            'games_without_scores': len(final_df) - len(games_with_scores),
            'week_distribution': week_distribution.to_dict()
        }
        summary['steps_completed'].append('validation')
        
        # Step 6: Retrain all models
        logger.info("\n" + "=" * 80)
        logger.info("STEP 6: RETRAIN ALL MODELS")
        logger.info("=" * 80)
        
        # Change to model_pack directory for model training
        original_cwd = Path.cwd()
        model_pack_dir = PROJECT_ROOT / 'model_pack'
        
        # Filter out games without scores for training (future games)
        logger.info("Filtering games with actual scores for model training...")
        final_df_with_scores = final_df[
            (final_df['home_points'].notna()) & 
            (final_df['away_points'].notna()) &
            ((final_df['home_points'] > 0) | (final_df['away_points'] > 0))
        ].copy()
        logger.info(f"Games with scores: {len(final_df_with_scores)} (out of {len(final_df)} total)")
        
        # Save filtered version temporarily for training
        temp_training_path = model_pack_dir / 'updated_training_data_with_scores.csv'
        final_df_with_scores.to_csv(temp_training_path, index=False)
        logger.info(f"Saved filtered training data to: {temp_training_path}")
        os.chdir(model_pack_dir)
        
        try:
            trainer = ModelTrainingAgent(data_path='updated_training_data_with_scores.csv')
            
            # Check if 2025 has games with scores for temporal validation
            df_check = pd.read_csv('updated_training_data_with_scores.csv')
            df_2025_with_scores = df_check[(df_check['season'] == 2025) & 
                                          (df_check['home_points'].notna()) & 
                                          (df_check['away_points'].notna()) &
                                          ((df_check['home_points'] > 0) | (df_check['away_points'] > 0))]
            
            if len(df_2025_with_scores) == 0:
                logger.warning("⚠️  No 2025 games with scores found. Using 2024 as test set instead.")
                # Modify the trainer to use 2024 as test set
                trainer.load_and_prepare_data()
                # Override the test split to use 2024 instead of 2025
                trainer.test_df = trainer.df[trainer.df['season'] == 2024].copy()
                trainer.train_df = trainer.df[trainer.df['season'] < 2024].copy()
                logger.info(f"Training set: {len(trainer.train_df)} games (2016-2023)")
                logger.info(f"Test set: {len(trainer.test_df)} games (2024)")
                
                # Add home_win target
                trainer.train_df = trainer.train_df.copy()
                trainer.test_df = trainer.test_df.copy()
                trainer.train_df['home_win'] = (trainer.train_df['home_points'] > trainer.train_df['away_points']).astype(int)
                trainer.test_df['home_win'] = (trainer.test_df['home_points'] > trainer.test_df['away_points']).astype(int)
                
                # Train models manually
                trainer.performance_metrics['ridge'] = trainer.train_ridge_regression()
                trainer.performance_metrics['xgboost'] = trainer.train_xgboost_classifier()
                trainer.performance_metrics['fastai'] = trainer.train_fastai_neural_network()
                trainer.generate_performance_comparison()
                trainer.generate_feature_importance_analysis()
                trainer.generate_temporal_validation_report()
                trainer.create_mission_summary()
            else:
                # Use standard pipeline
                trainer.run_complete_training_pipeline()
            
            logger.info("✅ All models retrained successfully")
            summary['steps_completed'].append('retrain_models')
        finally:
            os.chdir(original_cwd)
        
        # Step 7: Verify model files
        logger.info("\n" + "=" * 80)
        logger.info("STEP 7: VERIFY MODEL FILES")
        logger.info("=" * 80)
        
        model_files = {
            'ridge': model_pack_dir / 'ridge_model_2025.joblib',
            'xgboost': model_pack_dir / 'xgb_home_win_model_2025.pkl',
            'fastai': model_pack_dir / 'fastai_home_win_model_2025.pkl'
        }
        
        all_models_exist = True
        for model_name, model_path in model_files.items():
            if model_path.exists():
                size_mb = model_path.stat().st_size / (1024 * 1024)
                logger.info(f"✅ {model_name} model exists: {model_path.name} ({size_mb:.2f} MB)")
            else:
                logger.warning(f"⚠️  {model_name} model not found: {model_path}")
                all_models_exist = False
        
        summary['model_files'] = {
            name: {'exists': path.exists(), 'path': str(path)} 
            for name, path in model_files.items()
        }
        summary['steps_completed'].append('verify_models')
        
        # Final summary
        logger.info("\n" + "=" * 80)
        logger.info("PIPELINE COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)
        logger.info(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Steps completed: {len(summary['steps_completed'])}")
        logger.info(f"Final dataset: {summary['final_stats']['total_games']} games")
        logger.info(f"2025 games: {summary['final_stats']['2025_games']} games")
        
        summary['end_time'] = datetime.now().isoformat()
        summary['status'] = 'success'
        
    except Exception as e:
        logger.error(f"\n❌ PIPELINE FAILED: {str(e)}")
        traceback.print_exc()
        summary['status'] = 'failed'
        summary['errors'].append(str(e))
        summary['end_time'] = datetime.now().isoformat()
        return 1
    
    finally:
        # Save summary report
        summary_path = PROJECT_ROOT / 'logs' / 'weeks_1_12_integration_summary.json'
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        logger.info(f"\nSummary report saved to: {summary_path}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

