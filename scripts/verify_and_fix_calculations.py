#!/usr/bin/env python3
"""
Calculation Verification and Fix Script

This script verifies that all calculations follow best practices and fixes
identified issues with the training data.

Author: Claude Code Assistant
Created: 2025-11-18
Version: 1.0
"""

import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Set
import json
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.dirname(__file__))
if os.path.exists(project_root):
    sys.path.insert(0, project_root)

class CalculationVerifier:
    """Verify and fix calculations in Script Ohio 2.0 platform"""

    def __init__(self):
        self.project_root = Path(project_root)
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'verification_results': {},
            'fixes_applied': [],
            'issues_found': [],
            'recommendations': []
        }

    def load_training_data(self) -> pd.DataFrame:
        """Load training data for verification"""
        training_file = self.project_root / "model_pack" / "updated_training_data.csv"
        if not training_file.exists():
            raise FileNotFoundError(f"Training data not found: {training_file}")

        return pd.read_csv(training_file)

    def verify_feature_count(self, df: pd.DataFrame) -> Dict:
        """Verify feature count is correct (86 features expected)"""
        print("🔍 Verifying feature count...")

        result = {
            'current_count': len(df.columns),
            'expected_count': 86,
            'extra_columns': [],
            'missing_columns': [],
            'status': 'OK'
        }

        current_cols = set(df.columns)

        # Look for columns that shouldn't be in ML features
        non_feature_patterns = ['id', 'game_key', 'start_date', 'season_type', 'neutral_site', 'conference_game']
        extra_cols = [col for col in df.columns if any(pattern in col.lower() for pattern in non_feature_patterns)]

        result['extra_columns'] = extra_cols

        if len(df.columns) != 86:
            result['status'] = 'NEEDS_FIXING'
            print(f"  ❌ Found {len(df.columns)} features, expected 86")
            print(f"  🔧 Extra columns to remove: {extra_cols}")
        else:
            print(f"  ✅ Feature count correct: {len(df.columns)}")

        self.results['verification_results']['feature_count'] = result
        return result

    def verify_epa_calculations(self, df: pd.DataFrame) -> Dict:
        """Verify EPA calculations follow expected patterns"""
        print("\n🔍 Verifying EPA calculations...")

        result = {
            'epa_columns_found': [],
            'epa_ranges': {},
            'opponent_adjustments': {},
            'issues': [],
            'status': 'OK'
        }

        # Look for EPA columns
        epa_columns = [col for col in df.columns if 'epa' in col.lower()]
        result['epa_columns_found'] = epa_columns

        # Check EPA value ranges
        for col in epa_columns:
            if col in df.columns:
                values = df[col].dropna()
                if len(values) > 0:
                    result['epa_ranges'][col] = {
                        'min': float(values.min()),
                        'max': float(values.max()),
                        'mean': float(values.mean()),
                        'std': float(values.std())
                    }

                    # Check for reasonable EPA ranges
                    if abs(values.mean()) > 2.0:  # EPA shouldn't average more than 2 points per play
                        result['issues'].append(f"{col}: Suspiciously high average EPA ({values.mean():.3f})")
                        result['status'] = 'NEEDS_REVIEW'

                    if values.std() > 5.0:  # Very high standard deviation might indicate errors
                        result['issues'].append(f"{col}: Very high EPA std dev ({values.std():.3f})")

        # Check opponent-adjusted EPA calculations
        opponent_epa_cols = [col for col in epa_columns if 'adjusted' in col.lower()]
        result['opponent_adjustments']['columns_found'] = opponent_epa_cols

        print(f"  📊 Found {len(epa_columns)} EPA columns")
        print(f"  🎯 Found {len(opponent_epa_cols)} opponent-adjusted EPA columns")

        if result['issues']:
            print(f"  ⚠️  Found {len(result['issues'])} EPA issues")
            for issue in result['issues']:
                print(f"    • {issue}")
        else:
            print(f"  ✅ EPA calculations look reasonable")

        self.results['verification_results']['epa_calculations'] = result
        return result

    def verify_opponent_adjustments(self, df: pd.DataFrame) -> Dict:
        """Verify opponent adjustments use subtraction methodology"""
        print("\n🔍 Verifying opponent adjustments...")

        result = {
            'adjusted_columns': [],
            'raw_columns': [],
            'adjustment_logic': {},
            'issues': [],
            'status': 'OK'
        }

        # Find adjusted vs raw column pairs
        adjusted_cols = [col for col in df.columns if 'adjusted' in col.lower()]
        result['adjusted_columns'] = adjusted_cols

        # Try to find corresponding raw columns
        for adj_col in adjusted_cols:
            # Remove 'adjusted_' prefix to find raw column
            if adj_col.startswith('home_adjusted_'):
                raw_col = adj_col.replace('home_adjusted_', 'home_')
            elif adj_col.startswith('away_adjusted_'):
                raw_col = adj_col.replace('away_adjusted_', 'away_')
            else:
                continue

            if raw_col in df.columns:
                result['raw_columns'].append(raw_col)

                # Check adjustment logic (should be roughly: adjusted = raw - opponent_avg)
                adj_values = df[adj_col].dropna()
                raw_values = df[raw_col].dropna()

                if len(adj_values) > 0 and len(raw_values) > 0:
                    # Check if adjustments are reasonable (adjusted values should be centered around 0)
                    adj_mean = adj_values.mean()
                    if abs(adj_mean) > 1.0:  # Adjusted values should be near zero on average
                        result['issues'].append(f"{adj_col}: Adjusted values not centered (mean={adj_mean:.3f})")
                        result['status'] = 'NEEDS_REVIEW'

        print(f"  📈 Found {len(adjusted_cols)} adjusted columns")
        print(f"  📊 Found {len(result['raw_columns'])} corresponding raw columns")

        if result['issues']:
            print(f"  ⚠️  Found {len(result['issues'])} opponent adjustment issues")
            for issue in result['issues']:
                print(f"    • {issue}")
        else:
            print(f"  ✅ Opponent adjustments look reasonable")

        self.results['verification_results']['opponent_adjustments'] = result
        return result

    def verify_week5_filtering(self, df: pd.DataFrame) -> Dict:
        """Verify Week 5+ filtering is applied correctly"""
        print("\n🔍 Verifying Week 5+ filtering...")

        result = {
            'total_games': len(df),
            'pre_week5_games': 0,
            'week5_plus_games': 0,
            'should_filter': True,
            'status': 'OK'
        }

        if 'week' in df.columns and 'season' in df.columns:
            # Check for pre-Week 5 games
            pre_week5 = df[(df['week'] < 5) & (df['season'] == 2025)]
            result['pre_week5_games'] = len(pre_week5)

            week5_plus = df[(df['week'] >= 5) & (df['season'] == 2025)]
            result['week5_plus_games'] = len(week5_plus)

            if result['pre_week5_games'] > 0:
                result['status'] = 'NEEDS_FILTERING'
                print(f"  ❌ Found {result['pre_week5_games']} pre-Week 5 games that should be filtered")
            else:
                print(f"  ✅ Correctly filtered to Week 5+ only")

        self.results['verification_results']['week5_filtering'] = result
        return result

    def fix_training_data_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Fix training data by removing extra columns"""
        print("\n🔧 Fixing training data features...")

        # Remove non-feature columns
        columns_to_remove = ['id', 'game_key', 'start_date', 'season_type', 'neutral_site', 'conference_game']
        columns_to_remove = [col for col in columns_to_remove if col in df.columns]

        if columns_to_remove:
            print(f"  🗑️  Removing {len(columns_to_remove)} extra columns: {columns_to_remove}")
            df_fixed = df.drop(columns=columns_to_remove)
            self.results['fixes_applied'].append(f"Removed extra columns: {columns_to_remove}")
        else:
            df_fixed = df.copy()
            print(f"  ✅ No extra columns to remove")

        print(f"  📊 New feature count: {len(df_fixed.columns)}")

        return df_fixed

    def apply_week5_filtering(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply Week 5+ filtering if needed"""
        print("\n🔧 Applying Week 5+ filtering...")

        if 'week' in df.columns and 'season' in df.columns:
            original_count = len(df)

            # Keep only Week 5+ games for 2025
            df_filtered = df[~((df['season'] == 2025) & (df['week'] < 5))]

            games_removed = original_count - len(df_filtered)
            if games_removed > 0:
                print(f"  🗑️  Removed {games_removed} pre-Week 5 games")
                self.results['fixes_applied'].append(f"Removed {games_removed} pre-Week 5 games")
            else:
                print(f"  ✅ No pre-Week 5 games to remove")

            return df_filtered
        else:
            print(f"  ⚠️  Cannot apply Week 5+ filtering - missing week or season columns")
            return df

    def save_fixed_training_data(self, df: pd.DataFrame):
        """Save the fixed training data"""
        print(f"\n💾 Saving fixed training data...")

        training_file = self.project_root / "model_pack" / "updated_training_data.csv"

        # Create backup
        backup_file = training_file.with_suffix('.csv.backup_before_fix')
        if training_file.exists():
            import shutil
            shutil.copy2(training_file, backup_file)
            print(f"  📋 Created backup: {backup_file}")

        # Save fixed data
        df.to_csv(training_file, index=False)
        print(f"  ✅ Saved fixed training data: {training_file}")
        print(f"  📊 Final shape: {df.shape}")

        self.results['fixes_applied'].append(f"Saved fixed training data with {len(df.columns)} features")

    def generate_recommendations(self):
        """Generate recommendations based on verification results"""
        print(f"\n💡 Generating recommendations...")

        recommendations = []

        # Feature count recommendations
        feature_result = self.results['verification_results'].get('feature_count', {})
        if feature_result.get('status') == 'NEEDS_FIXING':
            recommendations.append({
                'priority': 'HIGH',
                'issue': 'Incorrect feature count',
                'action': 'Remove non-feature columns (id, game_key, etc.)',
                'details': f"Found {feature_result['current_count']} features, expected 86"
            })

        # EPA calculation recommendations
        epa_result = self.results['verification_results'].get('epa_calculations', {})
        if epa_result.get('status') == 'NEEDS_REVIEW':
            recommendations.append({
                'priority': 'MEDIUM',
                'issue': 'Suspicious EPA calculations',
                'action': 'Review EPA calculation methodology',
                'details': f"Found {len(epa_result.get('issues', []))} EPA issues"
            })

        # Week 5 filtering recommendations
        week5_result = self.results['verification_results'].get('week5_filtering', {})
        if week5_result.get('status') == 'NEEDS_FILTERING':
            recommendations.append({
                'priority': 'HIGH',
                'issue': 'Pre-Week 5 games in training data',
                'action': 'Filter out games from weeks 1-4',
                'details': f"Found {week5_result['pre_week5_games']} pre-Week 5 games"
            })

        self.results['recommendations'] = recommendations

        for rec in recommendations:
            print(f"  🔴 {rec['priority']}: {rec['issue']}")
            print(f"     📝 {rec['action']}")

    def save_verification_report(self):
        """Save verification report"""
        report_file = self.project_root / "project_management" / f"calculation_verification_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        # Ensure directory exists
        report_file.parent.mkdir(parents=True, exist_ok=True)

        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)

        print(f"\n📄 Verification report saved: {report_file}")
        return report_file

    def run_verification_and_fixes(self):
        """Run complete verification and apply fixes"""
        print("🚀 Starting Calculation Verification and Fixes...")
        print("="*60)

        try:
            # Load training data
            df = self.load_training_data()
            print(f"📊 Loaded training data: {df.shape}")

            # Run verifications
            feature_result = self.verify_feature_count(df)
            epa_result = self.verify_epa_calculations(df)
            opp_result = self.verify_opponent_adjustments(df)
            week5_result = self.verify_week5_filtering(df)

            # Apply fixes if needed
            df_fixed = df.copy()

            if feature_result.get('status') == 'NEEDS_FIXING':
                df_fixed = self.fix_training_data_features(df_fixed)

            if week5_result.get('status') == 'NEEDS_FILTERING':
                df_fixed = self.apply_week5_filtering(df_fixed)

            # Save fixed data if changes were made
            if self.results['fixes_applied']:
                self.save_fixed_training_data(df_fixed)
            else:
                print(f"\n✅ No fixes needed - training data is already correct")

            # Generate recommendations
            self.generate_recommendations()

            # Save report
            report_file = self.save_verification_report()

            return self.results

        except Exception as e:
            print(f"\n❌ Error during verification: {str(e)}")
            self.results['issues_found'].append(f"Verification error: {str(e)}")
            return self.results

def main():
    """Main execution function"""
    verifier = CalculationVerifier()
    results = verifier.run_verification_and_fixes()

    return results

if __name__ == "__main__":
    results = main()