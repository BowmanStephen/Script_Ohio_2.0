#!/usr/bin/env python3
"""
Organize Model Pack Backup Files

Scans model_pack/ directory for backup files and organizes them into a structured
directory hierarchy.

Backup patterns detected:
- *.backup
- *.backup_*
- *_BACKUP_*
- *backup_*
- .backup*

Organization structure:
- backups/data/daily/ - timestamped data backups
- backups/models/daily/ - timestamped model backups
- backups/data/critical/ - pre-fix backups
- backups/models/critical/ - pre-major-change backups
"""

import argparse
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# Backup filename patterns
BACKUP_PATTERNS = [
    r'.*\.backup$',
    r'.*\.backup\d+$',  # .backup2, .backup3, etc.
    r'.*\.backup_.*',
    r'.*_BACKUP_.*',
    r'.*backup_.*',
    r'\.backup.*'
]

# Directory backup patterns (directories that are backups)
DIRECTORY_BACKUP_PATTERNS = [
    r'.*_backup_\d+$',      # models_backup_20251114_135815
    r'.*_backup_\d+_\d+$',  # models_backup_20251114_135815 (full timestamp)
    r'.*BACKUP_\d+$',       # MODELS_BACKUP_20251114
    r'.*_backup$',          # models_backup
]

# Critical backup indicators (pre-fix or pre-major-change)
CRITICAL_INDICATORS = [
    'margin_fix',
    'before_fix',
    'pre_fix',
    'critical',
    'major_change',
    'before_migration'
]

# Data file extensions
DATA_EXTENSIONS = {'.csv'}

# Model file extensions
MODEL_EXTENSIONS = {'.pkl', '.joblib', '.pth', '.pt', '.h5'}

# Timestamp pattern: YYYYMMDD_HHMMSS
TIMESTAMP_PATTERN = r'(\d{8})_(\d{6})'


def parse_timestamp(filename: str) -> Optional[datetime]:
    """Extract timestamp from filename if present."""
    match = re.search(TIMESTAMP_PATTERN, filename)
    if match:
        date_str = match.group(1)
        time_str = match.group(2)
        try:
            return datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
        except ValueError:
            return None
    return None


def is_critical_backup(filename: str) -> bool:
    """Check if backup is marked as critical."""
    filename_lower = filename.lower()
    return any(indicator in filename_lower for indicator in CRITICAL_INDICATORS)


def categorize_file(file_path: Path) -> Optional[str]:
    """Categorize file as 'data' or 'models' based on extension."""
    filename = file_path.name.lower()
    
    # Check direct suffix first
    suffix = file_path.suffix.lower()
    if suffix in DATA_EXTENSIONS:
        return 'data'
    elif suffix in MODEL_EXTENSIONS:
        return 'models'
    
    # Check for backup patterns with extensions
    # e.g., file.pkl.backup_20251118, file.csv.backup, etc.
    for model_ext in MODEL_EXTENSIONS:
        if filename.startswith(f'{model_ext}.backup') or f'{model_ext}.backup' in filename:
            return 'models'
    
    for data_ext in DATA_EXTENSIONS:
        if filename.startswith(f'{data_ext}.backup') or f'{data_ext}.backup' in filename:
            return 'data'
    
    # Check base name before .backup for files ending in .backup
    if filename.endswith('.backup'):
        base_name = file_path.stem
        base_path = Path(base_name)
        base_suffix = base_path.suffix.lower()
        if base_suffix in DATA_EXTENSIONS:
            return 'data'
        elif base_suffix in MODEL_EXTENSIONS:
            return 'models'
    
    # Try to infer from filename patterns (e.g., contains "model" or "training_data")
    if 'model' in filename and any(ext in filename for ext in MODEL_EXTENSIONS):
        return 'models'
    elif 'training_data' in filename or 'data' in filename:
        return 'data'
    
    return None


def matches_backup_pattern(filename: str) -> bool:
    """Check if filename matches any backup pattern."""
    for pattern in BACKUP_PATTERNS:
        if re.match(pattern, filename, re.IGNORECASE):
            return True
    return False


def matches_directory_backup_pattern(dirname: str) -> bool:
    """Check if directory name matches any backup pattern."""
    dirname_lower = dirname.lower()
    for pattern in DIRECTORY_BACKUP_PATTERNS:
        if re.match(pattern, dirname_lower):
            return True
    # Also check if it contains "backup" as a keyword (catch-all)
    if 'backup' in dirname_lower and not dirname_lower.startswith('.'):
        return True
    return False


def find_backup_files(model_pack_dir: Path) -> List[Path]:
    """Find all backup files and directories in model_pack directory."""
    backup_items = []
    backups_dir = model_pack_dir / 'backups'
    
    # Find backup files
    for file_path in model_pack_dir.rglob('*'):
        # Skip if already in backups subdirectories
        if backups_dir in file_path.parents:
            continue
        
        # Check if it's a file and matches backup pattern
        if file_path.is_file() and matches_backup_pattern(file_path.name):
            backup_items.append(file_path)
    
    # Find backup directories (only in model_pack root, not recursive)
    for item_path in model_pack_dir.iterdir():
        # Skip the backups directory itself
        if item_path.name == 'backups' and item_path.is_dir():
            continue
        
        # Skip if already in backups subdirectories
        if backups_dir in item_path.parents:
            continue
        
        # Check if it's a directory and matches backup pattern
        if item_path.is_dir() and matches_directory_backup_pattern(item_path.name):
            backup_items.append(item_path)
    
    return backup_items


