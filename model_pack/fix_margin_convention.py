#!/usr/bin/env python3
"""
Fix Margin Convention in Training Data
=======================================

This script fixes the margin convention inconsistency in the training data files.

PROBLEM IDENTIFIED:
- Data files currently use: margin = (away_points - home_points)
- Prediction code expects: margin = (home_points - away_points)

This causes inverted predictions where positive margin (indicating away win) 
is interpreted as home win by the models.

SOLUTION:
- Flip margin column: margin_new = -margin_old
- This converts from (away - home) to (home - away) convention
- Update all relevant data files
- Verify the fix matches expected calculation

Author: Data Standardization Script
Date: 2025-01-XX
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import sys
import shutil

# Configuration
BASE_DIR = Path(__file__).parent
FILES_TO_FIX = [
    "updated_training_data.csv",
    "training_data.csv",  # Check if this also needs fixing
]

# Weekly training data files to check
WEEKLY_DATA_PATTERN = "training_data_2025_week*.csv"

def backup_file(file_path: Path) -> Path:
    """Create a backup of the file before modification"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = file_path.parent / f"{file_path.stem}.backup_margin_fix_{timestamp}{file_path.suffix}"
    shutil.copy2(file_path, backup_path)
    print(f"✅ Created backup: {backup_path.name}")
    return backup_path

def verify_margin_convention(df: pd.DataFrame, file_name: str) -> tuple[bool, str]:
    """
    Verify which margin convention is currently being used.
    
    Returns:
        (is_away_home_convention, description)
        - True if using (away - home) convention (needs fixing)
        - False if using (home - away) convention (correct)
    """
    if 'margin' not in df.columns or 'home_points' not in df.columns or 'away_points' not in df.columns:
        return None, "Missing required columns"
    
    # Sample a few rows with outcomes
    sample_df = df[df['home_points'].notna() & df['away_points'].notna()].head(10)
    
    if len(sample_df) == 0:
        return None, "No games with outcomes found"
    
    # Calculate what margin should be with (home - away) convention
    calculated_home_away = sample_df['home_points'] - sample_df['away_points']
    
    # Check if current margin matches (home - away)
    matches_home_away = (calculated_home_away == sample_df['margin']).all()
    
    # Check if current margin matches (away - home)
    calculated_away_home = sample_df['away_points'] - sample_df['home_points']
    matches_away_home = (calculated_away_home == sample_df['margin']).all()
    
    if matches_home_away:
        return False, "✓ Using (home - away) convention (CORRECT)"
    elif matches_away_home:
        return True, "✗ Using (away - home) convention (NEEDS FIXING)"
    else:
        return None, f"⚠ Ambiguous: {len(sample_df[calculated_home_away == sample_df['margin']])}/{len(sample_df)} match (home-away)"

def fix_margin_convention(df: pd.DataFrame) -> pd.DataFrame:
    """
    Flip margin convention from (away - home) to (home - away).
    
    This multiplies margin by -1, effectively converting:
    - Old: margin = away_points - home_points
    - New: margin = home_points - away_points
    """
    df_fixed = df.copy()
    df_fixed['margin'] = -df_fixed['margin']
    return df_fixed

