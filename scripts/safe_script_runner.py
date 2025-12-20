#!/usr/bin/env python3
"""
Safe Script Runner for Script Ohio 2.0

Provides enhanced safety checks and error handling for critical scripts
in the Script Ohio 2.0 ecosystem.
"""

import json
import os
import subprocess
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class SafeScriptRunner:
    """Enhanced script runner with safety checks and error handling"""

    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.safety_log = []
        self.execution_history = []

    def log_safety_check(self, check_name: str, status: str, details: str = ""):
        """Log a safety check"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "check": check_name,
            "status": status,
            "details": details,
        }
        self.safety_log.append(entry)

    def validate_script_safety(self, script_path: str) -> Dict[str, Any]:
        """Validate a script before execution"""
        script_path = Path(script_path)
        safety_report = {
            "script": str(script_path),
            "safe": True,
            "warnings": [],
            "critical_issues": [],
        }

        # Check if script exists
        if not script_path.exists():
            safety_report["safe"] = False
            safety_report["critical_issues"].append("Script does not exist")
            return safety_report

        # Check if script is in safe directory
        safe_directories = ["scripts", "agents", "src"]
        if not any(
            str(script_path).startswith(safe_dir) for safe_dir in safe_directories
        ):
            safety_report["warnings"].append(
                "Script is outside standard safe directories"
            )

        # Check script extension
        if script_path.suffix != ".py":
            safety_report["warnings"].append("Script is not a Python file")

        # Basic syntax check for Python files
        if script_path.suffix == ".py":
            try:
                with open(script_path, "r") as f:
                    compile(f.read(), str(script_path), "exec")
                self.log_safety_check("Syntax Check", "PASS", f"{script_path.name}")
            except SyntaxError as e:
                safety_report["safe"] = False
                safety_report["critical_issues"].append(f"Syntax error: {e}")
                self.log_safety_check(
                    "Syntax Check", "FAIL", f"{script_path.name}: {e}"
                )

        # Check for dangerous patterns (basic security)
        dangerous_patterns = [
            "rm -rf /",
            "sudo rm",
            "format c:",
            "del /f /s /q",
            "chmod -R 777 /",
            "wget http://evil.com",
            "curl http://evil.com",
        ]

        try:
            with open(script_path, "r") as f:
                content = f.read().lower()
                for pattern in dangerous_patterns:
                    if pattern in content:
                        safety_report["safe"] = False
                        safety_report["critical_issues"].append(
                            f"Dangerous pattern detected: {pattern}"
                        )
        except Exception:
            pass  # File read errors are handled elsewhere

        return safety_report

    def create_backup(self) -> str:
        """Create a backup of current state"""
        backup_name = f"backup_before_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        try:
            # Create git backup
            result = subprocess.run(
                ["git", "checkout", "-b", backup_name],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                self.log_safety_check(
                    "Backup Creation", "PASS", f"Created branch {backup_name}"
                )
                return backup_name
            else:
                # If branch already exists, create commit instead
                subprocess.run(
                    ["git", "add", "-A"], cwd=self.project_root, capture_output=True
                )
                subprocess.run(
                    [
                        "git",
                        "commit",
                        "-m",
                        f"Backup before script run {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    ],
                    cwd=self.project_root,
                    capture_output=True,
                )
                self.log_safety_check(
                    "Backup Creation", "PASS", "Created backup commit"
                )
                return "backup_commit"
        except Exception as e:
            self.log_safety_check("Backup Creation", "FAIL", str(e))
            return ""

    def run_script_safely(
        self,
        script_path: str,
        args: List[str] = None,
        create_backup: bool = True,
        timeout: int = 300,
    ) -> Dict[str, Any]:
        """
        Safely execute a script with comprehensive error handling

        Args:
            script_path: Path to the script to execute
            args: Command line arguments for the script
            create_backup: Whether to create a backup before execution
            timeout: Maximum execution time in seconds

        Returns:
            Dictionary with execution results and safety information
        """
        script_path = Path(script_path)
        args = args or []

        execution_result = {
            "script": str(script_path),
            "args": args,
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "safety_checks": {},
            "execution": {},
            "backup_created": None,
            "error": None,
        }

        try:
            # Step 1: Validate script safety
            self.log_safety_check("Script Validation", "START", str(script_path))
            safety_report = self.validate_script_safety(script_path)
            execution_result["safety_checks"] = safety_report

            if not safety_report["safe"]:
                execution_result["error"] = (
                    f"Script failed safety validation: {'; '.join(safety_report['critical_issues'])}"
                )
                self.log_safety_check(
                    "Script Validation", "FAIL", execution_result["error"]
                )
                return execution_result

            self.log_safety_check(
                "Script Validation",
                "PASS",
                f"{len(safety_report['warnings'])} warnings",
            )

            # Step 2: Create backup if requested
            if create_backup:
                backup_name = self.create_backup()
                execution_result["backup_created"] = backup_name

            # Step 3: Prepare execution environment
            self.log_safety_check(
                "Script Execution", "START", f"Running {script_path.name}"
            )

            # Set up environment with safety
            env = os.environ.copy()
            env["PYTHONPATH"] = str(self.project_root)
            env["SAFE_SCRIPT_RUN"] = "true"

            # Step 4: Execute script
            cmd = ["python3", str(script_path)] + args
            start_time = time.time()

            process = subprocess.Popen(
                cmd,
                cwd=self.project_root,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            try:
                stdout, stderr = process.communicate(timeout=timeout)
                return_code = process.returncode
                execution_time = time.time() - start_time

                execution_result["execution"] = {
                    "return_code": return_code,
                    "stdout": stdout,
                    "stderr": stderr,
                    "execution_time": execution_time,
                    "timeout": False,
                }

                if return_code == 0:
                    execution_result["success"] = True
                    self.log_safety_check(
                        "Script Execution",
                        "PASS",
                        f"Completed in {execution_time:.2f}s",
                    )
                else:
                    execution_result["error"] = (
                        f"Script failed with return code {return_code}: {stderr}"
                    )
                    self.log_safety_check(
                        "Script Execution", "FAIL", f"Return code: {return_code}"
                    )

            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                execution_time = timeout

                execution_result["execution"] = {
                    "return_code": -1,
                    "stdout": stdout,
                    "stderr": stderr or "Script execution timed out",
                    "execution_time": execution_time,
                    "timeout": True,
                }

                execution_result["error"] = (
                    f"Script execution timed out after {timeout}s"
                )
                self.log_safety_check(
                    "Script Execution", "FAIL", f"Timeout after {timeout}s"
                )

        except Exception as e:
            execution_result["error"] = f"Unexpected error: {str(e)}"
            execution_result["traceback"] = traceback.format_exc()
            self.log_safety_check("Script Execution", "FAIL", f"Exception: {str(e)}")

        # Step 5: Post-execution safety check
        if execution_result["success"]:
            self.run_post_execution_checks()

        # Store in execution history
        self.execution_history.append(execution_result)

        return execution_result

    def run_post_execution_checks(self):
        """Run safety checks after script execution"""
        # Check if critical files are still intact
        critical_files = [
            "CLAUDE.md",
            "agents/core/agent_framework.py",
            "model_pack/updated_training_data.csv",
        ]

        for file_path in critical_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                self.log_safety_check(
                    "Post-Execution Check", "PASS", f"{file_path} intact"
                )
            else:
                self.log_safety_check(
                    "Post-Execution Check", "FAIL", f"{file_path} missing!"
                )

    def get_safety_report(self) -> Dict[str, Any]:
        """Get comprehensive safety report"""
        return {
            "project_root": str(self.project_root),
            "safety_log": self.safety_log,
            "execution_history": self.execution_history,
            "summary": {
                "total_checks": len(self.safety_log),
                "passed_checks": len(
                    [log for log in self.safety_log if log["status"] == "PASS"]
                ),
                "failed_checks": len(
                    [log for log in self.safety_log if log["status"] == "FAIL"]
                ),
                "total_executions": len(self.execution_history),
                "successful_executions": len(
                    [exec for exec in self.execution_history if exec["success"]]
                ),
            },
        }

    def save_safety_report(self, output_file: str = None) -> str:
        """Save safety report to file"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"safety_report_{timestamp}.json"

        output_path = self.project_root / output_file
        report = self.get_safety_report()

        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)

        return str(output_path)


