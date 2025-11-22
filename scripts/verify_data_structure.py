#!/usr/bin/env python3
"""
Verify Data Structure and File Locations
========================================
Checks if the project structure reorganization was successful.
"""

import os
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def check_path(path, description):
    if path.exists():
        print(f"✅ Found {description}: {path}")
        return True
    else:
        print(f"❌ Missing {description}: {path}")
        return False

def verify_structure():
    print("Verifying Directory Structure...")
    
    # Check weekly training directory
    weekly_dir = PROJECT_ROOT / 'data' / 'weekly_training'
    if not check_path(weekly_dir, "Weekly Training Directory"):
        return False
    
    # Check weekly files
    weeks = ['05', '06', '07', '08', '09', '10', '11', '12', '13']
    all_weeks_present = True
    for week in weeks:
        path = weekly_dir / f'training_data_2025_week{week}.csv'
        if not check_path(path, f"Week {week} Data"):
            all_weeks_present = False
            
    if all_weeks_present:
        print("✅ All weekly training files present.")
    
    # Check script updates (simple grep-like check)
    print("\nVerifying Script Updates...")
    
    scripts_to_check = [
        ('scripts/combine_weeks_5_13_and_retrain.py', 'weekly_training'),
        ('scripts/recover_missing_games_local_first.py', 'weekly_training'),
        ('scripts/validate_data_alignment.py', 'weekly_training')
    ]
    
    all_scripts_updated = True
    for script_rel, string_to_find in scripts_to_check:
        script_path = PROJECT_ROOT / script_rel
        if script_path.exists():
            content = script_path.read_text()
            if string_to_find in content:
                print(f"✅ Script updated: {script_rel}")
            else:
                print(f"❌ Script NOT updated (missing '{string_to_find}'): {script_rel}")
                all_scripts_updated = False
        else:
             print(f"❌ Script not found: {script_rel}")
             all_scripts_updated = False
             
    # Check for removal of copy directories references
    recover_script = PROJECT_ROOT / 'scripts/recover_missing_games_local_first.py'
    if recover_script.exists():
        content = recover_script.read_text()
        if 'starter_pack copy' in content or 'model_pack copy' in content:
             print(f"❌ 'copy' directory references still found in {recover_script.name}")
             all_scripts_updated = False
        else:
             print(f"✅ 'copy' directory references removed from {recover_script.name}")

    return all_weeks_present and all_scripts_updated

if __name__ == "__main__":
    success = verify_structure()
    if success:
        print("\n🎉 Verification Successful! Project structure is correct.")
        sys.exit(0)
    else:
        print("\n⚠️  Verification Failed. Please check errors above.")
        sys.exit(1)