def organize_backups(model_pack_dir: Path, dry_run: bool = False) -> Dict[str, List[str]]:
    """
    Organize backup files into structured directories.
    
    Returns:
        Dictionary with 'moved', 'skipped', and 'errors' lists
    """
    backups_dir = model_pack_dir / 'backups'
    
    # Create directory structure
    dirs_to_create = [
        backups_dir / 'data' / 'daily',
        backups_dir / 'data' / 'critical',
        backups_dir / 'models' / 'daily',
        backups_dir / 'models' / 'critical',
    ]
    
    if not dry_run:
        for dir_path in dirs_to_create:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    # Find all backup files
    backup_files = find_backup_files(model_pack_dir)
    
    results = {
        'moved': [],
        'skipped': [],
        'errors': []
    }
    
    # Generate migration log timestamp
    log_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_lines = [
        f"Backup Organization Log - {datetime.now().isoformat()}",
        f"{'DRY RUN MODE' if dry_run else 'EXECUTION MODE'}",
        "=" * 80,
        ""
    ]
    
    for item_path in sorted(backup_files):
        try:
            # Handle directories differently
            if item_path.is_dir():
                # For directories, determine category from name
                dirname = item_path.name.lower()
                if 'model' in dirname:
                    category = 'models'
                elif 'data' in dirname or 'training' in dirname:
                    category = 'data'
                else:
                    # Default to data for unknown directory backups
                    category = 'data'
                
                # Directories are typically critical backups
                is_critical = True
            else:
                # Categorize file
                category = categorize_file(item_path)
                if not category:
                    results['skipped'].append(f"{item_path.name} (unknown type)")
                    log_lines.append(f"SKIPPED: {item_path.name} (unknown file type)")
                    continue
                
                # Determine if critical
                is_critical = is_critical_backup(item_path.name)
            
            # Determine if critical (if not already set for directories)
            if item_path.is_file():
                is_critical = is_critical_backup(item_path.name)
            
            # Determine destination
            if is_critical:
                dest_dir = backups_dir / category / 'critical'
            else:
                dest_dir = backups_dir / category / 'daily'
            
            dest_path = dest_dir / item_path.name
            
            # Check if destination already exists
            if dest_path.exists():
                results['skipped'].append(f"{item_path.name} (destination exists)")
                log_lines.append(f"SKIPPED: {item_path.name} (already exists at {dest_path})")
                continue
            
            # Move file or directory
            if dry_run:
                item_type = "DIR" if item_path.is_dir() else "FILE"
                log_lines.append(f"WOULD MOVE [{item_type}]: {item_path} -> {dest_path}")
                results['moved'].append(f"{item_path.name} [{item_type}] -> {dest_path.relative_to(model_pack_dir)}")
            else:
                shutil.move(str(item_path), str(dest_path))
                item_type = "DIR" if item_path.is_dir() else "FILE"
                log_lines.append(f"MOVED [{item_type}]: {item_path} -> {dest_path}")
                results['moved'].append(f"{item_path.name} [{item_type}] -> {dest_path.relative_to(model_pack_dir)}")
        
        except Exception as e:
            error_msg = f"{item_path.name}: {str(e)}"
            results['errors'].append(error_msg)
            log_lines.append(f"ERROR: {item_path.name} - {str(e)}")
    
    # Write migration log
    if not dry_run:
        log_file = backups_dir / f"migration_log_{log_timestamp}.txt"
        with open(log_file, 'w') as f:
            f.write('\n'.join(log_lines))
        log_lines.insert(0, f"Log file: {log_file}")
    
    return results, log_lines


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Organize backup files in model_pack directory"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without actually moving files'
    )
    parser.add_argument(
        '--model-pack-dir',
        type=Path,
        default=Path(__file__).parent.parent,
        help='Path to model_pack directory (default: parent of scripts/)'
    )
    
    args = parser.parse_args()
    
    model_pack_dir = args.model_pack_dir.resolve()
    
    if not model_pack_dir.exists():
        print(f"❌ Error: Model pack directory not found: {model_pack_dir}")
        return 1
    
    print(f"🔍 Scanning for backup files in: {model_pack_dir}")
    print(f"{'🔍 DRY RUN MODE - No files will be moved' if args.dry_run else '▶️  EXECUTION MODE - Files will be moved'}")
    print("=" * 80)
    
    results, log_lines = organize_backups(model_pack_dir, dry_run=args.dry_run)
    
    # Print summary
    print(f"\n📊 Summary:")
    print(f"   Moved: {len(results['moved'])}")
    print(f"   Skipped: {len(results['skipped'])}")
    print(f"   Errors: {len(results['errors'])}")
    
    if results['moved']:
        print(f"\n✅ Files {'that would be ' if args.dry_run else ''}moved:")
        for item in results['moved'][:20]:  # Show first 20
            print(f"   - {item}")
        if len(results['moved']) > 20:
            print(f"   ... and {len(results['moved']) - 20} more")
    
    if results['skipped']:
        print(f"\n⏭️  Skipped:")
        for item in results['skipped'][:10]:  # Show first 10
            print(f"   - {item}")
        if len(results['skipped']) > 10:
            print(f"   ... and {len(results['skipped']) - 10} more")
    
    if results['errors']:
        print(f"\n❌ Errors:")
        for item in results['errors']:
            print(f"   - {item}")
        return 1
    
    if args.dry_run:
        print(f"\n💡 Run without --dry-run to actually move files")
    
    # Print log location if not dry run
    if not args.dry_run and results['moved']:
        print(f"\n📄 Migration log saved to: model_pack/backups/migration_log_*.txt")
    
    return 0


if __name__ == "__main__":
    exit(main())