def main():
    """Main execution function"""
    import argparse

    parser = argparse.ArgumentParser(description="Safe Script Runner")
    parser.add_argument("script", help="Script to execute")
    parser.add_argument("args", nargs="*", help="Script arguments")
    parser.add_argument("--no-backup", action="store_true", help="Skip backup creation")
    parser.add_argument(
        "--timeout", type=int, default=300, help="Execution timeout in seconds"
    )
    parser.add_argument("--project-root", help="Project root directory")
    parser.add_argument("--safety-report", help="Save safety report to file")

    args = parser.parse_args()

    runner = SafeScriptRunner(args.project_root)

    print("🛡️  Safe Script Runner - Script Ohio 2.0")
    print("=" * 50)
    print(f"Script: {args.script}")
    print(f"Args: {args.args}")
    print(f"Timeout: {args.timeout}s")
    print(f"Backup: {'Disabled' if args.no_backup else 'Enabled'}")
    print()

    # Run script safely
    result = runner.run_script_safely(
        args.script, args.args, create_backup=not args.no_backup, timeout=args.timeout
    )

    # Display results
    print("📊 EXECUTION RESULTS")
    print("=" * 30)
    print(f"Success: {'✅' if result['success'] else '❌'}")

    if result.get("backup_created"):
        print(f"Backup: {result['backup_created']}")

    if "execution" in result:
        exec_info = result["execution"]
        print(f"Return Code: {exec_info['return_code']}")
        print(f"Execution Time: {exec_info['execution_time']:.2f}s")

        if exec_info.get("timeout"):
            print("⏰ Execution timed out")

    if result.get("error"):
        print(f"Error: {result['error']}")

    # Show safety warnings
    safety_warnings = result.get("safety_checks", {}).get("warnings", [])
    if safety_warnings:
        print(f"\n⚠️  Safety Warnings:")
        for warning in safety_warnings:
            print(f"   - {warning}")

    # Save safety report if requested
    if args.safety_report or not result["success"]:
        report_file = runner.save_safety_report(args.safety_report)
        print(f"\n📄 Safety report saved to: {report_file}")

    # Exit with appropriate code
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
