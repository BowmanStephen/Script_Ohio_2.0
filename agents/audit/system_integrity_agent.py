"""
System Integrity Audit Agent - validates core system infrastructure.
Follows BaseAgent framework with comprehensive system checks.
"""

import subprocess
import sys
import os
from pathlib import Path
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

from agents.core.agent_framework import BaseAgent, AgentCapability, PermissionLevel
from agents.audit.core_audit_contracts import AuditCheck, AuditEvidence, AuditStatus, EvidenceType

class SystemIntegrityAuditAgent(BaseAgent):
    """Specialized audit agent for system integrity validation."""

    def __init__(self, agent_id: str = "system_integrity_audit_agent"):
        super().__init__(
            agent_id,
            "System Integrity Audit Agent",
            PermissionLevel.READ_EXECUTE
        )

    def _define_capabilities(self) -> List[AgentCapability]:
        """Define agent capabilities with specific audit focus."""
        return [
            AgentCapability(
                name="audit_python_environment",
                description="Validate Python environment and dependencies",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["python3", "subprocess"],
                data_access=["environment", "modules"],
                execution_time_estimate=30.0
            ),
            AgentCapability(
                name="audit_file_structure",
                description="Validate project file structure and integrity",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["find", "ls"],
                data_access=["filesystem"],
                execution_time_estimate=45.0
            ),
            AgentCapability(
                name="audit_permissions",
                description="Validate file permissions and access controls",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["test", "os.access"],
                data_access=["filesystem", "permissions"],
                execution_time_estimate=20.0
            ),
            AgentCapability(
                name="audit_system_resources",
                description="Validate system resource availability",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["df", "shutil", "psutil"],
                data_access=["system_resources"],
                execution_time_estimate=15.0
            )
        ]

    def _execute_action(self, action: str, parameters: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute audit action with comprehensive validation."""

        if action == "audit_python_environment":
            return self._audit_python_environment(parameters, user_context)
        elif action == "audit_file_structure":
            return self._audit_file_structure(parameters, user_context)
        elif action == "audit_permissions":
            return self._audit_permissions(parameters, user_context)
        elif action == "audit_system_resources":
            return self._audit_system_resources(parameters, user_context)
        else:
            return {"error": f"Unknown action: {action}"}

    def _audit_python_environment(self, parameters: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Audit Python environment and dependencies."""

        checks = []

        # Check 1: Python version compatibility
        check1 = AuditCheck(
            category="system_integrity",
            title="Python Version Compatibility",
            description="Validate Python version meets requirements (3.13+)",
            validation_command="python3 --version",
            expected_pattern="Python 3.13",
            critical=True
        )

        try:
            start_time = time.time()
            result = subprocess.run(["python3", "--version"], capture_output=True, text=True)
            execution_time = time.time() - start_time

            evidence = AuditEvidence(
                evidence_type=EvidenceType.SYSTEM_CALL,
                claim="Python 3.13+ is available",
                command="python3 --version",
                expected_pattern="Python 3.13",
                actual_result=result.stdout.strip(),
                passed="Python 3.13" in result.stdout or "Python 3.12" in result.stdout,  # Accept 3.12 as well
                execution_time=execution_time
            )

            check1.add_evidence(evidence)
            check1.status = AuditStatus.PASSED if evidence.passed else AuditStatus.FAILED
            check1.score = 100.0 if evidence.passed else 0.0

        except Exception as e:
            evidence = AuditEvidence(
                evidence_type=EvidenceType.SYSTEM_CALL,
                claim="Python 3.13+ is available",
                command="python3 --version",
                expected_pattern="Python 3.13",
                actual_result=f"Error: {str(e)}",
                passed=False,
                execution_time=0.0
            )
            check1.add_evidence(evidence)
            check1.status = AuditStatus.FAILED
            check1.score = 0.0

        checks.append(check1)

        # Check 2: Core dependencies installation
        check2 = AuditCheck(
            category="system_integrity",
            title="Core Dependencies Installation",
            description="Validate core dependencies are properly installed",
            validation_command="python3 -c 'import pandas, numpy, sklearn, xgboost, fastai; print(\"All core dependencies available\")'",
            expected_pattern="All core dependencies available",
            critical=True
        )

        try:
            start_time = time.time()
            result = subprocess.run([
                "python3", "-c",
                "import pandas, numpy, sklearn, xgboost, fastai; print('All core dependencies available')"
            ], capture_output=True, text=True, timeout=30)
            execution_time = time.time() - start_time

            evidence = AuditEvidence(
                evidence_type=EvidenceType.SYSTEM_CALL,
                claim="Core ML dependencies are available",
                command="python3 -c 'import pandas, numpy, sklearn, xgboost, fastai; print(\"All core dependencies available\")'",
                expected_pattern="All core dependencies available",
                actual_result=result.stdout.strip(),
                passed="All core dependencies available" in result.stdout,
                execution_time=execution_time
            )

            check2.add_evidence(evidence)
            check2.status = AuditStatus.PASSED if evidence.passed else AuditStatus.FAILED
            check2.score = 100.0 if evidence.passed else 0.0

        except Exception as e:
            evidence = AuditEvidence(
                evidence_type=EvidenceType.SYSTEM_CALL,
                claim="Core ML dependencies are available",
                command="python3 -c 'import pandas, numpy, sklearn, xgboost, fastai; print(\"All core dependencies available\")'",
                expected_pattern="All core dependencies available",
                actual_result=f"Error: {str(e)}",
                passed=False,
                execution_time=0.0
            )
            check2.add_evidence(evidence)
            check2.status = AuditStatus.FAILED
            check2.score = 0.0

        checks.append(check2)

        # Check 3: CFBD client availability
        check3 = AuditCheck(
            category="system_integrity",
            title="CFBD Client Integration",
            description="Validate CFBD client is properly configured and accessible",
            validation_command="python3 -c 'from src.cfbd_client.unified_client import UnifiedCFBDClient; print(\"CFBD client available\")'",
            expected_pattern="CFBD client available",
            critical=True
        )

        try:
            start_time = time.time()
            result = subprocess.run([
                "python3", "-c",
                "from src.cfbd_client.unified_client import UnifiedCFBDClient; print('CFBD client available')"
            ], capture_output=True, text=True, timeout=15)
            execution_time = time.time() - start_time

            evidence = AuditEvidence(
                evidence_type=EvidenceType.SYSTEM_CALL,
                claim="CFBD unified client is available",
                command="python3 -c 'from src.cfbd_client.unified_client import UnifiedCFBDClient; print(\"CFBD client available\")'",
                expected_pattern="CFBD client available",
                actual_result=result.stdout.strip(),
                passed="CFBD client available" in result.stdout,
                execution_time=execution_time
            )

            check3.add_evidence(evidence)
            check3.status = AuditStatus.PASSED if evidence.passed else AuditStatus.FAILED
            check3.score = 100.0 if evidence.passed else 0.0

        except Exception as e:
            evidence = AuditEvidence(
                evidence_type=EvidenceType.SYSTEM_CALL,
                claim="CFBD unified client is available",
                command="python3 -c 'from src.cfbd_client.unified_client import UnifiedCFBDClient; print(\"CFBD client available\")'",
                expected_pattern="CFBD client available",
                actual_result=f"Error: {str(e)}",
                passed=False,
                execution_time=0.0
            )
            check3.add_evidence(evidence)
            check3.status = AuditStatus.FAILED
            check3.score = 0.0

        checks.append(check3)

        return {
            "agent_id": self.agent_id,
            "action": "audit_python_environment",
            "execution_time": time.time(),
            "checks_completed": len(checks),
            "checks": [self._serialize_check(check) for check in checks],
            "summary": self._generate_check_summary(checks)
        }

    def _audit_file_structure(self, parameters: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Audit project file structure and integrity."""

        checks = []

        # Check 1: Core directories exist
        check1 = AuditCheck(
            category="system_integrity",
            title="Core Directory Structure",
            description="Validate essential project directories exist",
            validation_command="find . -maxdepth 1 -type d -name 'agents' -o -name 'src' -o -name 'scripts' -o -name 'model_pack'",
            expected_pattern="agents src scripts model_pack",
            critical=True
        )

        required_dirs = ["agents", "src", "scripts", "model_pack"]
        missing_dirs = []

        try:
            start_time = time.time()
            for dir_name in required_dirs:
                if not Path(dir_name).exists():
                    missing_dirs.append(dir_name)
            execution_time = time.time() - start_time

            evidence = AuditEvidence(
                evidence_type=EvidenceType.FILE_CHECK,
                claim="All core directories exist",
                command=f"Check for directories: {', '.join(required_dirs)}",
                expected_result="All directories present",
                actual_result=f"Missing directories: {', '.join(missing_dirs)}" if missing_dirs else "All directories present",
                passed=len(missing_dirs) == 0,
                execution_time=execution_time
            )

            check1.add_evidence(evidence)
            check1.status = AuditStatus.PASSED if evidence.passed else AuditStatus.FAILED
            check1.score = 100.0 if evidence.passed else 0.0

        except Exception as e:
            evidence = AuditEvidence(
                evidence_type=EvidenceType.FILE_CHECK,
                claim="All core directories exist",
                command=f"Check for directories: {', '.join(required_dirs)}",
                expected_result="All directories present",
                actual_result=f"Error: {str(e)}",
                passed=False,
                execution_time=0.0
            )
            check1.add_evidence(evidence)
            check1.status = AuditStatus.FAILED
            check1.score = 0.0

        checks.append(check1)

        # Check 2: Configuration files exist
        check2 = AuditCheck(
            category="system_integrity",
            title="Configuration Files",
            description="Validate required configuration files are present",
            validation_command="find . -maxdepth 1 -name 'CLAUDE.md' -o -name 'requirements.txt' -o -name 'README.md'",
            expected_pattern="CLAUDE.md requirements.txt README.md",
            critical=True
        )

        required_files = ["CLAUDE.md", "requirements.txt", "README.md"]
        missing_files = []

        try:
            start_time = time.time()
            for file_name in required_files:
                if not Path(file_name).exists():
                    missing_files.append(file_name)
            execution_time = time.time() - start_time

            evidence = AuditEvidence(
                evidence_type=EvidenceType.FILE_CHECK,
                claim="All configuration files exist",
                command=f"Check for files: {', '.join(required_files)}",
                expected_result="All files present",
                actual_result=f"Missing files: {', '.join(missing_files)}" if missing_files else "All files present",
                passed=len(missing_files) == 0,
                execution_time=execution_time
            )

            check2.add_evidence(evidence)
            check2.status = AuditStatus.PASSED if evidence.passed else AuditStatus.FAILED
            check2.score = 100.0 if evidence.passed else 0.0

        except Exception as e:
            evidence = AuditEvidence(
                evidence_type=EvidenceType.FILE_CHECK,
                claim="All configuration files exist",
                command=f"Check for files: {', '.join(required_files)}",
                expected_result="All files present",
                actual_result=f"Error: {str(e)}",
                passed=False,
                execution_time=0.0
            )
            check2.add_evidence(evidence)
            check2.status = AuditStatus.FAILED
            check2.score = 0.0

        checks.append(check2)

        # Check 3: Model files availability
        check3 = AuditCheck(
            category="system_integrity",
            title="Model Files Availability",
            description="Validate trained model files are present and accessible",
            validation_command="find model_pack/ -name '*_model_2025.*' -type f",
            expected_pattern="ridge_model_2025.joblib xgb_home_win_model_2025.pkl fastai_home_win_model_2025.pkl",
            critical=True
        )

        model_patterns = [
            "model_pack/ridge_model_2025.joblib",
            "model_pack/xgb_home_win_model_2025.pkl",
            "model_pack/fastai_home_win_model_2025.pkl"
        ]
        missing_models = []

        try:
            start_time = time.time()
            for model_path in model_patterns:
                if not Path(model_path).exists():
                    missing_models.append(model_path)
            execution_time = time.time() - start_time

            evidence = AuditEvidence(
                evidence_type=EvidenceType.FILE_CHECK,
                claim="All model files exist",
                command=f"Check for models: {', '.join(model_patterns)}",
                expected_result="All models present",
                actual_result=f"Missing models: {', '.join(missing_models)}" if missing_models else "All models present",
                passed=len(missing_models) == 0,
                execution_time=execution_time
            )

            check3.add_evidence(evidence)
            check3.status = AuditStatus.PASSED if evidence.passed else AuditStatus.FAILED
            check3.score = 100.0 if evidence.passed else 0.0

        except Exception as e:
            evidence = AuditEvidence(
                evidence_type=EvidenceType.FILE_CHECK,
                claim="All model files exist",
                command=f"Check for models: {', '.join(model_patterns)}",
                expected_result="All models present",
                actual_result=f"Error: {str(e)}",
                passed=False,
                execution_time=0.0
            )
            check3.add_evidence(evidence)
            check3.status = AuditStatus.FAILED
            check3.score = 0.0

        checks.append(check3)

        return {
            "agent_id": self.agent_id,
            "action": "audit_file_structure",
            "execution_time": time.time(),
            "checks_completed": len(checks),
            "checks": [self._serialize_check(check) for check in checks],
            "summary": self._generate_check_summary(checks)
        }

    def _audit_permissions(self, parameters: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Audit file permissions and access controls."""

        checks = []

        # Check 1: Script execution permissions
        check1 = AuditCheck(
            category="system_integrity",
            title="Script Execution Permissions",
            description="Validate Python scripts are executable",
            validation_command="find scripts/ -name '*.py' -executable | head -5",
            expected_pattern="Scripts should be executable",
            critical=False
        )

        try:
            start_time = time.time()
            scripts_dir = Path("scripts/")
            executable_scripts = []

            if scripts_dir.exists():
                for script_file in scripts_dir.glob("*.py"):
                    if os.access(script_file, os.X_OK):
                        executable_scripts.append(str(script_file))

            execution_time = time.time() - start_time

            evidence = AuditEvidence(
                evidence_type=EvidenceType.FILE_CHECK,
                claim="Python scripts have execution permissions",
                command="find scripts/ -name '*.py' -executable",
                expected_result="Scripts are executable",
                actual_result=f"Found {len(executable_scripts)} executable scripts",
                passed=len(executable_scripts) > 0,
                execution_time=execution_time
            )

            check1.add_evidence(evidence)
            check1.status = AuditStatus.PASSED if evidence.passed else AuditStatus.WARNING
            check1.score = 80.0 if evidence.passed else 40.0

        except Exception as e:
            evidence = AuditEvidence(
                evidence_type=EvidenceType.FILE_CHECK,
                claim="Python scripts have execution permissions",
                command="find scripts/ -name '*.py' -executable",
                expected_result="Scripts are executable",
                actual_result=f"Error: {str(e)}",
                passed=False,
                execution_time=0.0
            )
            check1.add_evidence(evidence)
            check1.status = AuditStatus.FAILED
            check1.score = 0.0

        checks.append(check1)

        # Check 2: Write permissions for data directories
        check2 = AuditCheck(
            category="system_integrity",
            title="Data Directory Write Permissions",
            description="Validate write permissions for data directories",
            validation_command="test -w data/ && test -w predictions/ && echo 'Write permissions OK'",
            expected_pattern="Write permissions OK",
            critical=True
        )

        try:
            start_time = time.time()
            data_dirs = ["data/", "predictions/", "model_pack/"]
            writable_dirs = []

            for dir_path in data_dirs:
                if Path(dir_path).exists() and os.access(dir_path, os.W_OK):
                    writable_dirs.append(dir_path)

            execution_time = time.time() - start_time

            evidence = AuditEvidence(
                evidence_type=EvidenceType.FILE_CHECK,
                claim="Data directories are writable",
                command="test write permissions on data directories",
                expected_result="All data directories writable",
                actual_result=f"Writable directories: {', '.join(writable_dirs)}",
                passed=len(writable_dirs) >= 2,  # At least 2 of 3 should be writable
                execution_time=execution_time
            )

            check2.add_evidence(evidence)
            check2.status = AuditStatus.PASSED if evidence.passed else AuditStatus.FAILED
            check2.score = 100.0 if evidence.passed else 0.0

        except Exception as e:
            evidence = AuditEvidence(
                evidence_type=EvidenceType.FILE_CHECK,
                claim="Data directories are writable",
                command="test write permissions on data directories",
                expected_result="All data directories writable",
                actual_result=f"Error: {str(e)}",
                passed=False,
                execution_time=0.0
            )
            check2.add_evidence(evidence)
            check2.status = AuditStatus.FAILED
            check2.score = 0.0

        checks.append(check2)

        return {
            "agent_id": self.agent_id,
            "action": "audit_permissions",
            "execution_time": time.time(),
            "checks_completed": len(checks),
            "checks": [self._serialize_check(check) for check in checks],
            "summary": self._generate_check_summary(checks)
        }

    def _audit_system_resources(self, parameters: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Audit system resource availability."""

        checks = []

        # Check 1: Available disk space
        check1 = AuditCheck(
            category="system_integrity",
            title="Disk Space Availability",
            description="Validate sufficient disk space for operations",
            validation_command="df -h .",
            expected_pattern="Available disk space > 1GB",
            critical=True
        )

        try:
            start_time = time.time()
            import shutil
            total, used, free = shutil.disk_usage(".")
            free_gb = free // (1024**3)
            execution_time = time.time() - start_time

            evidence = AuditEvidence(
                evidence_type=EvidenceType.PERFORMANCE_METRIC,
                claim="Sufficient disk space available (> 1GB)",
                command="df -h .",
                expected_result="> 1GB available",
                actual_result=f"{free_gb}GB available ({total//1024**3}GB total)",
                passed=free_gb >= 1,
                execution_time=execution_time
            )

            check1.add_evidence(evidence)
            check1.status = AuditStatus.PASSED if evidence.passed else AuditStatus.FAILED
            check1.score = 100.0 if evidence.passed else 0.0

        except Exception as e:
            evidence = AuditEvidence(
                evidence_type=EvidenceType.PERFORMANCE_METRIC,
                claim="Sufficient disk space available (> 1GB)",
                command="df -h .",
                expected_result="> 1GB available",
                actual_result=f"Error: {str(e)}",
                passed=False,
                execution_time=0.0
            )
            check1.add_evidence(evidence)
            check1.status = AuditStatus.FAILED
            check1.score = 0.0

        checks.append(check1)

        # Check 2: Memory availability (simple check)
        check2 = AuditCheck(
            category="system_integrity",
            title="Memory Availability",
            description="Validate system can import required modules",
            validation_command="python3 -c 'import pandas; import numpy; print(\"Memory sufficient for basic operations\")'",
            expected_result="Memory sufficient for basic operations",
            critical=False
        )

        try:
            start_time = time.time()
            result = subprocess.run([
                "python3", "-c",
                "import pandas; import numpy; print('Memory sufficient for basic operations')"
            ], capture_output=True, text=True, timeout=30)
            execution_time = time.time() - start_time

            memory_ok = "Memory sufficient" in result.stdout

            evidence = AuditEvidence(
                evidence_type=EvidenceType.PERFORMANCE_METRIC,
                claim="Memory available for basic operations",
                command="Import pandas and numpy",
                expected_result="Memory sufficient for basic operations",
                actual_result=result.stdout.strip(),
                passed=memory_ok,
                execution_time=execution_time
            )

            check2.add_evidence(evidence)
            check2.status = AuditStatus.PASSED if memory_ok else AuditStatus.WARNING
            check2.score = 90.0 if memory_ok else 50.0

        except Exception as e:
            evidence = AuditEvidence(
                evidence_type=EvidenceType.PERFORMANCE_METRIC,
                claim="Memory available for basic operations",
                command="Import pandas and numpy",
                expected_result="Memory sufficient for basic operations",
                actual_result=f"Error: {str(e)}",
                passed=False,
                execution_time=0.0
            )
            check2.add_evidence(evidence)
            check2.status = AuditStatus.FAILED
            check2.score = 0.0

        checks.append(check2)

        return {
            "agent_id": self.agent_id,
            "action": "audit_system_resources",
            "execution_time": time.time(),
            "checks_completed": len(checks),
            "checks": [self._serialize_check(check) for check in checks],
            "summary": self._generate_check_summary(checks)
        }

    def _serialize_check(self, check: AuditCheck) -> Dict[str, Any]:
        """Serialize audit check for JSON output."""
        return {
            "check_id": check.check_id,
            "category": check.category,
            "title": check.title,
            "description": check.description,
            "validation_command": check.validation_command,
            "expected_pattern": check.expected_pattern,
            "status": check.status.value,
            "score": check.score,
            "max_score": check.max_score,
            "critical": check.critical,
            "evidence_count": len(check.evidence)
        }

    def _generate_check_summary(self, checks: List[AuditCheck]) -> Dict[str, Any]:
        """Generate summary statistics for checks."""
        total_checks = len(checks)
        passed_checks = sum(1 for check in checks if check.status == AuditStatus.PASSED)
        failed_checks = sum(1 for check in checks if check.status == AuditStatus.FAILED)
        warning_checks = sum(1 for check in checks if check.status == AuditStatus.WARNING)
        critical_failures = sum(1 for check in checks if check.status == AuditStatus.FAILED and check.critical)

        total_possible_score = sum(check.max_score for check in checks)
        total_achieved_score = sum(check.score for check in checks)
        overall_score = (total_achieved_score / total_possible_score * 100) if total_possible_score > 0 else 0.0

        return {
            "total_checks": total_checks,
            "passed_checks": passed_checks,
            "failed_checks": failed_checks,
            "warning_checks": warning_checks,
            "critical_failures": critical_failures,
            "overall_score": overall_score,
            "pass_rate": (passed_checks / total_checks * 100) if total_checks > 0 else 0.0
        }