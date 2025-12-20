#!/usr/bin/env python3
"""
Safe Code Improvement Validator for Script Ohio 2.0

This script provides comprehensive validation before applying any code improvements
to ensure system integrity and prevent breaking changes.
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class SafeImprovementValidator:
    """Comprehensive validator for safe code improvements"""

    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.validation_results = {
            "timestamp": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "validations": {},
            "errors": [],
            "warnings": [],
            "summary": {},
        }

    def validate_syntax(self) -> bool:
        """Validate Python syntax across all files"""
        print("🔍 Validating Python syntax...")

        syntax_errors = []
        python_files = []

        # Find all Python files in core directories
        for pattern in ["agents/**/*.py", "src/**/*.py", "scripts/**/*.py"]:
            python_files.extend(self.project_root.glob(pattern))

        total_files = len(python_files)
        valid_files = 0

        for file_path in python_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    compile(f.read(), str(file_path), "exec")
                valid_files += 1
            except SyntaxError as e:
                syntax_errors.append(
                    {
                        "file": str(file_path.relative_to(self.project_root)),
                        "line": e.lineno,
                        "error": str(e),
                    }
                )
            except Exception as e:
                syntax_errors.append(
                    {
                        "file": str(file_path.relative_to(self.project_root)),
                        "error": f"File read error: {e}",
                    }
                )

        self.validation_results["validations"]["syntax"] = {
            "total_files": total_files,
            "valid_files": valid_files,
            "errors": len(syntax_errors),
            "error_details": syntax_errors,
        }

        if syntax_errors:
            print(f"❌ Syntax errors found in {len(syntax_errors)} files")
            for error in syntax_errors[:3]:  # Show first 3 errors
                print(
                    f"   - {error['file']}:{error.get('line', '?')}: {error['error']}"
                )
            if len(syntax_errors) > 3:
                print(f"   ... and {len(syntax_errors) - 3} more")
            return False
        else:
            print(f"✅ All {total_files} Python files have valid syntax")
            return True

    def validate_critical_files(self) -> bool:
        """Validate presence and integrity of critical files"""
        print("🔍 Validating critical files...")

        critical_files = [
            "CLAUDE.md",
            "requirements.txt",
            "Makefile",
            "agents/core/agent_framework.py",
            "agents/meta_agent.py",
            "src/cfbd_client/unified_client.py",
            "model_pack/updated_training_data.csv",
        ]

        missing_files = []
        existing_files = []

        for file_path in critical_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                existing_files.append(file_path)
                # Check file size for basic integrity
                size = full_path.stat().st_size
                if size == 0:
                    self.validation_results["warnings"].append(
                        f"File is empty: {file_path}"
                    )
            else:
                missing_files.append(file_path)

        self.validation_results["validations"]["critical_files"] = {
            "total_critical": len(critical_files),
            "existing": len(existing_files),
            "missing": len(missing_files),
            "missing_files": missing_files,
            "existing_files": existing_files,
        }

        if missing_files:
            print(f"❌ {len(missing_files)} critical files missing")
            for file_path in missing_files:
                print(f"   - {file_path}")
            return False
        else:
            print(f"✅ All {len(critical_files)} critical files present")
            return True

    def validate_data_integrity(self) -> bool:
        """Validate data files and models"""
        print("🔍 Validating data integrity...")

        data_checks = []

        # Check training data
        training_data_paths = [
            "model_pack/updated_training_data.csv",
            "data/processed/training/master_training_data_v2.csv",
        ]

        training_data_found = False
        for data_path in training_data_paths:
            full_path = self.project_root / data_path
            if full_path.exists():
                try:
                    import pandas as pd

                    df = pd.read_csv(full_path)
                    if len(df) > 0:
                        training_data_found = True
                        data_checks.append(
                            {
                                "file": data_path,
                                "status": "valid",
                                "rows": len(df),
                                "columns": len(df.columns),
                            }
                        )
                        break
                except Exception as e:
                    data_checks.append(
                        {"file": data_path, "status": "error", "error": str(e)}
                    )

        if not training_data_found:
            data_checks.append(
                {
                    "file": "training_data",
                    "status": "missing",
                    "error": "No valid training data found",
                }
            )

        # Check model files
        model_files = [
            "model_pack/ridge_model_2025.joblib",
            "model_pack/xgb_home_win_model_2025.pkl",
            "model_pack/fastai_home_win_model_2025.pkl",
        ]

        existing_models = []
        for model_file in model_files:
            full_path = self.project_root / model_file
            if full_path.exists():
                existing_models.append(model_file)

        self.validation_results["validations"]["data_integrity"] = {
            "training_data": data_checks,
            "model_files": {
                "expected": len(model_files),
                "found": len(existing_models),
                "files": existing_models,
            },
        }

        # Report results
        training_valid = any(check.get("status") == "valid" for check in data_checks)
        models_found = len(existing_models) > 0

        if training_valid and models_found:
            print(f"✅ Data integrity validated")
            print(f"   - Training data: {len(data_checks)} locations checked")
            print(f"   - Model files: {len(existing_models)}/{len(model_files)} found")
            return True
        else:
            print(f"⚠️  Data integrity issues detected")
            if not training_valid:
                print(f"   - Training data: No valid files found")
            if not models_found:
                print(
                    f"   - Model files: {len(existing_models)}/{len(model_files)} found"
                )
            return False  # Data issues are warnings, not failures

    def check_git_status(self) -> bool:
        """Check git status for uncommitted changes"""
        print("🔍 Checking git status...")

        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )

            modified_files = (
                len(result.stdout.strip().split("\n")) if result.stdout.strip() else 0
            )

            self.validation_results["validations"]["git_status"] = {
                "modified_files": modified_files,
                "has_changes": modified_files > 0,
            }

            if modified_files > 0:
                print(f"⚠️  {modified_files} uncommitted changes detected")
                print("   Consider committing or stashing changes before improvements")
                return True  # Don't fail, just warn
            else:
                print(f"✅ No uncommitted changes")
                return True

        except subprocess.CalledProcessError:
            print("⚠️  Git status check failed (not a git repository?)")
            return True  # Don't fail for git issues

    def validate_dependencies(self) -> bool:
        """Validate Python dependencies"""
        print("🔍 Validating dependencies...")

        requirements_file = self.project_root / "requirements.txt"
        if not requirements_file.exists():
            print("⚠️  requirements.txt not found")
            return True  # Don't fail

        try:
            # Check if requirements.txt is well-formed
            with open(requirements_file, "r") as f:
                requirements = [
                    line.strip()
                    for line in f
                    if line.strip() and not line.startswith("#")
                ]

            self.validation_results["validations"]["dependencies"] = {
                "requirements_file": str(requirements_file),
                "total_requirements": len(requirements),
                "sample_requirements": requirements[:5],  # Show first 5
            }

            print(f"✅ {len(requirements)} dependencies found in requirements.txt")
            return True

        except Exception as e:
            print(f"❌ Error reading requirements.txt: {e}")
            return False

    def run_comprehensive_validation(self) -> Dict:
        """Run all validation checks"""
        print("🏈 Script Ohio 2.0 - Comprehensive Safe Improvement Validation")
        print("=" * 70)
        print()

        validations = [
            ("Syntax Validation", self.validate_syntax),
            ("Critical Files", self.validate_critical_files),
            ("Data Integrity", self.validate_data_integrity),
            ("Git Status", self.check_git_status),
            ("Dependencies", self.validate_dependencies),
        ]

        passed = 0
        total = len(validations)

        for name, validator in validations:
            try:
                if validator():
                    passed += 1
                print()
            except Exception as e:
                print(f"❌ {name} failed with exception: {e}")
                print()
                self.validation_results["errors"].append(f"{name}: {e}")

        # Generate summary
        success_rate = (passed / total) * 100
        self.validation_results["summary"] = {
            "total_validations": total,
            "passed": passed,
            "failed": total - passed,
            "success_rate": success_rate,
            "can_proceed": passed >= total - 1,  # Allow 1 validation to fail
        }

        # Final report
        print("🎯 VALIDATION SUMMARY")
        print("=" * 30)
        print(f"Passed: {passed}/{total} ({success_rate:.1f}%)")
        print(f"Errors: {len(self.validation_results['errors'])}")
        print(f"Warnings: {len(self.validation_results['warnings'])}")

        if self.validation_results["summary"]["can_proceed"]:
            print("✅ Safe to proceed with improvements!")
        else:
            print("❌ Address critical issues before proceeding")

        return self.validation_results

    def save_report(self, output_file: str = None) -> str:
        """Save validation report to file"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"validation_report_{timestamp}.json"

        output_path = self.project_root / output_file

        with open(output_path, "w") as f:
            json.dump(self.validation_results, f, indent=2)

        return str(output_path)


def main():
    """Main execution function"""
    import argparse

    parser = argparse.ArgumentParser(description="Safe Code Improvement Validator")
    parser.add_argument("--project-root", help="Project root directory")
    parser.add_argument("--output", help="Output report file")
    parser.add_argument("--quiet", action="store_true", help="Minimal output")

    args = parser.parse_args()

    validator = SafeImprovementValidator(args.project_root)

    if args.quiet:
        import contextlib
        import io

        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            results = validator.run_comprehensive_validation()
    else:
        results = validator.run_comprehensive_validation()

    # Save report
    report_file = validator.save_report(args.output)

    if not args.quiet:
        print(f"\n📄 Detailed report saved to: {report_file}")

    # Exit with appropriate code
    if results["summary"]["can_proceed"]:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
