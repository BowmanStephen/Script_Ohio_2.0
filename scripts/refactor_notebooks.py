import json
import os

NOTEBOOKS_TO_UPDATE = [
    "model_pack/05_logistic_regression_win_probability.ipynb",
    "model_pack/06_shap_interpretability.ipynb",
    "model_pack/07_stacked_ensemble.ipynb"
]

def update_notebook(filepath):
    print(f"Processing {filepath}...")
    try:
        with open(filepath, 'r') as f:
            nb = json.load(f)
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return

    cells = nb.get('cells', [])
    modified = False

    for cell in cells:
        if cell.get('cell_type') != 'code':
            continue
        
        source = cell.get('source', [])
        source_str = "".join(source)

        # 1. Update Auto-setup
        if "_auto_setup.py" in source_str and "%run" in source_str:
            print("  Found auto-setup cell. Updating...")
            new_source = [
                "# 🚀 Auto-setup: installs deps + configures CFBD access\n",
                "import sys, os\n",
                "sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..', 'scripts')))\n",
                "%run ../scripts/_auto_setup.py\n"
            ]
            cell['source'] = new_source
            modified = True

        # 2. Update Data Loading
        if 'pd.read_csv("training_data.csv")' in source_str or "pd.read_csv('training_data.csv')" in source_str:
            print("  Found data loading cell. Updating...")
            
            new_source_lines = []
            has_data_manager_import = False
            
            for line in source:
                if "import pandas as pd" in line:
                    new_source_lines.append(line)
                    if not has_data_manager_import:
                        new_source_lines.append("from data_manager import DataManager\n")
                        has_data_manager_import = True
                elif 'pd.read_csv("training_data.csv")' in line or "pd.read_csv('training_data.csv')" in line:
                    new_source_lines.append("dm = DataManager()\n")
                    new_source_lines.append("df = dm.load_training_data()\n")
                else:
                    new_source_lines.append(line)
            
            cell['source'] = new_source_lines
            modified = True

    if modified:
        with open(filepath, 'w') as f:
            json.dump(nb, f, indent=1)
        print(f"  Saved updates to {filepath}")
    else:
        print(f"  No changes needed for {filepath}")

if __name__ == "__main__":
    # Adjust paths to be absolute or relative to root
    # This script is in scripts/, so root is ..
    current_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(current_dir)
    
    for nb_rel_path in NOTEBOOKS_TO_UPDATE:
        nb_path = os.path.join(base_dir, nb_rel_path)
        if os.path.exists(nb_path):
            update_notebook(nb_path)
        else:
            print(f"Warning: Notebook not found at {nb_path}")
