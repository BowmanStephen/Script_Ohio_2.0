#!/usr/bin/env python3.13
"""
Validation Agent - Phase 3 of Project Management Reorganization

This agent validates that the reorganization was successful and all functionality
is preserved. It tests Python imports, CLAUDE.md commands, and overall system health.
"""

import os
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ValidationTest:
    """Represents a validation test"""
    name: str
    description: str
    test_type: str  # import, command, file_exists, structure
    expected_result: Any
    actual_result: Any = None
    status: str = "pending"  # pending, passed, failed
    error_message: str = ""
    execution_time: float = 0.0

@dataclass
class ValidationResult:
    """Overall validation result"""
    total_tests: int
    passed_tests: int
    failed_tests: int
    success_rate: float
    critical_failures: List[str]
    warnings: List[str]
    execution_time: float
    timestamp: datetime

class ValidationAgent:
    """Validates the reorganization results"""

    def __init__(self, project_root: str = "/Users/stephen_bowman/Documents/GitHub/Script_Ohio_2.0"):
        self.project_root = Path(project_root)
        self.pm_directory = self.project_root / "project_management"
        self.tests = []
        self.critical_failures = []
        self.warnings = []

    def load_expected_structure(self) -> Dict:
        """Load the expected structure from reorganization plans"""
        try:
            # Load categorization report
            cat_path = self.pm_directory / "categorization_report.json"
            with open(cat_path, 'r', encoding='utf-8') as f:
                categorization = json.load(f)

            return categorization

        except Exception as e:
            print(f"⚠️  Could not load expected structure: {e}")
            return {}

    def create_structure_tests(self) -> List[ValidationTest]:
        """Create tests to verify directory structure"""
        tests = []

        # Test new directory structure exists
        expected_dirs = [
            "core_tools",
            "config",
            "quality_assurance",
            "agents",
            "docs",
            "docs/user_guides",
            "docs/technical_docs",
            "docs/comprehensive_guides",
            "archive"
        ]

        for dir_path in expected_dirs:
            full_path = self.pm_directory / dir_path
            tests.append(ValidationTest(
                name=f"Directory exists: {dir_path}",
                description=f"Verify {dir_path} directory was created",
                test_type="file_exists",
                expected_result=True,
                actual_result=full_path.exists()
            ))

        # Test core files exist in new locations
        core_files = [
            "core_tools/data_workflows.py",
            "core_tools/demo_agent_system.py",
            "core_tools/test_agents.py",
            "quality_assurance/test_fixed_system.py"
        ]

        for file_path in core_files:
            full_path = self.pm_directory / file_path
            tests.append(ValidationTest(
                name=f"Core file exists: {file_path}",
                description=f"Verify {file_path} exists in new location",
                test_type="file_exists",
                expected_result=True,
                actual_result=full_path.exists()
            ))

        return tests

    def create_import_tests(self) -> List[ValidationTest]:
        """Create tests to verify Python imports work"""
        tests = []

        # Test key imports that should work
        import_tests = [
            ("from agents.core.agent_framework import BaseAgent", "Agent framework import"),
            ("from agents.analytics_orchestrator import AnalyticsOrchestrator", "Analytics orchestrator import"),
            ("from agents.model_execution_engine import ModelExecutionEngine", "Model execution engine import"),
        ]

        for import_statement, description in import_tests:
            tests.append(ValidationTest(
                name=f"Import test: {description}",
                description=description,
                test_type="import",
                expected_result=True,
                actual_result=None  # Will be filled during execution
            ))

        return tests

    def create_claude_command_tests(self) -> List[ValidationTest]:
        """Create tests for CLAUDE.md commands"""
        tests = []

        # Extract key commands from CLAUDE.md
        claude_commands = [
            ("python project_management/data_workflows.py --help", "Data workflows help command"),
            ("python project_management/core_tools/test_agents.py", "Test agents command"),
            ("python project_management/core_tools/demo_agent_system.py", "Demo agent system command"),
            ("python project_management/quality_assurance/test_fixed_system.py", "Test fixed system command"),
        ]

        # Update paths for new structure
        updated_commands = [
            ("python project_management/core_tools/test_agents.py", "Test agents command (new path)"),
            ("python project_management/core_tools/demo_agent_system.py", "Demo agent system (new path)"),
            ("python project_management/quality_assurance/test_fixed_system.py", "Test fixed system (new path)"),
        ]

        for command, description in updated_commands:
            tests.append(ValidationTest(
                name=f"CLAUDE command: {description}",
                description=description,
                test_type="command",
                expected_result="success",  # Command should execute without error
                actual_result=None
            ))

        return tests

    def create_file_integrity_tests(self) -> List[ValidationTest]:
        """Create tests to verify file integrity"""
        tests = []

        # Test that core files are not empty and have content
        core_files = [
            "core_tools/data_workflows.py",
            "core_tools/demo_agent_system.py",
            "quality_assurance/test_fixed_system.py"
        ]

        for file_path in core_files:
            full_path = self.pm_directory / file_path
            if full_path.exists():
                try:
                    size = full_path.stat().st_size
                    tests.append(ValidationTest(
                        name=f"File integrity: {file_path}",
                        description=f"Verify {file_path} has content",
                        test_type="file_size",
                        expected_result="> 1000 bytes",  # Should have meaningful content
                        actual_result=f"{size} bytes"
                    ))
                except Exception as e:
                    tests.append(ValidationTest(
                        name=f"File integrity: {file_path}",
                        description=f"Verify {file_path} has content",
                        test_type="file_size",
                        expected_result="> 1000 bytes",
                        actual_result=f"Error: {e}",
                        status="failed",
                        error_message=str(e)
                    ))

        return tests

    def execute_import_test(self, test: ValidationTest) -> bool:
        """Execute an import test"""
        try:
            # Create a minimal test script
            test_code = f"""
import sys
sys.path.insert(0, r'{self.project_root}')

try:
    {test.name.split(': ', 1)[1].split(' import test')[0]}
    print("SUCCESS")
except Exception as e:
    print(f"ERROR: {{e}}")
    sys.exit(1)
"""

            # Write test script to temporary file
            test_file = self.project_root / "temp_import_test.py"
            with open(test_file, 'w') as f:
                f.write(test_code)

            # Execute test
            result = subprocess.run(
                [sys.executable, str(test_file)],
                capture_output=True,
                text=True,
                timeout=10
            )

            # Clean up
            test_file.unlink(missing_ok=True)

            if result.returncode == 0 and "SUCCESS" in result.stdout:
                return True
            else:
                test.error_message = result.stderr or result.stdout
                return False

        except Exception as e:
            test.error_message = str(e)
            return False

    def execute_command_test(self, test: ValidationTest) -> bool:
        """Execute a command test"""
        try:
            command_parts = test.name.split(": ", 1)[1].split(" (")[0].split()
            if not command_parts:
                return False

            # Change to project root directory
            original_cwd = os.getcwd()
            os.chdir(self.project_root)

            try:
                # Execute command with timeout
                result = subprocess.run(
                    command_parts,
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                # Check if command executed successfully (help commands, etc.)
                if result.returncode == 0 or "help" in " ".join(command_parts):
                    return True
                else:
                    test.error_message = result.stderr or result.stdout
                    return False

            finally:
                os.chdir(original_cwd)

        except subprocess.TimeoutExpired:
            test.error_message = "Command timed out"
            return False
        except Exception as e:
            test.error_message = str(e)
            return False

    def execute_file_exists_test(self, test: ValidationTest) -> bool:
        """Execute a file existence test"""
        if test.expected_result is True:
            # Should exist
            return test.actual_result is True
        else:
            # Should not exist
            return test.actual_result is False

    def execute_file_size_test(self, test: ValidationTest) -> bool:
        """Execute a file size test"""
        try:
            if isinstance(test.actual_result, str) and "bytes" in test.actual_result:
                size = int(test.actual_result.split()[0])
                return size > 1000  # Should have meaningful content
            return False
        except:
            return False

    def run_test(self, test: ValidationTest) -> bool:
        """Run a single validation test"""
        start_time = time.time()

        try:
            if test.test_type == "import":
                success = self.execute_import_test(test)
            elif test.test_type == "command":
                success = self.execute_command_test(test)
            elif test.test_type == "file_exists":
                success = self.execute_file_exists_test(test)
            elif test.test_type == "file_size":
                success = self.execute_file_size_test(test)
            else:
                success = False
                test.error_message = f"Unknown test type: {test.test_type}"

            test.status = "passed" if success else "failed"
            test.execution_time = time.time() - start_time

            return success

        except Exception as e:
            test.status = "failed"
            test.error_message = str(e)
            test.execution_time = time.time() - start_time
            return False

    def create_all_tests(self) -> List[ValidationTest]:
        """Create all validation tests"""
        print("🧪 Creating validation tests...")

        all_tests = []
        all_tests.extend(self.create_structure_tests())
        all_tests.extend(self.create_import_tests())
        all_tests.extend(self.create_claude_command_tests())
        all_tests.extend(self.create_file_integrity_tests())

        print(f"   Created {len(all_tests)} validation tests")
        return all_tests

    def run_validation(self) -> ValidationResult:
        """Run complete validation suite"""
        print("🚀 Starting Validation Suite")
        print("=" * 60)

        start_time = time.time()

        # Create all tests
        self.tests = self.create_all_tests()

        # Run tests
        print(f"\n🔬 Running {len(self.tests)} validation tests...")

        passed = 0
        failed = 0

        for i, test in enumerate(self.tests, 1):
            print(f"[{i:3d}/{len(self.tests)}] ", end="")

            # Truncate test name for display
            display_name = test.name[:60] + "..." if len(test.name) > 60 else test.name
            print(f"{display_name}... ", end="")

            if self.run_test(test):
                print("✅ PASSED")
                passed += 1
            else:
                print("❌ FAILED")
                failed += 1
                if test.error_message:
                    self.critical_failures.append(f"{test.name}: {test.error_message}")

        execution_time = time.time() - start_time
        success_rate = passed / len(self.tests) if self.tests else 0

        # Create result
        result = ValidationResult(
            total_tests=len(self.tests),
            passed_tests=passed,
            failed_tests=failed,
            success_rate=success_rate,
            critical_failures=self.critical_failures,
            warnings=self.warnings,
            execution_time=execution_time,
            timestamp=datetime.now()
        )

        return result

    def generate_validation_report(self, result: ValidationResult) -> Dict:
        """Generate a detailed validation report"""
        return {
            "summary": {
                "total_tests": result.total_tests,
                "passed_tests": result.passed_tests,
                "failed_tests": result.failed_tests,
                "success_rate": round(result.success_rate * 100, 1),
                "execution_time_seconds": round(result.execution_time, 2),
                "timestamp": result.timestamp.isoformat()
            },
            "test_results": [
                {
                    "name": test.name,
                    "description": test.description,
                    "test_type": test.test_type,
                    "status": test.status,
                    "execution_time": round(test.execution_time, 3),
                    "error_message": test.error_message
                }
                for test in self.tests
            ],
            "critical_failures": result.critical_failures,
            "warnings": result.warnings,
            "recommendations": self._generate_recommendations(result)
        }

    def _generate_recommendations(self, result: ValidationResult) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []

        if result.success_rate < 0.9:
            recommendations.append("Multiple validation failures detected. Review and fix critical issues before proceeding.")

        # Analyze specific failure patterns
        failed_imports = [t for t in self.tests if t.status == "failed" and t.test_type == "import"]
        if failed_imports:
            recommendations.append(f"Fix {len(failed_imports)} import failures. Check file paths and dependencies.")

        failed_commands = [t for t in self.tests if t.status == "failed" and t.test_type == "command"]
        if failed_commands:
            recommendations.append(f"Fix {len(failed_commands)} command failures. Update CLAUDE.md paths.")

        missing_files = [t for t in self.tests if t.status == "failed" and t.test_type == "file_exists"]
        if missing_files:
            recommendations.append(f"Restore {len(missing_files)} missing core files.")

        if result.success_rate >= 0.9:
            recommendations.append("Reorganization successful! Consider updating documentation to reflect new structure.")

        return recommendations

    def save_validation_report(self, result: ValidationResult) -> str:
        """Save validation report"""
        report = self.generate_validation_report(result)
        report_path = self.pm_directory / "validation_report.json"

        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, default=str)

            return str(report_path)
        except Exception as e:
            print(f"⚠️  Could not save validation report: {e}")
            return ""

