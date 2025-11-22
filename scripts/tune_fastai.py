#!/usr/bin/env python3
"""
FastAI Hyperparameter Tuning using Optuna

This script uses Optuna to find optimal hyperparameters for the FastAI neural network model.
It optimizes for validation accuracy on the home win prediction task.

Author: Script Ohio 2.0 Agent
Created: 2025-11-19
"""

import logging
import sys
import json
from pathlib import Path
import pandas as pd
import numpy as np

# Add project paths
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

# Import feature definitions
try:
    from project_management.TOOLS_AND_CONFIG.model_features import RIDGE_FEATURES, XGB_FEATURES
except ImportError:
    # Fallback if direct import fails
    sys.path.append(str(PROJECT_ROOT / "project_management" / "TOOLS_AND_CONFIG"))
    from model_features import RIDGE_FEATURES, XGB_FEATURES

# Import data manager
try:
    from scripts.data_manager import DataManager
except ImportError:
    # Fallback if running from different location
    sys.path.append(str(PROJECT_ROOT / 'scripts'))
    from data_manager import DataManager

# Check if FastAI is available
try:
    from fastai.tabular.all import (
        TabularDataLoaders, Categorify, FillMissing, Normalize,
        tabular_learner, accuracy, RocAucBinary, RandomSplitter
    )
    FASTAI_AVAILABLE = True
except ImportError:
    FASTAI_AVAILABLE = False
    print("⚠️ FastAI not available. Please install: pip install fastai")
    sys.exit(1)

# Check if Optuna is available
try:
    import optuna
    from optuna.samplers import TPESampler
    OPTUNA_AVAILABLE = True
except ImportError:
    OPTUNA_AVAILABLE = False
    print("⚠️ Optuna not available. Please install: pip install optuna")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Suppress FastAI warnings
import warnings
warnings.filterwarnings('ignore')


def load_training_data():
    """Load training data using DataManager."""
    logger.info("📁 Loading training data...")
    dm = DataManager()
    df = dm.load_training_data()
    
    # Calculate home_win if missing
    if 'home_win' not in df.columns and 'home_points' in df.columns and 'away_points' in df.columns:
        # Ensure points are numeric
        df['home_points'] = pd.to_numeric(df['home_points'], errors='coerce')
        df['away_points'] = pd.to_numeric(df['away_points'], errors='coerce')
        # Drop games without scores
        df = df.dropna(subset=['home_points', 'away_points'])
        # Calculate result
        df['home_win'] = (df['home_points'] > df['away_points']).astype(int)
    
    # Filter to games with outcomes
    df = df.dropna(subset=['home_win'])
    
    logger.info(f"✅ Loaded {len(df)} games with outcomes")
    return df


def create_objective_function(train_df, cat_features, cont_features):
    """Create Optuna objective function for FastAI hyperparameter tuning.
    
    Args:
        train_df: Training dataframe
        cat_features: List of categorical feature names
        cont_features: List of continuous feature names
        
    Returns:
        Objective function for Optuna
    """
    
    def objective(trial):
        """Optuna objective function to minimize validation loss."""
        
        # Suggest hyperparameters
        n_epochs = trial.suggest_int('n_epochs', 3, 10)
        batch_size = trial.suggest_categorical('batch_size', [32, 64, 128])
        lr = trial.suggest_float('learning_rate', 1e-4, 1e-2, log=True)
        
        # Layer architecture
        n_layers = trial.suggest_int('n_layers', 2, 4)
        layer_sizes = []
        for i in range(n_layers):
            if i == 0:
                size = trial.suggest_int(f'layer_{i}_size', 200, 800, step=100)
            else:
                # Each subsequent layer should be smaller
                max_size = layer_sizes[-1]
                size = trial.suggest_int(f'layer_{i}_size', 100, max_size, step=50)
            layer_sizes.append(size)
        
        # Dropout
        dropout = trial.suggest_float('dropout', 0.1, 0.5, step=0.1)
        
        try:
            # Create validation split
            splitter = RandomSplitter(valid_pct=0.2, seed=42)
            train_idx, valid_idx = splitter(train_df)
            
            # Create DataLoaders
            dls = TabularDataLoaders.from_df(
                train_df,
                procs=[Categorify, FillMissing, Normalize],
                cat_names=cat_features,
                cont_names=cont_features,
                y_names='home_win',
                valid_idx=valid_idx,
                bs=batch_size
            )
            
            # Create learner with suggested architecture
            learn = tabular_learner(
                dls,
                metrics=[accuracy, RocAucBinary()],
                layers=layer_sizes,
                config={'ps': dropout}  # Dropout probability
            )
            
            # Train model
            learn.fit_one_cycle(n_epochs, lr)
            
            # Get validation metrics
            val_loss = learn.validate()[0]
            
            # Return validation loss (Optuna minimizes)
            return float(val_loss)
            
        except Exception as e:
            logger.warning(f"Trial failed: {e}")
            # Return a large value to indicate failure
            return float('inf')
    
    return objective


