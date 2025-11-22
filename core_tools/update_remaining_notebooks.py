#!/usr/bin/env python3
"""
Script to update remaining starter pack notebooks with configuration system

This script updates notebooks that have literal "config.current_year.csv" strings
or hard-coded DATA_DIR and year values.
"""

import json
import sys
from pathlib import Path

def update_notebook_file(notebook_path: Path):
    """Update a single notebook file"""
    print(f"Updating {notebook_path.name}...")
    
    with open(notebook_path, 'r', encoding='utf-8') as f:
        notebook = json.load(f)
    
    updated = False
    
    # Configuration import code to add at the beginning
    config_import = """import sys
from pathlib import Path

# Import starter pack configuration system
_config_dir = Path().resolve() / "config"
if str(_config_dir.parent) not in sys.path:
    sys.path.insert(0, str(_config_dir.parent))
from config.data_config import get_starter_pack_config

# Get configuration
config = get_starter_pack_config()
"""
    
    for cell in notebook.get('cells', []):
        if cell.get('cell_type') == 'code':
            source = ''.join(cell.get('source', []))
            original_source = source
            
            # Replace DATA_DIR = "./data" with config setup
            if 'DATA_DIR = "./data"' in source and 'get_starter_pack_config' not in source:
                # Check if config import is already in this cell
                if 'import sys' not in source or 'get_starter_pack_config' not in source:
                    # Add config import at the beginning
                    if source.strip().startswith('DATA_DIR'):
                        source = config_import + source.replace('DATA_DIR = "./data"', 'DATA_DIR = str(config.data_dir)')
                    else:
                        # Insert after imports
                        lines = source.split('\n')
                        insert_idx = 0
                        for i, line in enumerate(lines):
                            if line.strip().startswith('import ') or line.strip().startswith('from '):
                                insert_idx = i + 1
                        lines.insert(insert_idx, '')
                        lines.insert(insert_idx + 1, config_import)
                        source = '\n'.join(lines)
                        source = source.replace('DATA_DIR = "./data"', 'DATA_DIR = str(config.data_dir)')
                    updated = True
            
            # Replace literal "config.current_year.csv" strings
            if 'config.current_year.csv' in source:
                source = source.replace(
                    '"config.current_year.csv"',
                    'f"{config.current_year}.csv"'
                )
                source = source.replace(
                    "'config.current_year.csv'",
                    "f'{config.current_year}.csv'"
                )
                # Also handle os.path.join cases
                if 'os.path.join(DATA_DIR' in source and 'config.current_year' in source:
                    # Replace patterns like: os.path.join(DATA_DIR, "advanced_season_stats", "config.current_year.csv")
                    import re
                    source = re.sub(
                        r'os\.path\.join\(DATA_DIR,\s*"([^"]+)",\s*"config\.current_year\.csv"\)',
                        r'config.get_advanced_stats_path(year=config.current_year)',
                        source
                    )
                    source = re.sub(
                        r'os\.path\.join\(DATA_DIR,\s*"drives",\s*"drives_config\.current_year\.csv"\)',
                        r'str(config.get_drives_path(year=config.current_year))',
                        source
                    )
                    source = re.sub(
                        r'os\.path\.join\(DATA_DIR,\s*"advanced_game_stats",\s*"config\.current_year\.csv"\)',
                        r'str(config.get_data_path(f"advanced_game_stats/{config.current_year}.csv"))',
                        source
                    )
                updated = True
            
            # Replace hard-coded years in queries
            if 'season == 2023' in source or 'season == 2024' in source or 'season == 2025' in source:
                source = source.replace('season == 2023', f'season == {config.current_year}')
                source = source.replace('season == 2024', f'season == {config.current_year}')
                source = source.replace('season == 2025', f'season == {config.current_year}')
                # Add current_year variable if not present
                if 'current_year = config.current_year' not in source:
                    # Find a good place to insert it (after config setup)
                    if 'config = get_starter_pack_config()' in source:
                        source = source.replace(
                            'config = get_starter_pack_config()',
                            'config = get_starter_pack_config()\ncurrent_year = config.current_year'
                        )
                updated = True
            
            # Replace hard-coded year in file paths like "2023.csv"
            if '"2023.csv"' in source or "'2023.csv'" in source:
                if 'current_year' not in source:
                    # Add current_year variable
                    if 'config = get_starter_pack_config()' in source:
                        source = source.replace(
                            'config = get_starter_pack_config()',
                            'config = get_starter_pack_config()\ncurrent_year = config.current_year'
                        )
                source = source.replace('"2023.csv"', 'f"{current_year}.csv"')
                source = source.replace("'2023.csv'", "f'{current_year}.csv'")
                updated = True
            
            if source != original_source:
                cell['source'] = source.split('\n')
                # Add newline at end if not present
                if cell['source'] and cell['source'][-1]:
                    cell['source'].append('')
    
    if updated:
        with open(notebook_path, 'w', encoding='utf-8') as f:
            json.dump(notebook, f, indent=1, ensure_ascii=False)
        print(f"  ✅ Updated {notebook_path.name}")
        return True
    else:
        print(f"  ⏭️  No changes needed for {notebook_path.name}")
        return False

def main():
    """Update all starter pack notebooks"""
    starter_pack_dir = Path(__file__).parent.parent.parent / "starter_pack"
    notebooks = list(starter_pack_dir.glob("*.ipynb"))
    
    print(f"Found {len(notebooks)} notebooks to check")
    print("=" * 60)
    
    updated_count = 0
    for notebook in sorted(notebooks):
        if update_notebook_file(notebook):
            updated_count += 1
    
    print("=" * 60)
    print(f"✅ Updated {updated_count} notebooks")
    print(f"⏭️  Skipped {len(notebooks) - updated_count} notebooks (no changes needed)")

if __name__ == "__main__":
    main()

