#!/usr/bin/env python3
"""
Data Migration Script - Reorganization Implementation

Safely migrates data from old structure to new organized structure while
preserving all functionality and ensuring no data loss.

Author: Data Architecture Orchestrator
Created: 2025-12-18
"""

import hashlib
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd


class DataMigrator:
    """
    Handles safe migration of data from old structure to new organized structure.

    Migration Strategy:
    1. Create new structure alongside existing
    2. Copy critical files with validation
    3. Update script references
    4. Archive old files after verification
    """

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.root_path = Path(".").resolve()
        self.migration_log = []
        self.validation_results = {}

        # New directory structure
        self.new_structure = {
            "data/raw/cfbd": "CFBD API raw snapshots",
            "data/raw/historical": "Historical archives (originals)",
            "data/processed/training": "ML-ready training datasets",
            "data/processed/features": "Feature-specific datasets",
            "data/processed/enhanced": "Weekly processed data",
            "data/outputs/predictions": "Model predictions and forecasts",
            "data/outputs/analysis": "Analytical reports and insights",
            "data/outputs/dashboards": "Visual outputs and dashboards",
            "models/production": "Active production models",
            "models/components": "Model components and artifacts",
            "models/training": "Training artifacts and experiments",
            "models/legacy": "Deprecated model versions",
            "archive/backups": "Systematic backups by date",
            "archive/deprecated": "Deprecated file formats",
            "archive/snapshots": "Point-in-time snapshots",
        }

        # File mappings - old path → new path with categorization
        self.file_mappings = self._create_file_mappings()

    def _create_file_mappings(self) -> Dict[str, Dict]:
        """
        Create mapping of current files to new locations with categorization.
        This is the core logic that determines where each file goes.
        """
        mappings = {}

        # MASTER FILES - Highest Priority
        mappings["model_pack/updated_training_data.csv"] = {
            "new_path": "data/processed/training/master_training_data_v2.csv",
            "category": "critical_master",
            "description": "Primary training dataset for ML models",
        }

        # MODEL FILES
        model_files = [
            "model_pack/ridge_model_2025.joblib",
            "model_pack/xgb_home_win_model_2025.pkl",
            "model_pack/fastai_home_win_model_2025.pkl",
        ]
        for model_file in model_files:
            if model_file.startswith("ridge"):
                mappings[model_file] = {
                    "new_path": f"models/production/ridge_regression_2025_v2.joblib",
                    "category": "production_model",
                    "description": "Production Ridge Regression model",
                }
            elif model_file.startswith("xgb"):
                mappings[model_file] = {
                    "new_path": f"models/production/xgboost_classifier_2025_v2.pkl",
                    "category": "production_model",
                    "description": "Production XGBoost model",
                }
            elif model_file.startswith("fastai"):
                mappings[model_file] = {
                    "new_path": f"models/production/fastai_neural_net_2025_v2.pkl",
                    "category": "production_model",
                    "description": "Production FastAI neural network",
                }

        # HISTORICAL ARCHIVES
        mappings["starter_pack/data/games.csv"] = {
            "new_path": "data/raw/historical/games_1869_2025.csv",
            "category": "historical_archive",
            "description": "Complete historical games archive",
        }

        # WEEKLY TRAINING FILES
        weekly_pattern = "data/training/weekly/training_data_"
        for week in range(1, 16):  # Weeks 1-15
            old_path = f"{weekly_pattern}2025_week{week}.csv"
            mappings[old_path] = {
                "new_path": f"data/processed/training/weekly_updates/training_data_2025_week{week}.csv",
                "category": "weekly_update",
                "description": f"Week {week} training data update",
            }

        # ENHANCED WEEKLY FEATURES
        for week in range(1, 16):
            old_pattern = f"data/weekly/week{week:02d}/enhanced/"
            # Common feature files
            feature_files = [
                "week{week:02d}_features_86.csv",
                "enhanced_features_{week}.csv",
                "team_matchups_{week}.csv",
            ]
            for feature_file in feature_files:
                old_path = f"{old_pattern}{feature_file}"
                mappings[old_path] = {
                    "new_path": f"data/processed/enhanced/2025/week{week:02d}/{feature_file}",
                    "category": "weekly_features",
                    "description": f"Week {week} enhanced features",
                }

        # PREDICTION FILES
        predictions_dir = Path("predictions")
        if predictions_dir.exists():
            for pred_file in predictions_dir.glob("*.json"):
                if "bowl" in pred_file.name.lower():
                    mappings[f"predictions/{pred_file.name}"] = {
                        "new_path": f"data/outputs/predictions/2025/bowl_season/{pred_file.name}",
                        "category": "predictions",
                        "description": "Bowl season predictions",
                    }
                else:
                    mappings[f"predictions/{pred_file.name}"] = {
                        "new_path": f"data/outputs/predictions/2025/regular_season/{pred_file.name}",
                        "category": "predictions",
                        "description": "Regular season predictions",
                    }

        # MODEL COMPONENTS
        component_files = [
            "model_pack/rf_components/random_forest_home.joblib",
            "model_pack/rf_components/random_forest_away.joblib",
        ]
        for component_file in component_files:
            if component_file.endswith("home.joblib"):
                mappings[component_file] = {
                    "new_path": "models/components/rf_components/random_forest_home.joblib",
                    "category": "model_components",
                    "description": "Random Forest home team model component",
                }
            else:
                mappings[component_file] = {
                    "new_path": "models/components/rf_components/random_forest_away.joblib",
                    "category": "model_components",
                    "description": "Random Forest away team model component",
                }

        # BACKUP FILES - Move to systematic archive
        backup_patterns = ["model_pack/backups/", "*backup*", "*_backup_*"]

        # Legacy models to archive
        legacy_models = [
            "model_pack/random_forest_model_2025.pkl",
            "model_pack/random_forest_home.joblib",
            "model_pack/random_forest_away.joblib",
        ]
        for legacy_model in legacy_models:
            mappings[legacy_model] = {
                "new_path": f"models/legacy/v1_models/{legacy_model.split('/')[-1]}",
                "category": "legacy_model",
                "description": "Legacy model version - archived",
            }

        return mappings

    def create_directory_structure(self) -> bool:
        """Create the new directory structure."""
        print("🏗️  Creating new directory structure...")

        if self.dry_run:
            print("🔍 DRY RUN: Would create directories:")
            for dir_path, description in self.new_structure.items():
                print(f"  📁 {dir_path}/ - {description}")
            return True

        try:
            for dir_path, description in self.new_structure.items():
                full_path = self.root_path / dir_path
                full_path.mkdir(parents=True, exist_ok=True)
                print(f"  ✅ Created: {dir_path}/")

            return True

        except Exception as e:
            print(f"❌ Error creating directory structure: {e}")
            return False

    def validate_source_file(self, file_path: str) -> Tuple[bool, str]:
        """Validate that source file exists and is accessible."""
        full_path = self.root_path / file_path

        if not full_path.exists():
            return False, f"Source file does not exist: {file_path}"

        if not full_path.is_file():
            return False, f"Source path is not a file: {file_path}"

        try:
            # Test file access
            with open(full_path, "rb") as f:
                f.read(1)  # Read first byte to test accessibility
            return True, "File accessible"
        except Exception as e:
            return False, f"File not accessible: {e}"

    def calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum for file integrity verification."""
        sha256_hash = hashlib.sha256()

        try:
            with open(file_path, "rb") as f:
                # Read file in chunks to handle large files
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception as e:
            return f"ERROR: {e}"

    def copy_file_with_validation(
        self, old_path: str, new_path: str, metadata: Dict
    ) -> Tuple[bool, str]:
        """Copy file with comprehensive validation."""
        source_file = self.root_path / old_path
        dest_file = self.root_path / new_path

        # Validate source
        source_valid, source_msg = self.validate_source_file(old_path)
        if not source_valid:
            return False, f"Source validation failed: {source_msg}"

        # Create destination directory if needed
        dest_file.parent.mkdir(parents=True, exist_ok=True)

        if self.dry_run:
            print(f"  🔍 DRY RUN: Would copy {old_path} → {new_path}")
            return True, "DRY RUN - File would be copied"

        try:
            # Calculate source checksum before copy
            source_checksum = self.calculate_file_checksum(source_file)

            # Copy the file
            shutil.copy2(source_file, dest_file)

            # Verify copy integrity
            dest_checksum = self.calculate_file_checksum(dest_file)

            if source_checksum != dest_checksum:
                dest_file.unlink()  # Remove corrupted copy
                return False, f"Checksum mismatch: {source_checksum} != {dest_checksum}"

            # Log successful migration
            migration_record = {
                "timestamp": datetime.now().isoformat(),
                "source": old_path,
                "destination": new_path,
                "category": metadata["category"],
                "description": metadata["description"],
                "size_bytes": source_file.stat().st_size,
                "checksum": source_checksum,
            }

            self.migration_log.append(migration_record)

            return True, f"Successfully copied and verified"

        except Exception as e:
            return False, f"Copy failed: {e}"

    def execute_migration(self) -> Dict:
        """Execute the complete migration process."""
        print("🚀 Starting data migration...")

        results = {
            "started_at": datetime.now().isoformat(),
            "dry_run": self.dry_run,
            "directories_created": 0,
            "files_processed": 0,
            "files_success": 0,
            "files_failed": 0,
            "files_skipped": 0,
            "categories_processed": {},
            "errors": [],
        }

        # Step 1: Create directory structure
        if not self.create_directory_structure():
            results["errors"].append("Failed to create directory structure")
            return results

        results["directories_created"] = len(self.new_structure)

        # Step 2: Process file migrations by category
        category_groups = {}
        for old_path, metadata in self.file_mappings.items():
            category = metadata["category"]
            if category not in category_groups:
                category_groups[category] = []
            category_groups[category].append((old_path, metadata))

        # Process categories in priority order
        priority_order = [
            "critical_master",
            "production_model",
            "historical_archive",
            "weekly_update",
            "weekly_features",
            "predictions",
            "model_components",
            "legacy_model",
        ]

        for category in priority_order:
            if category not in category_groups:
                continue

            print(f"\n📂 Processing category: {category}")
            category_files = category_groups[category]
            results["categories_processed"][category] = {
                "total": len(category_files),
                "success": 0,
                "failed": 0,
                "skipped": 0,
            }

            for old_path, metadata in category_files:
                results["files_processed"] += 1

                # Check if source exists
                source_valid, source_msg = self.validate_source_file(old_path)
                if not source_valid:
                    print(f"  ⚠️  Skipping {old_path}: {source_msg}")
                    results["files_skipped"] += 1
                    results["categories_processed"][category]["skipped"] += 1
                    continue

                # Copy file with validation
                success, msg = self.copy_file_with_validation(
                    old_path, metadata["new_path"], metadata
                )

                if success:
                    print(f"  ✅ {old_path} → {metadata['new_path']}")
                    results["files_success"] += 1
                    results["categories_processed"][category]["success"] += 1
                else:
                    print(f"  ❌ {old_path}: {msg}")
                    results["files_failed"] += 1
                    results["categories_processed"][category]["failed"] += 1
                    results["errors"].append(f"{old_path}: {msg}")

        results["completed_at"] = datetime.now().isoformat()
        results["migration_log_file"] = str(self.root_path / "migration_log.json")

        # Save migration log
        if not self.dry_run and self.migration_log:
            with open(self.root_path / "migration_log.json", "w") as f:
                json.dump(self.migration_log, f, indent=2)

        return results

    def generate_migration_report(self, results: Dict) -> str:
        """Generate comprehensive migration report."""
        report = f"""
