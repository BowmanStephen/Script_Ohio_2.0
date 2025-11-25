#!/usr/bin/env python3
"""
Audit Week 13 prediction calculations
Validates win probabilities, margins, confidence values, and model agreement
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).parent.parent

def audit_predictions():
    """Audit Week 13 prediction calculations"""
    print("🔍 Auditing Week 13 predictions...")
    print("=" * 60)
    
    issues = []
    
    # Try multiple possible prediction file locations
    pred_files = [
        PROJECT_ROOT / "predictions" / "week13" / "week13_model_predictions.csv",
        PROJECT_ROOT / "predictions" / "week13" / "week13_comprehensive_predictions.csv",
        PROJECT_ROOT / "predictions" / "week13" / "week13_predictions_all_60_games.csv",
    ]
    
    pred_file = None
    for pf in pred_files:
        if pf.exists():
            pred_file = pf
            break
    
    if not pred_file:
        print(f"❌ No predictions file found. Checked:")
        for pf in pred_files:
            print(f"   - {pf}")
        return 1
    
    print(f"✅ Loading predictions from: {pred_file.name}")
    df = pd.read_csv(pred_file)
    print(f"✅ Loaded {len(df)} predictions")
    
    # Check 1: Win probabilities sum to 1.0
    prob_cols = [
        ('ensemble_home_win_probability', 'ensemble_away_win_probability'),
        ('home_win_probability', 'away_win_probability'),
        ('ridge_home_win_probability', None),
    ]
    
    for home_col, away_col in prob_cols:
        if home_col in df.columns:
            if away_col and away_col in df.columns:
                prob_sum = (df[home_col] + df[away_col]).round(2)
                invalid = prob_sum[prob_sum != 1.0]
                if len(invalid) > 0:
                    print(f"⚠️  {len(invalid)} games with {home_col}/{away_col} not summing to 1.0")
                    issues.append(f"Probability sum issue in {home_col}/{away_col}")
                    # Show first few examples
                    for idx in invalid.head(3).index:
                        print(f"   Game {idx}: {df.loc[idx, home_col]:.3f} + {df.loc[idx, away_col]:.3f} = {prob_sum.loc[idx]:.3f}")
                else:
                    print(f"✅ All {home_col}/{away_col} sum to 1.0")
    
    # Check 2: Predicted margin consistency
    margin_cols = ['predicted_margin', 'ensemble_margin', 'ridge_predicted_margin']
    for col in margin_cols:
        if col in df.columns:
            # Check for extreme values
            extreme = df[abs(df[col]) > 50]
            if len(extreme) > 0:
                print(f"⚠️  {len(extreme)} games with extreme {col} (>50 points)")
                issues.append(f"Extreme margins in {col}")
                for idx in extreme.head(3).index:
                    print(f"   {df.loc[idx, 'away_team']} @ {df.loc[idx, 'home_team']}: {df.loc[idx, col]:.1f}")
            else:
                print(f"✅ No extreme {col} values")
    
    # Check 3: Confidence values in valid range
    conf_cols = ['ensemble_confidence', 'confidence']
    for col in conf_cols:
        if col in df.columns:
            invalid_conf = df[(df[col] < 0) | (df[col] > 100)]
            if len(invalid_conf) > 0:
                print(f"⚠️  {len(invalid_conf)} games with invalid {col} (outside 0-100)")
                issues.append(f"Invalid confidence values in {col}")
            else:
                print(f"✅ All {col} values in valid range (0-100)")
    
    # Check 4: Model agreement consistency
    if 'model_agreement' in df.columns:
        agreement_counts = df['model_agreement'].value_counts()
        print(f"✅ Model agreement distribution:")
        for agreement, count in agreement_counts.items():
            print(f"   {agreement}: {count} games")
    
    # Check 5: Required columns
    required_cols = ['home_team', 'away_team']
    missing_req = [c for c in required_cols if c not in df.columns]
    if missing_req:
        issues.append(f"Missing required columns: {missing_req}")
        print(f"❌ Missing required columns: {missing_req}")
    else:
        print("✅ All required columns present")
    
    print("=" * 60)
    if issues:
        print(f"⚠️  Found {len(issues)} issues:")
        for issue in issues:
            print(f"   - {issue}")
        return 1
    else:
        print("✅ Audit complete - No issues found")
        return 0

if __name__ == "__main__":
    sys.exit(audit_predictions())

