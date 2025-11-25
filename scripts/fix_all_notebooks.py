#!/usr/bin/env python3
"""Fix auto-setup paths in all starter_pack and model_pack notebooks."""

import json
from pathlib import Path
from typing import List, Tuple

# Notebooks to fix
STARTER_PACK_NOTEBOOKS = [
    "starter_pack/00_data_dictionary.ipynb",
    "starter_pack/01_intro_to_data.ipynb",
    "starter_pack/02_build_simple_rankings.ipynb",
    "starter_pack/03_metrics_comparison.ipynb",
    "starter_pack/04_team_similarity.ipynb",
    "starter_pack/05_matchup_predictor.ipynb",
    "starter_pack/06_custom_rankings_by_metric.ipynb",
    "starter_pack/07_drive_efficiency.ipynb",
    "starter_pack/08_offense_vs_defense_comparison.ipynb",
    "starter_pack/09_opponent_adjustments.ipynb",
    "starter_pack/10_srs_adjusted_metrics.ipynb",
    "starter_pack/11_metric_distribution_explorer.ipynb",
    "starter_pack/12_efficiency_dashboards.ipynb",
]

MODEL_PACK_NOTEBOOKS = [
    "model_pack/01_linear_regression_margin.ipynb",
    "model_pack/02_random_forest_team_points.ipynb",
    "model_pack/03_xgboost_win_probability.ipynb",
    "model_pack/04_fastai_win_probability.ipynb",
    "model_pack/05_logistic_regression_win_probability.ipynb",
    "model_pack/06_shap_interpretability.ipynb",
    "model_pack/07_stacked_ensemble.ipynb",
    "model_pack/12_update_training_data.ipynb",
]

# New auto-setup cell source that works from any directory
# Note: Does not change working directory to avoid breaking subsequent cells
STARTER_PACK_AUTO_SETUP = [
    "# 🚀 Auto-setup: installs deps + configures CFBD access\n",
    "import os\n",
    "import sys\n",
    "from pathlib import Path\n",
    "\n",
    "# Find _auto_setup.py regardless of current working directory\n",
    "_current = Path().resolve()\n",
    "_auto_setup_path = None\n",
    "for parent in [_current] + list(_current.parents):\n",
    "    candidate = parent / \"starter_pack\" / \"_auto_setup.py\"\n",
    "    if candidate.exists():\n",
    "        _auto_setup_path = candidate\n",
    "        # Add project root to sys.path (auto_setup.py will also do this)\n",
    "        if str(parent) not in sys.path:\n",
    "            sys.path.insert(0, str(parent))\n",
    "        break\n",
    "\n",
    "if _auto_setup_path and _auto_setup_path.exists():\n",
    "    # Execute the file directly without changing directory\n",
    "    with open(_auto_setup_path, 'r') as f:\n",
    "        exec(f.read(), {'__file__': str(_auto_setup_path)})\n",
    "else:\n",
    "    # Fallback: try relative path\n",
    "    try:\n",
    "        with open(\"./_auto_setup.py\", 'r') as f:\n",
    "            exec(f.read(), {'__file__': './_auto_setup.py'})\n",
    "    except FileNotFoundError:\n",
    "        print(\"⚠️  Could not find _auto_setup.py. Please run from starter_pack directory.\")\n",
]

