#!/usr/bin/env python3
"""
Cleanup script for starter pack notebooks.

Removes stale execution outputs and fixes code duplication issues.
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any

def clear_notebook_outputs(notebook_path: Path) -> bool:
    """Clear all execution outputs from a notebook."""
    try:
        with open(notebook_path, 'r', encoding='utf-8') as f:
            nb = json.load(f)
        
        cleared = False
        for cell in nb.get('cells', []):
            if cell.get('cell_type') == 'code':
                if cell.get('outputs'):
                    cell['outputs'] = []
                    cleared = True
                if cell.get('execution_count') is not None:
                    cell['execution_count'] = None
                    cleared = True
        
        if cleared:
            with open(notebook_path, 'w', encoding='utf-8') as f:
                json.dump(nb, f, indent=1, ensure_ascii=False)
            return True
        return False
    except Exception as e:
        print(f"Error clearing outputs from {notebook_path}: {e}", file=sys.stderr)
        return False

def fix_duplicate_config_imports(notebook_path: Path) -> bool:
    """Remove duplicate config import code from notebooks."""
    try:
        with open(notebook_path, 'r', encoding='utf-8') as f:
            nb = json.load(f)
        
        fixed = False
        has_config_in_first_cell = False
        
        # Check if first code cell has config imports
        for cell in nb.get('cells', []):
            if cell.get('cell_type') == 'code':
                source = ''.join(cell.get('source', []))
                if 'get_starter_pack_config' in source:
                    has_config_in_first_cell = True
                    break
        
        # Remove duplicate config imports from subsequent cells
        config_import_patterns = [
            'from config.data_config import get_starter_pack_config',
            'get_starter_pack_config',
            '_config_dir = Path().resolve() / "config"'
        ]
        
        for i, cell in enumerate(nb.get('cells', [])):
            if cell.get('cell_type') == 'code' and i > 0:  # Skip first cell
                source_lines = cell.get('source', [])
                source_text = ''.join(source_lines)
                
                # Check if this cell has duplicate config imports
                has_duplicate = any(pattern in source_text for pattern in config_import_patterns)
                
                if has_duplicate and has_config_in_first_cell:
                    # Keep only the actual code, remove config setup
                    new_source = []
                    skip_config_block = False
                    
                    for line in source_lines:
                        # Skip config import block
                        if any(pattern in line for pattern in config_import_patterns):
                            skip_config_block = True
                            continue
                        
                        # Reset skip after blank line or comment
                        if skip_config_block and (not line.strip() or line.strip().startswith('#')):
                            skip_config_block = False
                        
                        if not skip_config_block:
                            new_source.append(line)
                    
                    if len(new_source) < len(source_lines):
                        cell['source'] = new_source
                        fixed = True
        
        if fixed:
            with open(notebook_path, 'w', encoding='utf-8') as f:
                json.dump(nb, f, indent=1, ensure_ascii=False)
        return fixed
    except Exception as e:
        print(f"Error fixing duplicate imports in {notebook_path}: {e}", file=sys.stderr)
        return False

def fix_duplicate_data_dir_assignments(notebook_path: Path) -> bool:
    """Remove duplicate DATA_DIR assignments from notebooks."""
    try:
        with open(notebook_path, 'r', encoding='utf-8') as f:
            nb = json.load(f)
        
        fixed = False
        
        for cell in nb.get('cells', []):
            if cell.get('cell_type') == 'code':
                source_lines = cell.get('source', [])
                data_dir_lines = []
                other_lines = []
                
                for line in source_lines:
                    if 'DATA_DIR = str(config.data_dir)' in line:
                        data_dir_lines.append(line)
                    else:
                        other_lines.append(line)
                
                # Keep only one DATA_DIR assignment
                if len(data_dir_lines) > 1:
                    # Keep the first occurrence, remove duplicates
                    new_source = []
                    data_dir_seen = False
                    
                    for line in source_lines:
                        if 'DATA_DIR = str(config.data_dir)' in line:
                            if not data_dir_seen:
                                new_source.append(line)
                                data_dir_seen = True
                            # Skip duplicates
                        else:
                            new_source.append(line)
                    
                    cell['source'] = new_source
                    fixed = True
        
        if fixed:
            with open(notebook_path, 'w', encoding='utf-8') as f:
                json.dump(nb, f, indent=1, ensure_ascii=False)
        return fixed
    except Exception as e:
        print(f"Error fixing duplicate DATA_DIR in {notebook_path}: {e}", file=sys.stderr)
        return False

def fix_template_strings(notebook_path: Path) -> bool:
    """Fix template strings like 'config.current_year' in code cells."""
    try:
        with open(notebook_path, 'r', encoding='utf-8') as f:
            nb = json.load(f)
        
        fixed = False
        
        for cell in nb.get('cells', []):
            if cell.get('cell_type') == 'code':
                source_lines = cell.get('source', [])
                new_source = []
                
                for line in source_lines:
                    # Fix template strings in f-strings and regular strings
                    if 'config.current_year' in line and '{current_year}' not in line:
                        # Check if it's in a string context
                        if 'f"' in line or "f'" in line:
                            # Replace in f-string context
                            line = line.replace('config.current_year', '{current_year}')
                        elif '"' in line or "'" in line:
                            # Replace in regular string
                            line = line.replace('config.current_year', '{current_year}')
                        fixed = True
                    
                    new_source.append(line)
                
                if fixed:
                    cell['source'] = new_source
        
        if fixed:
            with open(notebook_path, 'w', encoding='utf-8') as f:
                json.dump(nb, f, indent=1, ensure_ascii=False)
        return fixed
    except Exception as e:
        print(f"Error fixing template strings in {notebook_path}: {e}", file=sys.stderr)
        return False

def main():
    """Main cleanup function."""
    starter_pack_dir = Path(__file__).parent.parent / 'starter_pack'
    
    # Notebooks that need output clearing
    notebooks_to_clear = [
        '00_data_dictionary.ipynb',
        '01_intro_to_data.ipynb',
        '02_build_simple_rankings.ipynb',
        '03_metrics_comparison.ipynb',
        '04_team_similarity.ipynb',
        '05_matchup_predictor.ipynb',
    ]
    
    # Notebooks that need code fixes
    notebooks_to_fix = {
        '09_opponent_adjustments.ipynb': ['duplicate_imports', 'duplicate_data_dir', 'template_strings'],
        '12_efficiency_dashboards.ipynb': ['duplicate_imports', 'duplicate_data_dir'],
    }
    
    print("🧹 Cleaning up starter pack notebooks...\n")
    
    # Clear outputs
    print("📤 Clearing stale outputs...")
    cleared_count = 0
    for nb_name in notebooks_to_clear:
        nb_path = starter_pack_dir / nb_name
        if nb_path.exists():
            if clear_notebook_outputs(nb_path):
                print(f"  ✅ Cleared outputs from {nb_name}")
                cleared_count += 1
            else:
                print(f"  ⏭️  No outputs to clear in {nb_name}")
        else:
            print(f"  ⚠️  Notebook not found: {nb_name}")
    
    print(f"\n✅ Cleared outputs from {cleared_count} notebooks\n")
    
    # Fix code duplication and template strings
    print("🔧 Fixing code duplication and template strings...")
    fixed_count = 0
    for nb_name, fixes in notebooks_to_fix.items():
        nb_path = starter_pack_dir / nb_name
        if not nb_path.exists():
            print(f"  ⚠️  Notebook not found: {nb_name}")
            continue
        
        fixed_any = False
        if 'duplicate_imports' in fixes:
            if fix_duplicate_config_imports(nb_path):
                print(f"  ✅ Fixed duplicate config imports in {nb_name}")
                fixed_any = True
        
        if 'duplicate_data_dir' in fixes:
            if fix_duplicate_data_dir_assignments(nb_path):
                print(f"  ✅ Fixed duplicate DATA_DIR assignments in {nb_name}")
                fixed_any = True
        
        if 'template_strings' in fixes:
            if fix_template_strings(nb_path):
                print(f"  ✅ Fixed template strings in {nb_name}")
                fixed_any = True
        
        if fixed_any:
            fixed_count += 1
        else:
            print(f"  ⏭️  No fixes needed in {nb_name}")
    
    print(f"\n✅ Fixed code issues in {fixed_count} notebooks\n")
    print("🎉 Cleanup complete!")

if __name__ == '__main__':
    main()

