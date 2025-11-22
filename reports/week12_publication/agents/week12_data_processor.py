#!/usr/bin/env python3
"""
Week 12 Data Processing Agent

Professional data processing for Week 12 college football predictions.
Handles data loading, model prediction generation, and quality validation
for professional publication standards.

Author: Script Ohio 2.0 Agent System
Date: 2025-11-14
"""

import pandas as pd
import numpy as np
import joblib
import pickle
from pathlib import Path
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Tuple, Any
import warnings
warnings.filterwarnings('ignore')

# Set up professional logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('reports/week12_publication/assets/data_processing.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('Week12DataProcessor')

class Week12DataProcessor:
    """
    Professional data processing agent for Week 12 predictions.
    Combines existing model infrastructure with publication-quality data handling.
    """

    def __init__(self):
        self.project_root = Path(".")
        self.models_dir = self.project_root / "model_pack"
        self.data_dir = self.project_root / "model_pack"
        self.output_dir = Path("reports/week12_publication/assets/data")

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Model file paths
        self.ridge_model_path = self.models_dir / "ridge_model_2025.joblib"
        self.xgb_model_path = self.models_dir / "xgb_home_win_model_2025.pkl"
        self.fastai_model_path = self.models_dir / "fastai_home_win_model_2025.pkl"
        self.training_data_path = self.data_dir / "updated_training_data.csv"

        # Week 12 data path (enhanced dataset)
        self.week12_data_path = self.data_dir / "2025_raw_games_enhanced.csv"

        self.models = {}
        self.feature_columns = []
        self.week12_games = None

    def load_models(self) -> bool:
        """Load all production models with error handling"""
        try:
            logger.info("🔧 Loading production models...")

            # Load Ridge regression model
            if self.ridge_model_path.exists():
                self.models['ridge'] = joblib.load(self.ridge_model_path)
                logger.info("✅ Ridge regression model loaded successfully")
            else:
                logger.warning("⚠️  Ridge model not found - will skip ridge predictions")

            # Load XGBoost model
            if self.xgb_model_path.exists():
                with open(self.xgb_model_path, 'rb') as f:
                    self.models['xgb'] = pickle.load(f)
                logger.info("✅ XGBoost model loaded successfully")
            else:
                logger.warning("⚠️  XGBoost model not found - will skip XGBoost predictions")

            # Load FastAI model
            if self.fastai_model_path.exists():
                try:
                    self.models['fastai'] = joblib.load(self.fastai_model_path)
                    logger.info("✅ FastAI model loaded successfully")
                except Exception as e:
                    logger.warning(f"⚠️  FastAI model loading failed: {e}")
            else:
                logger.warning("⚠️  FastAI model not found - will skip FastAI predictions")

            logger.info(f"📊 Successfully loaded {len(self.models)} production models")
            return True

        except Exception as e:
            logger.error(f"❌ Model loading failed: {e}")
            return False

    def load_training_data_schema(self) -> bool:
        """Load training data to understand feature schema"""
        try:
            logger.info("📋 Loading training data schema...")

            if self.training_data_path.exists():
                training_data = pd.read_csv(self.training_data_path)
                # Get feature columns (exclude target variables)
                exclude_cols = ['home_team', 'away_team', 'season', 'week',
                               'home_score', 'away_score', 'home_win', 'margin']
                self.feature_columns = [col for col in training_data.columns
                                       if col not in exclude_cols]

                logger.info(f"✅ Training schema loaded: {len(self.feature_columns)} features")
                return True
            else:
                logger.error(f"❌ Training data not found: {self.training_data_path}")
                return False

        except Exception as e:
            logger.error(f"❌ Training data loading failed: {e}")
            return False

    def load_week12_data(self) -> bool:
        """Load and filter Week 12 games data"""
        try:
            logger.info("🏈 Loading Week 12 game data...")

            if self.week12_data_path.exists():
                # Load all 2025 data
                all_data = pd.read_csv(self.week12_data_path)
                logger.info(f"📊 Loaded 2025 data: {len(all_data)} total games")

                # Filter for Week 12 games
                self.week12_games = all_data[all_data['week'] == 12].copy()

                if len(self.week12_games) > 0:
                    logger.info(f"✅ Found {len(self.week12_games)} Week 12 games")

                    # Log game matchups for verification
                    for _, game in self.week12_games.iterrows():
                        logger.info(f"   {game['home_team']} vs {game['away_team']}")

                    return True
                else:
                    logger.error("❌ No Week 12 games found in the dataset")
                    return False
            else:
                logger.error(f"❌ Enhanced data file not found: {self.week12_data_path}")
                return False

        except Exception as e:
            logger.error(f"❌ Week 12 data loading failed: {e}")
            return False

    def validate_data_quality(self) -> Dict[str, Any]:
        """Validate data quality for Week 12 games"""
        logger.info("🔍 Validating Week 12 data quality...")

        quality_report = {
            'total_games': len(self.week12_games),
            'complete_games': 0,
            'missing_features': [],
            'feature_completeness': {},
            'validation_timestamp': datetime.now().isoformat()
        }

        if self.week12_games is not None and len(self.week12_games) > 0:
            # Check for complete games
            complete_mask = self.week12_games[self.feature_columns].notnull().all(axis=1)
            quality_report['complete_games'] = complete_mask.sum()

            # Check feature completeness
            for feature in self.feature_columns:
                missing_count = self.week12_games[feature].isnull().sum()
                completeness = (len(self.week12_games) - missing_count) / len(self.week12_games)
                quality_report['feature_completeness'][feature] = completeness

                if completeness < 1.0:
                    quality_report['missing_features'].append(feature)

            # Calculate overall data quality score
            overall_completeness = np.mean(list(quality_report['feature_completeness'].values()))
            quality_report['overall_completeness_score'] = overall_completeness

            logger.info(f"📊 Data quality score: {overall_completeness:.1%}")
            logger.info(f"✅ Complete games: {quality_report['complete_games']}/{quality_report['total_games']}")

            if quality_report['missing_features']:
                logger.warning(f"⚠️  Features with missing data: {quality_report['missing_features']}")

        return quality_report

    def generate_predictions(self) -> pd.DataFrame:
        """Generate predictions using all available models"""
        logger.info("🎯 Generating Week 12 predictions...")

        if self.week12_games is None or len(self.week12_games) == 0:
            logger.error("❌ No Week 12 games available for prediction")
            return pd.DataFrame()

        # Prepare results dataframe
        results = []

        for idx, game in self.week12_games.iterrows():
            try:
                game_prediction = {
                    'game_id': idx,
                    'home_team': game['home_team'],
                    'away_team': game['away_team'],
                    'week': game['week'],
                    'season': game['season'],
                    'actual_margin': game.get('margin', np.nan),
                    'actual_home_win': game.get('home_win', np.nan)
                }

                # Extract features for prediction
                if self.feature_columns:
                    feature_values = []
                    for feature in self.feature_columns:
                        if feature in game and pd.notna(game[feature]):
                            feature_values.append(game[feature])
                        else:
                            # Handle missing features with 0
                            feature_values.append(0.0)

                    features_array = np.array(feature_values).reshape(1, -1)

                    # Ridge model predictions (margin)
                    if 'ridge' in self.models:
                        try:
                            ridge_pred = self.models['ridge'].predict(features_array)[0]
                            game_prediction['ridge_margin_prediction'] = ridge_pred

                            # Calculate win probability from margin (normal distribution assumption)
                            import scipy.stats as stats
                            win_prob = stats.norm.cdf(ridge_pred / 14)  # 14 point SD
                            game_prediction['ridge_win_probability'] = win_prob
                        except Exception as e:
                            logger.warning(f"⚠️  Ridge prediction failed: {e}")
                            game_prediction['ridge_margin_prediction'] = np.nan
                            game_prediction['ridge_win_probability'] = np.nan

                    # XGBoost predictions (win probability)
                    if 'xgb' in self.models:
                        try:
                            xgb_pred = self.models['xgb'].predict_proba(features_array)[0, 1]
                            game_prediction['xgb_win_probability'] = xgb_pred

                            # Convert to approximate margin
                            margin = (xgb_pred - 0.5) * 28  # Rough conversion
                            game_prediction['xgb_margin_prediction'] = margin
                        except Exception as e:
                            logger.warning(f"⚠️  XGBoost prediction failed: {e}")
                            game_prediction['xgb_win_probability'] = np.nan
                            game_prediction['xgb_margin_prediction'] = np.nan

                    # FastAI predictions (if available)
                    if 'fastai' in self.models:
                        try:
                            fastai_pred = self.models['fastai'].predict_proba(features_array)[0, 1]
                            game_prediction['fastai_win_probability'] = fastai_pred
                            margin = (fastai_pred - 0.5) * 28
                            game_prediction['fastai_margin_prediction'] = margin
                        except Exception as e:
                            logger.warning(f"⚠️  FastAI prediction failed: {e}")
                            game_prediction['fastai_win_probability'] = np.nan
                            game_prediction['fastai_margin_prediction'] = np.nan

                # Calculate ensemble predictions
                margin_preds = [game_prediction.get('ridge_margin_prediction', np.nan),
                              game_prediction.get('xgb_margin_prediction', np.nan),
                              game_prediction.get('fastai_margin_prediction', np.nan)]
                win_prob_preds = [game_prediction.get('ridge_win_probability', np.nan),
                                game_prediction.get('xgb_win_probability', np.nan),
                                game_prediction.get('fastai_win_probability', np.nan)]

                # Remove NaN values and calculate ensemble
                valid_margin_preds = [p for p in margin_preds if not np.isnan(p)]
                valid_win_prob_preds = [p for p in win_prob_preds if not np.isnan(p)]

                if valid_margin_preds:
                    game_prediction['ensemble_margin_prediction'] = np.mean(valid_margin_preds)
                    game_prediction['margin_prediction_std'] = np.std(valid_margin_preds)
                else:
                    game_prediction['ensemble_margin_prediction'] = np.nan
                    game_prediction['margin_prediction_std'] = np.nan

                if valid_win_prob_preds:
                    game_prediction['ensemble_win_probability'] = np.mean(valid_win_prob_preds)
                    game_prediction['win_probability_std'] = np.std(valid_win_prob_preds)
                else:
                    game_prediction['ensemble_win_probability'] = np.nan
                    game_prediction['win_probability_std'] = np.nan

                # Calculate confidence scores
                if not np.isnan(game_prediction.get('ensemble_win_probability', np.nan)):
                    confidence = abs(game_prediction['ensemble_win_probability'] - 0.5) * 2
                    game_prediction['confidence_score'] = confidence
                else:
                    game_prediction['confidence_score'] = np.nan

                results.append(game_prediction)

            except Exception as e:
                logger.error(f"❌ Prediction failed for game {idx}: {e}")
                continue

        predictions_df = pd.DataFrame(results)
        logger.info(f"✅ Generated predictions for {len(predictions_df)} games")

        return predictions_df

    def save_predictions(self, predictions_df: pd.DataFrame) -> bool:
        """Save predictions and quality reports"""
        try:
            logger.info("💾 Saving Week 12 predictions and reports...")

            # Save raw predictions
            predictions_path = self.output_dir / "week12_predictions_raw.csv"
            predictions_df.to_csv(predictions_path, index=False)
            logger.info(f"✅ Predictions saved: {predictions_path}")

            # Save summary statistics
            summary_stats = {
                'total_games': len(predictions_df),
                'games_with_predictions': len(predictions_df.dropna(subset=['ensemble_margin_prediction'])),
                'average_confidence': predictions_df['confidence_score'].mean(),
                'high_confidence_games': len(predictions_df[predictions_df['confidence_score'] > 0.7]),
                'generation_timestamp': datetime.now().isoformat(),
                'models_used': list(self.models.keys())
            }

            summary_path = self.output_dir / "prediction_summary.json"
            import json
            with open(summary_path, 'w') as f:
                json.dump(summary_stats, f, indent=2)
            logger.info(f"✅ Summary saved: {summary_path}")

            return True

        except Exception as e:
            logger.error(f"❌ Saving predictions failed: {e}")
            return False

    def run_complete_pipeline(self) -> Tuple[bool, pd.DataFrame]:
        """Execute the complete Week 12 data processing pipeline"""
        logger.info("🚀 Starting Week 12 Data Processing Pipeline...")
        start_time = datetime.now()

        # Step 1: Load models
        if not self.load_models():
            return False, pd.DataFrame()

        # Step 2: Load training schema
        if not self.load_training_data_schema():
            return False, pd.DataFrame()

        # Step 3: Load Week 12 data
        if not self.load_week12_data():
            return False, pd.DataFrame()

        # Step 4: Validate data quality
        quality_report = self.validate_data_quality()

        # Save quality report
        quality_path = self.output_dir / "data_quality_report.json"
        import json
        # Convert numpy int64 to regular int for JSON serialization
        serializable_report = {}
        for key, value in quality_report.items():
            if isinstance(value, (np.integer, np.floating)):
                serializable_report[key] = float(value)
            elif isinstance(value, dict):
                serializable_report[key] = {k: float(v) if isinstance(v, (np.integer, np.floating)) else v
                                          for k, v in value.items()}
            else:
                serializable_report[key] = value

        with open(quality_path, 'w') as f:
            json.dump(serializable_report, f, indent=2)

        # Step 5: Generate predictions
        predictions_df = self.generate_predictions()

        if len(predictions_df) == 0:
            logger.error("❌ No predictions generated")
            return False, pd.DataFrame()

        # Step 6: Save results
        if not self.save_predictions(predictions_df):
            return False, pd.DataFrame()

        # Pipeline completion
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"✅ Week 12 Data Processing Pipeline completed in {execution_time:.1f} seconds")

        return True, predictions_df

# Main execution
if __name__ == "__main__":
    processor = Week12DataProcessor()
    success, predictions = processor.run_complete_pipeline()

    if success:
        print("\n🎉 Week 12 Data Processing Completed Successfully!")
        print(f"📊 Processed {len(predictions)} games")
        print("📁 Results saved to: reports/week12_publication/assets/data/")
        exit(0)
    else:
        print("\n❌ Week 12 Data Processing Failed!")
        exit(1)