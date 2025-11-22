#!/usr/bin/env python3
"""
Validate Integrated Training Dataset

This script performs comprehensive validation on the integrated training dataset
after missing games have been added.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

class DatasetValidator:
    """Validate integrated training dataset."""
    
    def __init__(self):
        self.training_data_path = PROJECT_ROOT / 'model_pack' / 'updated_training_data.csv'
        self.report_path = PROJECT_ROOT / 'reports' / 'validation_report.txt'
        
    def validate(self) -> dict:
        """Run all validation checks."""
        print("=" * 80)
        print("VALIDATING INTEGRATED TRAINING DATASET")
        print("=" * 80)
        
        if not self.training_data_path.exists():
            print(f"ERROR: Training data not found: {self.training_data_path}")
            return {'valid': False, 'errors': ['Training data file not found']}
        
        # Load data
        print(f"\nLoading training data from: {self.training_data_path}")
        df = pd.read_csv(self.training_data_path, low_memory=False)
        print(f"Loaded {len(df):,} games")
        
        results = {
            'valid': True,
            'total_games': len(df),
            'errors': [],
            'warnings': [],
            'checks': {}
        }
        
        # Check 1: Duplicate game IDs
        print("\n1. Checking for duplicate game IDs...")
        duplicate_ids = df[df.duplicated(subset=['id'], keep=False)]
        if len(duplicate_ids) > 0:
            results['errors'].append(f"Found {len(duplicate_ids)} duplicate game IDs")
            results['valid'] = False
            print(f"  ❌ Found {len(duplicate_ids)} duplicate game IDs")
        else:
            results['checks']['duplicates'] = 'PASS'
            print("  ✅ No duplicate game IDs")
        
        # Check 2: Missing critical columns
        print("\n2. Checking for required columns...")
        required_columns = [
            'id', 'season', 'week', 'home_team', 'away_team',
            'home_points', 'away_points', 'margin', 'game_key'
        ]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            results['errors'].append(f"Missing required columns: {missing_columns}")
            results['valid'] = False
            print(f"  ❌ Missing columns: {missing_columns}")
        else:
            results['checks']['required_columns'] = 'PASS'
            print("  ✅ All required columns present")
        
        # Check 3: Feature count (should be 86 features)
        print("\n3. Checking feature count...")
        # Exclude metadata columns
        metadata_cols = {'id', 'start_date', 'season_type', 'game_key', 'conference_game',
                        'home_conference', 'away_conference'}
        feature_cols = [col for col in df.columns if col not in metadata_cols]
        feature_count = len(feature_cols)
        results['checks']['feature_count'] = feature_count
        print(f"  Feature columns: {feature_count}")
        if feature_count < 80:
            results['warnings'].append(f"Feature count ({feature_count}) is lower than expected (86)")
            print(f"  ⚠️  Feature count lower than expected")
        else:
            print("  ✅ Feature count acceptable")
        
        # Check 4: Season distribution
        print("\n4. Checking season distribution...")
        season_counts = df['season'].value_counts().sort_index()
        results['checks']['season_distribution'] = season_counts.to_dict()
        print("  Games by season:")
        for season, count in season_counts.items():
            print(f"    {season}: {count:,} games")
        
        # Check 5: Week filtering (historical should be Week 5+)
        print("\n5. Checking week filtering...")
        for season in sorted(df['season'].unique()):
            if season < 2025:
                season_df = df[df['season'] == season]
                min_week = int(season_df['week'].min())
                if min_week < 5:
                    results['warnings'].append(
                        f"{season}: Contains Week {min_week} games (should be Week 5+)"
                    )
                    print(f"  ⚠️  {season}: Contains Week {min_week} games")
        
        # Check 6: Missing values in critical features
        print("\n6. Checking for missing values...")
        critical_features = [
            'home_elo', 'away_elo', 'home_talent', 'away_talent',
            'home_points', 'away_points', 'margin'
        ]
        missing_counts = {}
        for col in critical_features:
            if col in df.columns:
                missing = df[col].isna().sum()
                if missing > 0:
                    missing_counts[col] = missing
                    if missing > len(df) * 0.1:  # More than 10% missing
                        results['warnings'].append(f"{col}: {missing} missing values ({100*missing/len(df):.1f}%)")
        
        if missing_counts:
            print("  Missing values in critical features:")
            for col, count in missing_counts.items():
                pct = 100 * count / len(df)
                print(f"    {col}: {count} ({pct:.1f}%)")
        else:
            print("  ✅ No missing values in critical features")
        results['checks']['missing_values'] = missing_counts
        
        # Check 7: Data types
        print("\n7. Checking data types...")
        type_issues = []
        if 'id' in df.columns:
            if not pd.api.types.is_numeric_dtype(df['id']):
                type_issues.append("id should be numeric")
        if 'season' in df.columns:
            if not pd.api.types.is_integer_dtype(df['season']):
                type_issues.append("season should be integer")
        if 'week' in df.columns:
            if not pd.api.types.is_integer_dtype(df['week']):
                type_issues.append("week should be integer")
        
        if type_issues:
            results['warnings'].extend(type_issues)
            print(f"  ⚠️  Type issues: {type_issues}")
        else:
            print("  ✅ Data types correct")
        
        # Check 8: Game key uniqueness
        print("\n8. Checking game_key uniqueness...")
        duplicate_keys = df[df.duplicated(subset=['game_key'], keep=False)]
        if len(duplicate_keys) > 0:
            results['warnings'].append(f"Found {len(duplicate_keys)} duplicate game_keys")
            print(f"  ⚠️  Found {len(duplicate_keys)} duplicate game_keys")
        else:
            print("  ✅ All game_keys unique")
        
        # Generate report
        self._generate_report(results, df)
        
        return results
    
    def _generate_report(self, results: dict, df: pd.DataFrame):
        """Generate validation report."""
        PROJECT_ROOT / 'reports' / 'validation_report.txt'
        reports_dir = PROJECT_ROOT / 'reports'
        reports_dir.mkdir(exist_ok=True)
        
        with open(self.report_path, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("TRAINING DATASET VALIDATION REPORT\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"Validation Status: {'✅ PASS' if results['valid'] else '❌ FAIL'}\n")
            f.write(f"Total Games: {results['total_games']:,}\n\n")
            
            if results['errors']:
                f.write("ERRORS:\n")
                for error in results['errors']:
                    f.write(f"  ❌ {error}\n")
                f.write("\n")
            
            if results['warnings']:
                f.write("WARNINGS:\n")
                for warning in results['warnings']:
                    f.write(f"  ⚠️  {warning}\n")
                f.write("\n")
            
            f.write("CHECKS:\n")
            for check, value in results['checks'].items():
                if isinstance(value, dict):
                    f.write(f"  {check}:\n")
                    for k, v in value.items():
                        f.write(f"    {k}: {v}\n")
                else:
                    f.write(f"  {check}: {value}\n")
            
            f.write("\n" + "=" * 80 + "\n")
            f.write("SEASON DISTRIBUTION:\n")
            f.write("=" * 80 + "\n")
            season_counts = df['season'].value_counts().sort_index()
            for season, count in season_counts.items():
                f.write(f"{season}: {count:,} games\n")
        
        print(f"\nValidation report saved to: {self.report_path}")
        
        # Print summary
        print("\n" + "=" * 80)
        if results['valid']:
            print("✅ VALIDATION PASSED")
        else:
            print("❌ VALIDATION FAILED")
        print("=" * 80)
        print(f"Total games: {results['total_games']:,}")
        print(f"Errors: {len(results['errors'])}")
        print(f"Warnings: {len(results['warnings'])}")

def main():
    """Main execution."""
    validator = DatasetValidator()
    results = validator.validate()
    sys.exit(0 if results['valid'] else 1)

if __name__ == "__main__":
    main()