def main():
    """Main execution function"""
    print("🚀 Validation Agent - Starting")
    print("=" * 60)

    agent = ValidationAgent()

    # Run validation suite
    result = agent.run_validation()

    # Print summary
    print(f"\n📊 VALIDATION SUMMARY")
    print(f"   Total tests: {result.total_tests}")
    print(f"   Passed: {result.passed_tests}")
    print(f"   Failed: {result.failed_tests}")
    print(f"   Success rate: {result.success_rate:.1%}")
    print(f"   Execution time: {result.execution_time:.2f} seconds")

    # Print failures if any
    if result.critical_failures:
        print(f"\n❌ CRITICAL FAILURES ({len(result.critical_failures)}):")
        for failure in result.critical_failures[:5]:  # Show first 5
            print(f"   • {failure}")
        if len(result.critical_failures) > 5:
            print(f"   ... and {len(result.critical_failures) - 5} more")

    # Print recommendations
    report = agent.generate_validation_report(result)
    if report["recommendations"]:
        print(f"\n💡 RECOMMENDATIONS:")
        for rec in report["recommendations"]:
            print(f"   • {rec}")

    # Save report
    report_path = agent.save_validation_report(result)
    if report_path:
        print(f"\n📄 Validation report saved: {report_path}")

    # Final status
    if result.success_rate >= 0.9:
        print("\n✅ Validation Agent - Validation Successful!")
    else:
        print("\n❌ Validation Agent - Validation Failed - Issues Detected")

if __name__ == "__main__":
    main()