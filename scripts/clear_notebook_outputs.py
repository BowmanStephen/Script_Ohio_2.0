#!/usr/bin/env python3
"""
Clear execution outputs from Jupyter notebooks.

Removes all execution outputs and execution counts from notebook files,
useful for cleaning stale outputs before committing or re-running notebooks.
"""

import json
import sys
from pathlib import Path
from typing import List


def clear_notebook_outputs(notebook_path: Path) -> bool:
    """
    Clear all outputs and execution counts from a notebook.
    
    Args:
        notebook_path: Path to the notebook file
        
    Returns:
        True if outputs were cleared, False if no changes needed
    """
    try:
        with open(notebook_path, 'r', encoding='utf-8') as f:
            nb = json.load(f)
    except Exception as e:
        print(f"Error reading {notebook_path}: {e}", file=sys.stderr)
        return False
    
    modified = False
    cells = nb.get('cells', [])
    
    for cell in cells:
        if cell.get('cell_type') == 'code':
            # Clear outputs if present
            if cell.get('outputs'):
                cell['outputs'] = []
                modified = True
            
            # Clear execution count if present
            if cell.get('execution_count') is not None:
                cell['execution_count'] = None
                modified = True
    
    if modified:
        try:
            with open(notebook_path, 'w', encoding='utf-8') as f:
                json.dump(nb, f, indent=1, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error writing {notebook_path}: {e}", file=sys.stderr)
            return False
    
    return False


def main():
    """Main entry point for the script."""
    if len(sys.argv) < 2:
        print("Usage: python clear_notebook_outputs.py <notebook1.ipynb> [notebook2.ipynb ...]")
        print("   or: python clear_notebook_outputs.py starter_pack/*.ipynb")
        sys.exit(1)
    
    notebook_paths: List[Path] = []
    
    # Handle glob patterns and individual files
    for arg in sys.argv[1:]:
        path = Path(arg)
        if path.is_file() and path.suffix == '.ipynb':
            notebook_paths.append(path)
        elif '*' in arg or '?' in arg:
            # Handle glob patterns
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
    
    print(f"Clearing outputs from {len(notebook_paths)} notebook(s)...\n")
    
    cleared_count = 0
    for nb_path in sorted(notebook_paths):
        if clear_notebook_outputs(nb_path):
            print(f"Cleared outputs: {nb_path.name}")
            cleared_count += 1
        else:
            print(f"No changes needed: {nb_path.name}")
    
    print(f"\nDone! Cleared outputs from {cleared_count} of {len(notebook_paths)} notebook(s).")
    print("Re-run notebooks to generate fresh outputs.")


if __name__ == "__main__":
    main()

