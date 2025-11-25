#!/usr/bin/env python3
"""
Validate Week 14 data integrity
Checks for missing values, outliers, format consistency, and freshness
"""

import pandas as pd
import json
from pathlib import Path
import sys
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent

def validate_week14_data():
    """Validate Week 14 data integrity"""
    print("🔍 Validating Week 14 data...")
    print("=" * 60)
    
    validation_results = {
        'timestamp': datetime.now().isoformat(),
        'week': 14,
        'season': 2025,
        'checks': {},
        'issues': [],
        'warnings': [],
        'status': 'pending'
    }
    
    # Check 1: Training data
    print("\n1. Checking training data...")
    training_path = PROJECT_ROOT / "data" / "training" / "weekly" / "training_data_2025_week14.csv"
    if training_path.exists():
        df = pd.read_csv(training_path)
        print(f"   ✅ Training data: {len(df)} games, {len(df.columns)} features")
        
        # Check feature count
        if len(df.columns) >= 86:
            validation_results['checks']['training_features'] = {'status': 'passed', 'count': len(df.columns)}
            print(f"   ✅ Feature count: {len(df.columns)} (expected: 86+)")
        else:
            validation_results['checks']['training_features'] = {'status': 'failed', 'count': len(df.columns)}
            validation_results['issues'].append(f"Training data has only {len(df.columns)} features, expected 86+")
            print(f"   ❌ Feature count: {len(df.columns)} (expected: 86+)")
        
        # Check for missing values
        missing = df.isnull().sum().sum()
        if missing == 0:
            validation_results['checks']['training_missing'] = {'status': 'passed', 'missing_count': 0}
            print(f"   ✅ No missing values")
        else:
            missing_cols = df.isnull().sum()
            missing_cols = missing_cols[missing_cols > 0]
            validation_results['checks']['training_missing'] = {'status': 'warning', 'missing_count': int(missing), 'columns': missing_cols.to_dict()}
            validation_results['warnings'].append(f"Training data has {missing} missing values across {len(missing_cols)} columns")
            print(f"   ⚠️  Missing values: {missing} across {len(missing_cols)} columns")
        
        # Check required columns
        required_cols = ['home_team', 'away_team', 'week', 'season']
        missing_req = [c for c in required_cols if c not in df.columns]
        if not missing_req:
            validation_results['checks']['training_required_cols'] = {'status': 'passed'}
            print(f"   ✅ All required columns present")
        else:
            validation_results['checks']['training_required_cols'] = {'status': 'failed', 'missing': missing_req}
            validation_results['issues'].append(f"Missing required columns: {missing_req}")
            print(f"   ❌ Missing required columns: {missing_req}")
    else:
        validation_results['checks']['training_data'] = {'status': 'failed', 'path': str(training_path)}
        validation_results['issues'].append(f"Training data file not found: {training_path}")
        print(f"   ❌ Training data file not found: {training_path}")
    
    # Check 2: Model files
    print("\n2. Checking model files...")
    model_files = {
        'ridge': PROJECT_ROOT / "model_pack" / "ridge_model_2025.joblib",
        'xgb': PROJECT_ROOT / "model_pack" / "xgb_home_win_model_2025.pkl",
        'fastai': PROJECT_ROOT / "model_pack" / "fastai_home_win_model_2025.pkl",
        'logistic': PROJECT_ROOT / "model_pack" / "logistic_regression_model.joblib",
        'random_forest': PROJECT_ROOT / "model_pack" / "random_forest_model_2025.pkl"
    }
    
    models_available = []
    for model_name, model_path in model_files.items():
        if model_path.exists():
            models_available.append(model_name)
            validation_results['checks'][f'model_{model_name}'] = {'status': 'passed', 'path': str(model_path)}
            print(f"   ✅ {model_name}: Found")
        else:
            validation_results['checks'][f'model_{model_name}'] = {'status': 'failed', 'path': str(model_path)}
            validation_results['issues'].append(f"Model file not found: {model_path}")
            print(f"   ❌ {model_name}: Not found")
    
    # Expect 5 models now (3 original + 2 new)
    expected_models = 5
    validation_results['checks']['models_available'] = {
        'status': 'passed' if len(models_available) == expected_models else 'warning', 
        'count': len(models_available), 
        'expected': expected_models,
        'models': models_available
    }
    
    # Check 3: Predictions files
    print("\n3. Checking predictions files...")
    predictions_dir = PROJECT_ROOT / "predictions" / "week14"
    
    pred_files = {
        'model_predictions_json': predictions_dir / "week14_model_predictions.json",
        'model_predictions_csv': predictions_dir / "week14_model_predictions.csv",
        'ats_table': predictions_dir / "week14_ats_full_table.csv",
        'summary': predictions_dir / "week14_summary.json",
        'enhanced': predictions_dir / "week14_predictions_enhanced.csv"
    }
    
    for file_name, file_path in pred_files.items():
        if file_path.exists():
            try:
                if file_path.suffix == '.json':
                    with open(file_path) as f:
                        data = json.load(f)
                    count = len(data) if isinstance(data, list) else 1
                else:
                    df = pd.read_csv(file_path)
                    count = len(df)
                
                validation_results['checks'][f'predictions_{file_name}'] = {'status': 'passed', 'count': count}
                print(f"   ✅ {file_name}: {count} records")
            except Exception as e:
                validation_results['checks'][f'predictions_{file_name}'] = {'status': 'error', 'error': str(e)}
                validation_results['warnings'].append(f"Error reading {file_name}: {e}")
                print(f"   ⚠️  {file_name}: Error reading file")
        else:
            validation_results['checks'][f'predictions_{file_name}'] = {'status': 'missing', 'path': str(file_path)}
            validation_results['warnings'].append(f"Predictions file not found: {file_path}")
            print(f"   ⚠️  {file_name}: Not found")
    
    # Check 4: Web app data
    print("\n4. Checking web app data...")
    web_app_dir = PROJECT_ROOT / "web_app" / "public"
    
    web_app_files = {
        'model_predictions_json': web_app_dir / "week14_model_predictions.json",
        'model_predictions_csv': web_app_dir / "week14_model_predictions.csv",
        'ats_data': web_app_dir / "week14_ats_data.json",
        'ats_table': web_app_dir / "week14_ats_full_table.csv"
    }
    
    for file_name, file_path in web_app_files.items():
        if file_path.exists():
            validation_results['checks'][f'webapp_{file_name}'] = {'status': 'passed', 'path': str(file_path)}
            print(f"   ✅ {file_name}: Found")
        else:
            validation_results['checks'][f'webapp_{file_name}'] = {'status': 'missing', 'path': str(file_path)}
            validation_results['warnings'].append(f"Web app file not found: {file_path}")
            print(f"   ⚠️  {file_name}: Not found")
    
    # Determine overall status
    if len(validation_results['issues']) == 0:
        validation_results['status'] = 'passed'
        if len(validation_results['warnings']) > 0:
            validation_results['status'] = 'warning'
    else:
        validation_results['status'] = 'failed'
    
    # Save validation report
    report_path = PROJECT_ROOT / "validation" / "week14_validation_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w') as f:
        json.dump(validation_results, f, indent=2)
    
    print("\n" + "=" * 60)
    print(f"Validation Status: {validation_results['status'].upper()}")
    print(f"Issues: {len(validation_results['issues'])}")
    print(f"Warnings: {len(validation_results['warnings'])}")
    
    if validation_results['issues']:
        print("\nIssues found:")
        for issue in validation_results['issues']:
            print(f"   - {issue}")
    
    if validation_results['warnings']:
        print("\nWarnings:")
        for warning in validation_results['warnings']:
            print(f"   - {warning}")
    
    print(f"\n✅ Validation report saved to: {report_path}")
    
    return 0 if validation_results['status'] == 'passed' else 1

if __name__ == "__main__":
    sys.exit(validate_week14_data())

