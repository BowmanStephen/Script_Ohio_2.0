#!/usr/bin/env python3
"""
Comprehensive Test Suite for Script Ohio 2.0 Safety Improvements

Tests the enhanced safety mechanisms, error handling, and validation systems.
"""

import json
import os
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import safety modules
from scripts.safe_improvement_validator import SafeImprovementValidator
from scripts.safe_script_runner import SafeScriptRunner
from src.utils.enhanced_error_handler import (
    EnhancedError,
    ErrorCategory,
    ErrorHandler,
    ErrorSeverity,
    get_error_handler,
    handle_error,
    with_error_handling,
)


class TestSafeImprovementValidator(unittest.TestCase):
    """Test the SafeImprovementValidator class"""

    def setUp(self):
        self.validator = SafeImprovementValidator()
        self.temp_dir = tempfile.mkdtemp()

    def test_validate_syntax_valid_files(self):
        """Test syntax validation with valid Python files"""
        # Create temporary valid Python file
        valid_file = Path(self.temp_dir) / "valid.py"
        valid_file.write_text("print('Hello, world!')")

        # Mock the project root to include our temp directory
        self.validator.project_root = Path(self.temp_dir)

        result = self.validator.validate_syntax()
        self.assertTrue(result)

    def test_validate_syntax_invalid_files(self):
        """Test syntax validation with invalid Python files"""
        # Create temporary invalid Python file
        invalid_file = Path(self.temp_dir) / "invalid.py"
        invalid_file.write_text("print('Hello, world!'")  # Missing closing quote

        # Mock the project root to include our temp directory
        self.validator.project_root = Path(self.temp_dir)

        result = self.validator.validate_syntax()
        self.assertFalse(result)

    def test_validate_critical_files_all_present(self):
        """Test critical file validation when all files are present"""
        # Create mock critical files
        critical_files = [
            "CLAUDE.md",
            "requirements.txt",
            "agents/core/agent_framework.py",
        ]

        for file_path in critical_files:
            full_path = self.temp_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text("mock content")

        self.validator.project_root = Path(self.temp_dir)
        result = self.validator.validate_critical_files()
        self.assertTrue(result)

    def test_validate_critical_files_missing(self):
        """Test critical file validation when files are missing"""
        self.validator.project_root = Path(self.temp_dir)
        result = self.validator.validate_critical_files()
        self.assertFalse(result)

    def test_run_comprehensive_validation(self):
        """Test comprehensive validation"""
        # Create a minimal valid setup
        (Path(self.temp_dir) / "CLAUDE.md").write_text("# Test CLAUDE.md")
        (Path(self.temp_dir) / "requirements.txt").write_text("pytest")
        (Path(self.temp_dir) / "test.py").write_text("print('test')")

        self.validator.project_root = Path(self.temp_dir)
        result = self.validator.run_comprehensive_validation()

        self.assertIsInstance(result, dict)
        self.assertIn("summary", result)
        self.assertIn("validations", result)


class TestSafeScriptRunner(unittest.TestCase):
    """Test the SafeScriptRunner class"""

    def setUp(self):
        self.runner = SafeScriptRunner()
        self.temp_dir = tempfile.mkdtemp()

    def test_validate_script_safety_valid_script(self):
        """Test script safety validation with valid script"""
        # Create a valid Python script
        script_path = Path(self.temp_dir) / "safe_script.py"
        script_path.write_text("print('This is a safe script')")

        result = self.runner.validate_script_safety(str(script_path))
        self.assertTrue(result["safe"])
        self.assertEqual(len(result["critical_issues"]), 0)

    def test_validate_script_safety_syntax_error(self):
        """Test script safety validation with syntax error"""
        # Create a script with syntax error
        script_path = Path(self.temp_dir) / "bad_script.py"
        script_path.write_text("print('This has bad syntax'")

        result = self.runner.validate_script_safety(str(script_path))
        self.assertFalse(result["safe"])
        self.assertGreater(len(result["critical_issues"]), 0)

    def test_validate_script_safety_nonexistent(self):
        """Test script safety validation with non-existent script"""
        script_path = Path(self.temp_dir) / "nonexistent.py"

        result = self.runner.validate_script_safety(str(script_path))
        self.assertFalse(result["safe"])
        self.assertIn("does not exist", result["critical_issues"][0])

    def test_run_script_safely_success(self):
        """Test safe script execution with successful script"""
        # Create a successful script
        script_path = Path(self.temp_dir) / "success_script.py"
        script_path.write_text(
            """
import sys
print("Script executed successfully")
sys.exit(0)
"""
        )

        self.runner.project_root = Path(self.temp_dir)
        result = self.runner.run_script_safely(
            str(script_path), create_backup=False, timeout=10
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["execution"]["return_code"], 0)

    def test_run_script_safely_failure(self):
        """Test safe script execution with failing script"""
        # Create a failing script
        script_path = Path(self.temp_dir) / "fail_script.py"
        script_path.write_text(
            """
import sys
print("Script failed")
sys.exit(1)
"""
        )

        self.runner.project_root = Path(self.temp_dir)
        result = self.runner.run_script_safely(
            str(script_path), create_backup=False, timeout=10
        )

        self.assertFalse(result["success"])
        self.assertEqual(result["execution"]["return_code"], 1)

    def test_get_safety_report(self):
        """Test safety report generation"""
        report = self.runner.get_safety_report()

        self.assertIsInstance(report, dict)
        self.assertIn("project_root", report)
        self.assertIn("safety_log", report)
        self.assertIn("summary", report)


