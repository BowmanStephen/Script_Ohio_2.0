#!/usr/bin/env python3
"""
Validation script for starter pack notebooks.

Checks for:
- Presence of auto-setup cells
- Proper config imports
- Absence of stale template strings in outputs
- Code duplication patterns
"""

import json
import sys
import re
from pathlib import Path
from typing import List, Dict, Set, Tuple

def check_auto_setup_cell(notebook_path: Path) -> Tuple[bool, str]:
    """Check if notebook has auto-setup cell in first position."""
    try:
        with open(notebook_path, 'r', encoding='utf-8') as f:
            nb = json.load(f)
        
        cells = nb.get('cells', [])
        if not cells:
            return False, "No cells found"
        
        first_cell = cells[0]
        if first_cell.get('cell_type') != 'code':
            return False, "First cell is not a code cell"
        
        source = ''.join(first_cell.get('source', []))
        if '_auto_setup.py' in source:
            return True, "Auto-setup cell found"
        return False, "Auto-setup cell not found in first cell"
    except Exception as e:
        return False, f"Error checking auto-setup: {e}"

def check_config_imports(notebook_path: Path) -> Tuple[bool, str, List[str]]:
    """Check for proper config imports and identify duplicates."""
    try:
        with open(notebook_path, 'r', encoding='utf-8') as f:
            nb = json.load(f)
        
        config_import_patterns = [
            r'from config\.data_config import get_starter_pack_config',
            r'get_starter_pack_config',
            r'_config_dir = Path\(\)\.resolve\(\) / "config"'
        ]
        
        issues = []
        has_config_import = False
        config_cell_indices = []
        
        for i, cell in enumerate(nb.get('cells', [])):
            if cell.get('cell_type') == 'code':
                source = ''.join(cell.get('source', []))
                
                # Check for config imports
                for pattern in config_import_patterns:
                    if re.search(pattern, source):
                        if not has_config_import:
                            has_config_import = True
                            config_cell_indices.append(i)
                        elif i > 0:  # Duplicate in later cell
                            config_cell_indices.append(i)
        
        if not has_config_import:
            return False, "No config imports found", []
        
        if len(config_cell_indices) > 1:
            return False, f"Duplicate config imports found in cells: {config_cell_indices}", config_cell_indices
        
        return True, "Config imports OK", []
    except Exception as e:
        return False, f"Error checking config imports: {e}", []

def check_stale_template_strings(notebook_path: Path) -> Tuple[bool, str, List[str]]:
    """Check for stale template strings in outputs and code."""
    try:
        with open(notebook_path, 'r', encoding='utf-8') as f:
            nb = json.load(f)
        
        issues = []
        stale_patterns = [
            r'config\.current_year',  # Template string in outputs
            r'"config\.current_year"',  # Template string in code strings
            r"'config\.current_year'",  # Template string in code strings
        ]
        
        for i, cell in enumerate(nb.get('cells', [])):
            if cell.get('cell_type') == 'code':
                # Check code source
                source = ''.join(cell.get('source', []))
                
                # Skip if it's in an f-string context (which is correct)
                if 'f"' in source or "f'" in source:
                    # Check if it's properly formatted
                    if 'config.current_year' in source and '{current_year}' not in source:
                        issues.append(f"Cell {i}: Template string in code (should use f-string with {{current_year}})")
                
                # Check outputs
                for j, output in enumerate(cell.get('outputs', [])):
                    output_text = ''.join(output.get('text', []))
                    for pattern in stale_patterns:
                        if re.search(pattern, output_text):
                            issues.append(f"Cell {i}, Output {j}: Stale template string found")
        
        if issues:
            return False, f"Found {len(issues)} stale template string issues", issues
        
        return True, "No stale template strings found", []
    except Exception as e:
        return False, f"Error checking template strings: {e}", []

def check_duplicate_data_dir(notebook_path: Path) -> Tuple[bool, str, List[int]]:
    """Check for duplicate DATA_DIR assignments."""
    try:
        with open(notebook_path, 'r', encoding='utf-8') as f:
            nb = json.load(f)
        
        data_dir_cells = []
        
        for i, cell in enumerate(nb.get('cells', [])):
            if cell.get('cell_type') == 'code':
                source = ''.join(cell.get('source', []))
                
                # Count DATA_DIR assignments
                count = source.count('DATA_DIR = str(config.data_dir)')
                if count > 0:
                    data_dir_cells.append((i, count))
        
        # Find cells with multiple assignments
        duplicate_cells = [cell_idx for cell_idx, count in data_dir_cells if count > 1]
        
        # Find multiple cells with DATA_DIR assignments (might be OK if intentional)
        if len(data_dir_cells) > 1:
            return False, f"Multiple DATA_DIR assignments across cells: {[idx for idx, _ in data_dir_cells]}", [idx for idx, _ in data_dir_cells]
        
        if duplicate_cells:
            return False, f"Duplicate DATA_DIR assignments in cells: {duplicate_cells}", duplicate_cells
        
        return True, "DATA_DIR assignments OK", []
    except Exception as e:
        return False, f"Error checking DATA_DIR: {e}", []

