"""
Random Forest Score Predictor.
Based on model_pack/02_random_forest_team_points.ipynb.
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
import joblib
from typing import List, Dict, Tuple, Optional, Union
from pathlib import Path

class RandomForestScorePredictor:
    """
    Random Forest model for predicting home and away points.
    Uses two separate regressors for home and away scores.
    """
    
    DEFAULT_FEATURES = [
        'home_adjusted_success', 'home_adjusted_success_allowed', 
        'away_adjusted_success', 'away_adjusted_success_allowed',
        'home_adjusted_rushing_epa', 'home_adjusted_rushing_epa_allowed', 
        'away_adjusted_rushing_epa', 'away_adjusted_rushing_epa_allowed',
        'home_adjusted_passing_epa', 'home_adjusted_passing_epa_allowed', 
        'away_adjusted_passing_epa', 'away_adjusted_passing_epa_allowed'
    ]

    def __init__(self, features: Optional[List[str]] = None, n_estimators: int = 100, random_state: int = 77):
        """
        Initialize the predictor.
        
        Args:
            features: List of feature column names to use. Defaults to 12 key metrics.
            n_estimators: Number of trees in the forest.
            random_state: Seed for reproducibility.
        """
        self.features = features or self.DEFAULT_FEATURES
        self.n_estimators = n_estimators
        self.random_state = random_state
        
        self.model_home = RandomForestRegressor(n_estimators=n_estimators, random_state=random_state)
        self.model_away = RandomForestRegressor(n_estimators=n_estimators, random_state=random_state)
        self.is_trained = False

    def train(self, data: pd.DataFrame):
        """
        Train the models using the provided data.
        
        Args:
            data: DataFrame containing features and target columns ('home_points', 'away_points').
        """
        # Validate data columns
        missing_features = [f for f in self.features if f not in data.columns]
        if missing_features:
            raise ValueError(f"Missing features in training data: {missing_features}")
            
        if 'home_points' not in data.columns or 'away_points' not in data.columns:
            raise ValueError("Training data must contain 'home_points' and 'away_points' columns.")
            
        # Drop rows with NaN in targets or features
        train_data = data.dropna(subset=self.features + ['home_points', 'away_points']).copy()
        
        if train_data.empty:
            raise ValueError("No valid training data after dropping NaNs.")
            
        X = train_data[self.features]
        y_home = train_data['home_points']
        y_away = train_data['away_points']
        
        self.model_home.fit(X, y_home)
        self.model_away.fit(X, y_away)
        self.is_trained = True

    def predict(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Predict scores for the given data.
        
        Args:
            data: DataFrame containing feature columns.
            
        Returns:
            DataFrame with 'predicted_home_points', 'predicted_away_points', 'predicted_margin'.
        """
        if not self.is_trained:
            raise RuntimeError("Model has not been trained yet.")
            
        # Validate features
        missing_features = [f for f in self.features if f not in data.columns]
        if missing_features:
            # Check if we can be lenient? No, RF needs all features.
            raise ValueError(f"Missing features in input data: {missing_features}")
            
        X = data[self.features]
        
        pred_home = self.model_home.predict(X)
        pred_away = self.model_away.predict(X)
        
        results = pd.DataFrame({
            'predicted_home_points': pred_home,
            'predicted_away_points': pred_away,
            'predicted_margin': pred_away - pred_home  # margin = away - home usually? Or home - away?
            # Notebook says: implied_margin = y_pred_away - y_pred_home
        }, index=data.index)
        
        return results

    def save(self, directory: Union[str, Path]):
        """Save the models to disk."""
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        
        joblib.dump(self.model_home, directory / "random_forest_home.joblib")
        joblib.dump(self.model_away, directory / "random_forest_away.joblib")
        joblib.dump(self.features, directory / "random_forest_features.joblib")

    def load(self, directory: Union[str, Path]):
        """Load models from disk."""
        directory = Path(directory)
        
        self.model_home = joblib.load(directory / "random_forest_home.joblib")
        self.model_away = joblib.load(directory / "random_forest_away.joblib")
        
        # Try to load features list if exists, otherwise keep current default
        features_path = directory / "random_forest_features.joblib"
        if features_path.exists():
            self.features = joblib.load(features_path)
            
        self.is_trained = True