class TestEnhancedErrorHandler(unittest.TestCase):
    """Test the enhanced error handling system"""

    def setUp(self):
        # Use a temporary log file
        self.temp_log_file = tempfile.mktemp(suffix=".json")
        self.error_handler = ErrorHandler(log_file=self.temp_log_file)

    def tearDown(self):
        # Clean up temporary log file
        if os.path.exists(self.temp_log_file):
            os.remove(self.temp_log_file)

    def test_enhanced_error_creation(self):
        """Test EnhancedError object creation"""
        error = EnhancedError(
            message="Test error",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.API,
            suggestions=["Fix the API", "Check credentials"],
        )

        self.assertEqual(error.message, "Test error")
        self.assertEqual(error.severity, ErrorSeverity.HIGH)
        self.assertEqual(error.category, ErrorCategory.API)
        self.assertEqual(len(error.suggestions), 2)

    def test_enhanced_error_to_dict(self):
        """Test EnhancedError serialization"""
        error = EnhancedError(
            message="Test error",
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.DATA,
        )

        error_dict = error.to_dict()

        self.assertIsInstance(error_dict, dict)
        self.assertEqual(error_dict["message"], "Test error")
        self.assertEqual(error_dict["severity"], "medium")
        self.assertEqual(error_dict["category"], "data")

    def test_handle_basic_error(self):
        """Test basic error handling"""
        error = self.error_handler.handle_error(
            message="Test error",
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.UNKNOWN,
        )

        self.assertIsInstance(error, EnhancedError)
        self.assertEqual(error.message, "Test error")
        self.assertEqual(len(self.error_handler.error_history), 1)

    def test_handle_error_with_exception(self):
        """Test error handling with exception"""
        try:
            raise ValueError("Test exception")
        except Exception as e:
            error = self.error_handler.handle_error(
                message="Caught exception", exception=e, severity=ErrorSeverity.HIGH
            )

            self.assertEqual(error.exception, e)
            self.assertIsNotNone(error.traceback_str)

    def test_handle_error_with_context(self):
        """Test error handling with context"""
        context = {"function": "test_function", "line": 42, "user": "test_user"}

        error = self.error_handler.handle_error(
            message="Context error", context=context
        )

        self.assertEqual(error.context, context)

    def test_handle_recoverable_error(self):
        """Test handling recoverable errors"""
        recovery_called = False

        def recovery_action():
            nonlocal recovery_called
            recovery_called = True

        error = self.error_handler.handle_error(
            message="Recoverable error",
            recoverable=True,
            recovery_action=recovery_action,
        )

        self.assertTrue(error.recoverable)
        self.assertEqual(error.recovery_action, recovery_action)
        self.assertTrue(recovery_called)

    def test_auto_classify_error(self):
        """Test automatic error classification"""
        # Test file error
        file_error = FileNotFoundError("File not found")
        category, severity = self.error_handler.auto_classify_error(file_error)
        self.assertEqual(category, ErrorCategory.FILE_IO)
        self.assertEqual(severity, ErrorSeverity.HIGH)

        # Test syntax error
        syntax_error = SyntaxError("Invalid syntax")
        category, severity = self.error_handler.auto_classify_error(syntax_error)
        self.assertEqual(category, ErrorCategory.SYNTAX)
        self.assertEqual(severity, ErrorSeverity.CRITICAL)

        # Test network error
        network_error = ConnectionError("Connection failed")
        category, severity = self.error_handler.auto_classify_error(network_error)
        self.assertEqual(category, ErrorCategory.NETWORK)
        self.assertEqual(severity, ErrorSeverity.MEDIUM)

    def test_suggest_fixes(self):
        """Test error fix suggestions"""
        # Test API error suggestions
        error = EnhancedError(
            message="API request failed",
            category=ErrorCategory.API,
            suggestions=["Check API key"],
        )

        suggestions = self.error_handler.suggest_fixes(error)

        self.assertIn("Check API key", suggestions)
        self.assertTrue(any("API key is valid" in s for s in suggestions))
        self.assertTrue(any("rate limits" in s for s in suggestions))

        # Test file I/O error suggestions
        file_error = EnhancedError(
            message="Cannot read file", category=ErrorCategory.FILE_IO
        )

        suggestions = self.error_handler.suggest_fixes(file_error)

        self.assertTrue(any("file exists" in s for s in suggestions))
        self.assertTrue(any("file permissions" in s for s in suggestions))

    def test_get_error_summary(self):
        """Test error summary generation"""
        # Add some errors to history
        self.error_handler.handle_error("Error 1", category=ErrorCategory.API)
        self.error_handler.handle_error("Error 2", category=ErrorCategory.FILE_IO)
        self.error_handler.handle_error("Error 3", category=ErrorCategory.API)

        summary = self.error_handler.get_error_summary(days=7)

        self.assertEqual(summary["total_errors"], 3)
        self.assertEqual(summary["errors_by_category"]["api"], 2)
        self.assertEqual(summary["errors_by_category"]["file_io"], 1)

    def test_save_and_load_error_history(self):
        """Test saving and loading error history"""
        # Add an error
        self.error_handler.handle_error("Test error", category=ErrorCategory.DATA)

        # Save history
        self.error_handler.save_error_history()

        # Create new handler and load history
        new_handler = ErrorHandler(log_file=self.temp_log_file)

        self.assertEqual(len(new_handler.error_history), 1)
        self.assertEqual(new_handler.error_history[0].message, "Test error")

    def test_safe_execute_success(self):
        """Test safe execution with successful function"""

        def success_func():
            return "success"

        result = self.error_handler.safe_execute(
            func=success_func, context={"test": "safe_execute"}
        )

        self.assertEqual(result, "success")
        self.assertEqual(len(self.error_handler.error_history), 0)

    def test_safe_execute_failure(self):
        """Test safe execution with failing function"""

        def failing_func():
            raise ValueError("Function failed")

        result = self.error_handler.safe_execute(
            func=failing_func, context={"test": "safe_execute"}
        )

        self.assertIsNone(result)
        self.assertEqual(len(self.error_handler.error_history), 1)


