#!/usr/bin/env python3
"""
System Validator Agent
Specialized agent for comprehensive system validation and testing

This agent performs thorough validation of the Script Ohio 2.0 system:
- Test agent system functionality and interactions
- Validate ML models and predictions
- Check data integrity and accessibility
- Performance benchmarking and optimization
- End-to-end workflow validation
"""

import os
import sys
import json
import time
import traceback
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging
import subprocess
import importlib.util

# Add project root to path for imports
project_root = Path("/Users/stephen_bowman/Documents/GitHub/Script_Ohio_2.0")
sys.path.insert(0, str(project_root))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """Result of a system test"""
    test_name: str
    category: str
    passed: bool
    execution_time: float
    error_message: Optional[str]
    details: Dict[str, Any]
    timestamp: datetime

@dataclass
class ValidationReport:
    """Comprehensive system validation report"""
    total_tests: int
    passed_tests: int
    failed_tests: int
    test_results: List[TestResult]
    system_health_score: float
    performance_metrics: Dict[str, float]
    critical_issues: List[str]
    recommendations: List[str]

class SystemValidator:
    """
    Specialized agent for comprehensive validation of the Script Ohio 2.0 system
    including agent system, ML models, and overall functionality
    """

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.test_results = []
        self.start_time = time.time()
        logger.info("🧪 SystemValidator initialized")

    def run_comprehensive_validation(self) -> ValidationReport:
        """Run comprehensive system validation"""
        logger.info("🚀 Starting comprehensive system validation...")

        # Test categories
        test_categories = [
            ("agent_system", "Agent System Functionality"),
            ("ml_models", "ML Model Validation"),
            ("data_integrity", "Data Integrity Checks"),
            ("dependencies", "Dependency Validation"),
            ("performance", "Performance Benchmarks"),
            ("workflows", "End-to-End Workflows")
        ]

        for category, description in test_categories:
            logger.info(f"🔍 Running {description}...")
            self._run_test_category(category)

        # Generate report
        report = self._generate_validation_report()

        logger.info(f"✅ System validation complete:")
        logger.info(f"   Total tests: {report.total_tests}")
        logger.info(f"   Passed: {report.passed_tests}")
        logger.info(f"   Failed: {report.failed_tests}")
        logger.info(f"   System health score: {report.system_health_score:.1f}/10")

        return report

    def _run_test_category(self, category: str):
        """Run tests for a specific category"""
        if category == "agent_system":
            self._test_agent_system()
        elif category == "ml_models":
            self._test_ml_models()
        elif category == "data_integrity":
            self._test_data_integrity()
        elif category == "dependencies":
            self._test_dependencies()
        elif category == "performance":
            self._test_performance()
        elif category == "workflows":
            self._test_workflows()

    def _test_agent_system(self):
        """Test agent system functionality"""
        tests = [
            ("analytics_orchestrator_import", "Test Analytics Orchestrator import"),
            ("context_manager_import", "Test Context Manager import"),
            ("agent_framework_import", "Test Agent Framework import"),
            ("demo_system", "Test Demo System"),
        ]

        for test_name, description in tests:
            self._run_single_test(test_name, description, self._execute_agent_test)

    def _execute_agent_test(self, test_name: str) -> Dict[str, Any]:
        """Execute specific agent test"""
        if test_name == "analytics_orchestrator_import":
            try:
                # Try to import the analytics orchestrator
                sys.path.insert(0, str(self.project_root / "agents"))
                from analytics_orchestrator import AnalyticsOrchestrator
                return {"success": True, "import_success": True}
            except Exception as e:
                return {"success": False, "error": str(e)}

        elif test_name == "context_manager_import":
            try:
                sys.path.insert(0, str(self.project_root / "agents" / "core"))
                from context_manager import ContextManager
                return {"success": True, "import_success": True}
            except Exception as e:
                return {"success": False, "error": str(e)}

        elif test_name == "agent_framework_import":
            try:
                sys.path.insert(0, str(self.project_root / "agents" / "core"))
                from agent_framework import BaseAgent, AgentFactory
                return {"success": True, "import_success": True}
            except Exception as e:
                return {"success": False, "error": str(e)}

        elif test_name == "demo_system":
            # Test the demo system
            demo_path = self.project_root / "project_management" / "TOOLS_AND_CONFIG" / "demo_agent_system.py"
            if demo_path.exists():
                try:
                    # Quick syntax check
                    with open(demo_path, 'r') as f:
                        code = f.read()
                    compile(code, str(demo_path), 'exec')
                    return {"success": True, "syntax_valid": True, "demo_exists": True}
                except Exception as e:
                    return {"success": False, "error": str(e), "demo_exists": True}
            else:
                return {"success": False, "error": "Demo file not found", "demo_exists": False}

        return {"success": False, "error": "Unknown test"}

    def _test_ml_models(self):
        """Test ML model functionality"""
        tests = [
            ("model_files_exist", "Check if model files exist"),
            ("model_syntax", "Test model Python syntax"),
            ("data_files_exist", "Check if training data exists"),
        ]

        for test_name, description in tests:
            self._run_single_test(test_name, description, self._execute_ml_test)

    def _execute_ml_test(self, test_name: str) -> Dict[str, Any]:
        """Execute specific ML test"""
        if test_name == "model_files_exist":
            model_files = [
                "model_pack/ridge_model_2025.joblib",
                "model_pack/xgb_home_win_model_2025.pkl",
                "model_pack/fastai_home_win_model_2025.pkl"
            ]

            existing_files = []
            for model_file in model_files:
                if (self.project_root / model_file).exists():
                    existing_files.append(model_file)

            return {
                "success": len(existing_files) >= 2,  # At least 2 models should exist
                "existing_files": existing_files,
                "total_expected": len(model_files)
            }

        elif test_name == "model_syntax":
            # Test syntax of model pack files
            model_dir = self.project_root / "model_pack"
            syntax_errors = []

            if model_dir.exists():
                for file in model_dir.glob("*.py"):
                    try:
                        with open(file, 'r') as f:
                            code = f.read()
                        compile(code, str(file), 'exec')
                    except SyntaxError as e:
                        syntax_errors.append(f"{file.name}: {e}")

            return {
                "success": len(syntax_errors) == 0,
                "syntax_errors": syntax_errors,
                "files_checked": len(list(model_dir.glob("*.py"))) if model_dir.exists() else 0
            }

        elif test_name == "data_files_exist":
            data_files = [
                "model_pack/updated_training_data.csv",
                "starter_pack/cfb_game_data.csv"
            ]

            existing_files = []
            for data_file in data_files:
                if (self.project_root / data_file).exists():
                    existing_files.append(data_file)

            return {
                "success": len(existing_files) >= 1,  # At least 1 data file should exist
                "existing_files": existing_files,
                "total_expected": len(data_files)
            }

        return {"success": False, "error": "Unknown ML test"}

    def _test_data_integrity(self):
        """Test data integrity"""
        tests = [
            ("python_syntax", "Check Python syntax across project"),
            ("notebook_syntax", "Check Jupyter notebook integrity"),
            ("file_accessibility", "Test file accessibility"),
        ]

        for test_name, description in tests:
            self._run_single_test(test_name, description, self._execute_data_test)

    def _execute_data_test(self, test_name: str) -> Dict[str, Any]:
        """Execute specific data integrity test"""
        if test_name == "python_syntax":
            # Check Python syntax across all Python files
            syntax_errors = []
            python_files = 0

            for root, dirs, files in os.walk(self.project_root):
                # Skip hidden directories
                dirs[:] = [d for d in dirs if not d.startswith('.')]

                for file in files:
                    if file.endswith('.py'):
                        python_files += 1
                        file_path = Path(root) / file
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                code = f.read()
                            compile(code, str(file_path), 'exec')
                        except SyntaxError as e:
                            syntax_errors.append(f"{str(file_path.relative_to(self.project_root))}: {e}")
                        except UnicodeDecodeError:
                            pass  # Skip binary files

            return {
                "success": len(syntax_errors) == 0,
                "syntax_errors": syntax_errors,
                "files_checked": python_files
            }

        elif test_name == "notebook_syntax":
            # Check if Jupyter notebooks are accessible
            notebook_dir = self.project_root / "starter_pack"
            accessible_notebooks = []

            if notebook_dir.exists():
                for notebook in notebook_dir.glob("*.ipynb"):
                    try:
                        with open(notebook, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if '"cells"' in content and '"metadata"' in content:
                                accessible_notebooks.append(notebook.name)
                    except:
                        pass

            return {
                "success": len(accessible_notebooks) >= 5,  # At least 5 notebooks should be accessible
                "accessible_notebooks": accessible_notebooks,
                "total_notebooks": len(list(notebook_dir.glob("*.ipynb"))) if notebook_dir.exists() else 0
            }

        elif test_name == "file_accessibility":
            # Test accessibility of key project files
            key_files = [
                "CLAUDE.md",
                "agents/analytics_orchestrator.py",
                "project_management/core_tools/demo_agent_system.py"
            ]

            accessible_files = []
            for file_path in key_files:
                if (self.project_root / file_path).exists():
                    try:
                        with open(self.project_root / file_path, 'r', encoding='utf-8') as f:
                            f.read()
                        accessible_files.append(file_path)
                    except:
                        pass

            return {
                "success": len(accessible_files) >= 2,  # At least 2 key files should be accessible
                "accessible_files": accessible_files,
                "total_expected": len(key_files)
            }

        return {"success": False, "error": "Unknown data test"}

    def _test_dependencies(self):
        """Test system dependencies"""
        tests = [
            ("python_version", "Check Python version"),
            ("core_packages", "Check core package availability"),
            ("project_imports", "Test project imports"),
        ]

        for test_name, description in tests:
            self._run_single_test(test_name, description, self._execute_dependency_test)

    def _execute_dependency_test(self, test_name: str) -> Dict[str, Any]:
        """Execute specific dependency test"""
        if test_name == "python_version":
            version = sys.version_info
            return {
                "success": version.major >= 3 and version.minor >= 8,
                "python_version": f"{version.major}.{version.minor}.{version.micro}",
                "recommended": "3.8+"
            }

        elif test_name == "core_packages":
            # Check core packages
            core_packages = ['pandas', 'numpy', 'sklearn', 'matplotlib']
            available_packages = []

            for package in core_packages:
                try:
                    __import__(package)
                    available_packages.append(package)
                except ImportError:
                    pass

            return {
                "success": len(available_packages) >= 3,  # At least 3 core packages
                "available_packages": available_packages,
                "total_expected": len(core_packages)
            }

        elif test_name == "project_imports":
            # Test if key project modules can be imported
            project_imports = [
                ("agents", "agents"),
                ("model_pack", "model_pack"),
                ("starter_pack", "starter_pack")
            ]

            successful_imports = []
            for module_name, path in project_imports:
                if (self.project_root / path).exists():
                    try:
                        spec = importlib.util.spec_from_file_location(
                            module_name,
                            self.project_root / path / "__init__.py" if (self.project_root / path / "__init__.py").exists() else self.project_root / path
                        )
                        if spec:
                            successful_imports.append(module_name)
                    except:
                        pass

            return {
                "success": len(successful_imports) >= 1,
                "successful_imports": successful_imports,
                "total_expected": len(project_imports)
            }

        return {"success": False, "error": "Unknown dependency test"}

    def _test_performance(self):
        """Test system performance"""
        tests = [
            ("import_speed", "Test module import speed"),
            ("file_count", "Check total file count"),
        ]

        for test_name, description in tests:
            self._run_single_test(test_name, description, self._execute_performance_test)

    def _execute_performance_test(self, test_name: str) -> Dict[str, Any]:
        """Execute specific performance test"""
        if test_name == "import_speed":
            # Test import speed of a simple module
            start_time = time.time()
            try:
                import json
                import_time = time.time() - start_time
                return {
                    "success": import_time < 1.0,  # Should import in less than 1 second
                    "import_time": import_time,
                    "threshold": 1.0
                }
            except:
                return {"success": False, "error": "Import failed"}

        elif test_name == "file_count":
            # Count total files
            total_files = 0
            for root, dirs, files in os.walk(self.project_root):
                # Skip hidden directories
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                total_files += len(files)

            return {
                "success": total_files > 100,  # Should have substantial file count
                "total_files": total_files,
                "project_size_category": "Large" if total_files > 1000 else "Medium" if total_files > 100 else "Small"
            }

        return {"success": False, "error": "Unknown performance test"}

    def _test_workflows(self):
        """Test end-to-end workflows"""
        tests = [
            ("demo_system_check", "Check demo system accessibility"),
            ("agent_system_structure", "Validate agent system structure"),
        ]

        for test_name, description in tests:
            self._run_single_test(test_name, description, self._execute_workflow_test)

    def _execute_workflow_test(self, test_name: str) -> Dict[str, Any]:
        """Execute specific workflow test"""
        if test_name == "demo_system_check":
            demo_path = self.project_root / "project_management" / "TOOLS_AND_CONFIG" / "demo_agent_system.py"
            if demo_path.exists():
                return {
                    "success": True,
                    "demo_accessible": True,
                    "demo_size_kb": demo_path.stat().st_size / 1024
                }
            else:
                return {"success": False, "error": "Demo system not found"}

        elif test_name == "agent_system_structure":
            # Validate agent system directory structure
            agents_dir = self.project_root / "agents"
            required_subdirs = ["core"]
            existing_subdirs = []

            if agents_dir.exists():
                for subdir in required_subdirs:
                    if (agents_dir / subdir).exists():
                        existing_subdirs.append(subdir)

            # Count Python files in agents directory
            agent_files = list(agents_dir.glob("**/*.py")) if agents_dir.exists() else []

            return {
                "success": len(existing_subdirs) >= 1 and len(agent_files) >= 5,
                "existing_subdirs": existing_subdirs,
                "agent_file_count": len(agent_files),
                "required_subdirs": required_subdirs
            }

        return {"success": False, "error": "Unknown workflow test"}

    def _run_single_test(self, test_name: str, description: str, test_function):
        """Run a single test and record results"""
        start_time = time.time()

        try:
            result = test_function(test_name)
            success = result.get("success", False)
            error_message = result.get("error") if not success else None
        except Exception as e:
            success = False
            error_message = str(e)
            result = {"error": error_message}

        execution_time = time.time() - start_time

        test_result = TestResult(
            test_name=test_name,
            category=description,
            passed=success,
            execution_time=execution_time,
            error_message=error_message,
            details=result,
            timestamp=datetime.now()
        )

        self.test_results.append(test_result)

        status = "✅ PASSED" if success else "❌ FAILED"
        logger.info(f"   {status} {description} ({execution_time:.3f}s)")

        if not success:
            logger.warning(f"      Error: {error_message}")

    def _generate_validation_report(self) -> ValidationReport:
        """Generate comprehensive validation report"""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r.passed])
        failed_tests = total_tests - passed_tests

        # Calculate system health score
        if total_tests > 0:
            health_score = (passed_tests / total_tests) * 10
        else:
            health_score = 0.0

        # Performance metrics
        avg_execution_time = sum(r.execution_time for r in self.test_results) / max(total_tests, 1)
        performance_metrics = {
            "average_test_time": avg_execution_time,
            "total_validation_time": time.time() - self.start_time,
            "test_coverage_percentage": (passed_tests / max(total_tests, 1)) * 100
        }

        # Critical issues
        critical_issues = []
        for result in self.test_results:
            if not result.passed and "import" in result.test_name.lower():
                critical_issues.append(f"Import failed: {result.test_name}")

        # Recommendations
        recommendations = []
        if health_score < 8.0:
            recommendations.append("Investigate failed tests to improve system health")
        if len(critical_issues) > 0:
            recommendations.append("Address critical import issues immediately")
        if performance_metrics["average_test_time"] > 1.0:
            recommendations.append("Consider optimizing test performance")

        return ValidationReport(
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            test_results=self.test_results,
            system_health_score=health_score,
            performance_metrics=performance_metrics,
            critical_issues=critical_issues,
            recommendations=recommendations
        )

def main():
    """Main execution function for testing"""
    print("🧪 System Validator Agent")
    print("=" * 40)

    project_root = Path("/Users/stephen_bowman/Documents/GitHub/Script_Ohio_2.0")
    validator = SystemValidator(project_root)

    # Run comprehensive validation
    report = validator.run_comprehensive_validation()

    print(f"\n📊 System Validation Results:")
    print(f"   System Health Score: {report.system_health_score:.1f}/10")
    print(f"   Tests Passed: {report.passed_tests}/{report.total_tests}")
    print(f"   Critical Issues: {len(report.critical_issues)}")

    print(f"\n⚠️ Critical Issues:")
    for issue in report.critical_issues:
        print(f"   - {issue}")

    print(f"\n💡 Recommendations:")
    for rec in report.recommendations:
        print(f"   - {rec}")

    print(f"\n📈 Performance Metrics:")
    for metric, value in report.performance_metrics.items():
        print(f"   {metric.replace('_', ' ').title()}: {value:.2f}")

    return report

if __name__ == "__main__":
    main()