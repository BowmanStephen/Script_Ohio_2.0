import json
import os

NOTEBOOK_PATH = "model_pack/04_fastai_win_probability.ipynb"

def fix_notebook(filepath):
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

        # 1. Update Auto-setup (Standardization)
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

        # 2. Update Data Loading & Fix Time-Travel Bug
        # Look for the specific hardcoded query line
        if 'pd.read_csv("training_data.csv")' in source_str and 'query("season == 2023' in source_str:
            print("  Found hardcoded data loading cell. Updating to dynamic latest...")
            
            new_source_lines = []
            has_data_manager_import = False
            
            # We will completely replace this cell's logic with the dynamic version
            # But we need to keep other imports if they were there, though usually this cell is just data loading
            
            # Let's construct the new cell content
            new_source_lines.append("# Standardized Data Loading with Dynamic Season/Week Selection\n")
            new_source_lines.append("import pandas as pd\n")
            new_source_lines.append("from data_manager import DataManager\n")
            new_source_lines.append("\n")
            new_source_lines.append("dm = DataManager()\n")
            new_source_lines.append("df = dm.load_training_data()\n")
            new_source_lines.append("\n")
            new_source_lines.append("# Dynamically select the latest available season and week to prevent time-travel/stale data issues\n")
            new_source_lines.append("latest_season = df['season'].max()\n")
            new_source_lines.append("latest_week = df[df['season'] == latest_season]['week'].max()\n")
            new_source_lines.append("print(f\"Testing with data from Season {latest_season}, Week {latest_week}\")\n")
            new_source_lines.append("\n")
            new_source_lines.append("df = df.query(f\"season == {latest_season} and week == {latest_week}\").reset_index(drop=True)\n")
            
            # Check if there were other important lines in the original cell that we might be overwriting
            # The grep showed:
            # df = pd.read_csv("training_data.csv").query("season == 2023 and week == 8").reset_index(drop=True)
            # df[cat_features + cont_features].head()
            # dls = model.dls.test_dl(df[cat_features + cont_features])
            
            # We should preserve the usage of df after loading
            # Let's append the rest of the original cell if it had more logic
            
            # Actually, it's safer to just replace the loading line and keep the rest?
            # But the loading line was chained: read_csv().query().reset_index()
            
            # Let's try to parse the original source to preserve subsequent lines
            
            # Re-reading source to be careful
            preserved_lines = []
            skip_next = False
            
            for line in source:
                if 'pd.read_csv("training_data.csv")' in line and 'query("season == 2023' in line:
                    # This is the line we replace with our block
                    # We already added the block above to new_source_lines
                    pass 
                else:
                    # Keep other lines (like imports or dls = ...)
                    # But we need to be careful about imports we already added
                    if "import pandas as pd" in line:
                        continue # Already added
                    preserved_lines.append(line)
            
            # Combine
            cell['source'] = new_source_lines + preserved_lines
            modified = True

    if modified:
        with open(filepath, 'w') as f:
            json.dump(nb, f, indent=1)
        print(f"  Saved updates to {filepath}")
    else:
        print(f"  No changes needed for {filepath}")

if __name__ == "__main__":
    # Adjust paths to be absolute or relative to root
    current_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(current_dir)
    
    nb_path = os.path.join(base_dir, NOTEBOOK_PATH)
    if os.path.exists(nb_path):
        fix_notebook(nb_path)
    else:
        print(f"Warning: Notebook not found at {nb_path}")
