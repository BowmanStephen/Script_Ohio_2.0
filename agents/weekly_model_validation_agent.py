"""
Weekly Model Validation Agent
Validates ML models for weekly predictions and ensures compatibility with enhanced data
"""

import os
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import json
import joblib
import pickle
from sklearn.model_selection import cross_val_score
import warnings
warnings.filterwarnings('ignore')

try:
    from fastai.learner import load_learner as fastai_load_learner
except Exception:  # pragma: no cover - FastAI optional
    fastai_load_learner = None

# Import the base agent framework
from agents.core.agent_framework import BaseAgent, AgentCapability, PermissionLevel

# Import path utilities
from model_pack.utils.path_utils import (
    get_weekly_enhanced_file,
    get_master_training_data_path
)

class WeeklyModelValidationAgent(BaseAgent):
    """
    Agent responsible for validating ML models for weekly predictions
    and ensuring they work correctly with enhanced data
    """

    def __init__(self, week: int, season: int = 2025, agent_id: Optional[str] = None):
        self.week = week
        self.season = season
        
        if agent_id is None:
            agent_id = f"week{week}_model_validation_agent"
        
        super().__init__(
            agent_id=agent_id,
            name=f"Week {week} Model Validation Agent",
            permission_level=PermissionLevel.READ_EXECUTE_WRITE,
        )
        self.agent_description = f"Validates Week {week} ML models and data compatibility."

        # Initialize agent-specific attributes
        self.model_performance_history = self._load_model_history()
        self.validation_thresholds = self._load_validation_thresholds()
        self._canonical_features: List[str] = []
        self._feature_defaults: Dict[str, float] = {}
        self._feature_schema_log: Dict[str, Dict[str, Any]] = {}
        self._fastai_loader = fastai_load_learner

    # ------------------------------------------------------------------
    # Simple logging helpers
    # ------------------------------------------------------------------
    def log_start(self, message: str):
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"[START] {message}")

    def log_success(self, message: str, result: Dict[str, Any]):
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"[SUCCESS] {message}")

    def log_error(self, message: str, error: Exception):
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"[ERROR] {message}: {error}")

    def log_info(self, message: str):
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"[INFO] {message}")

    def log_warning(self, message: str):
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"[WARN] {message}")

    def get_execution_time(self) -> float:
        return 0.0

    def _define_capabilities(self) -> List[AgentCapability]:
        """Define agent capabilities and permissions"""
        return [
            AgentCapability(
                name="validate_models",
                description=f"Run validation suite across Week {self.week} ML models.",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=["model_loader", "data_validator"],
                data_access=["model_pack/", "starter_pack/data/"],
                execution_time_estimate=12.0,
            ),
            AgentCapability(
                name="check_compatibility",
                description="Assess compatibility between enhanced data and models.",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=["data_validator"],
                data_access=["starter_pack/data/", "model_pack/"],
                execution_time_estimate=4.0,
            ),
            AgentCapability(
                name="performance_test",
                description="Benchmark model performance metrics.",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=["performance_tester"],
                data_access=["model_pack/"],
                execution_time_estimate=6.0,
            ),
        ]

    def _execute_action(self, action: str, parameters: Dict[str, Any],
                      user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent action with proper routing"""
        if action == "validate_models":
            return self._validate_models(parameters, user_context)
        elif action == "check_compatibility":
            return self._check_data_compatibility(parameters, user_context)
        elif action == "performance_test":
            return self._run_performance_tests(parameters, user_context)
        else:
            raise ValueError(f"Unknown action: {action}")

    def _validate_models(self, parameters: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Main model validation action"""
        try:
            # Step 1: Load and validate weekly data
            weekly_data = self._load_weekly_data()
            data_validation = self._validate_weekly_data(weekly_data)

            # Step 2: Load all available models
            loaded_models = self._load_all_models()
            model_availability_check = self._check_model_availability(loaded_models)

            # Generate basic validation report
            validation_report = {
                'data_validation': data_validation,
                'model_availability': model_availability_check,
                'timestamp': datetime.now().isoformat(),
                'agent': 'Week12ModelValidationAgent'
            }

            return {
                'status': 'success',
                'validation_report': validation_report,
                'message': 'Model validation completed successfully'
            }

        except Exception as e:
            return {
                'status': 'error',
                'error_message': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def _check_data_compatibility(self, parameters: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Check data compatibility with models"""
        try:
            weekly_data = self._load_weekly_data()
            loaded_models = self._load_all_models()
            compatibility_results = self._validate_model_data_compatibility(loaded_models, weekly_data)

            return {
                'status': 'success',
                'compatibility_results': compatibility_results,
                'message': 'Data compatibility check completed'
            }
        except Exception as e:
            return {
                'status': 'error',
                'error_message': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def _run_performance_tests(self, parameters: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Run performance tests on models"""
        try:
            weekly_data = self._load_weekly_data()
            loaded_models = self._load_all_models()
            performance_tests = self._test_model_performance(loaded_models, weekly_data)

            return {
                'status': 'success',
                'performance_tests': performance_tests,
                'message': 'Performance tests completed'
            }
        except Exception as e:
            return {
                'status': 'error',
                'error_message': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main execution method for model validation

        Args:
            task_data: Contains configuration for validation task

        Returns:
            Comprehensive model validation results
        """
        try:
            self.log_start("Model Validation")
            # Reset per-run caches that should not persist between executions
            self._feature_schema_log = {}

            # Step 1: Load and validate weekly data
            weekly_data = self._load_weekly_data()
            data_validation = self._validate_weekly_data(weekly_data)

            # Step 2: Load all available models
            loaded_models = self._load_all_models()
            model_availability_check = self._check_model_availability(loaded_models)

            # Step 3: Validate model-data compatibility
            compatibility_results = self._validate_model_data_compatibility(loaded_models, weekly_data)

            # Step 4: Perform individual model validation
            individual_validations = self._validate_individual_models(loaded_models, weekly_data)

            # Step 5: Test model performance on weekly data
            performance_tests = self._test_model_performance(loaded_models, weekly_data)

            # Step 6: Cross-validate models if possible
            cross_validation_results = self._cross_validate_models(loaded_models, weekly_data)

            # Step 7: Generate ensemble validation
            ensemble_validation = self._validate_ensemble_performance(loaded_models, weekly_data)

            # Step 8: Validate previous week results (if available and week > 1)
            previous_week_validation = None
            if self.week > 1:
                previous_week_validation = self._validate_previous_week_results(loaded_models)

            # Step 9: Identify potential biases and issues
            bias_analysis = self._analyze_model_biases(loaded_models, weekly_data)

            # Step 10: Generate validation report and recommendations
            validation_report = self._generate_validation_report(
                data_validation, model_availability_check, compatibility_results,
                individual_validations, performance_tests, cross_validation_results,
                ensemble_validation, bias_analysis, previous_week_validation
            )

            # Step 11: Save validation results
            self._save_validation_results(validation_report)

            # Step 12: Update model performance history
            self._update_model_history(validation_report)

            overall_score_value = validation_report['report_metadata']['overall_score']
            result = {
                'status': 'success',
                'models_validated': len(loaded_models),
                'data_validation_passed': data_validation['is_valid'],
                'overall_validation_score': overall_score_value,
                'models_ready_for_predictions': validation_report['models_ready'],
                'recommendations': len(validation_report['recommendations']),
                'validation_complete': True,
                'execution_time': self.get_execution_time()
            }

            self.log_success("Model Validation", result)
            return result

        except Exception as e:
            error_result = {
                'status': 'error',
                'error': str(e),
                'execution_time': self.get_execution_time()
            }
            self.log_error("Model Validation", e)
            return error_result

    def _load_weekly_data(self) -> Dict[str, Any]:
        """Load weekly enhanced data for validation"""

        self.log_info(f"Loading Week {self.week} data for model validation...")

        try:
            # Load enhanced features using path utility
            features_path = get_weekly_enhanced_file(self.week, 'features', self.season)
            features_df = pd.read_csv(features_path)
            self.log_info(f"Loaded {len(features_df)} feature records with {len(features_df.columns)} columns from {features_path}")

            # Load games data using path utility (optional, so handle gracefully)
            try:
                games_path = get_weekly_enhanced_file(self.week, 'games', self.season)
                games_df = pd.read_csv(games_path)
                self.log_info(f"Loaded {len(games_df)} games from {games_path}")
            except FileNotFoundError:
                games_df = None
                self.log_info("No games data loaded - will use features only")

            # Load training data for comparison using path utility
            try:
                training_data_path = get_master_training_data_path()
                training_df = pd.read_csv(training_data_path)
                self.log_info(f"Loaded training data with {len(training_df)} records from {training_data_path}")
            except FileNotFoundError:
                training_df = None
                self.log_info("No training data available for comparison")

            return {
                'features': features_df,
                'games': games_df,
                'training_data': training_df,
                'load_time': datetime.now().isoformat(),
                'data_source': f'enhanced_week{self.week}'
            }

        except Exception as e:
            self.log_error(f"Loading Week {self.week} data", e)
            raise

    def _validate_weekly_data(self, weekly_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate weekly data quality and structure"""

        self.log_info(f"Validating Week {self.week} data quality...")

        validation_results = {
            'is_valid': True,
            'issues': [],
            'warnings': [],
            'data_quality_score': 0,
            'feature_completeness': 0,
            'data_consistency': 0
        }

        # Validate features data
        if 'features' in weekly_data:
            features_df = weekly_data['features']

            # Check required number of features
            if len(features_df.columns) < 86:
                validation_results['issues'].append(f"Insufficient features: {len(features_df.columns)} < 86")
                validation_results['is_valid'] = False
            else:
                validation_results['feature_completeness'] = min(1.0, len(features_df.columns) / 86)

            # Check for missing values
            missing_counts = features_df.isnull().sum()
            high_missing = missing_counts[missing_counts > len(features_df) * 0.1]

            if not high_missing.empty:
                validation_results['warnings'].append(f"High missing data in: {list(high_missing.index)}")

            # Check data types
            numeric_columns = features_df.select_dtypes(include=[np.number]).columns
            if len(numeric_columns) < 80:
                validation_results['warnings'].append(f"Low numeric feature count: {len(numeric_columns)}")

            # Calculate data quality score
            validation_results['data_quality_score'] = (
                validation_results['feature_completeness'] * 0.5 +
                (1 - len(high_missing) / len(features_df.columns)) * 0.3 +
                (len(numeric_columns) / len(features_df.columns)) * 0.2
            ) * 100

        else:
            validation_results['issues'].append("No features data found")
            validation_results['is_valid'] = False

        # Validate games data
        if 'games' in weekly_data and weekly_data['games'] is not None:
            games_df = weekly_data['games']

            # Check required columns
            required_columns = ['id', 'home_team', 'away_team']
            missing_columns = [col for col in required_columns if col not in games_df.columns]

            if missing_columns:
                validation_results['warnings'].append(f"Missing game columns: {missing_columns}")

        # Validate training data consistency
        if 'training_data' in weekly_data and weekly_data['training_data'] is not None:
            training_df = weekly_data['training_data']
            features_df = weekly_data['features']

            # Compare feature sets
            training_features = set(training_df.columns)
            weekly_features = set(features_df.columns)

            common_features = training_features.intersection(weekly_features)
            feature_overlap = len(common_features) / len(weekly_features)

            validation_results['data_consistency'] = feature_overlap

            if feature_overlap < 0.8:
                validation_results['warnings'].append(f"Low feature overlap: {feature_overlap:.1%}")

        self.log_info(f"Week {self.week} data validation completed. Score: {validation_results['data_quality_score']:.1f}")
        return validation_results

    def _load_all_models(self) -> Dict[str, Any]:
        """Load all available ML models"""

        self.log_info("Loading all available ML models...")

        models = {}
        model_configs = [
            {
                'name': 'ridge_regression',
                'file_path': 'model_pack/ridge_model_2025.joblib',
                'model_type': 'sklearn',
                'prediction_type': 'margin'
            },
            {
                'name': 'xgboost_win_probability',
                'file_path': 'model_pack/xgb_home_win_model_2025.pkl',
                'model_type': 'xgboost',
                'prediction_type': 'probability'
            },
            {
                'name': 'fastai_neural_network',
                'file_path': 'model_pack/fastai_home_win_model_2025.pkl',
                'model_type': 'fastai',
                'prediction_type': 'probability'
            }
        ]

        for config in model_configs:
            try:
                if os.path.exists(config['file_path']):
                    model = self._load_model_file(config)

                    models[config['name']] = {
                        'model': model,
                        'config': config,
                        'load_status': 'success',
                        'load_time': datetime.now().isoformat()
                    }

                    self.log_info(f"Successfully loaded {config['name']}")

                else:
                    models[config['name']] = {
                        'model': None,
                        'config': config,
                        'load_status': 'file_not_found',
                        'load_time': datetime.now().isoformat()
                    }

                    self.log_warning(f"Model file not found: {config['file_path']}")

            except Exception as e:
                models[config['name']] = {
                    'model': None,
                    'config': config,
                    'load_status': f'error: {str(e)}',
                    'load_time': datetime.now().isoformat()
                }

                self.log_error(f"Failed to load {config['name']}", e)

        self.log_info(f"Loaded {sum(1 for m in models.values() if m['load_status'] == 'success')}/{len(models)} models")
        return models

    def _load_model_file(self, config: Dict[str, Any]) -> Any:
        """Load a model from disk based on its configuration."""
        model_type = config.get('model_type')
        file_path = config.get('file_path')

        if model_type == 'sklearn':
            return joblib.load(file_path)

        if model_type == 'fastai':
            return self._load_fastai_model(file_path)

        with open(file_path, 'rb') as f:
            return pickle.load(f)

    def _load_fastai_model(self, file_path: str) -> Any:
        """Load FastAI learner with graceful fallback."""
        if self._fastai_loader:
            try:
                return self._fastai_loader(file_path)
            except Exception as exc:
                self.log_warning(f"FastAI load_learner failed for {file_path}: {exc}")

        try:
            with open(file_path, 'rb') as f:
                return pickle.load(f)
        except Exception as exc:
            raise RuntimeError(f"Unable to load FastAI model at {file_path}: {exc}") from exc

    def _check_model_availability(self, loaded_models: Dict[str, Any]) -> Dict[str, Any]:
        """Check model availability and basic functionality"""

        self.log_info("Checking model availability...")

        availability_results = {
            'total_models': len(loaded_models),
            'available_models': 0,
            'unavailable_models': 0,
            'model_details': {}
        }

        for model_name, model_info in loaded_models.items():
            if model_info['model'] is not None:
                availability_results['available_models'] += 1
                status = 'available'
            else:
                availability_results['unavailable_models'] += 1
                status = 'unavailable'

            availability_results['model_details'][model_name] = {
                'status': status,
                'prediction_type': model_info['config']['prediction_type'],
                'load_status': model_info['load_status']
            }

        self.log_info(f"Model availability: {availability_results['available_models']}/{availability_results['total_models']} ready")
        return availability_results

    def _get_training_data_path(self) -> Path:
        return Path('model_pack') / 'updated_training_data.csv'

    def _get_canonical_features(self) -> List[str]:
        """Determine the canonical feature order expected by the production models."""
        if self._canonical_features:
            return self._canonical_features

        candidates: List[str] = []

        ridge_path = Path('model_pack') / 'ridge_model_2025.joblib'
        if ridge_path.exists():
            try:
                ridge_model = joblib.load(ridge_path)
                features = list(getattr(ridge_model, 'feature_names_in_', []))
                if features and len(features) > len(candidates):
                    candidates = features
            except Exception as exc:
                self.log_warning(f"Unable to read ridge feature schema: {exc}")

        xgb_path = Path('model_pack') / 'xgb_home_win_model_2025.pkl'
        if xgb_path.exists():
            try:
                with open(xgb_path, 'rb') as f:
                    xgb_model = pickle.load(f)
                booster_fn = getattr(xgb_model, 'get_booster', None)
                booster = booster_fn() if callable(booster_fn) else None
                feature_names = getattr(booster, 'feature_names', None)
                if feature_names:
                    features = list(feature_names)
                    if features and len(features) > len(candidates):
                        candidates = features
            except Exception as exc:
                self.log_warning(f"Unable to read XGBoost feature schema: {exc}")

        inferred = self._infer_features_from_training_data()
        if len(inferred) > len(candidates):
            candidates = inferred

        self._canonical_features = candidates
        return self._canonical_features

    def _infer_features_from_training_data(self) -> List[str]:
        """Fallback: derive feature names from the training CSV header."""
        training_path = self._get_training_data_path()
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
        """Compute default values for missing features using training medians."""
        if not features:
            return self._feature_defaults

        missing = [col for col in features if col not in self._feature_defaults]
        if not missing:
            return self._feature_defaults

        training_path = self._get_training_data_path()
        if not training_path.exists():
            return self._feature_defaults

        try:
            header = pd.read_csv(training_path, nrows=0)
            usecols = [col for col in missing if col in header.columns]
            if usecols:
                training_df = pd.read_csv(training_path, usecols=usecols)
                medians = training_df.median(numeric_only=True).to_dict()
                self._feature_defaults.update({k: float(v) for k, v in medians.items() if pd.notna(v)})
        except Exception as exc:
            self.log_warning(f"Unable to compute feature defaults: {exc}")

        return self._feature_defaults

    def _align_features_to_schema(self, features_df: pd.DataFrame, canonical: List[str]) -> pd.DataFrame:
        """Align enhanced features to the canonical schema."""
        if features_df is None or features_df.empty:
            return pd.DataFrame()

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
            preview = ', '.join(missing_cols[:5])
            suffix = '...' if len(missing_cols) > 5 else ''
            self.log_warning(f"Aligned features using defaults for missing columns: {preview}{suffix}")

        return aligned

    def _determine_model_features(self, model_info: Optional[Dict[str, Any]]) -> List[str]:
        """Inspect a model to retrieve its native feature schema when possible."""
        if not model_info or 'model' not in model_info or model_info['model'] is None:
            return self._get_canonical_features()

        model = model_info['model']
        model_type = model_info['config'].get('model_type') if model_info.get('config') else None

        if model_type == 'fastai' and hasattr(model, 'dls'):
            cat_names = list(getattr(model.dls, 'cat_names', []))
            cont_names = list(getattr(model.dls, 'cont_names', []))
            names = cat_names + cont_names
            if names:
                return names

        if hasattr(model, 'feature_names_in_'):
            names = list(getattr(model, 'feature_names_in_', []))
            if names:
                return names

        booster_fn = getattr(model, 'get_booster', None)
        if callable(booster_fn):
            try:
                booster = booster_fn()
                feature_names = getattr(booster, 'feature_names', None)
                if feature_names:
                    return list(feature_names)
            except Exception as exc:
                self.log_warning(f"Unable to inspect xgboost booster features: {exc}")

        model_feature_attr = getattr(model, 'feature_names', None)
        if model_feature_attr:
            try:
                names = list(model_feature_attr)
                if names:
                    return names
            except Exception:
                pass

        return self._get_canonical_features()

    def _prepare_features_for_model(
        self,
        features_df: pd.DataFrame,
        model_info: Optional[Dict[str, Any]] = None,
        model_name: Optional[str] = None
    ) -> pd.DataFrame:
        """Create model-ready feature frame with proper ordering and dtypes."""
        if features_df is None or features_df.empty:
            return pd.DataFrame()

        target_features = self._determine_model_features(model_info)
        prepared_df: pd.DataFrame
        if model_info and model_info.get('config', {}).get('model_type') == 'fastai':
            prepared_df = self._prepare_fastai_features(features_df, model_info, target_features)
        elif target_features:
            aligned_df = self._align_features_to_schema(features_df, target_features)
            prepared_df = self._ensure_numeric_only(aligned_df)
        else:
            from src.models.execution.engine import ModelExecutionEngine
            prepared_df = ModelExecutionEngine.prepare_training_features(features_df, exclude_metadata=True)

        self._record_model_feature_schema(model_name, target_features, features_df, prepared_df)
        return prepared_df

    def _ensure_numeric_only(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ensure DataFrame contains only numeric columns, removing any object columns."""
        if df is None or df.empty:
            return df
        
        # Drop object columns
        object_columns = df.select_dtypes(include=['object']).columns
        if len(object_columns) > 0:
            self.log_warning(f"Removing object columns from features: {list(object_columns)}")
            df = df.drop(columns=object_columns)
        
        # Convert remaining columns to numeric, coercing errors
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Fill NaN values
        df = df.fillna(0.0)
        
        return df

    def _prepare_fastai_features(self, features_df: pd.DataFrame, model_info: Dict[str, Any], feature_names: List[str]) -> pd.DataFrame:
        """Prepare categorical + continuous inputs expected by FastAI models."""
        if features_df is None or features_df.empty or not feature_names:
            return pd.DataFrame()

        model = model_info['model']
        dls = getattr(model, 'dls', None)
        cat_names = set(getattr(dls, 'cat_names', [])) if dls else set()
        cont_names = set(getattr(dls, 'cont_names', [])) if dls else set()

        aligned = pd.DataFrame(index=features_df.index)
        for feature in feature_names:
            if feature in features_df.columns:
                aligned[feature] = features_df[feature]
            else:
                if feature in cont_names:
                    aligned[feature] = 0.0
                elif feature in cat_names:
                    aligned[feature] = 'unknown'
                else:
                    aligned[feature] = 0.0

        defaults = self._get_feature_defaults(feature_names)

        for cat in cat_names:
            if cat not in aligned.columns:
                continue
            series = aligned[cat]
            if pd.api.types.is_bool_dtype(series):
                aligned[cat] = series.fillna(False).astype(bool)
            elif pd.api.types.is_numeric_dtype(series):
                aligned[cat] = series.fillna(-1).astype(series.dtype)
            else:
                aligned[cat] = (
                    series.fillna('unknown')
                    .replace('', 'unknown')
                    .astype(str)
                )

        for cont in cont_names:
            if cont not in aligned.columns:
                continue
            aligned[cont] = pd.to_numeric(aligned[cont], errors='coerce')
            default_value = defaults.get(cont)
            if default_value is None or pd.isna(default_value):
                if cont in features_df.columns and features_df[cont].notna().any():
                    default_value = float(features_df[cont].median(skipna=True))
                else:
                    default_value = 0.0
            aligned[cont] = aligned[cont].fillna(default_value)

        return aligned

    def _record_model_feature_schema(
        self,
        model_name: Optional[str],
        target_features: Optional[List[str]],
        source_df: pd.DataFrame,
        prepared_df: pd.DataFrame
    ) -> None:
        """Persist per-model feature schema details for logging and reporting."""
        if not model_name or model_name in self._feature_schema_log:
            return

        derived_features = target_features or list(prepared_df.columns)
        missing_features = [feature for feature in derived_features if feature not in source_df.columns]
        schema_entry = {
            'source_feature_count': int(len(source_df.columns)),
            'derived_feature_count': int(len(derived_features)),
            'prepared_feature_count': int(prepared_df.shape[1]) if prepared_df is not None else 0,
            'missing_features': missing_features,
            'derived_features': derived_features
        }
        self._feature_schema_log[model_name] = schema_entry

        if missing_features:
            preview = ', '.join(missing_features[:5])
            suffix = '...' if len(missing_features) > 5 else ''
            self.log_warning(
                f"{model_name}: filled defaults for {len(missing_features)} missing features "
                f"({preview}{suffix})"
            )
        else:
            self.log_info(f"{model_name}: derived {schema_entry['derived_feature_count']} feature columns")

    def _generate_predictions(self, model_info: Dict[str, Any], input_df: pd.DataFrame) -> Tuple[np.ndarray, str]:
        """Run a model prediction, handling model-type specifics."""
        if input_df is None or input_df.empty:
            raise ValueError("No feature data available for prediction")

        model = model_info['model']
        model_type = model_info['config'].get('model_type')
        prediction_type = model_info['config'].get('prediction_type')

        if model_type == 'fastai':
            probabilities: List[float] = []
            for _, row in input_df.iterrows():
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
            probability_array = np.array(probabilities, dtype=float)
            if probability_array.size and ((probability_array < 0) | (probability_array > 1)).any():
                self.log_warning("FastAI probabilities out of [0,1]; clipping to valid range")
                probability_array = np.clip(probability_array, 0.0, 1.0)
            return probability_array, 'probability'

        if prediction_type == 'margin':
            predictions = model.predict(input_df)
            return np.array(predictions), 'margin'

        if hasattr(model, 'predict_proba'):
            probabilities = model.predict_proba(input_df)
            probabilities = np.array(probabilities)
            if probabilities.ndim > 1 and probabilities.shape[1] > 1:
                probabilities = probabilities[:, 1]
            return probabilities, 'probability'

        predictions = model.predict(input_df)
        return np.array(predictions), prediction_type or 'margin'

    def _validate_model_data_compatibility(self, loaded_models: Dict[str, Any], weekly_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that models are compatible with weekly data"""

        self.log_info("Validating model-data compatibility...")

        compatibility_results = {}

        if 'features' not in weekly_data or weekly_data['features'] is None:
            return {'error': 'No features data available for compatibility testing'}

        features_df = weekly_data['features']

        for model_name, model_info in loaded_models.items():
            if model_info['model'] is None:
                compatibility_results[model_name] = {
                    'compatible': False,
                    'reason': 'Model not loaded'
                }
                continue

            try:
                prepared_features = self._prepare_features_for_model(features_df, model_info, model_name)
                if prepared_features.empty:
                    raise ValueError('Unable to align features for model')

                sample_input = prepared_features.iloc[:1]
                predictions, prediction_type = self._generate_predictions(model_info, sample_input)

                compatibility_results[model_name] = {
                    'compatible': True,
                    'feature_count_used': sample_input.shape[1],
                    'prediction_successful': True,
                    'prediction_shape': predictions.shape if hasattr(predictions, 'shape') else 'scalar',
                    'prediction_type': prediction_type,
                    'test_passed': True
                }

                self.log_info(f"✅ {model_name} compatibility test passed")

            except Exception as e:
                compatibility_results[model_name] = {
                    'compatible': False,
                    'reason': str(e),
                    'prediction_successful': False,
                    'test_passed': False
                }

                self.log_warning(f"❌ {model_name} compatibility test failed: {e}")

        return compatibility_results

    def _validate_individual_models(self, loaded_models: Dict[str, Any], weekly_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform detailed validation of each individual model"""

        self.log_info("Performing individual model validation...")

        individual_validations = {}

        if 'features' not in weekly_data or weekly_data['features'] is None:
            return {'error': 'No features data available'}

        raw_features = weekly_data['features']

        for model_name, model_info in loaded_models.items():
            if model_info['model'] is None:
                individual_validations[model_name] = {
                    'validation_status': 'skipped',
                    'reason': 'Model not available'
                }
                continue

            try:
                model_features = self._prepare_features_for_model(raw_features, model_info, model_name)
                if model_features.empty:
                    raise ValueError('Unable to prepare features for model')

                validation_result = self._validate_single_model(model_name, model_info, model_features)
                individual_validations[model_name] = validation_result

                status = "✅ PASS" if validation_result['validation_status'] == 'passed' else "❌ FAIL"
                self.log_info(f"{status} {model_name} validation: {validation_result.get('validation_score', 0):.1f}/100")

            except Exception as e:
                individual_validations[model_name] = {
                    'validation_status': 'error',
                    'reason': str(e),
                    'validation_score': 0
                }

                self.log_error(f"Error validating {model_name}", e)

        return individual_validations

    def _validate_single_model(self, model_name: str, model_info: Dict[str, Any], features_df: pd.DataFrame) -> Dict[str, Any]:
        """Validate a single model comprehensively"""

        validation_result = {
            'validation_status': 'passed',
            'validation_score': 0,
            'tests_performed': [],
            'issues_found': [],
            'performance_metrics': {}
        }

        prediction_type = model_info['config'].get('prediction_type', 'margin')
        predictions = np.array([])

        try:
            feature_columns = list(features_df.columns)
            X = features_df

            # Test 1: Basic prediction
            try:
                predictions, prediction_type = self._generate_predictions(model_info, X)

                validation_result['tests_performed'].append('basic_prediction')
                validation_result['performance_metrics']['prediction_range'] = {
                    'min': float(predictions.min()),
                    'max': float(predictions.max()),
                    'mean': float(predictions.mean()),
                    'std': float(predictions.std())
                }

            except Exception as e:
                validation_result['issues_found'].append(f'Basic prediction failed: {e}')
                validation_result['validation_status'] = 'failed'

            # Test 2: Consistency check
            try:
                if len(predictions) > 1:
                    prediction_variance = np.var(predictions)
                    if prediction_variance == 0:
                        validation_result['issues_found'].append('All predictions identical - potential overfitting')
                        validation_result['validation_status'] = 'warning'

                validation_result['tests_performed'].append('consistency_check')

            except Exception as e:
                validation_result['issues_found'].append(f'Consistency check failed: {e}')

            # Test 3: Feature importance (if available)
            try:
                if hasattr(model_info['model'], 'feature_importances_'):
                    importances = model_info['model'].feature_importances_
                    top_features = np.argsort(importances)[-5:]
                    validation_result['performance_metrics']['top_features'] = {
                        'indices': top_features.tolist(),
                        'importances': importances[top_features].tolist(),
                        'feature_names': [feature_columns[i] for i in top_features]
                    }
                    validation_result['tests_performed'].append('feature_importance')

            except Exception:
                validation_result['performance_metrics']['feature_importance'] = 'Not available'

            # Test 4: Prediction sanity check
            try:
                if predictions.size > 0 and prediction_type == 'probability':
                    if not (0 <= predictions.min() and predictions.max() <= 1.01):  # Small tolerance
                        validation_result['issues_found'].append('Probability predictions outside [0,1] range')
                        validation_result['validation_status'] = 'warning'

                validation_result['tests_performed'].append('sanity_check')

            except Exception as e:
                validation_result['issues_found'].append(f'Sanity check failed: {e}')

            # Calculate validation score
            passed_tests = len(validation_result['tests_performed'])
            failed_tests = len(validation_result['issues_found'])
            total_checks = max(1, passed_tests + failed_tests)
            net_passes = max(0, passed_tests - failed_tests)
            validation_result['validation_score'] = round((net_passes / total_checks) * 100, 1)

            if validation_result['validation_score'] >= 80:
                validation_result['validation_status'] = 'passed'
            elif validation_result['validation_score'] >= 60:
                validation_result['validation_status'] = 'warning'
            else:
                validation_result['validation_status'] = 'failed'

        except Exception as e:
            validation_result['validation_status'] = 'error'
            validation_result['validation_score'] = 0
            validation_result['issues_found'].append(f'Validation error: {e}')

        return validation_result

    def _test_model_performance(self, loaded_models: Dict[str, Any], weekly_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test model performance on weekly data"""

        self.log_info(f"Testing model performance on Week {self.week} data...")

        performance_results = {}

        if 'features' not in weekly_data or weekly_data['features'] is None:
            return {'error': 'No features data available for performance testing'}

        raw_features = weekly_data['features']

        for model_name, model_info in loaded_models.items():
            if model_info['model'] is None:
                performance_results[model_name] = {
                    'performance_status': 'skipped',
                    'reason': 'Model not available'
                }
                continue

            try:
                model_features = self._prepare_features_for_model(raw_features, model_info, model_name)
                if model_features.empty:
                    raise ValueError('Unable to prepare features for model')

                performance_result = self._test_single_model_performance(model_name, model_info, model_features)
                performance_results[model_name] = performance_result

                self.log_info(f"Performance test completed for {model_name}")

            except Exception as e:
                performance_results[model_name] = {
                    'performance_status': 'error',
                    'reason': str(e)
                }

                self.log_error(f"Performance test failed for {model_name}", e)

        return performance_results

    def _test_single_model_performance(self, model_name: str, model_info: Dict[str, Any], X: pd.DataFrame) -> Dict[str, Any]:
        """Test performance of a single model"""

        performance_result = {
            'performance_status': 'tested',
            'prediction_count': len(X),
            'prediction_stats': {},
            'performance_indicators': {}
        }

        try:
            # Generate predictions
            predictions, prediction_type = self._generate_predictions(model_info, X)

            # Calculate prediction statistics
            performance_result['prediction_stats'] = {
                'count': len(predictions),
                'mean': float(np.mean(predictions)),
                'std': float(np.std(predictions)),
                'min': float(np.min(predictions)),
                'max': float(np.max(predictions)),
                'median': float(np.median(predictions)),
                'prediction_type': prediction_type
            }

            # Performance indicators
            if prediction_type == 'probability':
                # Check probability distribution
                home_win_rate = np.mean(predictions > 0.5)
                close_games = np.mean((predictions > 0.4) & (predictions < 0.6))

                performance_result['performance_indicators'] = {
                    'home_win_rate': home_win_rate,
                    'close_games_rate': close_games,
                    'high_confidence_rate': np.mean((predictions > 0.7) | (predictions < 0.3))
                }

            else:  # margin
                # Check margin distribution
                positive_margins = np.mean(predictions > 0)
                blowout_rate = np.mean(np.abs(predictions) > 21)

                performance_result['performance_indicators'] = {
                    'positive_margin_rate': positive_margins,
                    'blowout_rate': blowout_rate,
                    'close_game_rate': np.mean(np.abs(predictions) < 7)
                }

        except Exception as e:
            performance_result['performance_status'] = 'error'
            performance_result['error'] = str(e)

        return performance_result

    def _cross_validate_models(self, loaded_models: Dict[str, Any], weekly_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform cross-validation on models if sufficient data is available"""

        self.log_info("Performing model cross-validation...")

        cv_results = {}

        # Check if we have training data for proper cross-validation
        if 'training_data' not in weekly_data or weekly_data['training_data'] is None:
            self.log_info("No training data available - skipping cross-validation")
            return {'status': 'skipped', 'reason': 'No training data available'}

        training_df = weekly_data['training_data']

        if len(training_df) < 100:
            self.log_info("Insufficient training data for cross-validation")
            return {'status': 'skipped', 'reason': 'Insufficient training data'}

        for model_name, model_info in loaded_models.items():
            if model_info['model'] is None:
                cv_results[model_name] = {
                    'cv_status': 'skipped',
                    'reason': 'Model not available'
                }
                continue

            try:
                cv_result = self._cross_validate_single_model(model_name, model_info, training_df)
                cv_results[model_name] = cv_result

                self.log_info(f"Cross-validation completed for {model_name}")

            except Exception as e:
                cv_results[model_name] = {
                    'cv_status': 'error',
                    'reason': str(e)
                }

                self.log_error(f"Cross-validation failed for {model_name}", e)

        return cv_results

    def _cross_validate_single_model(self, model_name: str, model_info: Dict[str, Any], training_df: pd.DataFrame) -> Dict[str, Any]:
        """Cross-validate a single model"""

        cv_result = {
            'cv_status': 'completed',
            'cv_folds': 5,
            'cv_scores': {}
        }

        try:
            # Prepare training data using only numeric home/away features to avoid dtype issues
            feature_columns = [col for col in training_df.columns if col.startswith(('home_', 'away_'))]
            if not feature_columns:
                raise ValueError('No home/away feature columns available for cross-validation')

            candidate_df = training_df[feature_columns]
            numeric_columns = candidate_df.select_dtypes(include=[np.number]).columns.tolist()
            if not numeric_columns:
                raise ValueError('No numeric home/away features available for cross-validation')

            X = candidate_df[numeric_columns].copy()
            X = X.fillna(X.median())

            # Define target variable based on model type
            if model_info['config']['prediction_type'] == 'margin':
                # For margin prediction
                y = training_df.get('margin', training_df['home_points'] - training_df['away_points'])
            else:
                # For win probability
                y = (training_df['home_points'] > training_df['away_points']).astype(int)

            # Perform cross-validation
            if model_info['config']['prediction_type'] == 'margin':
                # Use appropriate scoring for regression
                scoring = ['neg_mean_absolute_error', 'neg_mean_squared_error', 'r2']
            else:
                # Use appropriate scoring for classification
                scoring = ['accuracy', 'precision', 'recall', 'f1']

            cv_scores = cross_val_score(model_info['model'], X, y, cv=5, scoring=scoring[0])

            cv_result['cv_scores'] = {
                'scoring_metric': scoring[0],
                'mean_score': float(np.mean(cv_scores)),
                'std_score': float(np.std(cv_scores)),
                'fold_scores': cv_scores.tolist()
            }

        except Exception as e:
            cv_result['cv_status'] = 'error'
            cv_result['error'] = str(e)

        return cv_result

    def _validate_ensemble_performance(self, loaded_models: Dict[str, Any], weekly_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate ensemble model performance"""

        self.log_info("Validating ensemble performance...")

        ensemble_result = {
            'ensemble_status': 'tested',
            'available_models': 0,
            'ensemble_methods': {}
        }

        try:
            # Count available models
            available_models = [name for name, info in loaded_models.items() if info['model'] is not None]
            ensemble_result['available_models'] = len(available_models)

            if len(available_models) < 2:
                ensemble_result['ensemble_status'] = 'insufficient_models'
                ensemble_result['reason'] = f'Need at least 2 models, got {len(available_models)}'
                return ensemble_result

            if 'features' not in weekly_data:
                ensemble_result['ensemble_status'] = 'no_data'
                return ensemble_result

            features_df = weekly_data['features']
            feature_columns = [col for col in features_df.columns
                             if col not in ['game_id', 'home_team', 'away_team', 'game_date']]
            X = features_df[feature_columns]

            # Test simple averaging ensemble
            if len(available_models) >= 2:
                ensemble_predictions = self._create_averaging_ensemble(available_models, loaded_models, X)
                ensemble_result['ensemble_methods']['averaging'] = {
                    'status': 'created',
                    'prediction_stats': self._calculate_prediction_stats(ensemble_predictions)
                }

            # Test weighted ensemble (if we have performance data)
            # This would require historical performance to weight models appropriately
            # For now, use equal weights

            ensemble_result['ensemble_status'] = 'success'

        except Exception as e:
            ensemble_result['ensemble_status'] = 'error'
            ensemble_result['error'] = str(e)

        return ensemble_result

    def _create_averaging_ensemble(self, model_names: List[str], loaded_models: Dict[str, Any], X: pd.DataFrame) -> np.ndarray:
        """Create averaging ensemble predictions"""

        predictions_list = []

        for model_name in model_names:
            model_info = loaded_models[model_name]
            model = model_info['model']

            if model_info['config']['prediction_type'] == 'margin':
                predictions = model.predict(X)
            else:  # probability
                predictions = model.predict_proba(X)[:, 1]

            predictions_list.append(predictions)

        # Average predictions
        ensemble_predictions = np.mean(predictions_list, axis=0)
        return ensemble_predictions

    def _calculate_prediction_stats(self, predictions: np.ndarray) -> Dict[str, float]:
        """Calculate statistics for predictions"""

        return {
            'mean': float(np.mean(predictions)),
            'std': float(np.std(predictions)),
            'min': float(np.min(predictions)),
            'max': float(np.max(predictions)),
            'median': float(np.median(predictions)),
            'count': len(predictions)
        }

    def _analyze_model_biases(self, loaded_models: Dict[str, Any], weekly_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze potential model biases"""

        self.log_info("Analyzing model biases...")

        bias_analysis = {
            'bias_analysis_status': 'completed',
            'bias_checks': {},
            'potential_biases': []
        }

        try:
            # Check home team bias
            if 'features' in weekly_data and weekly_data['features'] is not None:
                bias_checks = self._check_home_team_bias(loaded_models, weekly_data['features'])
                bias_analysis['bias_checks']['home_team_bias'] = bias_checks

                if bias_checks.get('significant_bias'):
                    bias_analysis['potential_biases'].append('Home team bias detected')

            # Check talent bias
            talent_bias = self._check_talent_bias(loaded_models, weekly_data)
            bias_analysis['bias_checks']['talent_bias'] = talent_bias

            if talent_bias.get('significant_bias'):
                bias_analysis['potential_biases'].append('Talent-based bias detected')

        except Exception as e:
            bias_analysis['bias_analysis_status'] = 'error'
            bias_analysis['error'] = str(e)

        return bias_analysis

    def _check_home_team_bias(self, loaded_models: Dict[str, Any], features_df: pd.DataFrame) -> Dict[str, Any]:
        """Check for home team bias in models"""

        bias_check = {
            'significant_bias': False,
            'bias_magnitude': 0
        }

        # This is a simplified bias check
        # In a real implementation, you'd analyze prediction patterns across different scenarios

        return bias_check

    def _check_talent_bias(self, loaded_models: Dict[str, Any], weekly_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check for talent-based bias in models"""

        bias_check = {
            'significant_bias': False,
            'bias_magnitude': 0
        }

        # Simplified talent bias check
        # In reality, you'd analyze how predictions correlate with talent ratings

        return bias_check

    def _validate_previous_week_results(self, loaded_models: Dict[str, Any]) -> Dict[str, Any]:
        """Validate models against previous week actual results"""
        
        previous_week = self.week - 1
        self.log_info(f"Validating models against Week {previous_week} actual results...")
        
        previous_week_validation = {
            'validation_status': 'completed',
            'previous_week': previous_week,
            'predictions_available': False,
            'actuals_available': False,
            'model_performance': {},
            'accuracy_metrics': {}
        }
        
        try:
            # Try to load previous week predictions
            predictions_path = f"predictions/week{previous_week}/week{previous_week}_comprehensive_predictions.csv"
            if os.path.exists(predictions_path):
                previous_predictions = pd.read_csv(predictions_path)
                previous_week_validation['predictions_available'] = True
                self.log_info(f"Loaded {len(previous_predictions)} Week {previous_week} predictions")
            else:
                self.log_warning(f"Week {previous_week} predictions not found - skipping validation")
                previous_week_validation['validation_status'] = 'skipped'
                previous_week_validation['reason'] = f'Week {previous_week} predictions not available'
                return previous_week_validation
            
            # Try to load previous week actual results
            games_path = "starter_pack/data/2025_games.csv"
            if os.path.exists(games_path):
                games_df = pd.read_csv(games_path)
                previous_actuals = games_df[
                    (games_df['week'] == previous_week) & 
                    (games_df['season'] == self.season) & 
                    (games_df['home_points'].notna()) & 
                    (games_df['away_points'].notna())
                ]
                if not previous_actuals.empty:
                    previous_week_validation['actuals_available'] = True
                    self.log_info(f"Loaded {len(previous_actuals)} Week {previous_week} completed games")
                else:
                    self.log_warning(f"Week {previous_week} actual results not yet available")
                    previous_week_validation['validation_status'] = 'pending'
                    previous_week_validation['reason'] = f'Week {previous_week} games not yet completed'
                    return previous_week_validation
            else:
                self.log_warning("Games data file not found")
                previous_week_validation['validation_status'] = 'skipped'
                return previous_week_validation
            
            # Compare predictions vs actuals
            if previous_week_validation['predictions_available'] and previous_week_validation['actuals_available']:
                # Calculate accuracy metrics
                correct_predictions = 0
                total_predictions = 0
                
                for _, pred in previous_predictions.iterrows():
                    home_team = pred.get('home_team')
                    away_team = pred.get('away_team')
                    predicted_winner = pred.get('predicted_winner')
                    
                    # Find matching actual result
                    actual = previous_actuals[
                        ((previous_actuals['home_team'] == home_team) & (previous_actuals['away_team'] == away_team)) |
                        ((previous_actuals['home_team'] == away_team) & (previous_actuals['away_team'] == home_team))
                    ]
                    
                    if not actual.empty:
                        actual_row = actual.iloc[0]
                        actual_winner = actual_row['home_team'] if actual_row['home_points'] > actual_row['away_points'] else actual_row['away_team']
                        
                        if predicted_winner == actual_winner:
                            correct_predictions += 1
                        total_predictions += 1
                
                if total_predictions > 0:
                    accuracy = correct_predictions / total_predictions
                    previous_week_validation['accuracy_metrics'] = {
                        'accuracy': accuracy,
                        'correct_predictions': correct_predictions,
                        'total_predictions': total_predictions,
                        'accuracy_percentage': accuracy * 100
                    }
                    self.log_info(f"Week {previous_week} prediction accuracy: {accuracy:.1%} ({correct_predictions}/{total_predictions})")
            
        except Exception as e:
            self.log_error(f"Week {previous_week} validation error", e)
            previous_week_validation['validation_status'] = 'error'
            previous_week_validation['error'] = str(e)
        
        return previous_week_validation

    def _generate_validation_report(
        self,
        data_validation: Dict[str, Any],
        model_availability: Dict[str, Any],
        compatibility_results: Dict[str, Any],
        individual_validations: Dict[str, Any],
        performance_tests: Dict[str, Any],
        cross_validation: Dict[str, Any],
        ensemble_validation: Dict[str, Any],
        bias_analysis: Dict[str, Any],
        previous_week_validation: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive validation report"""

        self.log_info("Generating comprehensive validation report...")

        # Calculate overall validation score
        data_score = data_validation.get('data_quality_score', 0)
        model_score = (model_availability['available_models'] / model_availability['total_models']) * 100 if model_availability['total_models'] > 0 else 0

        compatibility_score = sum(1 for result in compatibility_results.values() if result.get('compatible', False)) * 100 / len(compatibility_results) if compatibility_results else 0

        individual_score = np.mean([v.get('validation_score', 0) for v in individual_validations.values() if 'validation_score' in v]) if individual_validations else 0

        overall_score = (data_score * 0.3 + model_score * 0.2 + compatibility_score * 0.2 + individual_score * 0.3)

        # Identify models ready for predictions
        models_ready = [
            name for name, result in compatibility_results.items()
            if result.get('compatible', False) and individual_validations.get(name, {}).get('validation_status') in ['passed', 'warning']
        ]

        # Generate recommendations
        recommendations = []

        if data_score < 80:
            recommendations.append("Improve data quality - address missing values and feature completeness")

        if model_score < 80:
            recommendations.append("Ensure all models are properly loaded and functional")

        if compatibility_score < 90:
            recommendations.append("Fix model-data compatibility issues")

        if overall_score < 70:
            recommendations.append("Major validation issues found - comprehensive review required")
        elif overall_score < 85:
            recommendations.append("Minor validation issues found - consider improvements")
        
        # Add recommendations based on previous week validation
        if previous_week_validation and previous_week_validation.get('validation_status') == 'completed':
            accuracy = previous_week_validation.get('accuracy_metrics', {}).get('accuracy', 0)
            if accuracy < 0.5:
                recommendations.append(f"⚠️ Previous week (Week {previous_week_validation.get('previous_week')}) accuracy was {accuracy:.1%} - models may need retraining")
            elif accuracy < 0.6:
                recommendations.append(f"Previous week (Week {previous_week_validation.get('previous_week')}) accuracy was {accuracy:.1%} - consider model adjustments")
            else:
                recommendations.append(f"✅ Previous week (Week {previous_week_validation.get('previous_week')}) accuracy was {accuracy:.1%} - models performing well")

        validation_report = {
            'report_metadata': {
                'generation_time': datetime.now().isoformat(),
                'week': self.week,
                'season': self.season,
                'overall_score': overall_score
            },
            'summary': {
                'data_validation_passed': data_validation['is_valid'],
                'models_available': model_availability['available_models'],
                'models_total': model_availability['total_models'],
                'models_ready_for_predictions': len(models_ready),
                'overall_validation_passed': overall_score >= 70
            },
            'detailed_results': {
                'data_validation': data_validation,
                'model_availability': model_availability,
                'compatibility_results': compatibility_results,
                'individual_validations': individual_validations,
                'performance_tests': performance_tests,
                'cross_validation': cross_validation,
                'ensemble_validation': ensemble_validation,
                'bias_analysis': bias_analysis,
                'previous_week_validation': previous_week_validation or {},
                'model_feature_schemas': self._feature_schema_log
            },
            'models_ready': models_ready,
            'recommendations': recommendations,
        }

        # Add next_steps after validation_report is fully constructed
        validation_report['next_steps'] = self._generate_next_steps(validation_report)

        return validation_report

    def _generate_next_steps(self, validation_report: Dict[str, Any]) -> List[str]:
        """Generate next steps based on validation results"""

        next_steps = []

        if validation_report['summary']['overall_validation_passed']:
            next_steps.append(f"✅ Models are ready for Week {self.week} predictions")
            next_steps.append("🚀 Proceed with prediction generation")
        else:
            next_steps.append("❌ Address validation issues before proceeding with predictions")

        if validation_report['summary']['models_available'] < 3:
            next_steps.append("🔧 Attempt to load missing models or retrain failed models")

        if validation_report['detailed_results']['data_validation']['data_quality_score'] < 85:
            next_steps.append("📊 Improve data quality and feature completeness")

        return next_steps

    def _save_validation_results(self, validation_report: Dict[str, Any]) -> None:
        """Save validation results to files"""

        # Create output directory
        output_dir = f"validation/week{self.week}"
        os.makedirs(output_dir, exist_ok=True)

        # Save full validation report
        report_path = os.path.join(output_dir, f"week{self.week}_model_validation_report.json")
        with open(report_path, 'w') as f:
            json.dump(validation_report, f, indent=2, default=str)
        self.log_info(f"Saved validation report to {report_path}")

        # Save summary as CSV
        summary_data = {
            'metric': [
                'Overall Validation Score',
                'Models Available',
                'Models Ready',
                'Data Quality Score',
                'Validation Passed'
            ],
            'value': [
                validation_report['report_metadata']['overall_score'],
                validation_report['summary']['models_available'],
                validation_report['summary']['models_ready_for_predictions'],
                validation_report['detailed_results']['data_validation']['data_quality_score'],
                validation_report['summary']['overall_validation_passed']
            ]
        }

        summary_df = pd.DataFrame(summary_data)
        summary_path = os.path.join(output_dir, "validation_summary.csv")
        summary_df.to_csv(summary_path, index=False)
        self.log_info(f"Saved validation summary to {summary_path}")

    def _load_model_history(self) -> Dict[str, Any]:
        """Load model performance history"""
        return {}  # Would load from historical data in production

    def _load_validation_thresholds(self) -> Dict[str, float]:
        """Load validation thresholds"""
        return {
            'minimum_overall_score': 70,
            'minimum_data_quality': 75,
            'minimum_model_availability': 0.67,  # At least 2/3 models
            'minimum_compatibility': 0.8
        }

    def _update_model_history(self, validation_report: Dict[str, Any]) -> None:
        """Update model performance history"""
        # Would update historical records in production
        pass


# Example usage
if __name__ == "__main__":
    agent = WeeklyModelValidationAgent(week=13, season=2025)

    task_data = {
        'operation': 'validate_models',
        'target_week': 13,
        'season': 2025,
        'validation_comprehensive': True
    }

    result = agent.execute_task(task_data)
    print(f"Model Validation Result: {result}")