def main():
    """Main function to run FastAI hyperparameter tuning."""
    logger.info("🚀 Starting FastAI Hyperparameter Tuning with Optuna")
    logger.info("=" * 80)
    
    # Load data
    df = load_training_data()
    
    # Define features (matching the retrain script exactly)
    cat_features = ['week', 'home_conference', 'away_conference', 'neutral_site']
    
    # Continuous features - use the same set as retrain script
    cont_features = sorted(list(set(RIDGE_FEATURES + XGB_FEATURES)))
    
    # Ensure all features exist
    for col in cat_features + cont_features:
        if col not in df.columns:
            logger.warning(f"⚠️ Feature {col} not found, adding with default values")
            if col in cat_features:
                df[col] = 'Unknown'
            else:
                df[col] = 0.0
    
    # Filter to rows with all features
    df = df.dropna(subset=cat_features + cont_features + ['home_win'])
    logger.info(f"📊 Training on {len(df)} games with complete features")
    
    # Create objective function
    objective = create_objective_function(df, cat_features, cont_features)
    
    # Create Optuna study
    logger.info("🔍 Creating Optuna study...")
    study = optuna.create_study(
        direction='minimize',
        sampler=TPESampler(seed=42),
        study_name='fastai_hyperparameter_tuning'
    )
    
    # Run optimization
    n_trials = 5
    logger.info(f"🏃 Running {n_trials} optimization trials...")
    logger.info("This may take a while...")
    
    study.optimize(objective, n_trials=n_trials, show_progress_bar=True)
    
    # Get best parameters
    best_params = study.best_params
    best_value = study.best_value
    
    logger.info("=" * 80)
    logger.info("🎉 Optimization Complete!")
    logger.info(f"Best validation loss: {best_value:.4f}")
    logger.info("Best hyperparameters:")
    for param, value in best_params.items():
        logger.info(f"  {param}: {value}")
    
    # Save best parameters
    output_path = PROJECT_ROOT / 'model_pack' / 'fastai_best_params.json'
    output_path.parent.mkdir(exist_ok=True)
    
    # Format layer sizes as list
    n_layers = best_params['n_layers']
    layer_sizes = [best_params[f'layer_{i}_size'] for i in range(n_layers)]
    
    params_to_save = {
        'n_epochs': best_params['n_epochs'],
        'batch_size': best_params['batch_size'],
        'learning_rate': best_params['learning_rate'],
        'layers': layer_sizes,
        'dropout': best_params['dropout'],
        'best_validation_loss': best_value,
        'n_trials': n_trials,
        'optimization_date': pd.Timestamp.now().isoformat()
    }
    
    with open(output_path, 'w') as f:
        json.dump(params_to_save, f, indent=2)
    
    logger.info(f"💾 Saved best parameters to: {output_path}")
    logger.info("=" * 80)
    logger.info("✅ You can now retrain the FastAI model with these optimized parameters")
    
    return params_to_save


if __name__ == '__main__':
    best_params = main()
