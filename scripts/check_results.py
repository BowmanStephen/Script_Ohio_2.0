#!/usr/bin/env python3
"""
Check if weekly analysis results exist
Quick script to see what results are available
"""

import sys
from pathlib import Path

def check_week_results(week: int):
    """Check if results exist for a given week"""
    base_dir = Path(__file__).parent.parent
    
    print(f"\n{'='*70}")
    print(f"Checking Week {week} Results")
    print(f"{'='*70}\n")
    
    # Check analysis directory
    analysis_dir = base_dir / "analysis" / f"week{week}"
    print(f"📊 Analysis Results: {analysis_dir}")
    if analysis_dir.exists():
        files = list(analysis_dir.glob("*"))
        if files:
            for f in sorted(files):
                size = f.stat().st_size if f.is_file() else 0
                size_str = f"({size:,} bytes)" if size > 0 else "(directory)"
                print(f"   ✅ {f.name} {size_str}")
        else:
            print(f"   ⚠️  Directory exists but is empty")
    else:
        print(f"   ❌ Directory does not exist - analysis not run yet")
    
    # Check predictions directory
    predictions_dir = base_dir / "predictions" / f"week{week}"
    print(f"\n🎯 Predictions: {predictions_dir}")
    if predictions_dir.exists():
        files = list(predictions_dir.glob("*"))
        if files:
            for f in sorted(files):
                size = f.stat().st_size if f.is_file() else 0
                size_str = f"({size:,} bytes)" if size > 0 else "(directory)"
                print(f"   ✅ {f.name} {size_str}")
        else:
            print(f"   ⚠️  Directory exists but is empty")
    else:
        print(f"   ❌ Directory does not exist - predictions not generated yet")
    
    # Check validation directory
    validation_dir = base_dir / "validation" / f"week{week}"
    print(f"\n🔍 Validation: {validation_dir}")
    if validation_dir.exists():
        files = list(validation_dir.glob("*"))
        if files:
            for f in sorted(files):
                size = f.stat().st_size if f.is_file() else 0
                size_str = f"({size:,} bytes)" if size > 0 else "(directory)"
                print(f"   ✅ {f.name} {size_str}")
        else:
            print(f"   ⚠️  Directory exists but is empty")
    else:
        print(f"   ❌ Directory does not exist - validation not run yet")
    
    # Summary
    has_analysis = analysis_dir.exists() and any(analysis_dir.glob("*"))
    has_predictions = predictions_dir.exists() and any(predictions_dir.glob("*"))
    has_validation = validation_dir.exists() and any(validation_dir.glob("*"))
    
    print(f"\n{'='*70}")
    if has_analysis and has_predictions:
        print(f"✅ Week {week} analysis complete!")
        print(f"   Results available in:")
        print(f"   - {analysis_dir}")
        print(f"   - {predictions_dir}")
    elif has_analysis or has_predictions:
        print(f"⚠️  Week {week} analysis partially complete")
        print(f"   Run: python scripts/run_weekly_analysis.py --week {week}")
    else:
        print(f"❌ Week {week} analysis not run yet")
        print(f"   Run: python scripts/run_weekly_analysis.py --week {week}")
    print(f"{'='*70}\n")


def list_all_weeks():
    """List all weeks that have results"""
    base_dir = Path(__file__).parent.parent
    
    print(f"\n{'='*70}")
    print("Available Week Results")
    print(f"{'='*70}\n")
    
    # Check analysis directories
    analysis_base = base_dir / "analysis"
    if analysis_base.exists():
        week_dirs = sorted([d for d in analysis_base.iterdir() if d.is_dir() and d.name.startswith("week")])
        if week_dirs:
            print("📊 Analysis Results Available:")
            for week_dir in week_dirs:
                files = list(week_dir.glob("*"))
                file_count = len([f for f in files if f.is_file()])
                if file_count > 0:
                    print(f"   ✅ {week_dir.name}: {file_count} files")
        else:
            print("   No week directories found in analysis/")
    else:
        print("   analysis/ directory does not exist")
    
    # Check predictions directories
    predictions_base = base_dir / "predictions"
    if predictions_base.exists():
        week_dirs = sorted([d for d in predictions_base.iterdir() if d.is_dir() and d.name.startswith("week")])
        if week_dirs:
            print("\n🎯 Predictions Available:")
            for week_dir in week_dirs:
                files = list(week_dir.glob("*"))
                file_count = len([f for f in files if f.is_file()])
                if file_count > 0:
                    print(f"   ✅ {week_dir.name}: {file_count} files")
        else:
            print("   No week directories found in predictions/")
    else:
        print("   predictions/ directory does not exist")
    
    print(f"\n{'='*70}\n")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Check if weekly analysis results exist")
    parser.add_argument('--week', type=int, help='Check specific week (e.g., 13)')
    parser.add_argument('--list', action='store_true', help='List all weeks with results')
    args = parser.parse_args()
    
    if args.list:
        list_all_weeks()
    elif args.week:
        check_week_results(args.week)
    else:
        # Default: check Week 13 and list all
        check_week_results(13)
        list_all_weeks()


if __name__ == "__main__":
    main()

