#!/usr/bin/env python3
"""
Detect duplicate code patterns in Jupyter notebooks.

Identifies duplicate config imports and variable assignments that should
be cleaned up for better code maintainability.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple


def detect_duplicates(notebook_path: Path) -> Dict[str, List[Tuple[int, str]]]:
    """
    Detect duplicate patterns in a notebook.
    
    Args:
        notebook_path: Path to the notebook file
        
    Returns:
        Dictionary with issue types as keys and list of (cell_index, description) tuples
    """
    try:
        with open(notebook_path, 'r', encoding='utf-8') as f:
            nb = json.load(f)
    except Exception as e:
        print(f"Error reading {notebook_path}: {e}", file=sys.stderr)
        return {}
    
    issues: Dict[str, List[Tuple[int, str]]] = {
        'duplicate_config_imports': [],
        'duplicate_data_dir': [],
        'duplicate_current_year': []
    }
    
    cells = nb.get('cells', [])
    config_import_cells = []
    data_dir_cells = []
    current_year_cells = []
    
    for idx, cell in enumerate(cells):
        if cell.get('cell_type') != 'code':
            continue
        
        source = ''.join(cell.get('source', []))
        
        # Check for config import
        if 'from config.data_config import get_starter_pack_config' in source:
            config_import_cells.append((idx, source))
        
        # Check for DATA_DIR assignment
        if 'DATA_DIR = str(config.data_dir)' in source:
            data_dir_cells.append((idx, source))
        
        # Check for current_year assignment
        if 'current_year = config.current_year' in source:
            current_year_cells.append((idx, source))
    
    # Report duplicates
    if len(config_import_cells) > 1:
        for idx, _ in config_import_cells[1:]:  # Skip first occurrence
            issues['duplicate_config_imports'].append(
                (idx, f"Cell {idx} has duplicate config import (first in cell {config_import_cells[0][0]})")
            )
    
    # Check for multiple DATA_DIR in same cell
    for idx, source in data_dir_cells:
        count = source.count('DATA_DIR = str(config.data_dir)')
        if count > 1:
            issues['duplicate_data_dir'].append(
                (idx, f"Cell {idx} has {count} DATA_DIR assignments")
            )
    
    # Check for multiple current_year in same cell
    for idx, source in current_year_cells:
        count = source.count('current_year = config.current_year')
        if count > 1:
            issues['current_year'].append(
                (idx, f"Cell {idx} has {count} current_year assignments")
            )
    
    return issues


def main():
    """Main entry point for the script."""
    if len(sys.argv) < 2:
        print("Usage: python detect_notebook_duplicates.py <notebook1.ipynb> [notebook2.ipynb ...]")
        print("   or: python detect_notebook_duplicates.py starter_pack/*.ipynb")
        sys.exit(1)
    
    notebook_paths: List[Path] = []
    
    # Handle glob patterns and individual files
    for arg in sys.argv[1:]:
        path = Path(arg)
        if path.is_file() and path.suffix == '.ipynb':
            notebook_paths.append(path)
        elif '*' in arg or '?' in arg:
            from glob import glob
            for match in glob(arg):
                match_path = Path(match)
                if match_path.is_file() and match_path.suffix == '.ipynb':
                    notebook_paths.append(match_path)
        else:
            print(f"Warning: {arg} is not a valid notebook file, skipping", file=sys.stderr)
    
    if not notebook_paths:
        print("No notebook files found to process", file=sys.stderr)
        sys.exit(1)
    
    print(f"Detecting duplicates in {len(notebook_paths)} notebook(s)...\n")
    
    total_issues = 0
    for nb_path in sorted(notebook_paths):
        issues = detect_duplicates(nb_path)
        
        has_issues = any(issues.values())
        if has_issues:
            print(f"❌ {nb_path.name}:")
            for issue_type, issue_list in issues.items():
                if issue_list:
                    print(f"   {issue_type}:")
                    for cell_idx, description in issue_list:
                        print(f"      - {description}")
                    total_issues += len(issue_list)
        else:
            print(f"✅ {nb_path.name}: No duplicates found")
    
    print(f"\nTotal issues found: {total_issues}")
    
    if total_issues > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()

