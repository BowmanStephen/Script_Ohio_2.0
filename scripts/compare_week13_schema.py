import pandas as pd
from pathlib import Path
import sys

def compare_schemas():
    project_root = Path(__file__).parent.parent
    week13_path = project_root / "training_data_2025_week13.csv"
    training_path = project_root / "model_pack" / "updated_training_data.csv"
    
    if not week13_path.exists():
        print(f"❌ {week13_path} not found")
        return False
    if not training_path.exists():
        print(f"❌ {training_path} not found")
        return False
        
    df_week13 = pd.read_csv(week13_path)
    df_train = pd.read_csv(training_path)
    
    cols_week13 = set(df_week13.columns)
    cols_train = set(df_train.columns)
    
    missing_in_week13 = cols_train - cols_week13
    extra_in_week13 = cols_week13 - cols_train
    
    if missing_in_week13:
        print(f"❌ Week 13 is missing {len(missing_in_week13)} columns found in training data:")
        print(sorted(list(missing_in_week13)))
    else:
        print("✅ Week 13 has all columns from training data.")
        
    if extra_in_week13:
        print(f"⚠️ Week 13 has {len(extra_in_week13)} extra columns not in training data:")
        print(sorted(list(extra_in_week13)))
        
    # Check critical model features
    critical_features = [
        'home_talent', 'away_talent', 'home_elo', 'away_elo',
        'home_adjusted_epa', 'home_adjusted_epa_allowed',
        'away_adjusted_epa', 'away_adjusted_epa_allowed',
        'spread', 'home_adjusted_success', 'home_adjusted_success_allowed',
        'away_adjusted_success', 'away_adjusted_success_allowed'
    ]
    
    missing_critical = [col for col in critical_features if col not in cols_week13]
    if missing_critical:
        print(f"❌ Critical model features missing in Week 13: {missing_critical}")
        return False
    
    # Check for nulls in critical features (Week 13 specific)
    print("\nChecking for nulls in critical features (Week 13)...")
    has_nulls = False
    for col in critical_features:
        if col in df_week13.columns:
            null_count = df_week13[col].isna().sum()
            if null_count > 0:
                print(f"⚠️ {col}: {null_count} missing values")
                has_nulls = True
                
    if has_nulls:
        print("⚠️ Some critical features have missing values. Imputation may be needed.")
    else:
        print("✅ All critical features populated.")

    return True

if __name__ == "__main__":
    compare_schemas()

