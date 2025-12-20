#!/usr/bin/env python3
"""
Data Migration Validation Script

Comprehensive validation of migrated data to ensure integrity, completeness,
and functionality preservation.

Author: Data Architecture Orchestrator
Created: 2025-12-18
"""

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd


class MigrationValidator:
    """
    Validates data migration integrity and functionality.

    Validation Checks:
    1. File integrity verification (checksums)
    2. Data completeness validation
    3. Schema consistency checks
    4. Functional testing of ML pipelines
    5. Performance benchmarking
    """

    def __init__(self):
        self.root_path = Path(".").resolve()
        self.validation_results = {}
        self.critical_files = [
            "data/processed/training/master_training_data_v2.csv",
            "models/production/ridge_regression_2025_v2.joblib",
            "models/production/xgboost_classifier_2025_v2.pkl",
            "models/production/fastai_neural_net_2025_v2.pkl",
        ]

    def validate_file_integrity(self) -> Dict:
        """Validate file integrity using checksums from migration log."""
        print("🔍 Validating file integrity...")

        results = {
            "files_checked": 0,
            "checksums_valid": 0,
            "checksums_invalid": 0,
            "files_missing": 0,
            "details": [],
        }

        migration_log_path = self.root_path / "migration_log.json"
        if not migration_log_path.exists():
            results["details"].append(
                "Migration log not found - cannot validate checksums"
            )
            return results

        try:
            with open(migration_log_path, "r") as f:
                migration_log = json.load(f)

            for record in migration_log:
                results["files_checked"] += 1

                source_path = self.root_path / record["source"]
                dest_path = self.root_path / record["destination"]

                # Check if both files exist
                if not source_path.exists():
                    results["files_missing"] += 1
                    results["details"].append(
                        f"Source file missing: {record['source']}"
                    )
                    continue

                if not dest_path.exists():
                    results["files_missing"] += 1
                    results["details"].append(
                        f"Destination file missing: {record['destination']}"
                    )
                    continue

                # Calculate checksums
                source_checksum = self.calculate_checksum(source_path)
                dest_checksum = self.calculate_checksum(dest_path)

                # Compare with recorded checksum
                recorded_checksum = record.get("checksum", "")

                if (
                    source_checksum == recorded_checksum
                    and dest_checksum == recorded_checksum
                ):
                    results["checksums_valid"] += 1
                    results["details"].append(
                        f"✅ {record['destination']} - Checksum valid"
                    )
                else:
                    results["checksums_invalid"] += 1
                    results["details"].append(
                        f"❌ {record['destination']} - Checksum mismatch"
                    )

        except Exception as e:
            results["details"].append(f"Error reading migration log: {e}")

        return results

    def validate_data_completeness(self) -> Dict:
        """Validate that all critical data is present and accessible."""
        print("📊 Validating data completeness...")

        results = {
            "critical_files_checked": len(self.critical_files),
            "critical_files_found": 0,
            "critical_files_accessible": 0,
            "data_quality_issues": [],
            "details": [],
        }

        for file_path in self.critical_files:
            full_path = self.root_path / file_path

            if full_path.exists():
                results["critical_files_found"] += 1
                results["details"].append(f"✅ Found: {file_path}")

                # Test file accessibility
                try:
                    if file_path.endswith(".csv"):
                        # Test CSV file
                        df = pd.read_csv(full_path, nrows=5)
                        if len(df) > 0:
                            results["critical_files_accessible"] += 1
                            results["details"].append(
                                f"✅ Accessible: {file_path} ({len(df)} columns)"
                            )
                        else:
                            results["data_quality_issues"].append(
                                f"Empty or corrupted: {file_path}"
                            )
                    else:
                        # Test model file
                        with open(full_path, "rb") as f:
                            f.read(100)  # Read first 100 bytes
                        results["critical_files_accessible"] += 1
                        results["details"].append(f"✅ Accessible: {file_path}")

                except Exception as e:
                    results["data_quality_issues"].append(
                        f"Access error: {file_path} - {e}"
                    )
                    results["details"].append(f"❌ Inaccessible: {file_path}")
            else:
                results["details"].append(f"❌ Missing: {file_path}")

        return results

    def validate_schema_consistency(self) -> Dict:
        """Validate schema consistency for CSV datasets."""
        print("🏗️  Validating schema consistency...")

        results = {
            "datasets_validated": 0,
            "schemas_consistent": 0,
            "schema_issues": [],
            "details": [],
        }

        # Define expected schemas for critical datasets
        expected_schemas = {
            "data/processed/training/master_training_data_v2.csv": {
                "min_rows": 4000,
                "min_columns": 80,
                "key_columns": ["season", "week", "home_team", "away_team"],
            }
        }

        for file_path, expected_schema in expected_schemas.items():
            full_path = self.root_path / file_path

            if full_path.exists() and full_path.suffix == ".csv":
                results["datasets_validated"] += 1

                try:
                    df = pd.read_csv(full_path)

                    # Check dimensions
                    rows, cols = df.shape
                    if rows >= expected_schema["min_rows"]:
                        results["details"].append(f"✅ {file_path}: {rows:,} rows")
                    else:
                        results["schema_issues"].append(
                            f"{file_path}: Only {rows:,} rows (expected {expected_schema['min_rows']:,})"
                        )

                    if cols >= expected_schema["min_columns"]:
                        results["details"].append(f"✅ {file_path}: {cols} columns")
                    else:
                        results["schema_issues"].append(
                            f"{file_path}: Only {cols} columns (expected {expected_schema['min_columns']})"
                        )

                    # Check key columns
                    missing_columns = [
                        col
                        for col in expected_schema["key_columns"]
                        if col not in df.columns
                    ]
                    if not missing_columns:
                        results["details"].append(
                            f"✅ {file_path}: Key columns present"
                        )
                        results["schemas_consistent"] += 1
                    else:
                        results["schema_issues"].append(
                            f"{file_path}: Missing key columns: {missing_columns}"
                        )

                    # Check for excessive null values
                    null_percentage = (df.isnull().sum().sum() / (rows * cols)) * 100
                    if null_percentage < 5:
                        results["details"].append(
                            f"✅ {file_path}: {null_percentage:.1f}% null values"
                        )
                    else:
                        results["schema_issues"].append(
                            f"{file_path}: High null percentage: {null_percentage:.1f}%"
                        )

                except Exception as e:
                    results["schema_issues"].append(
                        f"Error validating {file_path}: {e}"
                    )

        return results

    def validate_ml_functionality(self) -> Dict:
        """Validate that ML models can be loaded and basic functionality works."""
        print("🤖 Validating ML model functionality...")

        results = {
            "models_tested": 0,
            "models_loaded": 0,
            "models_functional": 0,
            "model_errors": [],
            "details": [],
        }

        # Test model loading (basic validation)
        model_files = [
            "models/production/ridge_regression_2025_v2.joblib",
            "models/production/xgboost_classifier_2025_v2.pkl",
        ]

        for model_file in model_files:
            full_path = self.root_path / model_file
            results["models_tested"] += 1

            if not full_path.exists():
                results["model_errors"].append(f"Model file missing: {model_file}")
                continue

            try:
                if model_file.endswith(".joblib"):
                    # Test joblib model
                    import joblib

                    model = joblib.load(full_path)
                    results["models_loaded"] += 1
                    results["details"].append(f"✅ {model_file}: Loaded successfully")

                elif model_file.endswith(".pkl"):
                    # Test pickle model
                    import pickle

                    with open(full_path, "rb") as f:
                        model = pickle.load(f)
                    results["models_loaded"] += 1
                    results["details"].append(f"✅ {model_file}: Loaded successfully")

                # Basic functionality test
                if hasattr(model, "predict") or hasattr(model, "__call__"):
                    results["models_functional"] += 1
                    results["details"].append(
                        f"✅ {model_file}: Functional (has predict/call method)"
                    )
                else:
                    results["details"].append(
                        f"⚠️  {model_file}: Loaded but may lack predict method"
                    )

            except Exception as e:
                results["model_errors"].append(f"{model_file}: {e}")
                results["details"].append(f"❌ {model_file}: Failed to load")

        return results

    def validate_script_paths(self) -> Dict:
        """Validate that script paths can be updated to work with new structure."""
        print("🔧 Validating script path updates...")

        results = {
            "scripts_checked": 0,
            "scripts_need_update": 0,
            "path_updates_identified": [],
            "details": [],
        }

        # Common path patterns that need updating
        path_patterns = {
            "model_pack/updated_training_data.csv": "data/processed/training/master_training_data_v2.csv",
            "model_pack/": "models/production/",
            "predictions/": "data/outputs/predictions/",
            "data/weekly/": "data/processed/enhanced/",
        }

        scripts_dir = self.root_path / "scripts"
        if scripts_dir.exists():
            for script_file in scripts_dir.rglob("*.py"):
                results["scripts_checked"] += 1

                try:
                    content = script_file.read_text(encoding="utf-8")
                    script_relative = str(script_file.relative_to(self.root_path))
                    updates_needed = []

                    for old_pattern, new_pattern in path_patterns.items():
                        if old_pattern in content:
                            updates_needed.append((old_pattern, new_pattern))

                    if updates_needed:
                        results["scripts_need_update"] += 1
                        results["path_updates_identified"].append(
                            {
                                "script": script_relative,
                                "updates_needed": updates_needed,
                            }
                        )
                        results["details"].append(
                            f"⚠️  {script_relative}: {len(updates_needed)} path updates needed"
                        )
                    else:
                        results["details"].append(
                            f"✅ {script_relative}: No path updates needed"
                        )

                except Exception as e:
                    results["details"].append(
                        f"❌ {script_relative}: Error reading script - {e}"
                    )

        return results

    def run_performance_benchmark(self) -> Dict:
        """Run basic performance benchmarks on the new structure."""
        print("⚡ Running performance benchmarks...")

        results = {"file_access_times": {}, "dataset_load_times": {}, "details": []}

        # Test file access times for critical files
        for file_path in self.critical_files:
            full_path = self.root_path / file_path

            if full_path.exists():
                start_time = datetime.now()

                try:
                    # Simulate file access
                    with open(full_path, "rb") as f:
                        f.read(1024)  # Read first 1KB

                    access_time = (datetime.now() - start_time).total_seconds()
                    results["file_access_times"][file_path] = access_time

                    if access_time < 0.1:  # Less than 100ms
                        results["details"].append(
                            f"✅ {file_path}: {access_time:.3f}s access time"
                        )
                    else:
                        results["details"].append(
                            f"⚠️  {file_path}: {access_time:.3f}s access time (slow)"
                        )

                except Exception as e:
                    results["details"].append(f"❌ {file_path}: Access error - {e}")

        # Test dataset load times
        master_data_path = (
            self.root_path / "data/processed/training/master_training_data_v2.csv"
        )
        if master_data_path.exists():
            start_time = datetime.now()

            try:
                df = pd.read_csv(master_data_path)
                load_time = (datetime.now() - start_time).total_seconds()
                results["dataset_load_times"]["master_training_data"] = {
                    "load_time": load_time,
                    "rows": len(df),
                    "columns": len(df.columns),
                    "rows_per_second": (
                        len(df) / load_time if load_time > 0 else float("inf")
                    ),
                }

                results["details"].append(
                    f"✅ Master dataset: {len(df):,} rows loaded in {load_time:.2f}s"
                )

            except Exception as e:
                results["details"].append(f"❌ Master dataset load failed: {e}")

        return results

    def calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum for file."""
        sha256_hash = hashlib.sha256()

        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception:
            return "ERROR"

    def run_comprehensive_validation(self) -> Dict:
        """Run all validation checks and generate comprehensive report."""
        print("🔍 Starting comprehensive migration validation...")
        print("=" * 60)

        all_results = {
            "validation_timestamp": datetime.now().isoformat(),
            "validation_checks": {},
        }

        # Run all validation checks
        validation_checks = [
            ("file_integrity", self.validate_file_integrity),
            ("data_completeness", self.validate_data_completeness),
            ("schema_consistency", self.validate_schema_consistency),
            ("ml_functionality", self.validate_ml_functionality),
            ("script_paths", self.validate_script_paths),
            ("performance_benchmark", self.run_performance_benchmark),
        ]

        for check_name, check_func in validation_checks:
            print(f"\n{check_name.replace('_', ' ').title()}:")
            print("-" * 40)

            try:
                result = check_func()
                all_results["validation_checks"][check_name] = result

                # Print summary
                if "files_checked" in result:
                    print(f"Files checked: {result['files_checked']}")
                if "files_success" in result:
                    print(
                        f"Success rate: {result['files_success']}/{result['files_checked']}"
                    )
                if "critical_files_found" in result:
                    print(
                        f"Critical files: {result['critical_files_found']}/{result['critical_files_checked']}"
                    )

            except Exception as e:
                print(f"❌ Validation check failed: {e}")
                all_results["validation_checks"][check_name] = {
                    "error": str(e),
                    "status": "failed",
                }

        # Calculate overall validation score
        all_results["overall_score"] = self.calculate_overall_score(
            all_results["validation_checks"]
        )

        return all_results

    def calculate_overall_score(self, validation_results: Dict) -> Dict:
        """Calculate overall validation score."""
        score = {
            "total_checks": len(validation_results),
            "passed_checks": 0,
            "failed_checks": 0,
            "overall_percentage": 0,
            "status": "UNKNOWN",
        }

        for check_name, result in validation_results.items():
            if "error" in result:
                score["failed_checks"] += 1
            else:
                # Determine if check passed based on results
                if check_name == "file_integrity":
                    passed = (
                        result.get("checksums_invalid", 1) == 0
                        and result.get("files_missing", 1) == 0
                    )
                elif check_name == "data_completeness":
                    passed = result.get("critical_files_accessible", 0) == result.get(
                        "critical_files_checked", 1
                    )
                elif check_name == "schema_consistency":
                    passed = len(result.get("schema_issues", [])) == 0
                elif check_name == "ml_functionality":
                    passed = result.get("models_functional", 0) > 0
                else:
                    # Other checks are informational
                    passed = True

                if passed:
                    score["passed_checks"] += 1
                else:
                    score["failed_checks"] += 1

        score["overall_percentage"] = (
            (score["passed_checks"] / score["total_checks"]) * 100
            if score["total_checks"] > 0
            else 0
        )

        if score["overall_percentage"] >= 90:
            score["status"] = "EXCELLENT"
        elif score["overall_percentage"] >= 75:
            score["status"] = "GOOD"
        elif score["overall_percentage"] >= 50:
            score["status"] = "NEEDS_ATTENTION"
        else:
            score["status"] = "CRITICAL_ISSUES"

        return score

    def generate_validation_report(self, results: Dict) -> str:
        """Generate comprehensive validation report."""
        overall_score = results["overall_score"]

        report = f"""