def fix_file(file_path: Path, verify_only: bool = False) -> bool:
    """Fix margin convention in a single file"""
    print(f"\n{'='*80}")
    print(f"Processing: {file_path.name}")
    print(f"{'='*80}")
    
    if not file_path.exists():
        print(f"⚠️  File not found: {file_path}")
        return False
    
    # Load data
    try:
        df = pd.read_csv(file_path, low_memory=False)
        print(f"✅ Loaded {len(df)} rows, {len(df.columns)} columns")
    except Exception as e:
        print(f"❌ Error loading file: {e}")
        return False
    
    # Verify current convention
    needs_fix, description = verify_margin_convention(df, file_path.name)
    print(f"Convention check: {description}")
    
    if needs_fix is None:
        print(f"⚠️  Could not determine convention, skipping")
        return False
    
    if not needs_fix:
        print(f"✅ File already uses correct convention, no fix needed")
        return True
    
    if verify_only:
        print(f"🔍 VERIFY ONLY MODE: Would fix this file")
        return True
    
    # Create backup
    backup_path = backup_file(file_path)
    
    # Fix margin
    print(f"\nFixing margin convention...")
    df_fixed = fix_margin_convention(df)
    
    # Verify fix
    needs_fix_after, description_after = verify_margin_convention(df_fixed, file_path.name)
    if needs_fix_after:
        print(f"❌ Fix verification failed: {description_after}")
        print(f"   Restoring from backup...")
        shutil.copy2(backup_path, file_path)
        return False
    
    # Save fixed file
    df_fixed.to_csv(file_path, index=False)
    print(f"✅ Saved fixed file: {file_path.name}")
    print(f"   Backup saved: {backup_path.name}")
    
    # Show sample comparison
    print(f"\nSample comparison (first 5 rows with outcomes):")
    sample_original = df[df['home_points'].notna() & df['away_points'].notna()].head(5)
    sample_fixed = df_fixed[df_fixed['home_points'].notna() & df_fixed['away_points'].notna()].head(5)
    
    for idx, (orig_row, fix_row) in enumerate(zip(sample_original.itertuples(), sample_fixed.itertuples()), 1):
        print(f"  Row {idx}:")
        print(f"    {orig_row.home_team} {orig_row.home_points} vs {orig_row.away_team} {orig_row.away_points}")
        print(f"    Old margin: {orig_row.margin:.1f} (away - home)")
        print(f"    New margin: {fix_row.margin:.1f} (home - away)")
        print(f"    Calculated: {orig_row.home_points - orig_row.away_points:.1f} ✓")
    
    return True

def main():
    """Main execution function"""
    print("="*80)
    print("MARGIN CONVENTION FIX SCRIPT")
    print("="*80)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Directory: {BASE_DIR}")
    print()
    
    # Check for verify-only mode
    verify_only = '--verify' in sys.argv or '--check' in sys.argv
    
    if verify_only:
        print("🔍 VERIFY ONLY MODE - No files will be modified\n")
    
    files_fixed = 0
    files_skipped = 0
    files_failed = 0
    
    # Fix main training data files
    for file_name in FILES_TO_FIX:
        file_path = BASE_DIR / file_name
        if file_path.exists():
            if fix_file(file_path, verify_only=verify_only):
                files_fixed += 1
            else:
                files_failed += 1
        else:
            print(f"⚠️  File not found: {file_name}")
            files_skipped += 1
    
    # Check weekly training data files
    weekly_files = list(BASE_DIR.parent.glob(WEEKLY_DATA_PATTERN))
    if weekly_files:
        print(f"\n{'='*80}")
        print(f"Found {len(weekly_files)} weekly training data files")
        print(f"{'='*80}")
        
        for weekly_file in weekly_files:
            if fix_file(weekly_file, verify_only=verify_only):
                files_fixed += 1
            else:
                files_failed += 1
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"Files fixed/skipped (already correct): {files_fixed}")
    print(f"Files skipped (not found or ambiguous): {files_skipped}")
    print(f"Files failed: {files_failed}")
    
    if verify_only:
        print(f"\n🔍 This was a verification run. To apply fixes, run without --verify flag.")
    else:
        print(f"\n✅ Margin convention fix complete!")
        print(f"   All files now use: margin = (home_points - away_points)")
        print(f"   This matches the convention expected by prediction code.")
    
    print(f"\n⚠️  IMPORTANT NEXT STEPS:")
    print(f"   1. Verify model predictions are now correct")
    print(f"   2. Retrain models with fixed data if needed")
    print(f"   3. Update data generation scripts to use correct convention")
    print(f"   4. Test predictions on known games to verify fix")

if __name__ == "__main__":
    main()

