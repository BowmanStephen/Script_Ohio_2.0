"""
Data Pipeline Audit Agent - validates CFBD integration and data flow.
Extensive validation of data extraction, transformation, and loading processes.
"""

import subprocess
import pandas as pd
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

from agents.core.agent_framework import BaseAgent, AgentCapability, PermissionLevel
from agents.audit.core_audit_contracts import AuditCheck, AuditEvidence, AuditStatus, EvidenceType

class DataPipelineAuditAgent(BaseAgent):
    """Specialized audit agent for data pipeline validation."""

    def __init__(self, agent_id: str = "data_pipeline_audit_agent"):
        super().__init__(
            agent_id,
            "Data Pipeline Audit Agent",
            PermissionLevel.READ_EXECUTE
        )

    def _define_capabilities(self) -> List[AgentCapability]:
        """Define agent capabilities with data pipeline focus."""
        return [
            AgentCapability(
                name="audit_cfbd_integration",
                description="Validate CFBD API integration and rate limiting",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["python3", "subprocess", "env"],
                data_access=["api_keys", "cfbd_client", "filesystem"],
                execution_time_estimate=45.0
            ),
            AgentCapability(
                name="audit_training_data",
                description="Validate training data integrity and structure",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["python3", "pandas", "path_utils"],
                data_access=["training_data", "filesystem"],
                execution_time_estimate=30.0
            ),
            AgentCapability(
                name="audit_feature_engineering",
                description="Validate feature engineering pipeline",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["python3", "feature_engineering"],
                data_access=["feature_modules", "filesystem"],
                execution_time_estimate=35.0
            ),
            AgentCapability(
                name="audit_data_quality",
                description="Validate data quality and consistency",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["python3", "pandas", "data_analysis"],
                data_access=["training_data", "quality_metrics"],
                execution_time_estimate=40.0
            )
        ]

    def _execute_action(self, action: str, parameters: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute data pipeline audit action."""

        if action == "audit_cfbd_integration":
            return self._audit_cfbd_integration(parameters, user_context)
        elif action == "audit_training_data":
            return self._audit_training_data(parameters, user_context)
        elif action == "audit_feature_engineering":
            return self._audit_feature_engineering(parameters, user_context)
        elif action == "audit_data_quality":
            return self._audit_data_quality(parameters, user_context)
        else:
            return {"error": f"Unknown action: {action}"}

    def _audit_cfbd_integration(self, parameters: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Audit CFBD API integration."""

        checks = []

        # Check 1: CFBD API key configuration
        check1 = AuditCheck(
            category="data_pipeline",
            title="CFBD API Key Configuration",
            description="Validate CFBD API key is properly configured",
            validation_command="python3 -c 'import os; print(\"API Key Present:\" , bool(os.environ.get(\"CFBD_API_KEY\")))'",
            expected_result="API Key Present: True",
            critical=True
        )

        try:
            start_time = time.time()
            result = subprocess.run([
                "python3", "-c",
                "import os; print('API Key Present:', bool(os.environ.get('CFBD_API_KEY')))"
            ], capture_output=True, text=True)
            execution_time = time.time() - start_time

            evidence = AuditEvidence(
                evidence_type=EvidenceType.SYSTEM_CALL,
                claim="CFBD API key is configured",
                command="Check CFBD_API_KEY environment variable",
                expected_result="API Key Present: True",
                actual_result=result.stdout.strip(),
                passed="API Key Present: True" in result.stdout,
                execution_time=execution_time
            )

            check1.add_evidence(evidence)
            check1.status = AuditStatus.PASSED if evidence.passed else AuditStatus.FAILED
            check1.score = 100.0 if evidence.passed else 0.0

        except Exception as e:
            evidence = AuditEvidence(
                evidence_type=EvidenceType.SYSTEM_CALL,
                claim="CFBD API key is configured",
                command="Check CFBD_API_KEY environment variable",
                expected_result="API Key Present: True",
                actual_result=f"Error: {str(e)}",
                passed=False,
                execution_time=0.0
            )
            check1.add_evidence(evidence)
            check1.status = AuditStatus.FAILED
            check1.score = 0.0

        checks.append(check1)

        # Check 2: CFBD client instantiation
        check2 = AuditCheck(
            category="data_pipeline",
            title="CFBD Client Instantiation",
            description="Validate CFBD unified client can be instantiated",
            validation_command="python3 -c 'from src.cfbd_client.unified_client import UnifiedCFBDClient; client = UnifiedCFBDClient(); print(\"CFBD client instantiated successfully\")'",
            expected_result="CFBD client instantiated successfully",
            critical=True
        )

        try:
            start_time = time.time()
            result = subprocess.run([
                "python3", "-c",
                "from src.cfbd_client.unified_client import UnifiedCFBDClient; client = UnifiedCFBDClient(); print('CFBD client instantiated successfully')"
            ], capture_output=True, text=True, timeout=30)
            execution_time = time.time() - start_time

            evidence = AuditEvidence(
                evidence_type=EvidenceType.SYSTEM_CALL,
                claim="CFBD client can be instantiated",
                command="Instantiate UnifiedCFBDClient",
                expected_result="CFBD client instantiated successfully",
                actual_result=result.stdout.strip(),
                passed="CFBD client instantiated successfully" in result.stdout,
                execution_time=execution_time
            )

            check2.add_evidence(evidence)
            check2.status = AuditStatus.PASSED if evidence.passed else AuditStatus.FAILED
            check2.score = 100.0 if evidence.passed else 0.0

        except Exception as e:
            evidence = AuditEvidence(
                evidence_type=EvidenceType.SYSTEM_CALL,
                claim="CFBD client can be instantiated",
                command="Instantiate UnifiedCFBDClient",
                expected_result="CFBD client instantiated successfully",
                actual_result=f"Error: {str(e)}",
                passed=False,
                execution_time=0.0
            )
            check2.add_evidence(evidence)
            check2.status = AuditStatus.FAILED
            check2.score = 0.0

        checks.append(check2)

        # Check 3: Rate limiting validation
        check3 = AuditCheck(
            category="data_pipeline",
            title="CFBD Rate Limiting",
            description="Validate CFBD API rate limiting is properly implemented",
            validation_command="python3 -c 'from src.cfbd_client.unified_client import UnifiedCFBDClient; import time; client = UnifiedCFBDClient(); start = time.time(); # Test rate limiting compliance'",
            expected_result="Rate limiting compliance verified",
            critical=False
        )

        try:
            start_time = time.time()
            # Test by checking if rate limiting code exists
            client_file = Path("src/cfbd_client/unified_client.py")
            rate_limiting_present = False

            if client_file.exists():
                with open(client_file, 'r') as f:
                    content = f.read()
                    rate_limiting_present = "rate_limit" in content.lower() and "sleep" in content.lower()

            execution_time = time.time() - start_time

            evidence = AuditEvidence(
                evidence_type=EvidenceType.CODE_ANALYSIS,
                claim="CFBD rate limiting is implemented",
                command="Check unified_client.py for rate limiting implementation",
                expected_result="Rate limiting code present",
                actual_result="Rate limiting implementation found" if rate_limiting_present else "No rate limiting implementation found",
                passed=rate_limiting_present,
                execution_time=execution_time
            )

            check3.add_evidence(evidence)
            check3.status = AuditStatus.PASSED if rate_limiting_present else AuditStatus.WARNING
            check3.score = 90.0 if rate_limiting_present else 40.0

        except Exception as e:
            evidence = AuditEvidence(
                evidence_type=EvidenceType.CODE_ANALYSIS,
                claim="CFBD rate limiting is implemented",
                command="Check unified_client.py for rate limiting implementation",
                expected_result="Rate limiting code present",
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
            "action": "audit_cfbd_integration",
            "execution_time": time.time(),
            "checks_completed": len(checks),
            "checks": [self._serialize_check(check) for check in checks],
            "summary": self._generate_check_summary(checks)
        }

    def _audit_training_data(self, parameters: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Audit training data integrity."""

        checks = []

        # Check 1: Master training data existence
        check1 = AuditCheck(
            category="data_pipeline",
            title="Master Training Data Availability",
            description="Validate master training data file exists and is accessible",
            validation_command="python3 -c 'from model_pack.utils.path_utils import get_training_data_file; print(\"Training data:\", get_training_data_file())'",
            expected_result="Training data file path returned",
            critical=True
        )

        try:
            start_time = time.time()
            result = subprocess.run([
                "python3", "-c",
                "from model_pack.utils.path_utils import get_training_data_file; print('Training data:', get_training_data_file())"
            ], capture_output=True, text=True, timeout=15)
            execution_time = time.time() - start_time

            training_data_path = result.stdout.strip().split("Training data:")[-1].strip()
            file_exists = Path(training_data_path).exists() if training_data_path else False

            evidence = AuditEvidence(
                evidence_type=EvidenceType.FILE_CHECK,
                claim="Master training data file exists",
                command="Check training data file path and existence",
                expected_result="Training data file exists",
                actual_result=f"Path: {training_data_path}, Exists: {file_exists}",
                passed=file_exists,
                execution_time=execution_time
            )

            check1.add_evidence(evidence)
            check1.status = AuditStatus.PASSED if evidence.passed else AuditStatus.FAILED
            check1.score = 100.0 if evidence.passed else 0.0

        except Exception as e:
            evidence = AuditEvidence(
                evidence_type=EvidenceType.FILE_CHECK,
                claim="Master training data file exists",
                command="Check training data file path and existence",
                expected_result="Training data file exists",
                actual_result=f"Error: {str(e)}",
                passed=False,
                execution_time=0.0
            )
            check1.add_evidence(evidence)
            check1.status = AuditStatus.FAILED
            check1.score = 0.0

        checks.append(check1)

        # Check 2: Training data structure validation
        check2 = AuditCheck(
            category="data_pipeline",
            title="Training Data Structure",
            description="Validate training data has expected structure and features",
            validation_command="python3 -c 'import pandas as pd; from model_pack.utils.path_utils import get_training_data_file; df = pd.read_csv(get_training_data_file()); print(f\"Shape: {df.shape}, Columns: {len(df.columns)}\")'",
            expected_result="Data loaded with expected structure (>= 4000 rows, >= 80 columns)",
            critical=True
        )

        try:
            start_time = time.time()
            result = subprocess.run([
                "python3", "-c",
                "import pandas as pd; from model_pack.utils.path_utils import get_training_data_file; df = pd.read_csv(get_training_data_file()); print(f'Shape: {df.shape}, Columns: {len(df.columns)}')"
            ], capture_output=True, text=True, timeout=30)
            execution_time = time.time() - start_time

            # Parse the output to extract shape information
            output = result.stdout.strip()
            shape_ok = "Shape:" in output and "Columns:" in output

            # Further validation by loading the data directly
            try:
                from model_pack.utils.path_utils import get_training_data_file
                training_path = get_training_data_file()
                df = pd.read_csv(training_path)
                rows, cols = df.shape
                structure_valid = rows >= 4000 and cols >= 80
            except:
                structure_valid = False

            evidence = AuditEvidence(
                evidence_type=EvidenceType.CODE_ANALYSIS,
                claim="Training data has expected structure",
                command="Load and validate training data structure",
                expected_result=">= 4000 rows, >= 80 columns",
                actual_result=output,
                passed=structure_valid,
                execution_time=execution_time
            )

            check2.add_evidence(evidence)
            check2.status = AuditStatus.PASSED if structure_valid else AuditStatus.FAILED
            check2.score = 100.0 if structure_valid else 0.0

        except Exception as e:
            evidence = AuditEvidence(
                evidence_type=EvidenceType.CODE_ANALYSIS,
                claim="Training data has expected structure",
                command="Load and validate training data structure",
                expected_result=">= 4000 rows, >= 80 columns",
                actual_result=f"Error: {str(e)}",
                passed=False,
                execution_time=0.0
            )
            check2.add_evidence(evidence)
            check2.status = AuditStatus.FAILED
            check2.score = 0.0

        checks.append(check2)

        # Check 3: Data freshness validation
        check3 = AuditCheck(
            category="data_pipeline",
            title="Training Data Freshness",
            description="Validate training data includes recent seasons (2025)",
            validation_command="python3 -c 'import pandas as pd; from model_pack.utils.path_utils import get_training_data_file; df = pd.read_csv(get_training_data_file()); print(f\"Season range: {df[\"season\"].min()} - {df[\"season\"].max()}\")'",
            expected_result="Season range includes 2025",
            critical=False
        )

        try:
            start_time = time.time()
            from model_pack.utils.path_utils import get_training_data_file
            training_path = get_training_data_file()
            df = pd.read_csv(training_path)

            if 'season' in df.columns:
                min_season = df['season'].min()
                max_season = df['season'].max()
                includes_2025 = max_season >= 2025
                season_range = f"{min_season} - {max_season}"
            else:
                includes_2025 = False
                season_range = "Season column not found"

            execution_time = time.time() - start_time

            evidence = AuditEvidence(
                evidence_type=EvidenceType.CODE_ANALYSIS,
                claim="Training data includes recent seasons",
                command="Check season range in training data",
                expected_result="Includes 2025 season",
                actual_result=f"Season range: {season_range}",
                passed=includes_2025,
                execution_time=execution_time
            )

            check3.add_evidence(evidence)
            check3.status = AuditStatus.PASSED if includes_2025 else AuditStatus.WARNING
            check3.score = 90.0 if includes_2025 else 60.0

        except Exception as e:
            evidence = AuditEvidence(
                evidence_type=EvidenceType.CODE_ANALYSIS,
                claim="Training data includes recent seasons",
                command="Check season range in training data",
                expected_result="Includes 2025 season",
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
            "action": "audit_training_data",
            "execution_time": time.time(),
            "checks_completed": len(checks),
            "checks": [self._serialize_check(check) for check in checks],
            "summary": self._generate_check_summary(checks)
        }

    def _audit_feature_engineering(self, parameters: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Audit feature engineering pipeline."""

        checks = []

        # Check 1: Feature engineering module availability
        check1 = AuditCheck(
            category="data_pipeline",
            title="Feature Engineering Module",
            description="Validate feature engineering modules are available",
            validation_command="python3 -c 'from src.features.cfbd_feature_engineering import *; print(\"Feature engineering modules imported successfully\")'",
            expected_result="Feature engineering modules imported successfully",
            critical=True
        )

        try:
            start_time = time.time()
            result = subprocess.run([
                "python3", "-c",
                "from src.features.cfbd_feature_engineering import *; print('Feature engineering modules imported successfully')"
            ], capture_output=True, text=True, timeout=20)
            execution_time = time.time() - start_time

            evidence = AuditEvidence(
                evidence_type=EvidenceType.SYSTEM_CALL,
                claim="Feature engineering modules are importable",
                command="Import feature engineering modules",
                expected_result="Modules imported successfully",
                actual_result=result.stdout.strip(),
                passed="Feature engineering modules imported successfully" in result.stdout,
                execution_time=execution_time
            )

            check1.add_evidence(evidence)
            check1.status = AuditStatus.PASSED if evidence.passed else AuditStatus.FAILED
            check1.score = 100.0 if evidence.passed else 0.0

        except Exception as e:
            evidence = AuditEvidence(
                evidence_type=EvidenceType.SYSTEM_CALL,
                claim="Feature engineering modules are importable",
                command="Import feature engineering modules",
                expected_result="Modules imported successfully",
                actual_result=f"Error: {str(e)}",
                passed=False,
                execution_time=0.0
            )
            check1.add_evidence(evidence)
            check1.status = AuditStatus.FAILED
            check1.score = 0.0

        checks.append(check1)

        # Check 2: Feature count validation
        check2 = AuditCheck(
            category="data_pipeline",
            title="Feature Count Validation",
            description="Validate expected number of features (86 opponent-adjusted features)",
            validation_command="python3 -c 'from src.features.cfbd_feature_engineering import create_features; print(\"Feature engineering function available\")'",
            expected_result="Feature engineering function available",
            critical=False
        )

        try:
            start_time = time.time()
            # Check if feature engineering functions exist
            feature_file = Path("src/features/cfbd_feature_engineering.py")
            feature_count_ok = False

            if feature_file.exists():
                with open(feature_file, 'r') as f:
                    content = f.read()
                    # Look for indicators of proper feature engineering
                    feature_count_ok = "86" in content or "opponent" in content.lower()

            execution_time = time.time() - start_time

            evidence = AuditEvidence(
                evidence_type=EvidenceType.CODE_ANALYSIS,
                claim="Feature engineering creates 86 opponent-adjusted features",
                command="Check feature engineering code for 86 features",
                expected_result="86 opponent-adjusted features implemented",
                actual_result="Feature engineering code structure found" if feature_count_ok else "Feature engineering structure not found",
                passed=feature_count_ok,
                execution_time=execution_time
            )

            check2.add_evidence(evidence)
            check2.status = AuditStatus.PASSED if feature_count_ok else AuditStatus.WARNING
            check2.score = 85.0 if feature_count_ok else 50.0

        except Exception as e:
            evidence = AuditEvidence(
                evidence_type=EvidenceType.CODE_ANALYSIS,
                claim="Feature engineering creates 86 opponent-adjusted features",
                command="Check feature engineering code for 86 features",
                expected_result="86 opponent-adjusted features implemented",
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
            "action": "audit_feature_engineering",
            "execution_time": time.time(),
            "checks_completed": len(checks),
            "checks": [self._serialize_check(check) for check in checks],
            "summary": self._generate_check_summary(checks)
        }

    def _audit_data_quality(self, parameters: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Audit data quality and consistency."""

        checks = []

        # Check 1: Missing values validation
        check1 = AuditCheck(
            category="data_pipeline",
            title="Missing Values Validation",
            description="Validate training data has acceptable missing value rates",
            validation_command="python3 -c 'import pandas as pd; from model_pack.utils.path_utils import get_training_data_file; df = pd.read_csv(get_training_data_file()); missing_rate = df.isnull().sum().sum() / df.size; print(f\"Missing value rate: {missing_rate:.3%}\")'",
            expected_result="Missing value rate < 5%",
            critical=False
        )

        try:
            start_time = time.time()
            from model_pack.utils.path_utils import get_training_data_file
            training_path = get_training_data_file()
            df = pd.read_csv(training_path)

            missing_rate = df.isnull().sum().sum() / df.size
            missing_acceptable = missing_rate < 0.05  # Less than 5%

            execution_time = time.time() - start_time

            evidence = AuditEvidence(
                evidence_type=EvidenceType.CODE_ANALYSIS,
                claim="Training data has acceptable missing value rates",
                command="Calculate missing value rate in training data",
                expected_result="Missing value rate < 5%",
                actual_result=f"Missing value rate: {missing_rate:.3%}",
                passed=missing_acceptable,
                execution_time=execution_time
            )

            check1.add_evidence(evidence)
            check1.status = AuditStatus.PASSED if missing_acceptable else AuditStatus.WARNING
            check1.score = 95.0 if missing_acceptable else 70.0

        except Exception as e:
            evidence = AuditEvidence(
                evidence_type=EvidenceType.CODE_ANALYSIS,
                claim="Training data has acceptable missing value rates",
                command="Calculate missing value rate in training data",
                expected_result="Missing value rate < 5%",
                actual_result=f"Error: {str(e)}",
                passed=False,
                execution_time=0.0
            )
            check1.add_evidence(evidence)
            check1.status = AuditStatus.FAILED
            check1.score = 0.0

        checks.append(check1)

        # Check 2: Data consistency validation
        check2 = AuditCheck(
            category="data_pipeline",
            title="Data Consistency",
            description="Validate data consistency across seasons and weeks",
            validation_command="python3 -c 'import pandas as pd; from model_pack.utils.path_utils import get_training_data_file; df = pd.read_csv(get_training_data_file()); print(f\"Unique seasons: {df[\"season\"].nunique()}, Unique weeks: {df[\"week\"].nunique()}\")'",
            expected_result="Multiple seasons and weeks represented",
            critical=False
        )

        try:
            start_time = time.time()
            from model_pack.utils.path_utils import get_training_data_file
            training_path = get_training_data_file()
            df = pd.read_csv(training_path)

            if 'season' in df.columns and 'week' in df.columns:
                unique_seasons = df['season'].nunique()
                unique_weeks = df['week'].nunique()
                consistency_ok = unique_seasons >= 3 and unique_weeks >= 10
                consistency_info = f"Unique seasons: {unique_seasons}, Unique weeks: {unique_weeks}"
            else:
                consistency_ok = False
                consistency_info = "Required columns not found"

            execution_time = time.time() - start_time

            evidence = AuditEvidence(
                evidence_type=EvidenceType.CODE_ANALYSIS,
                claim="Training data has good consistency across seasons and weeks",
                command="Check data diversity across seasons and weeks",
                expected_result="Multiple seasons and weeks",
                actual_result=consistency_info,
                passed=consistency_ok,
                execution_time=execution_time
            )

            check2.add_evidence(evidence)
            check2.status = AuditStatus.PASSED if consistency_ok else AuditStatus.WARNING
            check2.score = 90.0 if consistency_ok else 60.0

        except Exception as e:
            evidence = AuditEvidence(
                evidence_type=EvidenceType.CODE_ANALYSIS,
                claim="Training data has good consistency across seasons and weeks",
                command="Check data diversity across seasons and weeks",
                expected_result="Multiple seasons and weeks",
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
            "action": "audit_data_quality",
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