MODEL_PACK_AUTO_SETUP = [
    "# 🚀 Auto-setup: installs deps + configures CFBD access\n",
    "import os\n",
    "import sys\n",
    "from pathlib import Path\n",
    "\n",
    "# Find _auto_setup.py regardless of current working directory\n",
    "_current = Path().resolve()\n",
    "_auto_setup_path = None\n",
    "for parent in [_current] + list(_current.parents):\n",
    "    candidate = parent / \"model_pack\" / \"_auto_setup.py\"\n",
    "    if candidate.exists():\n",
    "        _auto_setup_path = candidate\n",
    "        # Add project root to sys.path (auto_setup.py will also do this)\n",
    "        if str(parent) not in sys.path:\n",
    "            sys.path.insert(0, str(parent))\n",
    "        break\n",
    "\n",
    "if _auto_setup_path and _auto_setup_path.exists():\n",
    "    # Execute the file directly without changing directory\n",
    "    with open(_auto_setup_path, 'r') as f:\n",
    "        exec(f.read(), {'__file__': str(_auto_setup_path)})\n",
    "else:\n",
    "    # Fallback: try relative path\n",
    "    try:\n",
    "        with open(\"./_auto_setup.py\", 'r') as f:\n",
    "            exec(f.read(), {'__file__': './_auto_setup.py'})\n",
    "    except FileNotFoundError:\n",
    "        print(\"⚠️  Could not find _auto_setup.py. Please run from model_pack directory.\")\n",
]


def fix_notebook(notebook_path: Path, pack_type: str) -> Tuple[bool, str]:
    """Fix auto-setup cell in a notebook.
    
    Returns:
        (modified, message) tuple
    """
    try:
        with notebook_path.open("r", encoding="utf-8") as f:
            nb = json.load(f)
    except Exception as e:
        return False, f"Error reading {notebook_path}: {e}"

    cells = nb.get("cells", [])
    modified = False

    for cell in cells:
        if cell.get("cell_type") != "code":
            continue

        source = cell.get("source", [])
        source_str = "".join(source)

        # Check if this is an auto-setup cell that needs fixing
        if "_auto_setup.py" in source_str:
            # Check if it's the old simple pattern or has os.chdir (needs update)
            needs_fix = (
                "%run ./_auto_setup.py" in source_str
                or "os.chdir" in source_str
                or "Find _auto_setup.py regardless" not in source_str
            )
            
            if needs_fix:
                # Determine which auto-setup template to use
                if pack_type == "starter_pack":
                    new_source = STARTER_PACK_AUTO_SETUP.copy()
                else:
                    new_source = MODEL_PACK_AUTO_SETUP.copy()

                # Replace the cell source
                cell["source"] = new_source
                modified = True
                break

    if modified:
        try:
            with notebook_path.open("w", encoding="utf-8") as f:
                json.dump(nb, f, indent=1, ensure_ascii=False)
            return True, f"Fixed {notebook_path}"
        except Exception as e:
            return False, f"Error writing {notebook_path}: {e}"

    return False, f"No changes needed for {notebook_path}"


def main():
    """Fix all notebooks."""
    project_root = Path(__file__).resolve().parent.parent
    os.chdir(project_root)

    fixed_count = 0
    error_count = 0

    # Fix starter_pack notebooks
    print("Fixing starter_pack notebooks...")
    for nb_path_str in STARTER_PACK_NOTEBOOKS:
        nb_path = project_root / nb_path_str
        if not nb_path.exists():
            print(f"  ⚠️  {nb_path_str} not found, skipping")
            continue

        modified, message = fix_notebook(nb_path, "starter_pack")
        if modified:
            print(f"  ✅ {message}")
            fixed_count += 1
        elif "Error" in message:
            print(f"  ❌ {message}")
            error_count += 1
        else:
            print(f"  ℹ️  {message}")

    # Fix model_pack notebooks
    print("\nFixing model_pack notebooks...")
    for nb_path_str in MODEL_PACK_NOTEBOOKS:
        nb_path = project_root / nb_path_str
        if not nb_path.exists():
            print(f"  ⚠️  {nb_path_str} not found, skipping")
            continue

        modified, message = fix_notebook(nb_path, "model_pack")
        if modified:
            print(f"  ✅ {message}")
            fixed_count += 1
        elif "Error" in message:
            print(f"  ❌ {message}")
            error_count += 1
        else:
            print(f"  ℹ️  {message}")

    print(f"\n📊 Summary: {fixed_count} notebooks fixed, {error_count} errors")


if __name__ == "__main__":
    import os

    main()

