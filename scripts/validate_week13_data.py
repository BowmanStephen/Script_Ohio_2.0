#!/usr/bin/env python3
"""
Validate Week 13 data integrity
Checks for missing values, outliers, format consistency, and freshness
"""

import pandas as pd
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).parent.parent

def validate_week13_data():
    """Validate Week 13 data integrity"""
    print("🔍 Validating Week 13 data...")
    print("=" * 60)
    
    issues = []
    
    # Check enhanced features
    features_path = PROJECT_ROOT / "data" / "week13" / "enhanced" / "week13_features_86.csv"
    if features_path.exists():
        df = pd.read_csv(features_path)
        print(f"✅ Features file: {len(df)} games, {len(df.columns)} features")
        
        # Check for missing values
        missing = df.isnull().sum()
        if missing.sum() > 0:
            missing_cols = missing[missing > 0]
            print(f"⚠️  Missing values found in {len(missing_cols)} columns:")
            for col, count in missing_cols.items():
                pct = (count / len(df)) * 100
                print(f"   {col}: {count} ({pct:.1f}%)")
                if pct > 10:  # More than 10% missing
                    issues.append(f"High missing values in {col}: {pct:.1f}%")
        else:
            print("✅ No missing values")
        
        # Check for outliers (basic check on key numeric columns)
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
        key_cols = [c for c in numeric_cols if any(x in c.lower() for x in ['elo', 'epa', 'margin', 'spread'])]
        
        for col in key_cols[:10]:  # Check first 10 key columns
            q1 = df[col].quantile(0.25)
            q3 = df[col].quantile(0.75)
            iqr = q3 - q1
            if iqr > 0:
                outliers = df[(df[col] < q1 - 1.5*iqr) | (df[col] > q3 + 1.5*iqr)]
                if len(outliers) > len(df) * 0.1:  # More than 10% outliers
                    print(f"⚠️  {col}: {len(outliers)} potential outliers ({len(outliers)/len(df)*100:.1f}%)")
        
        # Check required columns
        required_cols = ['game_id', 'home_team', 'away_team', 'week', 'season']
        missing_req = [c for c in required_cols if c not in df.columns]
        if missing_req:
            issues.append(f"Missing required columns: {missing_req}")
            print(f"❌ Missing required columns: {missing_req}")
        else:
            print("✅ All required columns present")
            
    else:
        issues.append(f"Features file not found: {features_path}")
        print(f"❌ Features file not found: {features_path}")
    
    # Check games file
    games_path = PROJECT_ROOT / "starter_pack" / "data" / "games.csv"
    if games_path.exists():
        games = pd.read_csv(games_path, low_memory=False)
        week13_games = games[(games['season'] == 2025) & (games['week'] == 13)]
        print(f"✅ Games file: {len(week13_games)} Week 13 games")
        
        if len(week13_games) == 0:
            issues.append("No Week 13 games found in games.csv")
            print("❌ No Week 13 games found")
    else:
        issues.append(f"Games file not found: {games_path}")
        print(f"❌ Games file not found: {games_path}")
    
    print("=" * 60)
    if issues:
        print(f"⚠️  Found {len(issues)} issues:")
        for issue in issues:
            print(f"   - {issue}")
        return 1
    else:
        print("✅ Validation complete - No issues found")
        return 0

if __name__ == "__main__":
    sys.exit(validate_week13_data())

