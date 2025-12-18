"""
Core audit system contracts and schemas following OpenAI best practices.
Provides formal definitions for audit checks, evidence collection, and reporting.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import json
from datetime import datetime
import uuid

class AuditStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"

class EvidenceType(Enum):
    SYSTEM_CALL = "system_call"
    FILE_CHECK = "file_check"
    API_TEST = "api_test"
    CODE_ANALYSIS = "code_analysis"
    PERFORMANCE_METRIC = "performance_metric"
    LOG_ANALYSIS = "log_analysis"

@dataclass
class AuditEvidence:
    """Individual evidence item for audit claims."""
    evidence_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    evidence_type: EvidenceType = EvidenceType.SYSTEM_CALL
    claim: str = ""
    command: str = ""
    expected_result: Any = None
    actual_result: Any = None
    passed: bool = False
    execution_time: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AuditCheck:
    """Individual audit check with comprehensive validation."""
    check_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    category: str = ""
    title: str = ""
    description: str = ""
    validation_command: str = ""
    expected_pattern: str = ""
    evidence: List[AuditEvidence] = field(default_factory=list)
    status: AuditStatus = AuditStatus.PENDING
    score: float = 0.0
    max_score: float = 100.0
    critical: bool = False
    dependencies: List[str] = field(default_factory=list)

    def add_evidence(self, evidence: AuditEvidence) -> None:
        """Add evidence to this check."""
        self.evidence.append(evidence)

    def calculate_score(self) -> float:
        """Calculate score based on evidence."""
        if not self.evidence:
            return 0.0

        passed_evidence = sum(1 for e in self.evidence if e.passed)
        total_evidence = len(self.evidence)

        self.score = (passed_evidence / total_evidence) * self.max_score
        return self.score

    def determine_status(self) -> AuditStatus:
        """Determine status based on evidence."""
        if not self.evidence:
            return AuditStatus.PENDING

        passed_evidence = sum(1 for e in self.evidence if e.passed)
        total_evidence = len(self.evidence)

        if passed_evidence == total_evidence:
            self.status = AuditStatus.PASSED
        elif passed_evidence > 0:
            self.status = AuditStatus.WARNING
        else:
            self.status = AuditStatus.FAILED

        return self.status

@dataclass
class AuditReport:
    """Comprehensive audit report with multi-format support."""
    audit_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    audit_name: str = ""
    start_time: str = field(default_factory=lambda: datetime.now().isoformat())
    end_time: Optional[str] = None
    overall_status: AuditStatus = AuditStatus.PENDING
    total_checks: int = 0
    passed_checks: int = 0
    failed_checks: int = 0
    warning_checks: int = 0
    critical_failures: int = 0
    overall_score: float = 0.0
    checks: List[AuditCheck] = field(default_factory=list)
    system_info: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)

    def add_check(self, check: AuditCheck) -> None:
        """Add a check to the audit report."""
        self.checks.append(check)
        self.total_checks += 1

        if check.status == AuditStatus.PASSED:
            self.passed_checks += 1
        elif check.status == AuditStatus.FAILED:
            self.failed_checks += 1
            if check.critical:
                self.critical_failures += 1
        elif check.status == AuditStatus.WARNING:
            self.warning_checks += 1

    def calculate_overall_score(self) -> float:
        """Calculate overall audit score."""
        if self.total_checks == 0:
            return 0.0

        total_possible_score = sum(check.max_score for check in self.checks)
        total_achieved_score = sum(check.score for check in self.checks)

        self.overall_score = (total_achieved_score / total_possible_score) * 100
        return self.overall_score

    def determine_overall_status(self) -> AuditStatus:
        """Determine overall audit status."""
        if self.critical_failures > 0:
            self.overall_status = AuditStatus.FAILED
        elif self.failed_checks > 0:
            self.overall_status = AuditStatus.WARNING
        elif self.warning_checks > 0:
            self.overall_status = AuditStatus.WARNING
        else:
            self.overall_status = AuditStatus.PASSED

        return self.overall_status

    def finalize_report(self) -> None:
        """Finalize the audit report."""
        self.end_time = datetime.now().isoformat()
        self.calculate_overall_score()
        self.determine_overall_status()

        # Calculate final scores for all checks
        for check in self.checks:
            check.calculate_score()
            check.determine_status()

class AuditContract:
    """Formal contract for audit operations and validation."""

    REQUIRED_FIELDS = {
        'check_id': str,
        'category': str,
        'title': str,
        'validation_command': str,
        'expected_pattern': str
    }

    VALID_CATEGORIES = [
        'system_integrity', 'agent_framework', 'data_pipeline',
        'model_validation', 'api_connectivity', 'performance',
        'security', 'code_quality', 'documentation'
    ]

    @staticmethod
    def validate_audit_check(check: AuditCheck) -> tuple[bool, List[str]]:
        """Validate audit check against contract requirements."""
        errors = []

        # Check required fields
        for field, field_type in AuditContract.REQUIRED_FIELDS.items():
            if not hasattr(check, field) or getattr(check, field) is None:
                errors.append(f"Missing required field: {field}")
            elif not isinstance(getattr(check, field), field_type):
                errors.append(f"Invalid type for {field}: expected {field_type.__name__}")

        # Validate category
        if check.category not in AuditContract.VALID_CATEGORIES:
            errors.append(f"Invalid category: {check.category}. Must be one of {AuditContract.VALID_CATEGORIES}")

        # Validate validation command
        if not check.validation_command.strip():
            errors.append("validation_command cannot be empty")

        return len(errors) == 0, errors

    @staticmethod
    def generate_audit_summary(report: AuditReport) -> Dict[str, Any]:
        """Generate standardized audit summary."""
        return {
            'audit_id': report.audit_id,
            'audit_name': report.audit_name,
            'overall_status': report.overall_status.value,
            'overall_score': report.overall_score,
            'total_checks': report.total_checks,
            'passed_checks': report.passed_checks,
            'failed_checks': report.failed_checks,
            'warning_checks': report.warning_checks,
            'critical_failures': report.critical_failures,
            'execution_time': (
                datetime.fromisoformat(report.end_time) - datetime.fromisoformat(report.start_time)
            ).total_seconds() if report.end_time else None,
            'recommendations_count': len(report.recommendations)
        }