class TestGlobalErrorHandling(unittest.TestCase):
    """Test global error handling functions"""

    def setUp(self):
        # Reset global error handler
        import src.utils.enhanced_error_handler

        src.utils.enhanced_error_handler._global_error_handler = None

    def test_get_error_handler_singleton(self):
        """Test that get_error_handler returns singleton instance"""
        handler1 = get_error_handler()
        handler2 = get_error_handler()

        self.assertIs(handler1, handler2)

    def test_handle_error_convenience_function(self):
        """Test the global handle_error convenience function"""
        error = handle_error(
            message="Test global error",
            category=ErrorCategory.VALIDATION,
            suggestions=["Fix validation"],
        )

        self.assertIsInstance(error, EnhancedError)
        self.assertEqual(error.message, "Test global error")

    def test_with_error_handling_decorator(self):
        """Test the error handling decorator"""

        @with_error_handling(
            get_error_handler(),
            category=ErrorCategory.RUNTIME,
            suggestions=["Check function logic"],
        )
        def decorated_function():
            raise RuntimeError("Decorated function error")

        with self.assertRaises(RuntimeError):
            decorated_function()

        # Check that error was handled
        handler = get_error_handler()
        self.assertEqual(len(handler.error_history), 1)
        self.assertEqual(handler.error_history[0].category, ErrorCategory.RUNTIME)


class TestIntegration(unittest.TestCase):
    """Integration tests for safety improvements"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def test_makefile_targets_simulation(self):
        """Test simulation of Makefile targets"""
        # Create minimal project structure
        (Path(self.temp_dir) / "CLAUDE.md").write_text("# Test")
        (Path(self.temp_dir) / "requirements.txt").write_text("pytest")
        (Path(self.temp_dir) / "test_script.py").write_text("print('test')")

        # Test syntax validation (simulating make syntax-validate)
        validator = SafeImprovementValidator(self.temp_dir)
        result = validator.validate_syntax()
        self.assertTrue(result)

        # Test safety validation (simulating make safe-validate)
        result = validator.run_comprehensive_validation()
        self.assertTrue(result["summary"]["can_proceed"])

    def test_end_to_end_safe_execution(self):
        """Test end-to-end safe script execution"""
        # Create a test script that might fail
        script_content = """
import sys
import json

# Simulate some work
print("Starting script execution...")

# Simulate potential error condition
if len(sys.argv) > 1 and sys.argv[1] == "fail":
    print("Simulating failure...")
    sys.exit(1)

print("Script completed successfully")
sys.exit(0)
"""

        script_path = Path(self.temp_dir) / "test_script.py"
        script_path.write_text(script_content)

        # Test successful execution
        runner = SafeScriptRunner(self.temp_dir)
        result = runner.run_script_safely(
            str(script_path), create_backup=False, timeout=5
        )

        self.assertTrue(result["success"])

        # Test failed execution
        result = runner.run_script_safely(
            str(script_path), ["fail"], create_backup=False, timeout=5
        )

        self.assertFalse(result["success"])
        self.assertIn("Script failed", result["execution"]["stderr"])


if __name__ == "__main__":
    # Create test suite
    test_suite = unittest.TestSuite()

    # Add test cases
    test_classes = [
        TestSafeImprovementValidator,
        TestSafeScriptRunner,
        TestEnhancedErrorHandler,
        TestGlobalErrorHandling,
        TestIntegration,
    ]

    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    # Print summary
    print(f"\n{'='*60}")
    print(f"SAFETY IMPROVEMENTS TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(
        f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%"
    )

    if result.failures:
        print(f"\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")

    if result.errors:
        print(f"\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")

    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
