#!/usr/bin/env python3
"""
Validate starter pack notebooks for structure and content issues.

Checks for:
- Auto-setup cell presence
- Config import presence
- Stale template strings in outputs
- Duplicate code patterns
- Proper f-string usage
"""

import json
import sys
from pathlib import Path


def validate_notebook(nb_path: Path) -> tuple[bool, list[str]]:
    """
    Validate a single notebook.
    
    Args:
        nb_path: Path to the notebook file
        
    Returns:
        Tuple of (is_valid: bool, issues: List[str])
    """
    try:
        with open(nb_path, 'r', encoding='utf-8') as f:
            nb = json.load(f)
    except Exception as e:
        return False, [f"Error reading notebook: {e}"]
    
    issues: list[str] = []
    cells = nb.get('cells', [])
    
    # Check for auto-setup cell in first 2 cells
    has_auto_setup = False
    for cell in cells[:2]:
        if cell.get('cell_type') == 'code':
            source = ''.join(cell.get('source', []))
            if '%run ./_auto_setup.py' in source or '_auto_setup.py' in source:
                has_auto_setup = True
                break
    
    if not has_auto_setup:
        issues.append("Missing auto-setup cell in first 2 cells")
    
    # Check for config import in first 5 cells
    has_config = False
    config_import_count = 0
    for cell in cells[:5]:
        if cell.get('cell_type') == 'code':
            source = ''.join(cell.get('source', []))
            if 'get_starter_pack_config' in source:
                has_config = True
            if 'from config.data_config import get_starter_pack_config' in source:
                config_import_count += 1
    
    if not has_config:
        issues.append("Missing config import in first 5 cells")
    
    # Check for too many config imports (more than 2 is suspicious)
    MAX_CONFIG_IMPORTS = 2
    if config_import_count > MAX_CONFIG_IMPORTS:
        issues.append(f"Too many config imports ({config_import_count}), possible duplicates")
    
    # Check for stale template strings in outputs
    has_stale_outputs = False
    for cell in cells:
        for output in cell.get('outputs', []):
            if 'text' in output:
                text = ''.join(output.get('text', []))
                # Check for template strings that weren't evaluated
                if 'config.current_year' in text and '202' not in text:
                    has_stale_outputs = True
                    break
            if 'data' in output and 'text/plain' in output.get('data', {}):
                text = ''.join(output['data'].get('text/plain', []))
                if 'config.current_year' in text and '202' not in text:
                    has_stale_outputs = True
                    break
        if has_stale_outputs:
            break
    
    if has_stale_outputs:
        issues.append("Has stale outputs with template strings (config.current_year not evaluated)")
    
    # Check for duplicate DATA_DIR assignments in same cell
    for idx, cell in enumerate(cells):
        if cell.get('cell_type') == 'code':
            source = ''.join(cell.get('source', []))
            data_dir_count = source.count('DATA_DIR = str(config.data_dir)')
            if data_dir_count > 1:
                issues.append(f"Cell {idx} has {data_dir_count} DATA_DIR assignments (duplicate)")
    
    # Check for duplicate current_year assignments in same cell
    for idx, cell in enumerate(cells):
        if cell.get('cell_type') == 'code':
            source = ''.join(cell.get('source', []))
            current_year_count = source.count('current_year = config.current_year')
            if current_year_count > 1:
                issues.append(f"Cell {idx} has {current_year_count} current_year assignments (duplicate)")
    
    return len(issues) == 0, issues


def main() -> None:
    """Main entry point for the script."""
    notebook_paths: list[Path] = []
    
    if len(sys.argv) < 2:
        # Default to all starter pack notebooks
        starter_pack_dir = Path("starter_pack")
        if starter_pack_dir.exists():
            notebook_paths = sorted(starter_pack_dir.glob("*.ipynb"))
        else:
            print("Usage: python validate_starter_pack_notebooks.py [notebook1.ipynb ...]")
            print("   or: python validate_starter_pack_notebooks.py (validates all in starter_pack/)")
            sys.exit(1)
    else:
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
    
    if not notebook_paths:
        print("No notebook files found to validate", file=sys.stderr)
        sys.exit(1)
    
    print(f"Validating {len(notebook_paths)} notebook(s)...\n")
    
    all_valid = True
    for nb_path in sorted(notebook_paths):
        is_valid, issues = validate_notebook(nb_path)
        status = "✅" if is_valid else "❌"
        print(f"{status} {nb_path.name}")
        if issues:
            for issue in issues:
                print(f"   - {issue}")
            all_valid = False
    
    print()
    if all_valid:
        print("✅ All notebooks validated successfully")
        sys.exit(0)
    else:
        print("❌ Some notebooks have issues")
        sys.exit(1)


if __name__ == "__main__":
    main()
