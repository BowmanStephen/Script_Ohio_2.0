#!/usr/bin/env python3
"""
Fix 2025 Data Structure
=======================

This script ensures the 2025 data structure matches the original training_data.csv
format exactly by adding missing columns and ensuring compatibility.

Author: Data Acquisition Agent
Date: November 7, 2025
"""

import pandas as pd
import numpy as np

def fix_2025_data_structure():
    """Fix the 2025 data structure to match training_data.csv format."""

    # Load original training data to get column structure
    print("Loading original training data structure...")
    training_data = pd.read_csv('/Users/stephen_bowman/Documents/GitHub/Script_Ohio_2.0/model_pack/training_data.csv')
    training_columns = training_data.columns.tolist()

    print(f"Original training data has {len(training_columns)} columns")

    # Load 2025 mock data
    print("Loading 2025 mock data...")
    games_2025 = pd.read_csv('/Users/stephen_bowman/Documents/GitHub/Script_Ohio_2.0/model_pack/2025_raw_games.csv')

    print(f"2025 data currently has {len(games_2025.columns)} columns")

    # Find missing columns
    missing_columns = set(training_columns) - set(games_2025.columns)
    print(f"Missing columns: {len(missing_columns)}")

    # Add missing columns with default values
    for col in missing_columns:
        if col in training_data.columns:
            # Use historical average if possible, otherwise use realistic default
            if training_data[col].dtype in ['float64', 'int64']:
                default_value = training_data[col].mean()
                if pd.isna(default_value):
                    default_value = 0.0
                games_2025[col] = default_value
            else:
                # For categorical/string columns, use empty string
                games_2025[col] = ''
            print(f"Added column: {col}")

    # Reorder columns to match training data exactly
    # Keep any additional columns from 2025 data at the end
    common_columns = [col for col in training_columns if col in games_2025.columns]
    extra_columns = [col for col in games_2025.columns if col not in training_columns]

    final_column_order = common_columns + extra_columns
    games_2025 = games_2025[final_column_order]

    # Save the corrected data
    output_file = '/Users/stephen_bowman/Documents/GitHub/Script_Ohio_2.0/model_pack/2025_raw_games_fixed.csv'
    games_2025.to_csv(output_file, index=False)

    print(f"Fixed data saved as: {output_file}")
    print(f"Final structure has {len(games_2025.columns)} columns")
    print(f"Games included: {len(games_2025)}")

    # Show data sample
    print("\nSample of corrected data:")
    print(games_2025.head(2).to_string())

    return games_2025

if __name__ == "__main__":
    fix_2025_data_structure()