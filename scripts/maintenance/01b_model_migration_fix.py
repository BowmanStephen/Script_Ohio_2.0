#!/usr/bin/env python3
"""
Model Migration Fix - Supplemental migration for production models

Fixes the model migration by copying the correct production models to their expected locations.
"""

import shutil
from pathlib import Path


def fix_model_migration():
    """Fix production model migration."""
    root_path = Path(".")

    # Production models that need to be moved
    model_mappings = {
        "models/production/ridge_regression_2025_v2.joblib": "models/production/ridge_regression_2025_v2.joblib",
        "models/production/xgboost_classifier_2025_v2.pkl": "models/production/xgboost_classifier_2025_v2.pkl",
        "models/production/fastai_neural_net_2025_v2.pkl": "models/production/fastai_neural_net_2025_v2.pkl",
    }

    print("🔧 Fixing production model migration...")

    success_count = 0
    for old_path, new_path in model_mappings.items():
        source_file = root_path / old_path
        dest_file = root_path / new_path

        if source_file.exists():
            try:
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_file, dest_file)
                print(f"  ✅ {old_path} → {new_path}")
                success_count += 1
            except Exception as e:
                print(f"  ❌ {old_path}: {e}")
        else:
            print(f"  ⚠️  {old_path}: Source file not found")

    print(
        f"\n📊 Model migration fix complete: {success_count}/{len(model_mappings)} models moved"
    )
    return success_count


if __name__ == "__main__":
    fix_model_migration()
