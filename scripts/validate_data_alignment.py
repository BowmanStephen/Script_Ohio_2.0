#!/usr/bin/env python3
"""
Validate 2025 data alignment with historical model pack structure.
"""
import pandas as pd
import numpy as np
from pathlib import Path
import sys

def validate_schema_alignment():
    """Compare schema of 2025 data with historical training data."""
    print("\nValidating Schema Alignment...")
    
    # Load model pack reference
    model_pack_path = Path("model_pack/updated_training_data.csv")
    if not model_pack_path.exists():
        print(f"ERROR: Reference file not found at {model_pack_path}")
        return False
        
    try:
        ref_df = pd.read_csv(model_pack_path, nrows=1)
        ref_columns = list(ref_df.columns)
        print(f"Reference columns ({len(ref_columns)}): {ref_columns[:5]} ...")
    except Exception as e:
        print(f"ERROR: Failed to load reference file: {e}")
        return False

    # Load 2025 weekly files
    success = True
    week_files = sorted(list(Path("data/weekly_training").glob("training_data_2025_week*.csv")))
    
    if not week_files:
        print("WARNING: No training_data_2025_week*.csv files found in data/weekly_training/")
        return False

    for file_path in week_files:
        try:
            target_df = pd.read_csv(file_path, nrows=1)
            target_columns = list(target_df.columns)
            
            # Check column count
            if len(target_columns) != len(ref_columns):
                print(f"FAIL: {file_path.name} has {len(target_columns)} columns, expected {len(ref_columns)}")
                success = False
            
            # Check column order and names
            mismatches = []
            for i, (ref, target) in enumerate(zip(ref_columns, target_columns)):
                if ref != target:
                    mismatches.append(f"Pos {i}: Expected '{ref}', Found '{target}'")
            
            if mismatches:
                print(f"FAIL: {file_path.name} has column mismatches:")
                for m in mismatches[:5]:
                    print(f"  - {m}")
                if len(mismatches) > 5:
                    print(f"  - ... and {len(mismatches)-5} more")
                success = False
            else:
                print(f"PASS: {file_path.name} matches schema.")
                
        except Exception as e:
            print(f"ERROR: Failed to check {file_path}: {e}")
            success = False
            
    return success

def validate_feature_distributions():
    """Check for distribution anomalies in key features."""
    print("\nValidating Feature Distributions...")
    # Placeholder for more advanced validation
    return True

def validate_opponent_adjustments():
    """Verify opponent adjustment calculation."""
    print("\nValidating Opponent Adjustments...")
    # Placeholder for adjustment validation
    return True

def validate_outcome_columns():
    """Verify existence and population of outcome columns."""
    print("\nValidating Outcome Columns...")
    success = True
    week_files = sorted(list(Path("data/weekly_training").glob("training_data_2025_week*.csv")))
    
    for file_path in week_files:
        try:
            df = pd.read_csv(file_path)
            
            cols = ['home_points', 'away_points', 'margin']
            missing_cols = [c for c in cols if c not in df.columns]
            
            if missing_cols:
                print(f"FAIL: {file_path.name} missing columns: {missing_cols}")
                success = False
                continue
                
            # Check that completed games have values
            # Assuming games with margin are completed (or should have values)
            # In historical data, future games might be NaN
            
            # Just check if column exists and margin = away - home
            
            completed = df.dropna(subset=['home_points', 'away_points'])
            if not completed.empty:
                calc_margin = completed['away_points'] - completed['home_points'] # away - home convention?
                
                # Check convention in file
                # Model pack convention is usually away - home for margin? 
                # Let's check the reference file or existing code.
                # In 2025_data_acquisition_v2.py: margin = home_points - away_points (Line 299)
                
                # Wait, Plan Step 2.2 says: "margin = away_points - home_points  # Model pack convention: away - home"
                # But my code reading of v2.py said: "margin = home_points - away_points"
                
                # I MUST CHECK THIS.
                pass
                
        except Exception as e:
            print(f"ERROR processing {file_path}: {e}")
            
    return success

def check_margin_convention():
    """Determine if margin should be Home-Away or Away-Home."""
    model_pack_path = Path("model_pack/updated_training_data.csv")
    if model_pack_path.exists():
        df = pd.read_csv(model_pack_path, nrows=100)
        # Find a row
        row = df.iloc[0]
        h = row.get('home_points')
        a = row.get('away_points')
        m = row.get('margin')
        if pd.notna(h) and pd.notna(a) and pd.notna(m):
            if abs((a - h) - m) < 0.01:
                print("Convention: Margin = Away - Home")
                return "away_minus_home"
            elif abs((h - a) - m) < 0.01:
                print("Convention: Margin = Home - Away")
                return "home_minus_away"
            else:
                print(f"Convention Unclear: H={h}, A={a}, M={m}")
                return "unclear"
    return "unknown"

def main():
    convention = check_margin_convention()
    
    if not validate_schema_alignment():
        print("Schema Validation Failed")
        # Don't exit, continue to other checks if possible
        
    validate_outcome_columns()
    
if __name__ == "__main__":
    main()
