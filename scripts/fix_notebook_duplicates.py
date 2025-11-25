#!/usr/bin/env python3
"""
Fix duplicate code patterns in Jupyter notebooks.

Automatically removes duplicate config imports and variable assignments,
keeping only the first occurrence in the appropriate setup cell.
"""

import json
import shutil
import sys
from pathlib import Path
from typing import List, Tuple


def fix_notebook_duplicates(notebook_path: Path, create_backup: bool = True) -> Tuple[bool, List[str]]:
    """
    Fix duplicate patterns in a notebook.
    
    Args:
        notebook_path: Path to the notebook file
        create_backup: Whether to create a backup before modifying
        
    Returns:
        Tuple of (modified: bool, changes: List[str])
    """
    try:
        with open(notebook_path, 'r', encoding='utf-8') as f:
            nb = json.load(f)
    except Exception as e:
        print(f"Error reading {notebook_path}: {e}", file=sys.stderr)
        return False, []
    
    changes: List[str] = []
    cells = nb.get('cells', [])
    modified = False
    
    # Find first config import cell (should be in first 5 cells)
    first_config_cell_idx = None
    for idx in range(min(5, len(cells))):
        cell = cells[idx]
        if cell.get('cell_type') == 'code':
            source = ''.join(cell.get('source', []))
            if 'from config.data_config import get_starter_pack_config' in source:
                first_config_cell_idx = idx
                break
    
    # Process each cell
    for idx, cell in enumerate(cells):
        if cell.get('cell_type') != 'code':
            continue
        
        source_lines = cell.get('source', [])
        source_text = ''.join(source_lines)
        original_source = source_text
        
        # Fix duplicate config imports (if not the first one)
        if idx != first_config_cell_idx and first_config_cell_idx is not None:
            if 'from config.data_config import get_starter_pack_config' in source_text:
                # Remove the entire config import block
                new_lines = []
                skip_block = False
                in_config_block = False
                
                for i, line in enumerate(source_lines):
                    line_text = line if isinstance(line, str) else line
                    
                    # Detect start of config import block
                    if 'import sys' in line_text and i < 10:
                        skip_block = True
                        in_config_block = True
                        continue
                    
                    # Skip lines in config import block
                    if skip_block and in_config_block:
                        if 'from config.data_config import get_starter_pack_config' in line_text:
                            in_config_block = False
                            skip_block = False
                            continue
                        if any(keyword in line_text for keyword in [
                            'config = get_starter_pack_config()',
                            'current_year = config.current_year',
                            'DATA_DIR = str(config.data_dir)',
                            '_config_dir = Path().resolve()',
                            'sys.path.insert'
                        ]):
                            continue
                        # End of block when we hit a non-empty line that's not part of config
                        if line_text.strip() and not line_text.strip().startswith('#'):
                            in_config_block = False
                            skip_block = False
                    
                    if not skip_block or not in_config_block:
                        new_lines.append(line)
                
                if len(new_lines) != len(source_lines):
                    cell['source'] = new_lines
                    modified = True
                    changes.append(f"Removed duplicate config import from cell {idx}")
        
        # Fix duplicate DATA_DIR assignments in same cell
        data_dir_count = source_text.count('DATA_DIR = str(config.data_dir)')
        if data_dir_count > 1:
            new_lines = []
            seen_data_dir = False
            for line in source_lines:
                line_text = line if isinstance(line, str) else line
                if 'DATA_DIR = str(config.data_dir)' in line_text:
                    if not seen_data_dir:
                        new_lines.append(line)
                        seen_data_dir = True
                    # Skip duplicates
                else:
                    new_lines.append(line)
            
            if len(new_lines) < len(source_lines):
                cell['source'] = new_lines
                modified = True
                changes.append(f"Removed {data_dir_count - 1} duplicate DATA_DIR assignment(s) from cell {idx}")
        
        # Fix duplicate current_year assignments in same cell
        current_year_count = source_text.count('current_year = config.current_year')
        if current_year_count > 1:
            new_lines = []
            seen_current_year = False
            for line in source_lines:
                line_text = line if isinstance(line, str) else line
                if 'current_year = config.current_year' in line_text:
                    if not seen_current_year:
                        new_lines.append(line)
                        seen_current_year = True
                    # Skip duplicates
                else:
                    new_lines.append(line)
            
            if len(new_lines) < len(source_lines):
                cell['source'] = new_lines
                modified = True
                changes.append(f"Removed {current_year_count - 1} duplicate current_year assignment(s) from cell {idx}")
    
    if modified:
        # Create backup if requested
        if create_backup:
            backup_path = notebook_path.with_suffix('.ipynb.backup')
            shutil.copy2(notebook_path, backup_path)
            changes.append(f"Created backup: {backup_path.name}")
        
        # Write modified notebook
        try:
            with open(notebook_path, 'w', encoding='utf-8') as f:
                json.dump(nb, f, indent=1, ensure_ascii=False)
            return True, changes
        except Exception as e:
            print(f"Error writing {notebook_path}: {e}", file=sys.stderr)
            return False, []
    
    return False, []


def main():
    """Main entry point for the script."""
    if len(sys.argv) < 2:
        print("Usage: python fix_notebook_duplicates.py <notebook1.ipynb> [notebook2.ipynb ...]")
        print("   or: python fix_notebook_duplicates.py starter_pack/*.ipynb")
        print("\nThis script will:")
        print("  - Remove duplicate config imports (keeps first in setup cell)")
        print("  - Remove duplicate DATA_DIR assignments")
        print("  - Create backup files before modifying")
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
    
    print(f"Fixing duplicates in {len(notebook_paths)} notebook(s)...\n")
    
    fixed_count = 0
    for nb_path in sorted(notebook_paths):
        modified, changes = fix_notebook_duplicates(nb_path)
        if modified:
            print(f"Fixed {nb_path.name}:")
            for change in changes:
                print(f"  - {change}")
            fixed_count += 1
        else:
            print(f"No changes needed: {nb_path.name}")
    
    print(f"\nDone! Fixed {fixed_count} of {len(notebook_paths)} notebook(s).")


if __name__ == "__main__":
    main()

