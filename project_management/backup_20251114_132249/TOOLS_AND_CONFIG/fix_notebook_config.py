#!/usr/bin/env python3
"""
Fix remaining notebooks with config.current_year.csv and hard-coded values
"""

import json
import re
from pathlib import Path

def fix_notebook(notebook_path: Path):
    """Fix a single notebook"""
    print(f"Processing {notebook_path.name}...")
    
    try:
        with open(notebook_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix JSON syntax error if present
        content = content.replace('{,"cell_type', '{ "cell_type')
        
        notebook = json.loads(content)
        updated = False
        
        config_setup = """import sys
from pathlib import Path

# Import starter pack configuration system
_config_dir = Path().resolve() / "config"
if str(_config_dir.parent) not in sys.path:
    sys.path.insert(0, str(_config_dir.parent))
from config.data_config import get_starter_pack_config

# Get configuration
config = get_starter_pack_config()
current_year = config.current_year
DATA_DIR = str(config.data_dir)
"""
        
        for cell in notebook.get('cells', []):
            if cell.get('cell_type') == 'code':
                source_lines = cell.get('source', [])
                source = ''.join(source_lines)
                original = source
                
                # Add config setup if DATA_DIR is present but config is not
                if 'DATA_DIR' in source and 'get_starter_pack_config' not in source:
                    if 'import sys' not in source:
                        # Insert config setup after imports
                        lines = source.split('\n')
                        insert_pos = 0
                        for i, line in enumerate(lines):
                            if line.strip().startswith(('import ', 'from ')):
                                insert_pos = i + 1
                        if insert_pos > 0:
                            lines.insert(insert_pos, '')
                            lines.insert(insert_pos + 1, config_setup)
                            source = '\n'.join(lines)
                        else:
                            source = config_setup + source
                        source = source.replace('DATA_DIR = "./data"', 'DATA_DIR = str(config.data_dir)')
                        updated = True
                
                # Fix config.current_year.csv strings
                if 'config.current_year.csv' in source:
                    # Replace in os.path.join calls
                    source = re.sub(
                        r'os\.path\.join\(DATA_DIR,\s*"advanced_season_stats",\s*"config\.current_year\.csv"\)',
                        'str(config.get_advanced_stats_path(year=current_year))',
                        source
                    )
                    source = re.sub(
                        r'os\.path\.join\(DATA_DIR,\s*"drives",\s*"drives_config\.current_year\.csv"\)',
                        'str(config.get_drives_path(year=current_year))',
                        source
                    )
                    source = re.sub(
                        r'os\.path\.join\(DATA_DIR,\s*"advanced_game_stats",\s*"config\.current_year\.csv"\)',
                        'str(config.get_data_path(f"advanced_game_stats/{current_year}.csv"))',
                        source
                    )
                    # Replace literal strings
                    source = source.replace('"config.current_year.csv"', 'f"{current_year}.csv"')
                    source = source.replace("'config.current_year.csv'", "f'{current_year}.csv'")
                    updated = True
                
                # Fix season == config.current_year in queries (should be current_year variable)
                if 'season == config.current_year' in source:
                    source = source.replace('season == config.current_year', 'season == current_year')
                    updated = True
                
                if source != original:
                    cell['source'] = source.split('\n')
                    if cell['source'] and cell['source'][-1]:
                        cell['source'].append('')
        
        if updated:
            with open(notebook_path, 'w', encoding='utf-8') as f:
                json.dump(notebook, f, indent=1, ensure_ascii=False)
            print(f"  ✅ Updated {notebook_path.name}")
            return True
        else:
            print(f"  ⏭️  No changes needed")
            return False
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

if __name__ == "__main__":
    starter_pack = Path(__file__).parent.parent.parent / "starter_pack"
    notebooks = [
        "03_metrics_comparison.ipynb",
        "06_custom_rankings_by_metric.ipynb",
        "07_drive_efficiency.ipynb",
        "08_offense_vs_defense_comparison.ipynb",
        "09_opponent_adjustments.ipynb",
        "10_srs_adjusted_metrics.ipynb",
        "11_metric_distribution_explorer.ipynb",
        "12_efficiency_dashboards.ipynb",
    ]
    
    for nb_name in notebooks:
        nb_path = starter_pack / nb_name
        if nb_path.exists():
            fix_notebook(nb_path)
        else:
            print(f"⚠️  {nb_name} not found")