def check_notebook_outputs(notebook_path: Path) -> Tuple[bool, str]:
    """Check if notebook has any execution outputs."""
    try:
        with open(notebook_path, 'r', encoding='utf-8') as f:
            nb = json.load(f)
        
        has_outputs = False
        for cell in nb.get('cells', []):
            if cell.get('cell_type') == 'code':
                if cell.get('outputs'):
                    has_outputs = True
                    break
                if cell.get('execution_count') is not None:
                    has_outputs = True
                    break
        
        if has_outputs:
            return False, "Notebook has execution outputs (may be stale)"
        return True, "No execution outputs (clean)"
    except Exception as e:
        return False, f"Error checking outputs: {e}"

def validate_notebook(notebook_path: Path, strict: bool = False) -> Dict:
    """Validate a single notebook and return results."""
    results = {
        'notebook': notebook_path.name,
        'valid': True,
        'issues': []
    }
    
    # Check auto-setup
    has_auto_setup, auto_setup_msg = check_auto_setup_cell(notebook_path)
    if not has_auto_setup:
        results['valid'] = False
        results['issues'].append(f"Auto-setup: {auto_setup_msg}")
    
    # Check config imports
    config_ok, config_msg, config_issues = check_config_imports(notebook_path)
    if not config_ok:
        results['valid'] = False
        results['issues'].append(f"Config imports: {config_msg}")
    
    # Check stale template strings
    template_ok, template_msg, template_issues = check_stale_template_strings(notebook_path)
    if not template_ok:
        results['valid'] = False
        results['issues'].append(f"Template strings: {template_msg}")
        if template_issues:
            results['issues'].extend(template_issues)
    
    # Check duplicate DATA_DIR
    data_dir_ok, data_dir_msg, data_dir_issues = check_duplicate_data_dir(notebook_path)
    if not data_dir_ok:
        results['valid'] = False
        results['issues'].append(f"DATA_DIR: {data_dir_msg}")
    
    # Check outputs (only in strict mode or as info)
    if strict:
        outputs_ok, outputs_msg = check_notebook_outputs(notebook_path)
        if not outputs_ok:
            results['issues'].append(f"Outputs: {outputs_msg} (info only)")
    
    return results

def main():
    """Main validation function."""
    starter_pack_dir = Path(__file__).parent.parent / 'starter_pack'
    
    if not starter_pack_dir.exists():
        print(f"❌ Starter pack directory not found: {starter_pack_dir}", file=sys.stderr)
        sys.exit(1)
    
    # Find all notebooks
    notebooks = sorted(starter_pack_dir.glob('*.ipynb'))
    
    if not notebooks:
        print(f"❌ No notebooks found in {starter_pack_dir}", file=sys.stderr)
        sys.exit(1)
    
    print(f"🔍 Validating {len(notebooks)} starter pack notebooks...\n")
    
    all_valid = True
    results_summary = {
        'total': len(notebooks),
        'valid': 0,
        'invalid': 0,
        'details': []
    }
    
    for nb_path in notebooks:
        results = validate_notebook(nb_path, strict=True)
        results_summary['details'].append(results)
        
        if results['valid']:
            results_summary['valid'] += 1
            print(f"✅ {results['notebook']}")
        else:
            all_valid = False
            results_summary['invalid'] += 1
            print(f"⚠️  {results['notebook']}")
            for issue in results['issues']:
                print(f"   - {issue}")
    
    print(f"\n{'='*60}")
    print(f"Summary: {results_summary['valid']}/{results_summary['total']} notebooks valid")
    
    if results_summary['invalid'] > 0:
        print(f"⚠️  {results_summary['invalid']} notebook(s) have issues")
        sys.exit(1)
    else:
        print("✅ All notebooks validated successfully!")
        sys.exit(0)

if __name__ == '__main__':
    main()

