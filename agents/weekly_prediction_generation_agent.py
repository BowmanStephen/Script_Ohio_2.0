"""
Weekly Prediction Generation Agent
Generates weekly predictions using validated ML models and enhanced data
"""

import os
import logging
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import json
import joblib
import pickle
import warnings
warnings.filterwarnings('ignore')

# Import the base agent framework
from agents.core.agent_framework import BaseAgent, AgentCapability, PermissionLevel

# Import path utilities
from model_pack.utils.path_utils import (
    get_weekly_enhanced_file,
    get_weekly_enhanced_dir,
    get_model_file_path
)

# Import TOON format encoder for token-efficient output
try:
    from src.toon_format import encode as encode_toon
    TOON_AVAILABLE = True
except (ImportError, RuntimeError):
    TOON_AVAILABLE = False

logger = logging.getLogger(__name__)

class WeeklyPredictionGenerationAgent(BaseAgent):
    """
    Agent responsible for generating weekly predictions using validated ML models
    and enhanced matchup data
    """

    def __init__(self, week: int, season: int = 2025, agent_id: Optional[str] = None,
                 name: Optional[str] = None):
        self.week = week
        self.season = season
        
        if agent_id is None:
            agent_id = f"week{week}_prediction_generation_agent"
        if name is None:
            name = f"Week {week} Prediction Generation Agent"
        
        permission_level = PermissionLevel.READ_EXECUTE_WRITE
        super().__init__(agent_id, name, permission_level)

        # Initialize agent-specific attributes
        self.prediction_weights = self._load_prediction_weights()
        self.confidence_thresholds = self._load_confidence_thresholds()
        self._canonical_features: List[str] = []
        self._feature_defaults: Dict[str, float] = {}

    # ------------------------------------------------------------------
    # Lightweight logging helpers
    # ------------------------------------------------------------------
    def log_start(self, message: str):
        logger.info(f"[START] {message}")

    def log_success(self, message: str, result: Dict[str, Any]):
        logger.info(f"[SUCCESS] {message}")

    def log_error(self, message: str, error: Exception):
        logger.error(f"[ERROR] {message}: {error}")

    def log_info(self, message: str):
        logger.info(f"[INFO] {message}")

    def log_warning(self, message: str):
        logger.warning(f"[WARN] {message}")

    def get_execution_time(self) -> float:
        return 0.0

    # ------------------------------------------------------------------
    # Feature schema alignment helpers
    # ------------------------------------------------------------------
    def _get_canonical_features(self) -> List[str]:
        """Determine canonical feature order expected by ridge/XGB models."""
        if self._canonical_features:
            return self._canonical_features

        feature_candidates: List[str] = []

        ridge_path = Path('model_pack') / 'ridge_model_2025.joblib'
        xgb_path = Path('model_pack') / 'xgb_home_win_model_2025.pkl'

        try:
            if ridge_path.exists():
                ridge_model = joblib.load(ridge_path)
                feature_candidates = list(getattr(ridge_model, 'feature_names_in_', []))
        except Exception as exc:
            self.log_warning(f"Unable to load ridge feature schema: {exc}")

        if not feature_candidates:
            try:
                if xgb_path.exists():
                    with open(xgb_path, 'rb') as f:
                        xgb_model = pickle.load(f)
                    booster = getattr(xgb_model, 'get_booster', None)
                    if booster:
                        feature_candidates = list(booster.feature_names)
            except Exception as exc:
                self.log_warning(f"Unable to load XGB feature schema: {exc}")

        if not feature_candidates:
            feature_candidates = self._infer_features_from_training_data()

        self._canonical_features = feature_candidates
        return self._canonical_features

    def _infer_features_from_training_data(self) -> List[str]:
        """Fallback: derive feature list from training CSV headers."""
        training_path = Path('model_pack') / 'updated_training_data.csv'
        if not training_path.exists():
            return []

        header = pd.read_csv(training_path, nrows=0)
        drop_columns = {
            'id', 'start_date', 'season', 'season_type', 'week', 'neutral_site',
            'home_team', 'home_conference', 'away_team', 'away_conference',
            'home_points', 'away_points', 'margin', 'game_key', 'conference_game'
        }
        return [col for col in header.columns if col not in drop_columns]

    def _get_feature_defaults(self, features: List[str]) -> Dict[str, float]:
        """Compute per-feature defaults from training data medians."""
        if self._feature_defaults:
            return self._feature_defaults

        training_path = Path('model_pack') / 'updated_training_data.csv'
        if training_path.exists() and features:
            try:
                usecols = [col for col in features if col in pd.read_csv(training_path, nrows=0).columns]
                if usecols:
                    training_df = pd.read_csv(training_path, usecols=usecols)
                    medians = training_df.median(numeric_only=True).to_dict()
                    self._feature_defaults.update({k: float(v) for k, v in medians.items() if pd.notna(v)})
            except Exception as exc:
                self.log_warning(f"Unable to compute feature defaults: {exc}")

        return self._feature_defaults

    def _align_model_features(self, features_df: pd.DataFrame) -> pd.DataFrame:
        """Align enhanced features to the canonical model schema."""
        canonical = self._get_canonical_features()
        if not canonical or features_df is None or features_df.empty:
            return pd.DataFrame()

        # First, ensure we exclude object columns
        metadata_columns = ['home_team', 'away_team', 'home_conference', 'away_conference', 
                           'start_date', 'season_type', 'id', 'game_key', 'game_date']
        features_df = features_df.drop(columns=metadata_columns, errors='ignore')

        aligned = pd.DataFrame(index=features_df.index)
        for feature in canonical:
            if feature in features_df.columns:
                aligned[feature] = pd.to_numeric(features_df[feature], errors='coerce')
            else:
                aligned[feature] = np.nan

        defaults = self._get_feature_defaults(canonical)
        fill_values = {feature: defaults.get(feature, 0.0) for feature in canonical}
        aligned = aligned.fillna(fill_values)

        missing_cols = [feature for feature in canonical if feature not in features_df.columns]
        if missing_cols:
            self.log_warning(f"Aligned features using defaults for missing columns: {missing_cols[:5]}{'...' if len(missing_cols) > 5 else ''}")

        # Ensure no object columns remain
        object_columns = aligned.select_dtypes(include=['object']).columns
        if len(object_columns) > 0:
            logger.warning(f"Removing object columns from aligned features: {list(object_columns)}")
            aligned = aligned.drop(columns=object_columns)

        return aligned

    def _define_capabilities(self) -> List[AgentCapability]:
        """Define agent capabilities and permissions"""
        return [
            AgentCapability(
                name="generate_predictions",
                description="Generate predictions using validated ML models",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=["model_predictor", "data_processor", "confidence_calculator", "ensemble_generator"],
                data_access=["model_pack/", "starter_pack/data/"],
                execution_time_estimate=15.0,
            ),
            AgentCapability(
                name="calculate_confidence",
                description="Calculate confidence metrics for predictions",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=["confidence_calculator"],
                data_access=["model_pack/predictions/"],
                execution_time_estimate=2.0,
            ),
            AgentCapability(
                name="create_ensemble",
                description="Create ensemble predictions from model outputs",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=["ensemble_generator"],
                data_access=["model_pack/", "starter_pack/data/"],
                execution_time_estimate=4.0,
            ),
        ]

    def _execute_action(self, action: str, parameters: Dict[str, Any],
                      user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent action with proper routing"""
        if action == "generate_predictions":
            return self.execute_task(parameters or {})
        elif action == "calculate_confidence":
            # Calculate confidence is part of generate_predictions
            return {"status": "error", "message": "Use generate_predictions action instead"}
        elif action == "create_ensemble":
            # Create ensemble is part of generate_predictions
            return {"status": "error", "message": "Use generate_predictions action instead"}
        else:
            raise ValueError(f"Unknown action: {action}")

    def execute_task(self, _task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main execution method for weekly prediction generation

        Args:
            task_data: Contains configuration for prediction task

        Returns:
            Comprehensive weekly predictions with confidence scores
        """
        try:
            self.log_start(f"Week {self.week} Prediction Generation")

            # Step 1: Load validated models
            validated_models = self._load_validated_models()

            # Step 2: Load enhanced weekly data
            weekly_data = self._load_enhanced_data()

            # Step 2a: Align features to model schema and validate presence
            aligned_features = self._align_model_features(weekly_data['features'])
            if aligned_features.empty:
                raise ValueError(
                    "Aligned feature frame is empty. Check that weekly features are present and "
                    "aligned with model schemas."
                )
            missing_features = []
            canonical = self._get_canonical_features()
            if canonical:
                missing_features = [f for f in canonical if f not in aligned_features.columns]
            if missing_features:
                self.log_warning(f"Missing {len(missing_features)} expected features; filled with defaults/NaN.")

            weekly_data['features_aligned'] = aligned_features
            weekly_data['feature_alignment'] = {
                'canonical_count': len(canonical),
                'missing_count': len(missing_features),
                'missing_examples': missing_features[:5],
                'feature_count': aligned_features.shape[1],
            }

            # Step 3: Validate model-data compatibility
            _compatibility_check = self._validate_model_data_compatibility(validated_models, weekly_data)

            # Step 4: Generate individual model predictions
            individual_predictions = self._generate_individual_predictions(validated_models, weekly_data)
            if not individual_predictions or individual_predictions.get('error'):
                self.log_warning("No validated model predictions available; falling back to heuristic predictions.")
                individual_predictions = self._generate_fallback_predictions(weekly_data)
                if not individual_predictions:
                    raise RuntimeError(f"Unable to generate fallback predictions for Week {self.week}.")

            # Step 5: Create ensemble predictions
            ensemble_predictions = self._create_ensemble_predictions(individual_predictions, weekly_data)
            if 'combined_ensemble' not in ensemble_predictions or ensemble_predictions.get('combined_ensemble') is None:
                raise RuntimeError(f"Unable to create ensemble predictions for Week {self.week}.")

            # Step 6: Calculate confidence scores
            confidence_scores = self._calculate_prediction_confidence(individual_predictions, ensemble_predictions)

            # Step 7: Generate prediction explanations
            prediction_explanations = self._generate_prediction_explanations(ensemble_predictions, weekly_data)

            # Step 8: Create comprehensive prediction dataset
            comprehensive_predictions = self._create_comprehensive_predictions(
                ensemble_predictions, confidence_scores, prediction_explanations, weekly_data
            )

            # Step 9: Analyze prediction patterns and insights
            prediction_insights = self._analyze_prediction_patterns(comprehensive_predictions)

            # Step 10: Generate actionable recommendations
            actionable_recommendations = self._generate_actionable_recommendations(comprehensive_predictions)

            # Step 11: Create prediction summary report
            summary_report = self._create_prediction_summary_report(comprehensive_predictions)

            # Step 12: Save all prediction results
            self._save_prediction_results(
                comprehensive_predictions,
                prediction_insights,
                actionable_recommendations,
                summary_report=summary_report,
            )

            result = {
                'status': 'success',
                'models_used': len(validated_models),
                'games_predicted': len(comprehensive_predictions),
                'ensemble_created': True,
                'average_confidence': confidence_scores['average_confidence'],
                'high_confidence_predictions': len([p for p in confidence_scores['game_confidences'] if p['confidence'] > 0.75]),
                'recommendations_generated': len(actionable_recommendations),
                'predictions_complete': True,
                'execution_time': self.get_execution_time()
            }

            self.log_success(f"Week {self.week} Prediction Generation", result)
            return result

        except Exception as e:
            error_result = {
                'status': 'error',
                'error': str(e),
                'execution_time': self.get_execution_time()
            }
            self.log_error(f"Week {self.week} Prediction Generation", e)
            return error_result

    def _load_validated_models(self) -> Dict[str, Any]:
        """Load validated ML models for predictions"""

        self.log_info("Loading validated ML models for predictions...")

        models = {}
        model_configs = [
            {
                'name': 'ridge_regression',
                'file_name': 'ridge_model_2025.joblib',
                'model_type': 'sklearn',
                'prediction_type': 'margin',
                'weight': 0.35
            },
            {
                'name': 'xgboost_win_probability',
                'file_name': 'xgb_home_win_model_2025.pkl',
                'model_type': 'xgboost',
                'prediction_type': 'probability',
                'weight': 0.50
            },
            {
                'name': 'fastai_neural_network',
                'file_name': 'fastai_home_win_model_2025.pkl',
                'model_type': 'fastai',
                'prediction_type': 'probability',
                'weight': 0.15
            }
        ]

        for config in model_configs:
            try:
                # Use path utility to get model file path
                file_path = get_model_file_path(config['file_name'])
                
                if config['model_type'] == 'sklearn':
                    model = joblib.load(file_path)
                elif config['model_type'] == 'fastai':
                    # FastAI models saved with learn.export() must use load_learner()
                    model = self._load_fastai_model(str(file_path))
                else:
                    with open(file_path, 'rb') as f:
                        model = pickle.load(f)

                models[config['name']] = {
                    'model': model,
                    'config': config,
                    'file_path': str(file_path),
                    'load_status': 'success',
                    'validation_passed': True  # Assuming validation already passed
                }

                self.log_info(f"✅ Loaded validated model: {config['name']} from {file_path}")

            except FileNotFoundError:
                models[config['name']] = {
                    'model': None,
                    'config': config,
                    'load_status': 'file_not_found',
                    'validation_passed': False
                }

                self.log_warning(f"❌ Model file not found: {config['file_name']}")

            except Exception as e:
                models[config['name']] = {
                    'model': None,
                    'config': config,
                    'load_status': f'error: {str(e)}',
                    'validation_passed': False
                }

                self.log_error(f"Failed to load {config['name']}", e)

        available_count = sum(1 for m in models.values() if m['load_status'] == 'success')
        self.log_info(f"Successfully loaded {available_count}/{len(models)} validated models for predictions")

        return models

    def _load_fastai_model(self, file_path: str) -> Any:
        """Load FastAI learner using load_learner() - required for learn.export() format."""
        try:
            from fastai.tabular.all import load_learner
            return load_learner(file_path)
        except ImportError:
            self.log_warning("FastAI not available - cannot load FastAI model")
            raise
        except Exception as e:
            self.log_error(f"Failed to load FastAI model with load_learner()", e)
            raise

    def _load_enhanced_data(self) -> Dict[str, Any]:
        """Load enhanced weekly data for predictions"""

        self.log_info(f"Loading enhanced Week {self.week} data for predictions...")

        try:
            # Load enhanced features using path utility
            features_path = get_weekly_enhanced_file(self.week, 'features', self.season)
            features_df = pd.read_csv(features_path)
            self.log_info(f"Loaded {len(features_df)} feature records with {len(features_df.columns)} columns from {features_path}")

            # Load enhanced games using path utility (optional)
            try:
                games_path = get_weekly_enhanced_file(self.week, 'games', self.season)
                games_df = pd.read_csv(games_path)
                self.log_info(f"Loaded {len(games_df)} enhanced games from {games_path}")
            except FileNotFoundError:
                games_df = None
                self.log_warning("No enhanced games data found - using features only")

            # Load matchup analysis (path not in utilities yet, keep existing logic)
            analysis_candidates = [
                Path("analysis") / f"week{self.week}" / f"week{self.week}_comprehensive_analysis.json",
                Path("analysis") / f"week{self.week:02d}" / f"week{self.week}_comprehensive_analysis.json",
            ]
            analysis_path = next((p for p in analysis_candidates if p.exists()), None)
            if analysis_path:
                with analysis_path.open("r", encoding="utf-8") as f:
                    analysis_data = json.load(f)
                self.log_info(f"Loaded matchup analysis data from {analysis_path}")
            else:
                analysis_data = None
                self.log_warning("No matchup analysis data found")

            return {
                'features': features_df,
                'games': games_df,
                'analysis': analysis_data,
                'load_time': datetime.now().isoformat(),
                'data_source': f'enhanced_week{self.week}'
            }

        except Exception as e:
            self.log_error(f"Loading enhanced Week {self.week} data", e)
            raise

    def _validate_model_data_compatibility(self, validated_models: Dict[str, Any], weekly_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that loaded models are compatible with weekly data"""

        self.log_info("Validating model-data compatibility for predictions...")

        compatibility_results = {}

        feature_key = 'features_aligned' if 'features_aligned' in weekly_data else 'features'
        if feature_key not in weekly_data or weekly_data[feature_key] is None:
            return {'error': 'No features data available for compatibility testing'}

        features_df = weekly_data[feature_key]

        for model_name, model_info in validated_models.items():
            if model_info['model'] is None:
                compatibility_results[model_name] = {
                    'compatible': False,
                    'reason': 'Model not loaded'
                }
                continue

            try:
                # Test prediction compatibility with actual data
                feature_columns = [col for col in features_df.columns
                                 if col not in ['game_id', 'home_team', 'away_team', 'game_date']]
                sample_input = features_df[feature_columns].iloc[:1]

                # Test prediction
                if model_info['config']['prediction_type'] == 'margin':
                    prediction = model_info['model'].predict(sample_input)
                else:  # probability
                    prediction = model_info['model'].predict_proba(sample_input)

                compatibility_results[model_name] = {
                    'compatible': True,
                    'feature_count_used': len(feature_columns),
                    'prediction_successful': True,
                    'ready_for_predictions': True
                }

                self.log_info(f"✅ {model_name} compatibility verified for predictions")

            except Exception as e:
                compatibility_results[model_name] = {
                    'compatible': False,
                    'reason': str(e),
                    'prediction_successful': False,
                    'ready_for_predictions': False
                }

                self.log_warning(f"❌ {model_name} compatibility failed: {e}")

        ready_count = sum(1 for result in compatibility_results.values() if result.get('ready_for_predictions'))
        self.log_info(f"Compatibility check: {ready_count}/{len(compatibility_results)} models ready for predictions")

        return compatibility_results

    def _generate_individual_predictions(self, validated_models: Dict[str, Any], weekly_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate predictions using individual models"""

        self.log_info("Generating individual model predictions...")

        individual_predictions = {}

        feature_key = 'features_aligned' if 'features_aligned' in weekly_data else 'features'
        if feature_key not in weekly_data:
            return {}

        features_df = weekly_data[feature_key]
        feature_columns = [col for col in features_df.columns
                         if col not in ['game_id', 'home_team', 'away_team', 'game_date']]
        X = features_df[feature_columns]

        for model_name, model_info in validated_models.items():
            if model_info['model'] is None:
                continue

            try:
                model = model_info['model']
                prediction_type = model_info['config']['prediction_type']
                model_type = model_info['config'].get('model_type')

                # Generate predictions
                if prediction_type == 'margin':
                    predictions = model.predict(X)
                    pred_type = 'margin'
                elif model_type == 'fastai':
                    # FastAI models use predict() which returns tuple: (preds, targs, probs)
                    probabilities = []
                    for _, row in X.iterrows():
                        fastai_result = model.predict(row)
                        if isinstance(fastai_result, tuple):
                            if len(fastai_result) >= 3:
                                probs = fastai_result[2]
                                prob = float(probs[1]) if len(probs) > 1 else float(probs[0])
                            else:
                                prob = float(fastai_result[0])
                        else:
                            prob = float(fastai_result)
                        probabilities.append(prob)
                    predictions = np.array(probabilities, dtype=float)
                    predictions = np.clip(predictions, 0.0, 1.0)  # Ensure valid range
                    pred_type = 'probability'
                else:  # probability (XGBoost, etc.)
                    predictions = model.predict_proba(X)[:, 1]  # Home win probabilities
                    pred_type = 'probability'

                individual_predictions[model_name] = {
                    'predictions': predictions,
                    'prediction_type': pred_type,
                    'model_name': model_name,
                    'model_weight': model_info['config']['weight'],
                    'prediction_count': len(predictions),
                    'generation_time': datetime.now().isoformat()
                }

                self.log_info(f"✅ Generated {len(predictions)} {pred_type} predictions using {model_name}")

            except Exception as e:
                self.log_error(f"Failed to generate predictions with {model_name}", e)
                continue

        self.log_info(f"Generated predictions using {len(individual_predictions)} models")
        return individual_predictions

    def _generate_fallback_predictions(self, weekly_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate simple heuristic predictions when models are unavailable."""
        features_df = weekly_data.get('features')
        if features_df is None or features_df.empty:
            return {}

        self.log_info("Generating heuristic fallback predictions (talent/EPA driven).")
        margin_predictions = []
        probability_predictions = []

        for _, row in features_df.iterrows():
            home_talent = row.get('home_talent', 0)
            away_talent = row.get('away_talent', 0)
            talent_diff = (home_talent - away_talent) / 50.0

            home_epa = row.get('home_adjusted_epa', 0.0)
            away_epa = row.get('away_adjusted_epa', 0.0)
            epa_diff = (home_epa - away_epa) * 14.0

            home_success = row.get('home_adjusted_success', 0.0)
            away_success = row.get('away_adjusted_success', 0.0)
            success_diff = (home_success - away_success) * 20.0

            motivation_diff = (row.get('home_motivation_factor', 1.0) - row.get('away_motivation_factor', 1.0)) * 3.0
            rivalry_adj = (row.get('rivalry_game_adjustment', 1.0) - 1.0) * 3.0
            champ_adj = (row.get('championship_implication_adjustment', 1.0) - 1.0) * 10.0

            margin = talent_diff + epa_diff + success_diff + motivation_diff + rivalry_adj + champ_adj
            margin_predictions.append(margin)

            probability = 1 / (1 + np.exp(-margin / 6.0))
            probability_predictions.append(probability)

        heuristic_predictions = {
            'heuristic_margin': {
                'predictions': np.array(margin_predictions),
                'prediction_type': 'margin',
                'model_name': 'heuristic_margin',
                'model_weight': 0.5,
                'prediction_count': len(margin_predictions),
                'generation_time': datetime.now().isoformat()
            },
            'heuristic_probability': {
                'predictions': np.array(probability_predictions),
                'prediction_type': 'probability',
                'model_name': 'heuristic_probability',
                'model_weight': 0.5,
                'prediction_count': len(probability_predictions),
                'generation_time': datetime.now().isoformat()
            }
        }

        self.log_info(f"Generated heuristic predictions for {len(margin_predictions)} games.")
        return heuristic_predictions

    def _create_ensemble_predictions(self, individual_predictions: Dict[str, Any], weekly_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create ensemble predictions from individual model predictions"""

        self.log_info("Creating ensemble predictions...")

        if len(individual_predictions) < 2:
            return {'error': 'Need at least 2 models for ensemble predictions'}

        try:
            # Get predictions from all models
            margin_predictions = []
            probability_predictions = []

            for model_name, pred_data in individual_predictions.items():
                if pred_data['prediction_type'] == 'margin':
                    margin_predictions.append(pred_data['predictions'])
                else:
                    probability_predictions.append(pred_data['predictions'])

            # Create ensemble predictions
            ensemble_result = {
                'margin_ensemble': None,
                'probability_ensemble': None,
                'combined_ensemble': None,
                'models_used': list(individual_predictions.keys()),
                'ensemble_method': 'weighted_average',
                'generation_time': datetime.now().isoformat()
            }

            # Margin ensemble (if we have margin predictions)
            if margin_predictions:
                margin_array = np.vstack(margin_predictions)
                margin_weights = np.array([
                    individual_predictions[name]['model_weight']
                    for name in individual_predictions
                    if individual_predictions[name]['prediction_type'] == 'margin'
                ])

                weighted_margin = np.average(margin_array, axis=0, weights=margin_weights)
                ensemble_result['margin_ensemble'] = weighted_margin

            # Probability ensemble (if we have probability predictions)
            if probability_predictions:
                probability_array = np.vstack(probability_predictions)
                prob_weights = np.array([
                    individual_predictions[name]['model_weight']
                    for name in individual_predictions
                    if individual_predictions[name]['prediction_type'] == 'probability'
                ])

                weighted_probability = np.average(probability_array, axis=0, weights=prob_weights)
                ensemble_result['probability_ensemble'] = weighted_probability

            # Combined ensemble (convert everything to probabilities)
            if margin_predictions and probability_predictions:
                # Convert margin predictions to probabilities using sigmoid function
                margin_probs = 1 / (1 + np.exp(-np.array(margin_predictions) / 10))  # Scale margin to reasonable probability range

                # Combine all probabilities
                all_probs = np.vstack(probability_predictions + [margin_probs])
                all_weights = np.array([
                    individual_predictions[name]['model_weight']
                    for name in individual_predictions
                    if individual_predictions[name]['prediction_type'] == 'probability'
                ] + list(margin_weights))

                combined_prob = np.average(all_probs, axis=0, weights=all_weights)
                ensemble_result['combined_ensemble'] = combined_prob

            elif probability_predictions:  # Only have probability predictions
                ensemble_result['combined_ensemble'] = ensemble_result['probability_ensemble']
            elif margin_predictions:  # Only have margin predictions
                # Convert margin to probability
                margin_probs = 1 / (1 + np.exp(-ensemble_result['margin_ensemble'] / 10))
                ensemble_result['combined_ensemble'] = margin_probs

            self.log_info("✅ Successfully created ensemble predictions")
            return ensemble_result

        except Exception as e:
            self.log_error("Failed to create ensemble predictions", e)
            return {'error': f'Ensemble creation failed: {e}'}

    def _calculate_prediction_confidence(self, individual_predictions: Dict[str, Any], ensemble_predictions: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate confidence scores for predictions"""

        self.log_info("Calculating prediction confidence scores...")

        confidence_scores = {
            'average_confidence': 0,
            'game_confidences': [],
            'confidence_distribution': {},
            'high_confidence_count': 0,
            'low_confidence_count': 0
        }

        try:
            if 'combined_ensemble' not in ensemble_predictions:
                return {'error': 'No ensemble predictions available for confidence calculation'}

            ensemble_probs = ensemble_predictions['combined_ensemble']

            # Calculate confidence for each game
            for i, prob in enumerate(ensemble_probs):
                # Higher confidence when predictions are more extreme (close to 0 or 1)
                confidence = abs(prob - 0.5) * 2  # Scale to 0-1 range

                # Boost confidence based on model agreement
                model_agreement_boost = self._calculate_model_agreement_boost(i, individual_predictions)
                confidence = min(1.0, confidence + model_agreement_boost)

                confidence_scores['game_confidences'].append({
                    'game_index': i,
                    'confidence': confidence,
                    'home_win_probability': prob,
                    'prediction_confidence_level': self._get_confidence_level(confidence)
                })

            # Calculate overall statistics
            confidences = [item['confidence'] for item in confidence_scores['game_confidences']]
            confidence_scores['average_confidence'] = np.mean(confidences)
            confidence_scores['high_confidence_count'] = sum(1 for c in confidences if c > 0.75)
            confidence_scores['low_confidence_count'] = sum(1 for c in confidences if c < 0.5)

            # Create confidence distribution
            confidence_scores['confidence_distribution'] = {
                'very_high': sum(1 for c in confidences if c > 0.9),
                'high': sum(1 for c in confidences if 0.75 < c <= 0.9),
                'medium': sum(1 for c in confidences if 0.5 < c <= 0.75),
                'low': sum(1 for c in confidences if 0.25 < c <= 0.5),
                'very_low': sum(1 for c in confidences if c <= 0.25)
            }

            self.log_info(f"Calculated confidence scores: Average={confidence_scores['average_confidence']:.2f}")

        except Exception as e:
            self.log_error("Failed to calculate confidence scores", e)
            return {'error': f'Confidence calculation failed: {e}'}

        return confidence_scores

    def _calculate_model_agreement_boost(self, game_index: int, individual_predictions: Dict[str, Any]) -> float:
        """Calculate confidence boost based on model agreement for a specific game"""

        try:
            model_predictions = []
            model_types = []

            for model_name, pred_data in individual_predictions.items():
                predictions = pred_data['predictions']
                if game_index < len(predictions):
                    if pred_data['prediction_type'] == 'probability':
                        model_predictions.append(predictions[game_index])
                    else:  # margin - convert to probability
                        margin_prob = 1 / (1 + np.exp(-predictions[game_index] / 10))
                        model_predictions.append(margin_prob)
                    model_types.append(pred_data['prediction_type'])

            if len(model_predictions) < 2:
                return 0

            # Calculate standard deviation (lower = more agreement)
            std_dev = np.std(model_predictions)
            agreement_boost = max(0, 0.1 - std_dev)  # Boost up to 0.1 for strong agreement

            return agreement_boost

        except:
            return 0

    def _get_confidence_level(self, confidence: float) -> str:
        """Convert confidence score to confidence level"""

        if confidence > 0.85:
            return "Very High"
        elif confidence > 0.75:
            return "High"
        elif confidence > 0.6:
            return "Medium"
        elif confidence > 0.4:
            return "Low"
        else:
            return "Very Low"

    def _generate_prediction_explanations(self, ensemble_predictions: Dict[str, Any], weekly_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate explanations for predictions"""

        self.log_info("Generating prediction explanations...")

        explanations = []

        if 'combined_ensemble' not in ensemble_predictions or 'features' not in weekly_data:
            return explanations

        features_df = weekly_data['features']
        ensemble_probs = ensemble_predictions['combined_ensemble']

        for i, prob in enumerate(ensemble_probs):
            if i >= len(features_df):
                continue

            game_data = features_df.iloc[i]
            home_team = game_data.get('home_team', 'Unknown')
            away_team = game_data.get('away_team', 'Unknown')

            # Generate explanation based on key factors
            explanation = {
                'game_index': i,
                'home_team': home_team,
                'away_team': away_team,
                'predicted_winner': home_team if prob > 0.5 else away_team,
                'win_probability': prob,
                'margin_estimate': self._estimate_margin_from_probability(prob),
                'key_factors': self._identify_key_prediction_factors(game_data, prob),
                'risk_assessment': self._assess_prediction_risk(prob, game_data),
                'contextual_factors': self._get_contextual_factors(i, weekly_data),
                'explanation_text': self._generate_explanation_text(prob, home_team, away_team, game_data)
            }

            explanations.append(explanation)

        self.log_info(f"Generated explanations for {len(explanations)} games")
        return explanations

    def _estimate_margin_from_probability(self, probability: float) -> float:
        """Convert win probability to estimated margin"""
        # Using logistic function to convert probability to margin
        if probability == 0.5:
            return 0
        elif probability > 0.5:
            return -np.log((1 - probability) / probability) * 7  # Scale to realistic margin range
        else:
            return np.log(probability / (1 - probability)) * 7

    def _identify_key_prediction_factors(self, game_data: pd.Series, probability: float) -> List[str]:
        """Identify key factors influencing the prediction"""

        key_factors = []

        # Check talent differential
        home_talent = game_data.get('home_talent', 0)
        away_talent = game_data.get('away_talent', 0)
        talent_diff = home_talent - away_talent

        if abs(talent_diff) > 50:
            key_factors.append(f"{'Home team' if talent_diff > 0 else 'Away team'} has significant talent advantage ({abs(talent_diff)} points)")

        # Check EPA differential
        home_epa = game_data.get('home_adjusted_epa', 0)
        away_epa = game_data.get('away_adjusted_epa', 0)
        epa_diff = home_epa - away_epa

        if abs(epa_diff) > 0.2:
            key_factors.append(f"Strong {'offensive' if epa_diff > 0 else 'defensive'} efficiency advantage")

        # Check confidence level
        if probability > 0.75:
            key_factors.append("High confidence prediction based on model agreement")
        elif probability < 0.25:
            key_factors.append("High confidence away team prediction")
        elif 0.45 < probability < 0.55:
            key_factors.append("Very close matchup - could go either way")

        return key_factors[:3]  # Limit to top 3 factors

    def _assess_prediction_risk(self, probability: float, game_data: pd.Series) -> str:
        """Assess the risk level of the prediction"""

        confidence = abs(probability - 0.5) * 2

        # Additional risk factors
        risk_factors = []

        # Check for rivalry or championship implications
        # (This would need additional data from matchup analysis)

        if confidence > 0.8:
            return "Low Risk"
        elif confidence > 0.6:
            return "Medium Risk"
        else:
            return "High Risk"

    def _get_contextual_factors(self, game_index: int, weekly_data: Dict[str, Any]) -> List[str]:
        """Get contextual factors for the game"""

        contextual_factors = []

        # Add week-specific factors
        if self.week >= 10:
            contextual_factors.append(f"Week {self.week} - Late season momentum important")
            contextual_factors.append("Championship implications at stake")
            contextual_factors.append("Potential bowl eligibility impact")
        else:
            contextual_factors.append(f"Week {self.week} - Early season matchup")
            contextual_factors.append("Building momentum for conference play")

        return contextual_factors

    def _generate_explanation_text(self, prob: float, home_team: str, away_team: str, game_data: pd.Series) -> str:
        """Generate human-readable explanation text"""

        predicted_winner = home_team if prob > 0.5 else away_team
        win_prob = prob if prob > 0.5 else 1 - prob
        margin_estimate = abs(self._estimate_margin_from_probability(prob))

        explanation = f"{predicted_winner} is favored to win with {win_prob:.1%} confidence. "

        if margin_estimate > 10:
            explanation += f"Expected to win by approximately {margin_estimate:.0f} points. "
        elif margin_estimate > 3:
            explanation += f"Expected to win by a close margin of approximately {margin_estimate:.0f} points. "
        else:
            explanation += "Expected to be a very close game. "

        explanation += "This prediction is based on advanced statistical models considering team talent, recent performance, and matchup-specific factors."

        return explanation

    def _create_comprehensive_predictions(self, ensemble_predictions: Dict[str, Any], confidence_scores: Dict[str, Any], prediction_explanations: List[Dict[str, Any]], weekly_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create comprehensive prediction dataset"""

        self.log_info("Creating comprehensive prediction dataset...")

        comprehensive_predictions = []

        if 'combined_ensemble' not in ensemble_predictions:
            return comprehensive_predictions

        ensemble_probs = ensemble_predictions['combined_ensemble']
        features_df = weekly_data.get('features', pd.DataFrame())

        for i, prob in enumerate(ensemble_probs):
            if i >= len(features_df):
                continue

            game_data = features_df.iloc[i]
            explanation = prediction_explanations[i] if i < len(prediction_explanations) else {}

            # Get team names
            home_team = game_data.get('home_team', f'Team_{i}_Home')
            away_team = game_data.get('away_team', f'Team_{i}_Away')

            # Create comprehensive prediction record
            prediction_record = {
                'game_id': game_data.get('game_id', f'{self.season}_week{self.week}_{i+1:03d}'),
                'season': self.season,
                'week': self.week,
                'home_team': home_team,
                'away_team': away_team,
                'predicted_winner': home_team if prob > 0.5 else away_team,
                'home_win_probability': prob,
                'away_win_probability': 1 - prob,
                'predicted_margin': self._estimate_margin_from_probability(prob),
                'confidence_score': confidence_scores['game_confidences'][i]['confidence'],
                'confidence_level': confidence_scores['game_confidences'][i]['prediction_confidence_level'],
                'risk_assessment': explanation.get('risk_assessment', 'Medium Risk'),
                'key_factors': explanation.get('key_factors', []),
                'prediction_explanation': explanation.get('explanation_text', f'{home_team} vs {away_team} prediction'),
                'models_used': ensemble_predictions['models_used'],
                'ensemble_method': ensemble_predictions['ensemble_method'],
                'generation_time': datetime.now().isoformat()
            }

            # Add feature values for reference
            feature_subset = {
                'home_talent': game_data.get('home_talent', 0),
                'away_talent': game_data.get('away_talent', 0),
                'home_adjusted_epa': game_data.get('home_adjusted_epa', 0),
                'away_adjusted_epa': game_data.get('away_adjusted_epa', 0),
                'home_adjusted_success': game_data.get('home_adjusted_success', 0),
                'away_adjusted_success': game_data.get('away_adjusted_success', 0)
            }
            prediction_record.update(feature_subset)

            comprehensive_predictions.append(prediction_record)

        self.log_info(f"Created {len(comprehensive_predictions)} comprehensive prediction records")
        return comprehensive_predictions

    def _analyze_prediction_patterns(self, comprehensive_predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze patterns in the predictions"""

        self.log_info("Analyzing prediction patterns...")

        if not comprehensive_predictions:
            return {'error': 'No predictions available for pattern analysis'}

        analysis = {
            'total_predictions': len(comprehensive_predictions),
            'home_win_predictions': 0,
            'away_win_predictions': 0,
            'average_confidence': 0,
            'high_confidence_predictions': 0,
            'average_predicted_margin': 0,
            'upset_predictions': 0,
            'close_games': 0,
            'blowout_predictions': 0
        }

        confidences = []
        margins = []

        for pred in comprehensive_predictions:
            if pred['predicted_winner'] == pred['home_team']:
                analysis['home_win_predictions'] += 1
            else:
                analysis['away_win_predictions'] += 1

            confidences.append(pred['confidence_score'])
            margins.append(abs(pred['predicted_margin']))

            if pred['confidence_score'] > 0.75:
                analysis['high_confidence_predictions'] += 1

            # Define upset prediction (lower ranked team favored - simplified)
            # In a real implementation, you'd use actual rankings
            home_talent = pred.get('home_talent', 0)
            away_talent = pred.get('away_talent', 0)

            if (pred['predicted_winner'] == pred['away_team'] and home_talent > away_talent + 30) or \
               (pred['predicted_winner'] == pred['home_team'] and away_talent > home_talent + 30):
                analysis['upset_predictions'] += 1

            if abs(pred['predicted_margin']) < 7:
                analysis['close_games'] += 1
            elif abs(pred['predicted_margin']) > 21:
                analysis['blowout_predictions'] += 1

        analysis['average_confidence'] = np.mean(confidences)
        analysis['average_predicted_margin'] = np.mean(margins)

        # Additional pattern analysis
        analysis['prediction_patterns'] = {
            'home_win_rate': analysis['home_win_predictions'] / len(comprehensive_predictions),
            'upset_rate': analysis['upset_predictions'] / len(comprehensive_predictions),
            'close_game_rate': analysis['close_games'] / len(comprehensive_predictions),
            'blowout_rate': analysis['blowout_predictions'] / len(comprehensive_predictions)
        }

        self.log_info(f"Pattern analysis completed: {analysis['home_win_predictions']}/{analysis['total_predictions']} home wins predicted")
        return analysis

    def _generate_actionable_recommendations(self, comprehensive_predictions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate actionable recommendations based on predictions"""

        self.log_info("Generating actionable recommendations...")

        recommendations = []

        # Find high-confidence predictions
        high_confidence_preds = [pred for pred in comprehensive_predictions if pred['confidence_score'] > 0.8]

        # Find upset predictions
        upset_preds = [pred for pred in comprehensive_predictions if 'upset_prediction' in pred.get('key_factors', [])]

        # Find close games
        close_games = [pred for pred in comprehensive_predictions if abs(pred['predicted_margin']) < 3]

        # Generate recommendations for high-confidence games
        for pred in high_confidence_preds[:5]:  # Top 5 high confidence
            recommendations.append({
                'type': 'high_confidence',
                'game_id': pred['game_id'],
                'teams': f"{pred['home_team']} vs {pred['away_team']}",
                'recommendation': f"Strong bet on {pred['predicted_winner']} ({pred['confidence_score']:.1%} confidence)",
                'action': 'Consider strong bet',
                'confidence': pred['confidence_score']
            })

        # Generate recommendations for upset alerts
        for pred in upset_preds[:3]:  # Top 3 upset predictions
            recommendations.append({
                'type': 'upset_alert',
                'game_id': pred['game_id'],
                'teams': f"{pred['home_team']} vs {pred['away_team']}",
                'recommendation': f"Upset alert: {pred['predicted_winner']} favored despite talent disadvantage",
                'action': 'Monitor closely',
                'confidence': pred['confidence_score']
            })

        # Generate recommendations for close games
        for pred in close_games[:3]:  # Top 3 close games
            recommendations.append({
                'type': 'close_game',
                'game_id': pred['game_id'],
                'teams': f"{pred['home_team']} vs {pred['away_team']}",
                'recommendation': f"Very close game expected ({pred['predicted_margin']:.1f} margin)",
                'action': 'Consider prop bets',
                'confidence': pred['confidence_score']
            })

        self.log_info(f"Generated {len(recommendations)} actionable recommendations")
        return recommendations

    def _generate_markdown_summary(
        self,
        comprehensive_predictions: List[Dict[str, Any]],
        prediction_insights: Dict[str, Any],
        actionable_recommendations: List[Dict[str, Any]]
    ) -> str:
        """Generate a human-readable markdown summary of predictions"""
        
        if not comprehensive_predictions:
            return "# Weekly Predictions Summary\n\nNo predictions available."
        
        # Calculate statistics
        total_games = len(comprehensive_predictions)
        home_wins = sum(1 for pred in comprehensive_predictions if pred['predicted_winner'] == pred['home_team'])
        home_win_rate = home_wins / total_games if total_games else 0.0
        avg_confidence = np.mean([pred['confidence_score'] for pred in comprehensive_predictions])
        avg_margin = np.mean([abs(pred['predicted_margin']) for pred in comprehensive_predictions])
        close_games = sum(1 for pred in comprehensive_predictions if abs(pred['predicted_margin']) < 4)
        high_conf = sum(1 for pred in comprehensive_predictions if pred['confidence_score'] > 0.75)
        
        # Get top confident predictions
        sorted_predictions = sorted(
            comprehensive_predictions,
            key=lambda x: x['confidence_score'],
            reverse=True
        )
        top_predictions = sorted_predictions[:5]
        
        # Build markdown
        md_lines = [
            f"# Week {self.week} Predictions Summary",
            "",
            f"**Season:** {self.season}  ",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ",
            f"**Total Games:** {total_games}",
            "",
            "## Key Statistics",
            "",
            f"- **Average Confidence:** {avg_confidence:.1%}",
            f"- **Home Win Rate:** {home_win_rate:.1%} ({home_wins}/{total_games})",
            f"- **Average Margin:** {avg_margin:.1f} points",
            f"- **High Confidence Games:** {high_conf} (confidence > 75%)",
            f"- **Close Games:** {close_games} (margin < 4 points)",
            ""
        ]
        
        # Top predictions section
        if top_predictions:
            md_lines.extend([
                "## Top Predictions (Highest Confidence)",
                ""
            ])
            for i, pred in enumerate(top_predictions, 1):
                md_lines.append(
                    f"{i}. **{pred['away_team']} @ {pred['home_team']}**  \n"
                    f"   - Winner: {pred['predicted_winner']}  \n"
                    f"   - Margin: {pred['predicted_margin']:.1f} points  \n"
                    f"   - Confidence: {pred['confidence_score']:.1%}"
                )
            md_lines.append("")
        
        # Actionable recommendations section
        if actionable_recommendations:
            md_lines.extend([
                "## Actionable Recommendations",
                ""
            ])
            
            # Group by type
            high_conf_recs = [r for r in actionable_recommendations if r.get('type') == 'high_confidence']
            upset_recs = [r for r in actionable_recommendations if r.get('type') == 'upset_alert']
            close_recs = [r for r in actionable_recommendations if r.get('type') == 'close_game']
            
            if high_conf_recs:
                md_lines.append("### High Confidence Bets")
                for rec in high_conf_recs[:3]:
                    md_lines.append(f"- {rec['teams']}: {rec['recommendation']}")
                md_lines.append("")
            
            if upset_recs:
                md_lines.append("### Upset Alerts")
                for rec in upset_recs[:3]:
                    md_lines.append(f"- {rec['teams']}: {rec['recommendation']}")
                md_lines.append("")
            
            if close_recs:
                md_lines.append("### Close Games")
                for rec in close_recs[:3]:
                    md_lines.append(f"- {rec['teams']}: {rec['recommendation']}")
                md_lines.append("")
        
        # Prediction insights section
        if prediction_insights and prediction_insights.get('summary'):
            md_lines.extend([
                "## Insights",
                "",
                prediction_insights.get('summary', 'No insights available.'),
                ""
            ])
        
        return "\n".join(md_lines)

    def _save_prediction_results(self, comprehensive_predictions: List[Dict[str, Any]], prediction_insights: Dict[str, Any], actionable_recommendations: List[Dict[str, Any]], *, summary_report: Optional[Dict[str, Any]] = None) -> None:
        """Save prediction results to standardized CSV and markdown summary"""

        self.log_info("Saving prediction results...")

        # Standardized output location: predictions/week{XX}/
        output_dir = Path("predictions") / f"week{self.week}"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save canonical CSV: predictions/week{XX}/predictions.csv
        csv_path = output_dir / "predictions.csv"
        try:
            if comprehensive_predictions:
                # Convert predictions list to DataFrame
                predictions_df = pd.DataFrame(comprehensive_predictions)
                
                # Select key columns for CSV output (prioritize these)
                key_columns = [
                    'home_team', 'away_team', 'predicted_winner', 'predicted_margin',
                    'confidence_score', 'ridge_prediction', 'xgb_prediction',
                    'fastai_prediction', 'ensemble_prediction'
                ]
                # Only include columns that exist
                available_columns = [col for col in key_columns if col in predictions_df.columns]
                # Add any other columns that might be useful (exclude nested objects)
                other_columns = [
                    col for col in predictions_df.columns 
                    if col not in key_columns 
                    and col not in ['metadata', 'insights']
                    and not isinstance(predictions_df[col].iloc[0] if len(predictions_df) > 0 else None, (dict, list))
                ]
                final_columns = available_columns + other_columns
                
                # Ensure we have at least some columns
                if not final_columns:
                    final_columns = list(predictions_df.columns)
                
                predictions_df[final_columns].to_csv(csv_path, index=False)
                self.log_info(f"Saved {len(comprehensive_predictions)} predictions to {csv_path} ({len(final_columns)} columns)")
            else:
                self.log_warning("No predictions to save to CSV")
        except Exception as e:
            self.log_error(f"Failed to save predictions CSV to {csv_path}", e)
            raise

        # Save markdown summary: predictions/week{XX}/summary.md
        summary_path = output_dir / "summary.md"
        try:
            markdown_summary = self._generate_markdown_summary(
                comprehensive_predictions,
                prediction_insights,
                actionable_recommendations
            )
            with summary_path.open('w', encoding='utf-8') as f:
                f.write(markdown_summary)
            self.log_info(f"Saved markdown summary to {summary_path}")
        except Exception as e:
            self.log_error(f"Failed to save markdown summary to {summary_path}", e)
            raise

    def _create_prediction_summary_report(self, comprehensive_predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a summary report of all predictions"""

        self.log_info("Creating prediction summary report...")

        if not comprehensive_predictions:
            return {'error': 'No predictions available for summary report'}

        # Calculate summary statistics
        home_wins = sum(1 for pred in comprehensive_predictions if pred['predicted_winner'] == pred['home_team'])
        total_games = len(comprehensive_predictions)
        avg_confidence = np.mean([pred['confidence_score'] for pred in comprehensive_predictions])
        avg_margin = np.mean([abs(pred['predicted_margin']) for pred in comprehensive_predictions])
        close_games = sum(1 for pred in comprehensive_predictions if abs(pred['predicted_margin']) < 4)
        high_conf = sum(1 for pred in comprehensive_predictions if pred['confidence_score'] > 0.75)

        summary_report = {
            'week': self.week,
            'season': self.season,
            'generated_at': datetime.now().isoformat(),
            'games_predicted': total_games,
            'home_win_rate': home_wins / total_games if total_games else 0.0,
            'average_confidence': float(avg_confidence),
            'average_predicted_margin': float(avg_margin),
            'high_confidence_predictions': high_conf,
            'close_games': close_games,
            'models_used': ['ridge_regression', 'xgboost_win_probability', 'fastai_neural_network'],
        }

        # Summary report is now included in markdown summary via _save_prediction_results()
        # No need to save separate JSON file
        self.log_info(f"Prediction summary report generated (included in markdown summary)")
        return summary_report

    # Helper methods
    def _load_prediction_weights(self) -> Dict[str, float]:
        """Load prediction weights for ensemble"""
        return {
            'ridge_regression': 0.3,
            'xgboost_win_probability': 0.4,
            'fastai_neural_network': 0.3
        }

    def _load_confidence_thresholds(self) -> Dict[str, float]:
        """Load confidence thresholds"""
        return {
            'high_confidence': 0.75,
            'medium_confidence': 0.6,
            'low_confidence': 0.4
        }


# Example usage
if __name__ == "__main__":
    agent = WeeklyPredictionGenerationAgent(week=13, season=2025)

    task_data = {
        'operation': 'generate_predictions',
        'target_week': 13,
        'season': 2025,
        'use_ensemble': True,
        'generate_explanations': True
    }

    result = agent.execute_task(task_data)
    print(f"Prediction Generation Result: {result}")
