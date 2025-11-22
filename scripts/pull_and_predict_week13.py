#!/usr/bin/env python3
"""
Pull Week 13 Data and Generate Predictions
==========================================

This script:
1. Fetches Week 13 2025 games from CFBD API
2. Generates predictions using trained models

Usage:
    CFBD_API_KEY=your_key python scripts/pull_and_predict_week13.py
"""

import os
import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

def main():
    print("=" * 80)
    print("WEEK 13 DATA PULL AND PREDICTION GENERATION")
    print("=" * 80)
    print()
    
    # Check for API key
    api_key = os.environ.get("CFBD_API_KEY")
    if not api_key:
        print("❌ ERROR: CFBD_API_KEY environment variable not set")
        print("   Please set it with: export CFBD_API_KEY=your_key_here")
        return 1
    
    print("Step 1: Fetching Week 13 games from CFBD API...")
    print("-" * 80)
    
    # Fetch week 13 data
    fetch_script = PROJECT_ROOT / "project_management" / "TOOLS_AND_CONFIG" / "fetch_future_week.py"
    try:
        result = subprocess.run(
            [sys.executable, str(fetch_script), "--week", "13", "--season", "2025"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
        if result.stderr:
            print("Warnings:", result.stderr)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error fetching week 13 data: {e}")
        print(f"   Output: {e.stdout}")
        print(f"   Error: {e.stderr}")
        return 1
    
    print("\n" + "=" * 80)
    print("Step 2: Generating Week 13 predictions...")
    print("-" * 80)
    
    # Generate predictions using weekly analysis script
    analysis_script = PROJECT_ROOT / "scripts" / "run_weekly_analysis.py"
    try:
        result = subprocess.run(
            [sys.executable, str(analysis_script), "--week", "13", "--season", "2025", "--step", "predictions"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            check=False  # Don't fail if predictions have issues
        )
        print(result.stdout)
        if result.stderr:
            print("Warnings/Errors:", result.stderr)
        
        if result.returncode == 0:
            print("\n✅ Week 13 predictions generated successfully!")
            print(f"   Check: predictions/week13/")
        else:
            print("\n⚠️  Prediction generation had issues, but may have partial results")
            print(f"   Check: predictions/week13/")
    except Exception as e:
        print(f"❌ Error generating predictions: {e}")
        return 1
    
    print("\n" + "=" * 80)
    print("✅ WEEK 13 DATA PULL AND PREDICTIONS COMPLETE")
    print("=" * 80)
    print("\nNext steps:")
    print("  - Check predictions: predictions/week13/")
    print("  - Check analysis: analysis/week13/")
    print("  - View detailed logs for any issues")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

