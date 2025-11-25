#!/usr/bin/env python3
"""
Automated Hyperparameter Tuning for Model Pack

Provides hyperparameter optimization for:
- Ridge Regression (alpha parameter)
- XGBoost (learning_rate, max_depth, n_estimators, subsample)
- FastAI (learning rate, layer sizes, dropout)

Uses Optuna or scikit-learn's GridSearchCV for optimization.

Author: Model Pack Improvement Plan
Created: 2025-11-19
"""

import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
import pandas as pd
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class HyperparameterResults:
    """Results from hyperparameter tuning"""
    best_params: Dict[str, Any]
    best_score: float
    cv_scores: List[float]
    tuning_method: str


class HyperparameterTuner:
    """Automated hyperparameter tuning for ML models"""
    
    def __init__(self, use_optuna: bool = False):
        """
        Initialize hyperparameter tuner.
        
        Args:
            use_optuna: If True, use Optuna for optimization (requires optuna package)
        """
        self.use_optuna = use_optuna
        self.results = {}
        
        # Check if Optuna is available
        if use_optuna:
            try:
                import optuna
                self.optuna_available = True
            except ImportError:
                logger.warning("Optuna not available - falling back to GridSearchCV")
                self.optuna_available = False
                self.use_optuna = False
        else:
            self.optuna_available = False
    
    def tune_ridge(self, X_train: pd.DataFrame, y_train: pd.Series, 
                   cv_folds: int = 5) -> HyperparameterResults:
        """
        Tune Ridge regression hyperparameters.
        
        Args:
            X_train: Training features
            y_train: Training target
            cv_folds: Number of cross-validation folds
            
        Returns:
            HyperparameterResults with best parameters
        """
        from sklearn.linear_model import Ridge
        from sklearn.model_selection import GridSearchCV
        
        logger.info("Tuning Ridge regression hyperparameters...")
        
        # Parameter grid for Ridge
        param_grid = {
            'alpha': [0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
        }
        
        # Use negative MAE as scoring (GridSearchCV maximizes)
        from sklearn.metrics import make_scorer, mean_absolute_error
        mae_scorer = make_scorer(mean_absolute_error, greater_is_better=False)
        
        model = Ridge()
        grid_search = GridSearchCV(
            model,
            param_grid,
            cv=cv_folds,
            scoring=mae_scorer,
            n_jobs=-1,
            verbose=1
        )
        
        grid_search.fit(X_train, y_train)
        
        results = HyperparameterResults(
            best_params=grid_search.best_params_,
            best_score=-grid_search.best_score_,  # Convert back to positive MAE
            cv_scores=[-score for score in grid_search.cv_results_['mean_test_score']],
            tuning_method='GridSearchCV'
        )
        
        logger.info(f"Best Ridge alpha: {results.best_params['alpha']}, MAE: {results.best_score:.3f}")
        return results
    
    def tune_xgboost(self, X_train: pd.DataFrame, y_train: pd.Series,
                     cv_folds: int = 3, use_optuna: Optional[bool] = None) -> HyperparameterResults:
        """
        Tune XGBoost classifier hyperparameters.
        
        Args:
            X_train: Training features
            y_train: Training target
            cv_folds: Number of cross-validation folds
            use_optuna: Override instance setting for this call
            
        Returns:
            HyperparameterResults with best parameters
        """
        import xgboost as xgb
        from sklearn.model_selection import StratifiedKFold
        
        logger.info("Tuning XGBoost hyperparameters...")
        
        use_optuna = use_optuna if use_optuna is not None else (self.use_optuna and self.optuna_available)
        
        if use_optuna:
            return self._tune_xgboost_optuna(X_train, y_train, cv_folds)
        else:
            return self._tune_xgboost_gridsearch(X_train, y_train, cv_folds)
    
    def _tune_xgboost_gridsearch(self, X_train: pd.DataFrame, y_train: pd.Series,
                                  cv_folds: int) -> HyperparameterResults:
        """Tune XGBoost using GridSearchCV"""
        import xgboost as xgb
        from sklearn.model_selection import GridSearchCV, StratifiedKFold
        
        # Reduced parameter grid for faster tuning
        param_grid = {
            'learning_rate': [0.05, 0.1, 0.15],
            'max_depth': [4, 5, 6],
            'n_estimators': [100, 200],
            'subsample': [0.8, 0.9, 1.0],
        }
        
        model = xgb.XGBClassifier(
            eval_metric='logloss',
            random_state=77,
            use_label_encoder=False,
            tree_method='hist'
        )
        
        cv = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=77)
        grid_search = GridSearchCV(
            model,
            param_grid,
            cv=cv,
            scoring='roc_auc',
            n_jobs=-1,
            verbose=1
        )
        
        grid_search.fit(X_train, y_train)
        
        results = HyperparameterResults(
            best_params=grid_search.best_params_,
            best_score=grid_search.best_score_,
            cv_scores=grid_search.cv_results_['mean_test_score'].tolist(),
            tuning_method='GridSearchCV'
        )
        
        logger.info(f"Best XGBoost params: {results.best_params}, AUC: {results.best_score:.3f}")
        return results
    
    def _tune_xgboost_optuna(self, X_train: pd.DataFrame, y_train: pd.Series,
                             cv_folds: int) -> HyperparameterResults:
        """Tune XGBoost using Optuna"""
        import optuna
        import xgboost as xgb
        from sklearn.model_selection import cross_val_score, StratifiedKFold
        
        def objective(trial):
            params = {
                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                'max_depth': trial.suggest_int('max_depth', 3, 8),
                'n_estimators': trial.suggest_int('n_estimators', 50, 500),
                'subsample': trial.suggest_float('subsample', 0.6, 1.0),
                'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
                'eval_metric': 'logloss',
                'random_state': 77,
                'use_label_encoder': False,
                'tree_method': 'hist'
            }
            
            model = xgb.XGBClassifier(**params)
            cv = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=77)
            scores = cross_val_score(model, X_train, y_train, cv=cv, scoring='roc_auc')
            return scores.mean()
        
        study = optuna.create_study(direction='maximize')
        study.optimize(objective, n_trials=20)  # Can increase for better results
        
        results = HyperparameterResults(
            best_params=study.best_params,
            best_score=study.best_value,
            cv_scores=[trial.value for trial in study.trials if trial.value is not None],
            tuning_method='Optuna'
        )
        
        logger.info(f"Best XGBoost params (Optuna): {results.best_params}, AUC: {results.best_score:.3f}")
        return results
    
    def tune_fastai(self, dls, n_trials: int = 10) -> HyperparameterResults:
        """
        Tune FastAI neural network hyperparameters.
        
        Args:
            dls: FastAI DataLoaders
            n_trials: Number of optimization trials
            
        Returns:
            HyperparameterResults with best parameters
        """
        try:
            from fastai.tabular.all import tabular_learner, accuracy, RocAucBinary
        except ImportError:
            logger.error("FastAI not available for hyperparameter tuning")
            return HyperparameterResults(
                best_params={},
                best_score=0.0,
                cv_scores=[],
                tuning_method='N/A'
            )
        
        logger.info("Tuning FastAI hyperparameters...")
        
        # Simple grid search for FastAI (more complex tuning would require Optuna)
        best_score = 0.0
        best_params = {}
        cv_scores = []
        
        # Test different layer configurations
        layer_configs = [
            [200, 100],
            [300, 150],
            [400, 200],
            [200, 100, 50],
        ]
        
        learning_rates = [1e-3, 5e-3, 1e-2]
        
        for layers in layer_configs:
            for lr in learning_rates:
                try:
                    learn = tabular_learner(
                        dls,
                        layers=layers,
                        metrics=[accuracy, RocAucBinary()]
                    )
                    
                    # Quick training for evaluation
                    learn.fit_one_cycle(2, lr_max=lr)
                    
                    # Evaluate
                    preds, targs = learn.get_preds()
                    from sklearn.metrics import roc_auc_score
                    auc = roc_auc_score(targs.numpy(), preds[:, 1].numpy())
                    cv_scores.append(auc)
                    
                    if auc > best_score:
                        best_score = auc
                        best_params = {
                            'layers': layers,
                            'learning_rate': lr,
                            'n_epochs': 4  # Default
                        }
                except Exception as e:
                    logger.warning(f"FastAI tuning trial failed: {e}")
                    continue
        
        results = HyperparameterResults(
            best_params=best_params,
            best_score=best_score,
            cv_scores=cv_scores,
            tuning_method='GridSearch'
        )
        
        logger.info(f"Best FastAI params: {results.best_params}, AUC: {results.best_score:.3f}")
        return results
    
    def save_best_params(self, model_name: str, results: HyperparameterResults, 
                        output_dir: Optional[Path] = None):
        """
        Save best hyperparameters to JSON file.
        
        Args:
            model_name: Name of the model (ridge, xgboost, fastai)
            results: HyperparameterResults object
            output_dir: Directory to save parameters (defaults to model_pack/)
        """
        if output_dir is None:
            output_dir = Path(__file__).parent.parent
        
        output_file = output_dir / f"{model_name}_best_params.json"
        
        # Prepare data for JSON serialization
        params_data = {
            'best_params': results.best_params,
            'best_score': float(results.best_score),
            'tuning_method': results.tuning_method,
            'cv_scores_mean': float(np.mean(results.cv_scores)) if results.cv_scores else 0.0,
            'cv_scores_std': float(np.std(results.cv_scores)) if results.cv_scores else 0.0,
        }
        
        with open(output_file, 'w') as f:
            json.dump(params_data, f, indent=2)
        
        logger.info(f"Saved best parameters to {output_file}")
    
    def load_best_params(self, model_name: str, 
                         input_dir: Optional[Path] = None) -> Optional[Dict[str, Any]]:
        """
        Load best hyperparameters from JSON file.
        
        Args:
            model_name: Name of the model
            input_dir: Directory to load from (defaults to model_pack/)
            
        Returns:
            Dictionary of best parameters or None if file doesn't exist
        """
        if input_dir is None:
            input_dir = Path(__file__).parent.parent
        
        input_file = input_dir / f"{model_name}_best_params.json"
        
        if not input_file.exists():
            return None
        
        with open(input_file, 'r') as f:
            data = json.load(f)
        
        return data.get('best_params')


def main():
    """Example usage of hyperparameter tuner"""
    print("Hyperparameter Tuner - Example Usage")
    print("=" * 60)
    print("This module provides hyperparameter tuning for:")
    print("- Ridge Regression")
    print("- XGBoost Classifier")
    print("- FastAI Neural Network")
    print("\nImport and use HyperparameterTuner class in your training scripts.")


if __name__ == "__main__":
    main()