# 🔍 Migration Validation Report

**Validation Time**: {results['validation_timestamp']}

## 📊 Overall Assessment

**Status**: {overall_score['status']}
**Score**: {overall_score['overall_percentage']:.1f}% ({overall_score['passed_checks']}/{overall_score['total_checks']} checks passed)

---

## 📋 Detailed Results

### File Integrity Validation
{self._format_validation_section(results['validation_checks'].get('file_integrity', {}))}

### Data Completeness Check
{self._format_validation_section(results['validation_checks'].get('data_completeness', {}))}

### Schema Consistency Validation
{self._format_validation_section(results['validation_checks'].get('schema_consistency', {}))}

### ML Functionality Test
{self._format_validation_section(results['validation_checks'].get('ml_functionality', {}))}

### Script Path Validation
{self._format_validation_section(results['validation_checks'].get('script_paths', {}))}

### Performance Benchmarks
{self._format_validation_section(results['validation_checks'].get('performance_benchmark', {}))}

---

## 🎯 Recommendations

{self._generate_recommendations(results)}

## ✅ Next Steps

{self._generate_next_steps(results)}

---

*Generated by Migration Validator - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

        return report

    def _format_validation_section(self, result: Dict) -> str:
        """Format validation section for report."""
        if "error" in result:
            return f"❌ **Failed**: {result['error']}"

        section = ""

        # Add summary statistics
        for key, value in result.items():
            if key == "details":
                continue
            if isinstance(value, (int, float)):
                section += f"- **{key.replace('_', ' ').title()}**: {value:,}\n"
            elif isinstance(value, dict):
                section += (
                    f"- **{key.replace('_', ' ').title()}**: {len(value)} items\n"
                )

        # Add key details
        if "details" in result and result["details"]:
            section += "\n**Key Findings**:\n"
            for detail in result["details"][:5]:  # Limit to first 5 details
                section += f"- {detail}\n"
            if len(result["details"]) > 5:
                section += f"- ... and {len(result['details']) - 5} more items\n"

        return section if section else "✅ **All checks passed**"

    def _generate_recommendations(self, results: Dict) -> str:
        """Generate recommendations based on validation results."""
        recommendations = []

        # Analyze results and generate specific recommendations
        for check_name, result in results["validation_checks"].items():
            if "error" in result:
                recommendations.append(
                    f"**Critical**: Fix {check_name.replace('_', ' ').title()} validation error"
                )
                continue

            if (
                check_name == "script_paths"
                and result.get("scripts_need_update", 0) > 0
            ):
                recommendations.append(
                    f"**High Priority**: Update {result['scripts_need_update']} scripts with new file paths"
                )

            if (
                check_name == "schema_consistency"
                and len(result.get("schema_issues", [])) > 0
            ):
                recommendations.append(
                    f"**Medium Priority**: Address {len(result['schema_issues'])} schema consistency issues"
                )

            if check_name == "performance_benchmark":
                slow_files = [
                    path
                    for path, time in result.get("file_access_times", {}).items()
                    if time > 0.1
                ]
                if slow_files:
                    recommendations.append(
                        f"**Low Priority**: Optimize access to {len(slow_files)} slow files"
                    )

        if not recommendations:
            recommendations.append(
                "✅ **No issues found** - Migration validation passed successfully!"
            )

        return "\n".join(recommendations)

    def _generate_next_steps(self, results: Dict) -> str:
        """Generate next steps based on validation results."""
        overall_score = results["overall_score"]["overall_percentage"]

        if overall_score >= 90:
            return """
1. ✅ Migration validation successful - proceed with confidence
2. Update scripts with new file paths
3. Test critical workflows end-to-end
4. Archive old directory structure after validation period
5. Update documentation and team training materials
"""
        elif overall_score >= 75:
            return """
1. ⚠️  Migration mostly successful - address medium priority issues
2. Fix identified schema and functionality issues
3. Re-run validation after fixes
4. Proceed with script updates once issues resolved
5. Consider keeping old structure as backup during transition
"""
        else:
            return """
1. ❌ Critical issues found - do not proceed with production use
2. Address all critical validation failures
3. Re-run migration if necessary
4. Ensure all critical files are accessible and functional
5. Seek additional assistance if issues persist
"""


