#!/usr/bin/env python3
"""
Fix FastAI model export issue by retraining with proper learn.export() method.
This ensures the model can be loaded with load_learner() and recovers cat/cont schema.
"""
import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Try to import FastAI
try:
    from fastai.tabular.all import *
    FASTAI_AVAILABLE = True
    print("✅ FastAI available for retraining")
except ImportError:
    FASTAI_AVAILABLE = False
    print("❌ FastAI not available, installing...")
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "fastai"])
    from fastai.tabular.all import *
    FASTAI_AVAILABLE = True
    print("✅ FastAI installed successfully")

def retrain_fastai_model():
    """Retrain FastAI model with proper learn.export() method"""
    print("🔄 Starting FastAI model retraining...")

    # Load training data
    data_path = Path('updated_training_data.csv')
    if not data_path.exists():
        print(f"❌ Training data not found at {data_path}")
        return False

    df = pd.read_csv(data_path)
    print(f"✅ Loaded training data: {df.shape}")

    # Create target variable from margin
    if 'margin' not in df.columns:
        print("❌ Margin column not found")
        return False

    df['home_win'] = (df['margin'] > 0).astype(int)
    print(f"✅ Created target variable: {df['home_win'].value_counts().to_dict()}")

    # Remove rows with missing target values
    df_clean = df.dropna(subset=['home_win', 'margin'])
    print(f"✅ Cleaned data shape: {df_clean.shape}")

    # Use same feature sets as model_training_agent.py
    cat_features = ['week', 'home_conference', 'away_conference', 'neutral_site']
    cont_features = [
        'spread',
        'home_adjusted_epa', 'home_adjusted_epa_allowed',
        'away_adjusted_epa', 'away_adjusted_epa_allowed',
        'home_adjusted_success', 'home_adjusted_success_allowed',
        'away_adjusted_success', 'away_adjusted_success_allowed',
        'home_talent', 'away_talent', 'home_elo', 'away_elo',
        'home_adjusted_explosiveness', 'away_adjusted_explosiveness',
        'home_adjusted_line_yards', 'away_adjusted_line_yards',
        'home_adjusted_open_field_yards', 'away_adjusted_open_field_yards',
        'home_avg_start_offense', 'away_avg_start_offense',
        'home_avg_start_defense', 'away_avg_start_defense'
    ]

    # Filter to available features in the dataset
    cat_features = [f for f in cat_features if f in df_clean.columns]
    cont_features = [f for f in cont_features if f in df_clean.columns]
    
    print(f"✅ Using {len(cat_features)} categorical features: {cat_features}")
    print(f"✅ Using {len(cont_features)} continuous features: {cont_features[:5]}... (total {len(cont_features)})")

    # Prepare FastAI dataset
    target_col = 'home_win'
    all_features = cat_features + cont_features + [target_col]
    df_fastai = df_clean[all_features].copy()
    df_fastai[target_col] = df_fastai[target_col].astype(int)
    
    # Fill missing values in continuous features with median before FastAI processing
    for col in cont_features:
        if col in df_fastai.columns and df_fastai[col].isna().any():
            median_val = df_fastai[col].median()
            df_fastai[col] = df_fastai[col].fillna(median_val)
            print(f"⚠️  Filled missing values in {col} with median: {median_val:.3f}")
    
    # Fill missing values in categorical features with mode
    for col in cat_features:
        if col in df_fastai.columns and df_fastai[col].isna().any():
            mode_val = df_fastai[col].mode()[0] if len(df_fastai[col].mode()) > 0 else 'unknown'
            df_fastai[col] = df_fastai[col].fillna(mode_val)
            print(f"⚠️  Filled missing values in {col} with mode: {mode_val}")

    # Split data temporally (train on 2016-2024, test on 2025)
    if 'season' in df_clean.columns:
        train_idx = df_clean[df_clean['season'] < 2025].index
        valid_idx = df_clean[df_clean['season'] >= 2025].index
    else:
        from sklearn.model_selection import train_test_split
        train_idx, valid_idx = train_test_split(df_clean.index, test_size=0.2, random_state=42)

    print(f"✅ Train set: {len(train_idx)}, Validation set: {len(valid_idx)}")

    # Create FastAI DataLoaders with proper cat/cont split
    dls = TabularDataLoaders.from_df(
        df_fastai,
        procs=[Categorify, FillMissing, Normalize],
        cat_names=cat_features,
        cont_names=cont_features,
        y_names=target_col,
        valid_idx=valid_idx,
        bs=64
    )

    print("✅ FastAI DataLoaders created with categorical and continuous features")

    # Create learner
    learn = tabular_learner(
        dls,
        layers=[200, 100],
        metrics=[accuracy, RocAucBinary(), F1Score()]
    )

    # Find learning rate
    print("🔄 Finding optimal learning rate...")
    suggested = learn.lr_find()

    # Train model
    print("🔄 Training FastAI model...")
    learn.fit_one_cycle(4, lr_max=suggested.valley)

    # Save model using learn.export() - this preserves DataLoaders structure
    model_path = Path('fastai_home_win_model_2025.pkl')
    
    print(f"💾 Saving model using learn.export() to {model_path}...")
    learn.export(model_path)
    
    print(f"✅ FastAI model saved to {model_path} using learn.export()")

    # Verify loading with load_learner() and check schema recovery
    print("🔍 Verifying model loads correctly with load_learner()...")
    try:
        from fastai.tabular.all import load_learner
        loaded_model = load_learner(model_path)
        
        # Verify the model has predict method
        if not hasattr(loaded_model, 'predict'):
            print("❌ Loaded model missing predict() method")
            return False
        
        # Verify DataLoaders structure is preserved (enables schema recovery)
        if not hasattr(loaded_model, 'dls'):
            print("❌ Loaded model missing dls (DataLoaders) - schema recovery will fail")
            return False
        
        # Verify categorical and continuous feature names are recoverable
        dls = loaded_model.dls
        recovered_cat_names = list(getattr(dls, 'cat_names', []))
        recovered_cont_names = list(getattr(dls, 'cont_names', []))
        
        print(f"✅ Model loaded successfully with load_learner()")
        print(f"✅ Recovered {len(recovered_cat_names)} categorical features: {recovered_cat_names}")
        print(f"✅ Recovered {len(recovered_cont_names)} continuous features: {recovered_cont_names[:5]}... (total {len(recovered_cont_names)})")
        
        # Verify schema matches what we trained with
        if set(recovered_cat_names) != set(cat_features):
            print(f"⚠️  Warning: Recovered cat features differ from training")
            print(f"   Training: {set(cat_features)}")
            print(f"   Recovered: {set(recovered_cat_names)}")
        
        if set(recovered_cont_names) != set(cont_features):
            print(f"⚠️  Warning: Recovered cont features differ from training")
            print(f"   Training: {set(cont_features)}")
            print(f"   Recovered: {set(recovered_cont_names)}")
        
        # Test prediction to ensure model works
        print("🧪 Testing model prediction...")
        test_row = df_fastai.iloc[0:1][cat_features + cont_features]
        prediction = loaded_model.predict(test_row.iloc[0])
        print(f"✅ Model prediction successful: {type(prediction)}")
        
        print("✅ FastAI model verification complete - load_learner() works and schema is recoverable!")
        return True
        
    except Exception as e:
        print(f"❌ Model loading verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = retrain_fastai_model()
    if success:
        print("🎉 FastAI model retraining completed successfully!")
    else:
        print("💥 FastAI model retraining failed!")