#!/usr/bin/env python3
"""
Migrate Training Data Files

Systematically migrates weekly training data files from root and data/weekly_training/
to the canonical location: data/training/weekly/

This script:
1. Compares root files vs data/weekly_training/ files (uses root as canonical if newer)
2. Moves canonical version to data/training/weekly/
3. Logs all moves
4. Generates verification report
5. Optionally removes duplicates after migration
"""

import os
import sys
import shutil
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import hashlib

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(PROJECT_ROOT / 'logs' / 'migrate_training_data.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def calculate_file_hash(file_path: Path) -> str:
    """Calculate MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def find_canonical_file(week: int, season: int = 2025, project_root: Path = PROJECT_ROOT) -> Tuple[Optional[Path], str]:
    """
    Find canonical version of weekly training file.
    
    Returns:
        Tuple of (canonical_path, source_location)
        source_location: 'root', 'weekly_training', or 'neither'
    """
    filename = f"training_data_{season}_week{week:02d}.csv"
    
    root_file = project_root / filename
    weekly_training_file = project_root / "data" / "weekly_training" / filename
    
    root_exists = root_file.exists()
    weekly_exists = weekly_training_file.exists()
    
    if not root_exists and not weekly_exists:
        return None, "neither"
    
    if root_exists and not weekly_exists:
        return root_file, "root"
    
    if weekly_exists and not root_exists:
        return weekly_training_file, "weekly_training"
    
    # Both exist - compare timestamps
    root_mtime = root_file.stat().st_mtime
    weekly_mtime = weekly_training_file.stat().st_mtime
    
    if root_mtime >= weekly_mtime:
        # Root is newer or same - prefer root
        return root_file, "root"
    else:
        # Weekly is newer - prefer weekly_training
        return weekly_training_file, "weekly_training"


def migrate_weekly_file(week: int, season: int = 2025, project_root: Path = PROJECT_ROOT,
                        dry_run: bool = False) -> Dict:
    """
    Migrate a single weekly training file to canonical location.
    
    Returns:
        Dict with migration status and details
    """
    filename = f"training_data_{season}_week{week:02d}.csv"
    canonical_path = project_root / "data" / "training" / "weekly" / filename
    
    result = {
        "week": week,
        "filename": filename,
        "status": "skipped",
        "source": None,
        "canonical_path": str(canonical_path),
        "dry_run": dry_run
    }
    
    # Find canonical file
    source_file, source_location = find_canonical_file(week, season, project_root)
    
    if source_file is None:
        result["status"] = "not_found"
        result["error"] = f"Week {week} file not found in root or data/weekly_training/"
        logger.warning(f"Week {week}: {result['error']}")
        return result
    
    result["source"] = source_location
    result["source_path"] = str(source_file)
    
    # Check if canonical location already has file
    if canonical_path.exists():
        # Compare hashes
        source_hash = calculate_file_hash(source_file)
        canonical_hash = calculate_file_hash(canonical_path)
        
        if source_hash == canonical_hash:
            result["status"] = "already_migrated"
            logger.info(f"Week {week}: Already in canonical location (identical)")
            return result
        else:
            # Files differ - backup existing and overwrite
            if not dry_run:
                backup_path = canonical_path.with_suffix(f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
                shutil.copy2(canonical_path, backup_path)
                logger.info(f"Week {week}: Backed up existing file to {backup_path}")
    
    # Create target directory if needed
    canonical_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Move file
    if not dry_run:
        shutil.copy2(source_file, canonical_path)
        logger.info(f"Week {week}: Migrated from {source_location} to {canonical_path}")
        result["status"] = "migrated"
    else:
        logger.info(f"Week {week}: [DRY RUN] Would migrate from {source_location} to {canonical_path}")
        result["status"] = "would_migrate"
    
    return result


def remove_duplicates(week: int, season: int = 2025, project_root: Path = PROJECT_ROOT,
                     dry_run: bool = False, keep_canonical: bool = True) -> Dict:
    """
    Remove duplicate files from root and data/weekly_training/ after migration.
    
    Args:
        keep_canonical: If True, only remove if file exists in canonical location and matches
    """
    filename = f"training_data_{season}_week{week:02d}.csv"
    canonical_path = project_root / "data" / "training" / "weekly" / filename
    
    result = {
        "week": week,
        "removed_root": False,
        "removed_weekly": False,
        "dry_run": dry_run
    }
    
    if not canonical_path.exists():
        logger.warning(f"Week {week}: Cannot remove duplicates - canonical file does not exist")
        return result
    
    canonical_hash = calculate_file_hash(canonical_path)
    
    # Check root file
    root_file = project_root / filename
    if root_file.exists():
        root_hash = calculate_file_hash(root_file)
        if root_hash == canonical_hash:
            if not dry_run:
                root_file.unlink()
                logger.info(f"Week {week}: Removed duplicate from root")
            else:
                logger.info(f"Week {week}: [DRY RUN] Would remove duplicate from root")
            result["removed_root"] = True
    
    # Check weekly_training file
    weekly_file = project_root / "data" / "weekly_training" / filename
    if weekly_file.exists():
        weekly_hash = calculate_file_hash(weekly_file)
        if weekly_hash == canonical_hash:
            if not dry_run:
                weekly_file.unlink()
                logger.info(f"Week {week}: Removed duplicate from data/weekly_training/")
            else:
                logger.info(f"Week {week}: [DRY RUN] Would remove duplicate from data/weekly_training/")
            result["removed_weekly"] = True
    
    return result


def migrate_all_weeks(weeks: List[int], season: int = 2025, project_root: Path = PROJECT_ROOT,
                      dry_run: bool = False, remove_dups: bool = False) -> Dict:
    """Migrate all weekly training files."""
    results = {
        "migrations": [],
        "removals": [],
        "summary": {}
    }
    
    for week in weeks:
        # Migrate
        migration_result = migrate_weekly_file(week, season, project_root, dry_run)
        results["migrations"].append(migration_result)
        
        # Remove duplicates if requested
        if remove_dups and migration_result["status"] in ["migrated", "already_migrated", "would_migrate"]:
            removal_result = remove_duplicates(week, season, project_root, dry_run)
            results["removals"].append(removal_result)
    
    # Generate summary
    status_counts = {}
    for mig in results["migrations"]:
        status = mig["status"]
        status_counts[status] = status_counts.get(status, 0) + 1
    
    results["summary"] = {
        "total_weeks": len(weeks),
        "status_counts": status_counts,
        "removed_duplicates": sum(1 for r in results["removals"] if r["removed_root"] or r["removed_weekly"])
    }
    
    return results


def generate_report(results: Dict, output_path: Optional[Path] = None) -> str:
    """Generate migration report."""
    lines = [
        "=" * 80,
        "Training Data Migration Report",
        "=" * 80,
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Dry Run: {results['migrations'][0]['dry_run'] if results['migrations'] else False}",
        "",
        "SUMMARY",
        "-" * 80,
    ]
    
    summary = results["summary"]
    lines.append(f"Total weeks processed: {summary['total_weeks']}")
    lines.append(f"Status breakdown:")
    for status, count in summary["status_counts"].items():
        lines.append(f"  {status}: {count}")
    lines.append(f"Duplicates removed: {summary['removed_duplicates']}")
    
    lines.append("")
    lines.append("DETAILED RESULTS")
    lines.append("-" * 80)
    
    for mig in results["migrations"]:
        lines.append(f"\nWeek {mig['week']:02d}: {mig['filename']}")
        lines.append(f"  Status: {mig['status']}")
        if mig.get("source"):
            lines.append(f"  Source: {mig['source']} ({mig.get('source_path', 'N/A')})")
        lines.append(f"  Canonical: {mig['canonical_path']}")
        if mig.get("error"):
            lines.append(f"  Error: {mig['error']}")
    
    lines.append("\n" + "=" * 80)
    
    report = "\n".join(lines)
    
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            f.write(report)
        logger.info(f"Report written to: {output_path}")
    
    return report


def main():
    parser = argparse.ArgumentParser(description="Migrate weekly training data files to canonical location")
    parser.add_argument("--season", type=int, default=2025, help="Season year (default: 2025)")
    parser.add_argument("--weeks", type=int, nargs="+", default=list(range(1, 14)),
                       help="Week numbers to migrate (default: 1-13)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    parser.add_argument("--remove-duplicates", action="store_true",
                       help="Remove duplicate files from root and data/weekly_training/ after migration")
    parser.add_argument("--output", type=str, help="Output file path for report (default: reports/migration_report.txt)")
    
    args = parser.parse_args()
    
    # Ensure logs directory exists
    (PROJECT_ROOT / "logs").mkdir(exist_ok=True)
    
    logger.info("=" * 80)
    logger.info("Starting Training Data Migration")
    logger.info(f"Season: {args.season}")
    logger.info(f"Weeks: {args.weeks}")
    logger.info(f"Dry Run: {args.dry_run}")
    logger.info(f"Remove Duplicates: {args.remove_duplicates}")
    logger.info("=" * 80)
    
    # Migrate files
    results = migrate_all_weeks(
        args.weeks,
        args.season,
        PROJECT_ROOT,
        args.dry_run,
        args.remove_duplicates
    )
    
    # Generate report
    output_path = Path(args.output) if args.output else PROJECT_ROOT / "reports" / "migration_report.txt"
    report = generate_report(results, output_path)
    
    if not args.dry_run:
        logger.info("Migration complete!")
    else:
        logger.info("Dry run complete - no files were modified")
    
    print(report)


if __name__ == "__main__":
    main()