def main():
    """Main execution function."""
    import argparse

    parser = argparse.ArgumentParser(description="Migration Validation Script")
    parser.add_argument(
        "--check",
        type=str,
        choices=["integrity", "completeness", "schema", "ml", "scripts", "performance"],
        help="Run specific validation check only",
    )
    args = parser.parse_args()

    print("🔍 Migration Validation Script")
    print("=" * 50)

    # Initialize validator
    validator = MigrationValidator()

    if args.check:
        # Run specific check
        check_functions = {
            "integrity": validator.validate_file_integrity,
            "completeness": validator.validate_data_completeness,
            "schema": validator.validate_schema_consistency,
            "ml": validator.validate_ml_functionality,
            "scripts": validator.validate_script_paths,
            "performance": validator.run_performance_benchmark,
        }

        if args.check in check_functions:
            results = {args.check: check_functions[args.check]()}
        else:
            print(f"Unknown check: {args.check}")
            return 1
    else:
        # Run comprehensive validation
        results = validator.run_comprehensive_validation()

    # Generate and save report
    report = validator.generate_validation_report(results)

    # Print report
    print(report)

    # Save report
    report_file = Path("validation_report.md")
    with open(report_file, "w") as f:
        f.write(report)

    # Save detailed results as JSON
    results_file = Path("validation_results.json")
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n📄 Report saved to: {report_file}")
    print(f"📄 Detailed results saved to: {results_file}")

    # Exit with appropriate code
    overall_score = results.get("overall_score", {}).get("overall_percentage", 0)
    if overall_score >= 75:
        print(f"\n✅ Validation completed successfully ({overall_score:.1f}%)")
        return 0
    else:
        print(f"\n⚠️  Validation completed with issues ({overall_score:.1f}%)")
        return 1


if __name__ == "__main__":
    exit(main())
