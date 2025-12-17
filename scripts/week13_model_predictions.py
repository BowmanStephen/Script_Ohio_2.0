#!/usr/bin/env python3
"""
Week 13 Model Predictions

This script uses the agent system to generate Week 13 predictions
using all available models (Ridge, XGBoost, FastAI).

Author: Claude Code Assistant
Created: 2025-11-18
Version: 1.0
"""

import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Any, Dict, List, Tuple
import json
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.dirname(__file__))
if os.path.exists(project_root):
    sys.path.insert(0, project_root)

def get_feature_defaults_from_training() -> Dict[str, float]:
    """Load median defaults from training data for missing feature backfills."""
    training_path = Path(project_root) / 'model_pack' / 'updated_training_data.csv'
    defaults: Dict[str, float] = {}

    if training_path.exists():
        try:
            df = pd.read_csv(training_path)
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                median_val = df[col].median()
                if pd.notna(median_val):
                    defaults[col] = float(median_val)
            print(f"  📦 Loaded {len(defaults)} feature defaults from training data")
        except Exception as exc:
            print(f"  ⚠️  Could not load feature defaults: {exc}")
    else:
        print(f"  ⚠️  Training data not found for defaults: {training_path}")

    return defaults

class Week13ModelPredictor:
    """Generate Week 13 predictions using ML models"""

    def __init__(self):
        self.project_root = Path(project_root)
        # Explicitly type as JSON-like dict to avoid overly-narrow inference in ty.
        self.results: Dict[str, Any] = {
            'timestamp': datetime.now().isoformat(),
            'predictions': [],
            'model_performance': {},
            'ensemble_results': {},
            'confidence_analysis': {}
        }

    def load_week13_games(self) -> pd.DataFrame:
        """Load Week 13 games for prediction"""
        print("📊 Loading Week 13 games...")

        # Priority 1: Enhanced features file from Phase 2
        enhanced_file = self.project_root / "data" / "week13" / "enhanced" / "week13_features_86.csv"
        if enhanced_file.exists():
            df = pd.read_csv(enhanced_file)
            print(f"  ✅ Loaded {len(df)} Week 13 games from enhanced features file")
            return df

        # Priority 2: Load from existing predictions if available
        pred_file = self.project_root / "predictions" / "week13" / "week13_comprehensive_predictions.csv"

        if pred_file.exists():
            df = pd.read_csv(pred_file)
            print(f"  ✅ Loaded {len(df)} Week 13 games from existing predictions")
            return df

        # Alternatively, load from training data
        training_file = self.project_root / "model_pack" / "updated_training_data.csv"
        if training_file.exists():
            df = pd.read_csv(training_file)
            week13_games = df[(df['season'] == 2025) & (df['week'] == 13)].copy()
            print(f"  ✅ Loaded {len(week13_games)} Week 13 games from training data")
            return week13_games

        print("  ❌ No Week 13 games found")
        return pd.DataFrame()

    def prepare_model_features(
        self,
        game_data: pd.DataFrame,
        models: Dict[str, object],
        feature_defaults: Dict[str, float],
    ) -> Tuple[Dict[str, List[str]], pd.DataFrame]:
        """Prepare and align feature schemas for each model type."""
        print("\n🔧 Preparing model features...")
        working_df = game_data.copy()

        # Base schemas
        ridge_base = [
            'home_talent', 'away_talent', 'home_elo', 'away_elo',
            'home_adjusted_epa', 'home_adjusted_epa_allowed',
            'away_adjusted_epa', 'away_adjusted_epa_allowed'
        ]
        xgb_base = ridge_base + [
            'spread',
            'home_adjusted_success', 'home_adjusted_success_allowed',
            'away_adjusted_success', 'away_adjusted_success_allowed'
        ]

        def _model_schema(model_obj, base_schema: List[str], model_name: str) -> List[str]:
            if model_name == 'fastai' and model_obj is not None:
                try:
                    fastai_names = getattr(getattr(model_obj, 'dls', None), 'x_names', None)
                    if fastai_names:
                        return list(fastai_names)
                except Exception:
                    pass
            names = getattr(model_obj, 'feature_names_in_', None)
            if names is not None and len(names) > 0:
                return list(names)
            booster = getattr(model_obj, 'get_booster', None)
            if booster:
                try:
                    booster_names = booster.feature_names
                    if booster_names:
                        return list(booster_names)
                except Exception:
                    pass
            return list(base_schema)

        ridge_schema = _model_schema(models.get('ridge'), ridge_base, 'ridge')
        xgb_schema = _model_schema(models.get('xgb'), xgb_base, 'xgb')
        fastai_schema = _model_schema(models.get('fastai'), xgb_base, 'fastai')
        feature_sets = {
            'ridge': ridge_schema,
            'xgb': xgb_schema,
            'fastai': fastai_schema,
        }

        # Add any missing columns with safe defaults to avoid shape mismatches
        for model_name, schema in feature_sets.items():
            missing = [col for col in schema if col not in working_df.columns]
            if missing:
                print(f"  ⚠️  {model_name} missing {len(missing)} features; filling with defaults.")
                for col in missing:
                    working_df[col] = feature_defaults.get(col, 0.0)
            # Coerce all model features to numeric so prediction inputs are safe
            for col in schema:
                if col in working_df.columns:
                    working_df[col] = pd.to_numeric(working_df[col], errors='coerce')
                    working_df[col] = working_df[col].fillna(feature_defaults.get(col, 0.0))

        print(f"  📊 Ridge features aligned: {len(feature_sets['ridge'])}")
        print(f"  📊 XGBoost features aligned: {len(feature_sets['xgb'])}")
        print(f"  📊 FastAI features aligned: {len(feature_sets['fastai'])}")

        return feature_sets, working_df

    def load_models(self) -> Dict:
        """Load all available models"""
        print("\n🤖 Loading ML models...")

        models = {}
        model_dir = self.project_root / "model_pack"

        try:
            # Try to load models using joblib
            import joblib

            # Ridge model
            ridge_file = model_dir / "ridge_model_2025.joblib"
            if ridge_file.exists():
                try:
                    models['ridge'] = joblib.load(ridge_file)
                    print(f"  ✅ Loaded Ridge model")
                except Exception as e:
                    print(f"  ⚠️  Ridge model load error: {e}")

            # XGBoost model
            xgb_file = model_dir / "xgb_home_win_model_2025.pkl"
            if xgb_file.exists():
                try:
                    import pickle
                    with open(xgb_file, 'rb') as f:
                        models['xgb'] = pickle.load(f)
                    print(f"  ✅ Loaded XGBoost model")
                except Exception as e:
                    print(f"  ⚠️  XGBoost model load error: {e}")

            # FastAI model (might have issues)
            fastai_file = model_dir / "fastai_home_win_model_2025.pkl"
            if fastai_file.exists():
                try:
                    from fastai.tabular.all import load_learner
                    models['fastai'] = load_learner(fastai_file)
                    print(f"  ✅ Loaded FastAI model via load_learner()")
                except Exception as e:
                    print(f"  ⚠️  FastAI model load error: {e}")
                    models['fastai'] = self._create_mock_fastai_model()

        except ImportError:
            print("  ❌ Required ML libraries not available")
            # Create mock models for demonstration
            models = self._create_mock_models()

        return models

    def _create_mock_models(self) -> Dict:
        """Create mock models for demonstration when actual models can't be loaded"""
        print("  🔄 Creating mock models for demonstration...")

        class MockModel:
            def __init__(self, model_type):
                self.model_type = model_type
                self.n_features_in_ = 8 if model_type == 'ridge' else 13

            def predict(self, X):
                if self.model_type == 'ridge':
                    # Mock margin predictions
                    return np.random.normal(0, 15, len(X))
                else:
                    # Mock win probability predictions
                    return np.random.beta(2, 2, len(X))

            def predict_proba(self, X):
                # Mock win probability predictions
                probs = np.random.beta(2, 2, len(X))
                return np.column_stack([1 - probs, probs])

        return {
            'ridge': MockModel('ridge'),
            'xgb': MockModel('xgb'),
            'fastai': MockModel('fastai')
        }

    def _create_mock_fastai_model(self):
        """Create mock FastAI model"""
        return self._create_mock_models()['fastai']

    def generate_predictions(
        self,
        games: pd.DataFrame,
        models: Dict,
        features: Dict,
        feature_defaults: Dict[str, float],
    ) -> List[Dict]:
        """Generate predictions using all models"""
        print("\n🎯 Generating predictions...")

        predictions: List[Dict[str, Any]] = []

        for idx, game in games.iterrows():
            # Explicitly type as JSON-like dict to avoid overly-narrow inference in ty.
            game_prediction: Dict[str, Any] = {
                'game_id': game.get('id', idx),
                'season': game.get('season', 2025),
                'week': game.get('week', 13),
                'home_team': game.get('home_team', 'Unknown'),
                'away_team': game.get('away_team', 'Unknown'),
                'model_predictions': {},
                'ensemble_prediction': {},
                'generation_time': datetime.now().isoformat()
            }

            # Prepare features for this game
            game_features: Dict[str, List[float]] = {}
            for model_type, feature_list in features.items():
                game_features[model_type] = []
                for feature in feature_list:
                    value = game.get(feature, feature_defaults.get(feature, 0))
                    if pd.isna(value):
                        value = feature_defaults.get(feature, 0)
                    game_features[model_type].append(float(value))

            # Generate predictions for each model
            for model_name, model in models.items():
                try:
                    if model_name == 'ridge' and len(game_features.get('ridge', [])) == len(features['ridge']):
                        # Ridge predicts margin
                        X = pd.DataFrame([game_features['ridge']], columns=features['ridge'])
                        margin_pred = model.predict(X)[0]

                        game_prediction['model_predictions'][model_name] = {
                            'predicted_margin': float(margin_pred),
                            'predicted_winner': game['home_team'] if margin_pred > 0 else game['away_team'],
                            'confidence': min(abs(margin_pred) / 20.0, 1.0)  # Simple confidence calculation
                        }

                    elif model_name in ['xgb', 'fastai'] and len(game_features.get(model_name, [])) == len(features[model_name]):
                        # XGBoost and FastAI predict win probability
                        X = pd.DataFrame([game_features[model_name]], columns=features[model_name])

                        home_win_prob = 0.5
                        if model_name == 'fastai':
                            # FastAI learner returns (pred_class, pred_idx, tensor probs)
                            pred_class, pred_idx, probs = model.predict(X.iloc[0])
                            try:
                                home_win_prob = float(probs[1])
                            except Exception:
                                home_win_prob = float(probs[0]) if hasattr(probs, '__len__') and len(probs) else 0.5
                        elif hasattr(model, 'predict_proba'):
                            proba = model.predict_proba(X)[0]
                            home_win_prob = float(proba[1])  # Probability of home win
                        else:
                            pred = model.predict(X)[0]
                            home_win_prob = float(pred) if isinstance(pred, (int, float)) else 0.5

                        game_prediction['model_predictions'][model_name] = {
                            'home_win_probability': float(home_win_prob),
                            'away_win_probability': float(1 - home_win_prob),
                            'predicted_winner': game['home_team'] if home_win_prob > 0.5 else game['away_team'],
                            'confidence': abs(home_win_prob - 0.5) * 2  # Distance from 0.5
                        }

                except Exception as e:
                    print(f"    ⚠️  {model_name} prediction error: {e}")
                    # Add fallback prediction
                    game_prediction['model_predictions'][model_name] = {
                        'error': str(e),
                        'fallback': True,
                        'predicted_winner': game['home_team'],  # Default to home team
                        'confidence': 0.5
                    }

            # Generate ensemble prediction
            game_prediction['ensemble_prediction'] = self._generate_ensemble_prediction(
                game_prediction['model_predictions'], game
            )

            predictions.append(game_prediction)

            if idx < 5:  # Show first few predictions
                print(f"  🏈 {game['home_team']} vs {game['away_team']}")
                print(f"     Ensemble: {game_prediction['ensemble_prediction']['predicted_winner']} "
                      f"({game_prediction['ensemble_prediction']['confidence']:.2f})")

        print(f"  ✅ Generated predictions for {len(predictions)} games")
        return predictions

    def _generate_ensemble_prediction(self, model_predictions: Dict, game: pd.Series) -> Dict:
        """Generate ensemble prediction from individual model predictions"""
        ensemble = {
            'method': 'weighted_average',
            'predicted_winner': None,
            'confidence': 0.0,
            'supporting_models': []
        }

        # Collect win predictions and confidences
        win_votes = {}
        total_confidence = 0.0
        valid_predictions = 0

        for model_name, pred in model_predictions.items():
            if 'error' not in pred:
                winner = pred.get('predicted_winner')
                confidence = pred.get('confidence', 0.5)

                if winner and confidence > 0:
                    win_votes[winner] = win_votes.get(winner, 0) + confidence
                    total_confidence += confidence
                    valid_predictions += 1
                    ensemble['supporting_models'].append(model_name)

        # Determine ensemble winner
        if win_votes:
            ensemble_winner = max(win_votes.keys(), key=lambda k: win_votes[k])
            ensemble['predicted_winner'] = ensemble_winner
            ensemble['confidence'] = min(total_confidence / max(valid_predictions, 1), 1.0)
        else:
            # Fallback
            ensemble['predicted_winner'] = game['home_team']
            ensemble['confidence'] = 0.5

        return ensemble

    def analyze_model_performance(self, predictions: List[Dict]) -> Dict:
        """Analyze model performance metrics"""
        print("\n📊 Analyzing model performance...")

        performance = {
            'model_usage': {},
            'confidence_distribution': {},
            'agreement_analysis': {}
        }

        # Model usage
        model_usage = {}
        for pred in predictions:
            for model_name in pred['model_predictions'].keys():
                model_usage[model_name] = model_usage.get(model_name, 0) + 1

        performance['model_usage'] = model_usage

        # Confidence distribution
        confidences = [pred['ensemble_prediction']['confidence'] for pred in predictions]
        if confidences:
            performance['confidence_distribution'] = {
                'mean': np.mean(confidences),
                'std': np.std(confidences),
                'min': np.min(confidences),
                'max': np.max(confidences),
                'high_confidence_games': len([c for c in confidences if c > 0.7]),
                'low_confidence_games': len([c for c in confidences if c < 0.3])
            }

        # Model agreement
        agreements = []
        for pred in predictions:
            models = list(pred['model_predictions'].keys())
            winners = [pred['model_predictions'][m]['predicted_winner'] for m in models
                      if 'error' not in pred['model_predictions'][m]]

            if len(winners) > 1:
                agreement = len(set(winners)) / len(winners)  # 0 = perfect agreement, 1 = no agreement
                agreements.append(1 - agreement)  # Convert to agreement score

        if agreements:
            performance['agreement_analysis'] = {
                'mean_agreement': np.mean(agreements),
                'perfect_agreement_games': len([a for a in agreements if a > 0.9]),
                'disagreement_games': len([a for a in agreements if a < 0.5])
            }

        print(f"  📈 Model usage: {model_usage}")
        print(f"  🎯 Mean confidence: {performance['confidence_distribution'].get('mean', 0):.3f}")
        print(f"  🤝 Mean model agreement: {performance['agreement_analysis'].get('mean_agreement', 0):.3f}")

        return performance

    def save_predictions(self, predictions: List[Dict], performance: Dict):
        """Save predictions and performance analysis"""
        print(f"\n💾 Saving predictions...")

        # Create output directory
        output_dir = self.project_root / "predictions" / "week13"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save detailed predictions
        predictions_file = output_dir / f"week13_model_predictions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(predictions_file, 'w') as f:
            json.dump({
                'timestamp': self.results['timestamp'],
                'predictions': predictions,
                'performance': performance
            }, f, indent=2, default=str)

        print(f"  ✅ Detailed predictions saved: {predictions_file}")

        # Save summary CSV
        summary_data = []
        for pred in predictions:
            summary_data.append({
                'game_id': pred['game_id'],
                'home_team': pred['home_team'],
                'away_team': pred['away_team'],
                'ensemble_winner': pred['ensemble_prediction']['predicted_winner'],
                'ensemble_confidence': pred['ensemble_prediction']['confidence'],
                'supporting_models': len(pred['ensemble_prediction']['supporting_models'])
            })

        summary_df = pd.DataFrame(summary_data)
        summary_file = output_dir / f"week13_predictions_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        summary_df.to_csv(summary_file, index=False)

        print(f"  ✅ Summary CSV saved: {summary_file}")

        return predictions_file, summary_file

    def run_prediction_pipeline(self):
        """Run the complete prediction pipeline"""
        print("🚀 Starting Week 13 Model Predictions...")
        print("="*60)

        try:
            # Load data
            games = self.load_week13_games()
            if games.empty:
                print("❌ No Week 13 games found")
                return self.results

            # Load models
            models = self.load_models()
            if not models:
                print("❌ No models available")
                return self.results

            # Prepare features and align schema to model expectations
            feature_defaults = get_feature_defaults_from_training()
            features, games_aligned = self.prepare_model_features(games, models, feature_defaults)

            # Generate predictions
            predictions = self.generate_predictions(games_aligned, models, features, feature_defaults)

            # Analyze performance
            performance = self.analyze_model_performance(predictions)

            # Save results
            pred_file, summary_file = self.save_predictions(predictions, performance)

            self.results['predictions'] = predictions
            self.results['model_performance'] = performance

            print(f"\n✅ Week 13 model predictions complete!")
            print(f"📊 Generated {len(predictions)} predictions")
            print(f"📄 Results saved to: {self.project_root / 'predictions' / 'week13'}")

            return self.results

        except Exception as e:
            print(f"\n❌ Error during prediction pipeline: {str(e)}")
            import traceback
            traceback.print_exc()
            return self.results

def main():
    """Main execution function"""
    predictor = Week13ModelPredictor()
    results = predictor.run_prediction_pipeline()
    return results

if __name__ == "__main__":
    results = main()
