#!/usr/bin/env python3
"""
Train Random Forest model using src/models/random_forest.py
"""
import sys
import pandas as pd
from pathlib import Path
import joblib

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from src.models.random_forest import RandomForestScorePredictor

def main():
    print("Training Random Forest Model...")
    
    # Load training data
    data_path = project_root / "model_pack" / "updated_training_data.csv"
    if not data_path.exists():
        print(f"Error: Data not found at {data_path}")
        return
        
    df = pd.read_csv(data_path)
    print(f"Loaded {len(df)} records.")
    
    # Initialize predictor
    # Using default features from the class which match the notebook
    predictor = RandomForestScorePredictor(n_estimators=100, random_state=77)
    
    # Train
    try:
        predictor.train(df)
        print("Training complete.")
    except ValueError as e:
        print(f"Training failed: {e}")
        # Check if we need to fallback to available features
        print("Columns available:", df.columns.tolist())
        return

    # Save as a single object for easier loading
    save_path = project_root / "model_pack" / "random_forest_model_2025.pkl"
    joblib.dump(predictor, save_path)
    print(f"Model saved to {save_path}")
    
    # Also save individual files for reference using the class method
    predictor.save(project_root / "model_pack" / "rf_components")
    print("Components saved to model_pack/rf_components/")

if __name__ == "__main__":
    main()

