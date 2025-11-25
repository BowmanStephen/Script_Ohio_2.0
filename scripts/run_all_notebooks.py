#!/usr/bin/env python3
"""
Run all starter pack and model pack notebooks using papermill.

Executes notebooks and reports which ones succeeded or failed.
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import List, Tuple

try:
    import papermill as pm
except ImportError:
    print("Installing papermill...")
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'papermill', '-q'])
    import papermill as pm


def run_notebook(notebook_path: Path, output_dir: Path) -> Tuple[bool, str]:
    """
    Run a single notebook using papermill.
    
    Returns:
        (success: bool, message: str)
    """
    output_path = output_dir / f"{notebook_path.stem}.output.ipynb"
    
    try:
        # Set matplotlib backend for headless execution
        env = os.environ.copy()
        env['MPLBACKEND'] = 'Agg'
        env['CFB_AUTO_INSTALL'] = '0'  # Don't auto-install during batch run
        
        pm.execute_notebook(
            str(notebook_path),
            str(output_path),
            cwd=str(notebook_path.parent),
            kernel_name="python3",
            log_output=False,
            progress_bar=False,
        )
        return True, "Success"
    except Exception as e:
        error_msg = str(e)
        # Truncate long error messages
        if len(error_msg) > 200:
            error_msg = error_msg[:200] + "..."
        return False, error_msg


def main():
    """Main entry point."""
    project_root = Path(__file__).resolve().parent.parent
    
    notebooks = [
        'starter_pack/00_data_dictionary.ipynb',
        'starter_pack/01_intro_to_data.ipynb',
        'starter_pack/02_build_simple_rankings.ipynb',
        'starter_pack/03_metrics_comparison.ipynb',
        'starter_pack/04_team_similarity.ipynb',
        'starter_pack/05_matchup_predictor.ipynb',
        'starter_pack/06_custom_rankings_by_metric.ipynb',
        'starter_pack/07_drive_efficiency.ipynb',
        'starter_pack/08_offense_vs_defense_comparison.ipynb',
        'starter_pack/09_opponent_adjustments.ipynb',
        'starter_pack/10_srs_adjusted_metrics.ipynb',
        'starter_pack/11_metric_distribution_explorer.ipynb',
        'starter_pack/12_efficiency_dashboards.ipynb',
        'model_pack/01_linear_regression_margin.ipynb',
        'model_pack/02_random_forest_team_points.ipynb',
        'model_pack/03_xgboost_win_probability.ipynb',
        'model_pack/04_fastai_win_probability.ipynb',
        'model_pack/05_logistic_regression_win_probability.ipynb',
        'model_pack/06_shap_interpretability.ipynb',
        'model_pack/07_stacked_ensemble.ipynb',
        'model_pack/12_update_training_data.ipynb',
    ]
    
    # Create output directory
    output_dir = project_root / "notebook_outputs"
    output_dir.mkdir(exist_ok=True)
    
    print(f"Running {len(notebooks)} notebooks...\n")
    print("=" * 80)
    
    results = []
    for nb_path_str in notebooks:
        nb_path = project_root / nb_path_str
        if not nb_path.exists():
            print(f"❌ {nb_path.name:50} NOT FOUND")
            results.append((nb_path.name, False, "File not found"))
            continue
        
        print(f"Running {nb_path.name}...", end=" ", flush=True)
        success, message = run_notebook(nb_path, output_dir)
        
        status = "✅" if success else "❌"
        print(f"{status} {message}")
        results.append((nb_path.name, success, message))
    
    print("\n" + "=" * 80)
    print("\nSummary:")
    print("-" * 80)
    
    successful = [r for r in results if r[1]]
    failed = [r for r in results if not r[1]]
    
    print(f"✅ Successful: {len(successful)}/{len(results)}")
    if successful:
        for name, _, _ in successful:
            print(f"   - {name}")
    
    print(f"\n❌ Failed: {len(failed)}/{len(results)}")
    if failed:
        for name, _, msg in failed:
            print(f"   - {name}: {msg}")
    
    print(f"\nOutput files saved to: {output_dir}")
    
    # Exit with error code if any failed
    sys.exit(0 if len(failed) == 0 else 1)


if __name__ == "__main__":
    main()