# 📊 Data Migration Report

**Executed**: {results['started_at']}
**Completed**: {results['completed_at']}
**Dry Run**: {results['dry_run']}

## Summary
- **Directories Created**: {results['directories_created']}
- **Files Processed**: {results['files_processed']}
- **Successful**: {results['files_success']} ✅
- **Failed**: {results['files_failed']} ❌
- **Skipped**: {results['files_skipped']} ⚠️

## Category Breakdown
"""

        for category, stats in results["categories_processed"].items():
            report += f"""
### {category.replace('_', ' ').title()}
- Total: {stats['total']}
- Success: {stats['success']} ✅
- Failed: {stats['failed']} ❌
- Skipped: {stats['skipped']} ⚠️
"""

        if results["errors"]:
            report += "\n## Errors\n"
            for error in results["errors"][:10]:  # Limit to first 10 errors
                report += f"- {error}\n"

        report += f"""

## Migration Log
{'Saved to migration_log.json' if not self.dry_run else 'DRY RUN - No log file created'}

## Next Steps
1. Review any errors above
2. Run validation script to verify migration integrity
3. Test critical workflows with new structure
4. Archive old files after verification
"""

        return report


def main():
    """Main execution function."""
    import argparse

    parser = argparse.ArgumentParser(description="Data Migration Script")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate migration without making changes",
    )
    parser.add_argument("--category", type=str, help="Migrate specific category only")
    args = parser.parse_args()

    print("🔄 Data Migration Script")
    print("=" * 50)
    print(f"Dry Run: {args.dry_run}")
    print(f"Category: {args.category or 'ALL'}")
    print()

    # Initialize migrator
    migrator = DataMigrator(dry_run=args.dry_run)

    # Execute migration
    results = migrator.execute_migration()

    # Generate and save report
    report = migrator.generate_migration_report(results)

    # Print report
    print(report)

    # Save report to file
    report_file = Path("migration_report.md")
    with open(report_file, "w") as f:
        f.write(report)

    print(f"\n📄 Report saved to: {report_file}")

    # Exit with appropriate code
    if results["files_failed"] > 0:
        print(f"\n⚠️  Migration completed with {results['files_failed']} errors")
        return 1
    else:
        print(f"\n✅ Migration completed successfully!")
        return 0


if __name__ == "__main__":
    exit(main())
