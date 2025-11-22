#!/usr/bin/env python3
"""
Verify Weekly Training File Equivalence

Compares weekly training data files between root level and data/weekly_training/
to identify duplicates and determine which files are canonical.
"""

import os
import sys
import hashlib
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import argparse

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def calculate_file_hash(file_path: Path) -> str:
    """Calculate MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def get_file_info(file_path: Path) -> Dict:
    """Get file metadata."""
    if not file_path.exists():
        return None
    
    stat = file_path.stat()
    return {
        "path": str(file_path),
        "size": stat.st_size,
        "modified": datetime.fromtimestamp(stat.st_mtime),
        "hash": calculate_file_hash(file_path),
        "rows": None,
        "columns": None
    }


def get_dataframe_info(file_path: Path) -> Dict:
    """Get DataFrame metadata (rows, columns)."""
    try:
        df = pd.read_csv(file_path, low_memory=False, nrows=0)  # Read headers only
        return {
            "rows": len(pd.read_csv(file_path, low_memory=False)),
            "columns": len(df.columns),
            "column_names": list(df.columns)
        }
    except Exception as e:
        return {"error": str(e)}


def compare_weekly_files(week: int, season: int = 2025) -> Dict:
    """Compare weekly training file between root and data/weekly_training/."""
    filename = f"training_data_{season}_week{week:02d}.csv"
    
    root_file = PROJECT_ROOT / filename
    weekly_training_file = PROJECT_ROOT / "data" / "weekly_training" / filename
    
    result = {
        "week": week,
        "filename": filename,
        "root_exists": root_file.exists(),
        "weekly_training_exists": weekly_training_file.exists(),
        "root_info": None,
        "weekly_training_info": None,
        "equivalent": False,
        "canonical": None
    }
    
    # Get root file info
    if root_file.exists():
        result["root_info"] = get_file_info(root_file)
        df_info = get_dataframe_info(root_file)
        if result["root_info"]:
            result["root_info"].update(df_info)
    
    # Get weekly_training file info
    if weekly_training_file.exists():
        result["weekly_training_info"] = get_file_info(weekly_training_file)
        df_info = get_dataframe_info(weekly_training_file)
        if result["weekly_training_info"]:
            result["weekly_training_info"].update(df_info)
    
    # Compare if both exist
    if root_file.exists() and weekly_training_file.exists():
        root_hash = result["root_info"]["hash"]
        weekly_hash = result["weekly_training_info"]["hash"]
        result["equivalent"] = (root_hash == weekly_hash)
        
        # Determine canonical (prefer newer, or root if same)
        root_modified = result["root_info"]["modified"]
        weekly_modified = result["weekly_training_info"]["modified"]
        
        if root_modified > weekly_modified:
            result["canonical"] = "root"
        elif weekly_modified > root_modified:
            result["canonical"] = "weekly_training"
        else:
            # Same timestamp, prefer weekly_training as organized location
            result["canonical"] = "weekly_training"
    
    elif root_file.exists():
        result["canonical"] = "root"
    elif weekly_training_file.exists():
        result["canonical"] = "weekly_training"
    
    return result


def generate_report(weeks: List[int], season: int = 2025) -> str:
    """Generate comparison report for all weeks."""
    results = []
    for week in weeks:
        results.append(compare_weekly_files(week, season))
    
    # Summary statistics
    total_files = len(results)
    both_exist = sum(1 for r in results if r["root_exists"] and r["weekly_training_exists"])
    duplicates = sum(1 for r in results if r["equivalent"] and r["root_exists"] and r["weekly_training_exists"])
    different = sum(1 for r in results if r["root_exists"] and r["weekly_training_exists"] and not r["equivalent"])
    root_only = sum(1 for r in results if r["root_exists"] and not r["weekly_training_exists"])
    weekly_only = sum(1 for r in results if r["weekly_training_exists"] and not r["root_exists"])
    
    # Build report
    report_lines = [
        "=" * 80,
        "Weekly Training File Equivalence Report",
        "=" * 80,
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Season: {season}",
        "",
        "SUMMARY",
        "-" * 80,
        f"Total weeks analyzed: {total_files}",
        f"Files in both locations: {both_exist}",
        f"Identical files (duplicates): {duplicates}",
        f"Different files: {different}",
        f"Root-only files: {root_only}",
        f"Weekly training-only files: {weekly_only}",
        "",
        "DETAILED COMPARISON",
        "-" * 80,
    ]
    
    for result in results:
        report_lines.append(f"\nWeek {result['week']:02d}: {result['filename']}")
        
        if result["root_exists"] and result["weekly_training_exists"]:
            if result["equivalent"]:
                report_lines.append(f"  ✅ DUPLICATE: Files are identical")
                report_lines.append(f"     Canonical: {result['canonical']}")
            else:
                report_lines.append(f"  ⚠️  DIFFERENT: Files have different content")
                report_lines.append(f"     Root: {result['root_info']['size']} bytes, "
                                  f"{result['root_info']['rows']} rows, "
                                  f"modified {result['root_info']['modified']}")
                report_lines.append(f"     Weekly: {result['weekly_training_info']['size']} bytes, "
                                  f"{result['weekly_training_info']['rows']} rows, "
                                  f"modified {result['weekly_training_info']['modified']}")
                report_lines.append(f"     Canonical: {result['canonical']} (newer)")
        elif result["root_exists"]:
            report_lines.append(f"  📁 ROOT ONLY: File exists only at root")
            if result["root_info"]:
                report_lines.append(f"     Size: {result['root_info']['size']} bytes, "
                                  f"{result['root_info']['rows']} rows")
        elif result["weekly_training_exists"]:
            report_lines.append(f"  📁 WEEKLY ONLY: File exists only in data/weekly_training/")
            if result["weekly_training_info"]:
                report_lines.append(f"     Size: {result['weekly_training_info']['size']} bytes, "
                                  f"{result['weekly_training_info']['rows']} rows")
        else:
            report_lines.append(f"  ❌ MISSING: File not found in either location")
    
    report_lines.append("\n" + "=" * 80)
    report_lines.append("RECOMMENDATIONS")
    report_lines.append("-" * 80)
    
    if duplicates > 0:
        report_lines.append(f"- {duplicates} duplicate files can be removed from root after migration")
    
    if different > 0:
        report_lines.append(f"- {different} files differ between locations - investigate which is correct")
    
    if root_only > 0:
        report_lines.append(f"- {root_only} files exist only at root - should be moved to data/training/weekly/")
    
    if weekly_only > 0:
        report_lines.append(f"- {weekly_only} files exist only in data/weekly_training/ - already organized")
    
    report_lines.append("\n" + "=" * 80)
    
    return "\n".join(report_lines)


def main():
    parser = argparse.ArgumentParser(description="Verify weekly training file equivalence")
    parser.add_argument("--season", type=int, default=2025, help="Season year (default: 2025)")
    parser.add_argument("--weeks", type=int, nargs="+", default=list(range(1, 14)),
                       help="Week numbers to check (default: 1-13)")
    parser.add_argument("--output", type=str, help="Output file path (default: print to stdout)")
    
    args = parser.parse_args()
    
    report = generate_report(args.weeks, args.season)
    
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            f.write(report)
        print(f"Report written to: {output_path}")
    else:
        print(report)


if __name__ == "__main__":
    main()

