#!/usr/bin/env python3
"""
Validate Week 14 Web App Data
Checks data contract compatibility and validates file formats
"""

import pandas as pd
import json
from pathlib import Path
import sys
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent

def validate_web_app_data():
    """Validate Week 14 web app data compatibility"""
    print("🌐 Validating Week 14 Web App Data...")
    print("=" * 60)
    
    web_app_dir = PROJECT_ROOT / "web_app" / "public"
    validation_results = {
        'timestamp': datetime.now().isoformat(),
        'week': 14,
        'checks': {},
        'issues': [],
        'warnings': [],
        'status': 'pending'
    }
    
    # Check 1: Model predictions JSON
    print("\n1. Checking model predictions JSON...")
    preds_json_path = web_app_dir / "week14_model_predictions.json"
    if preds_json_path.exists():
        with open(preds_json_path) as f:
            preds = json.load(f)
        
        print(f"   ✅ Predictions JSON: {len(preds)} games")
        
        # Check required fields from DATA_CONTRACT.md
        required_fields = ['game_id', 'home_team', 'away_team', 'spread']
        if preds:
            sample = preds[0]
            missing_fields = [f for f in required_fields if f not in sample]
            if not missing_fields:
                validation_results['checks']['predictions_json'] = {'status': 'passed', 'count': len(preds)}
                print(f"   ✅ All required fields present")
            else:
                validation_results['checks']['predictions_json'] = {'status': 'warning', 'missing': missing_fields}
                validation_results['warnings'].append(f"Missing fields in predictions JSON: {missing_fields}")
                print(f"   ⚠️  Missing fields: {missing_fields}")
        else:
            validation_results['checks']['predictions_json'] = {'status': 'failed', 'count': 0}
            validation_results['issues'].append("Predictions JSON is empty")
            print(f"   ❌ Predictions JSON is empty")
    else:
        validation_results['checks']['predictions_json'] = {'status': 'failed', 'path': str(preds_json_path)}
        validation_results['issues'].append(f"Predictions JSON not found: {preds_json_path}")
        print(f"   ❌ Predictions JSON not found")
    
    # Check 2: Model predictions CSV
    print("\n2. Checking model predictions CSV...")
    preds_csv_path = web_app_dir / "week14_model_predictions.csv"
    if preds_csv_path.exists():
        df = pd.read_csv(preds_csv_path)
        print(f"   ✅ Predictions CSV: {len(df)} games")
        validation_results['checks']['predictions_csv'] = {'status': 'passed', 'count': len(df)}
    else:
        validation_results['checks']['predictions_csv'] = {'status': 'missing', 'path': str(preds_csv_path)}
        validation_results['warnings'].append(f"Predictions CSV not found: {preds_csv_path}")
        print(f"   ⚠️  Predictions CSV not found (fallback)")
    
    # Check 3: ATS data JSON
    print("\n3. Checking ATS data JSON...")
    ats_json_path = web_app_dir / "week14_ats_data.json"
    if ats_json_path.exists():
        with open(ats_json_path) as f:
            ats = json.load(f)
        
        print(f"   ✅ ATS data JSON: {len(ats)} games")
        
        # Check required ATS fields
        required_ats_fields = ['matchup', 'ats_pick', 'confidence_grade']
        if ats:
            sample = ats[0]
            missing_fields = [f for f in required_ats_fields if f not in sample]
            if not missing_fields:
                validation_results['checks']['ats_json'] = {'status': 'passed', 'count': len(ats)}
                print(f"   ✅ All required ATS fields present")
            else:
                validation_results['checks']['ats_json'] = {'status': 'warning', 'missing': missing_fields}
                validation_results['warnings'].append(f"Missing fields in ATS JSON: {missing_fields}")
                print(f"   ⚠️  Missing fields: {missing_fields}")
        else:
            validation_results['checks']['ats_json'] = {'status': 'failed', 'count': 0}
            validation_results['issues'].append("ATS JSON is empty")
            print(f"   ❌ ATS JSON is empty")
    else:
        validation_results['checks']['ats_json'] = {'status': 'missing', 'path': str(ats_json_path)}
        validation_results['warnings'].append(f"ATS JSON not found: {ats_json_path}")
        print(f"   ⚠️  ATS JSON not found")
    
    # Check 4: ATS table CSV
    print("\n4. Checking ATS table CSV...")
    ats_csv_path = web_app_dir / "week14_ats_full_table.csv"
    if ats_csv_path.exists():
        df = pd.read_csv(ats_csv_path)
        print(f"   ✅ ATS table CSV: {len(df)} games")
        validation_results['checks']['ats_csv'] = {'status': 'passed', 'count': len(df)}
    else:
        validation_results['checks']['ats_csv'] = {'status': 'missing', 'path': str(ats_csv_path)}
        validation_results['warnings'].append(f"ATS table CSV not found: {ats_csv_path}")
        print(f"   ⚠️  ATS table CSV not found (fallback)")
    
    # Check 5: Data consistency
    print("\n5. Checking data consistency...")
    if preds_json_path.exists() and ats_json_path.exists():
        with open(preds_json_path) as f:
            preds = json.load(f)
        with open(ats_json_path) as f:
            ats = json.load(f)
        
        if len(preds) == len(ats):
            validation_results['checks']['data_consistency'] = {'status': 'passed', 'count': len(preds)}
            print(f"   ✅ Data consistency: {len(preds)} games in both files")
        else:
            validation_results['checks']['data_consistency'] = {'status': 'warning', 'predictions': len(preds), 'ats': len(ats)}
            validation_results['warnings'].append(f"Data count mismatch: predictions={len(preds)}, ats={len(ats)}")
            print(f"   ⚠️  Data count mismatch: predictions={len(preds)}, ats={len(ats)}")
    
    # Determine overall status
    if len(validation_results['issues']) == 0:
        validation_results['status'] = 'passed'
        if len(validation_results['warnings']) > 0:
            validation_results['status'] = 'warning'
    else:
        validation_results['status'] = 'failed'
    
    # Save validation report
    report_path = PROJECT_ROOT / "validation" / "week14_web_app_validation.json"
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
    sys.exit(validate_web_app_data())

