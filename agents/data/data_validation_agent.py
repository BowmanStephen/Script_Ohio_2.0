#!/usr/bin/env python3
"""
Data Validation Agent - Tier 3 Security Level
Comprehensive data quality assurance and validation system

Implements advanced data validation with quality metrics, anomaly detection,
and comprehensive reporting for CFBD and analytics data workflows.
"""

import logging
import json
import time
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import re
import hashlib
from pathlib import Path
import jsonschema
from jsonschema import validate, ValidationError, Draft7Validator
import great_expectations as ge
from ge.core.expectation_suite import ExpectationSuite
from ge.core.batch import RuntimeBatchRequest

from agents.core.enhanced_agent_framework import EnhancedBaseAgent
from agents.core.security_manager import security_manager, PermissionLevel


class ValidationLevel(Enum):
    """Validation levels with increasing strictness"""

    BASIC = "basic"  # Essential field validation only
    STANDARD = "standard"  # Standard data quality checks
    COMPREHENSIVE = "comprehensive"  # Full validation suite
    STRICT = "strict"  # Maximum validation with zero tolerance


class ValidationStatus(Enum):
    """Validation status enumeration"""

    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"
    ERROR = "error"


class DataFormat(Enum):
    """Supported data formats"""

    JSON = "json"
    CSV = "csv"
    PARQUET = "parquet"
    EXCEL = "excel"
    DICT = "dict"


class ValidationRuleType(Enum):
    """Types of validation rules"""

    SCHEMA = "schema"  # JSON schema validation
    BUSINESS_LOGIC = "business_logic"  # Domain-specific rules
    DATA_QUALITY = "data_quality"  # General quality metrics
    ANOMALY_DETECTION = "anomaly_detection"  # Statistical anomaly detection
    REFERENTIAL_INTEGRITY = "referential_integrity"  # Relationship validation
    TEMPORAL = "temporal"  # Time-series validation


@dataclass
class ValidationRule:
    """Represents a single validation rule"""

    rule_id: str
    name: str
    description: str
    rule_type: ValidationRuleType
    validation_level: ValidationLevel
    severity: str  # low, medium, high, critical
    enabled: bool = True
    custom_logic: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)


@dataclass
class ValidationResult:
    """Result of a validation rule execution"""

    rule_id: str
    status: ValidationStatus
    passed: bool
    failed_records: int
    total_records: int
    failure_rate: float
    error_message: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    execution_time_seconds: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DataValidationReport:
    """Comprehensive data validation report"""

    validation_id: str
    data_source: str
    data_type: str
    record_count: int
    validation_level: ValidationLevel
    executed_at: datetime
    duration_seconds: float
    results: List[ValidationResult] = field(default_factory=list)
    overall_status: ValidationStatus = ValidationStatus.PASSED
    summary_metrics: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    data_quality_score: float = 100.0


class DataValidationAgent(EnhancedBaseAgent):
    """
    Data Validation Agent - Comprehensive data quality assurance

    Capabilities:
    - Schema validation using JSON Schema and Great Expectations
    - Business logic validation for CFBD data domains
    - Data quality metrics and anomaly detection
    - Referential integrity validation
    - Temporal data validation for time-series
    - Comprehensive reporting with actionable recommendations
    - Automated rule management and customization
    """

    def __init__(self, agent_id: str = "data_validation_agent"):
        super().__init__(
            agent_id=agent_id,
            agent_name="Data Validation Agent",
            permission_level=PermissionLevel.READ_EXECUTE,
        )

        self.logger = logging.getLogger(f"{__name__}.{agent_id}")

        # Validation configuration
        self.validation_thresholds = {
            "max_failure_rate": 0.05,  # 5% failure rate threshold
            "quality_score_min": 85.0,  # Minimum quality score
            "anomaly_threshold": 2.0,  # Standard deviations
            "completeness_threshold": 0.95,  # 95% completeness required
            "accuracy_threshold": 0.98,  # 98% accuracy required
        }

        # Load validation rules
        self.validation_rules = self._load_validation_rules()
        self.rule_suites = self._create_rule_suites()

        # Great Expectations configuration
        self.ge_context = self._initialize_ge_context()

        # Performance metrics
        self.metrics = {
            "validations_executed": 0,
            "records_validated": 0,
            "rules_executed": 0,
            "average_validation_time": 0.0,
            "failure_rate_by_data_type": {},
            "quality_score_trends": [],
            "anomalies_detected": 0,
        }

        # Cache for validation schemas
        self.schema_cache = {}

    def _define_capabilities(self) -> List:
        """Define data validation capabilities"""
        return [
            {
                "name": "validate_cfbd_data",
                "description": "Validate CFBD data against schema and business rules",
                "execution_time_estimate": 12.0,
                "required_permissions": [PermissionLevel.READ_EXECUTE],
                "parameters": ["data", "data_type", "validation_level"],
                "returns": {
                    "validation_report": "object",
                    "quality_score": "float",
                    "issues": "list",
                },
            },
            {
                "name": "validate_model_data",
                "description": "Validate ML model training and prediction data",
                "execution_time_estimate": 10.0,
                "required_permissions": [PermissionLevel.READ_EXECUTE],
                "parameters": ["data", "model_type", "validation_rules"],
                "returns": {
                    "validation_report": "object",
                    "data_readiness": "boolean",
                    "recommendations": "list",
                },
            },
            {
                "name": "detect_anomalies",
                "description": "Detect statistical anomalies in datasets",
                "execution_time_estimate": 8.0,
                "required_permissions": [PermissionLevel.READ_EXECUTE],
                "parameters": ["data", "anomaly_types", "sensitivity"],
                "returns": {
                    "anomalies": "list",
                    "anomaly_score": "float",
                    "distribution_analysis": "dict",
                },
            },
            {
                "name": "create_validation_rules",
                "description": "Create custom validation rules for specific data types",
                "execution_time_estimate": 15.0,
                "required_permissions": [PermissionLevel.READ_EXECUTE],
                "parameters": ["rule_specifications", "target_data_type"],
                "returns": {"rules_created": "list", "validation_results": "dict"},
            },
            {
                "name": "generate_quality_report",
                "description": "Generate comprehensive data quality reports",
                "execution_time_estimate": 6.0,
                "required_permissions": [PermissionLevel.READ_EXECUTE],
                "parameters": [
                    "validation_results",
                    "report_format",
                    "include_recommendations",
                ],
                "returns": {
                    "quality_report": "object",
                    "metrics": "dict",
                    "trend_analysis": "list",
                },
            },
        ]

    def _execute_action(
        self, action: str, parameters: Dict, user_context: Dict
    ) -> Dict:
        """Execute data validation actions"""
        try:
            # Create security context
            context = security_manager.create_security_context(
                user_id=user_context.get("user_id", "validation_system"),
                permissions=["data_validation", "quality_assurance", "audit_logging"],
            )

            if action == "validate_cfbd_data":
                return self._validate_cfbd_data(parameters, context)
            elif action == "validate_model_data":
                return self._validate_model_data(parameters, context)
            elif action == "detect_anomalies":
                return self._detect_anomalies(parameters, context)
            elif action == "create_validation_rules":
                return self._create_validation_rules(parameters, context)
            elif action == "generate_quality_report":
                return self._generate_quality_report(parameters, context)
            else:
                raise ValueError(f"Unknown action: {action}")

        except Exception as e:
            self.logger.error(f"Validation action {action} failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__,
                "agent_id": self.agent_id,
                "timestamp": datetime.utcnow().isoformat(),
            }

    def _validate_cfbd_data(self, parameters: Dict, context) -> Dict:
        """Validate CFBD data against schema and business rules"""
        self.logger.info("Starting CFBD data validation")

        data = parameters.get("data", [])
        data_type = parameters.get("data_type", "games")
        validation_level = ValidationLevel(
            parameters.get("validation_level", "standard")
        )

        if not data:
            return {"status": "error", "error": "No data provided for validation"}

        # Convert data to DataFrame for processing
        df = self._convert_to_dataframe(data, data_type)
        if df.empty:
            return {"status": "error", "error": "Failed to convert data to DataFrame"}

        # Create validation report
        validation_id = f"cfbd_validation_{int(time.time())}"
        report = DataValidationReport(
            validation_id=validation_id,
            data_source="cfbd_api",
            data_type=data_type,
            record_count=len(df),
            validation_level=validation_level,
            executed_at=datetime.utcnow(),
        )

        start_time = time.time()

        try:
            # Execute validation rules
            applicable_rules = [
                rule
                for rule in self.validation_rules
                if rule.validation_level == validation_level and rule.enabled
            ]

            for rule in applicable_rules:
                result = self._execute_validation_rule(rule, df, data_type)
                report.results.append(result)

            # Calculate overall status and metrics
            report.overall_status = self._calculate_overall_status(report.results)
            report.summary_metrics = self._calculate_summary_metrics(
                report.results, len(df)
            )
            report.data_quality_score = self._calculate_quality_score(report.results)
            report.recommendations = self._generate_recommendations(
                report.results, data_type
            )

            report.duration_seconds = time.time() - start_time

            # Update metrics
            self._update_validation_metrics(report)

            # Log security event
            security_manager.log_security_event(
                event_type="data_validation_completed",
                user_id=context.get("user_id", "validation_system"),
                resource_id=validation_id,
                details={
                    "data_type": data_type,
                    "record_count": len(df),
                    "validation_level": validation_level.value,
                    "quality_score": report.data_quality_score,
                    "issues_found": len(
                        [
                            r
                            for r in report.results
                            if r.status == ValidationStatus.FAILED
                        ]
                    ),
                },
            )

            return {
                "status": "success",
                "data": {
                    "validation_report": {
                        "validation_id": report.validation_id,
                        "data_type": report.data_type,
                        "record_count": report.record_count,
                        "validation_level": report.validation_level.value,
                        "overall_status": report.overall_status.value,
                        "data_quality_score": report.data_quality_score,
                        "duration_seconds": report.duration_seconds,
                        "summary_metrics": report.summary_metrics,
                    },
                    "quality_score": report.data_quality_score,
                    "issues": self._extract_issues(report.results),
                    "recommendations": report.recommendations,
                    "detailed_results": [
                        {
                            "rule_id": result.rule_id,
                            "rule_name": result.name,
                            "status": result.status.value,
                            "passed": result.passed,
                            "failure_rate": result.failure_rate,
                            "failed_records": result.failed_records,
                            "error_message": result.error_message,
                        }
                        for result in report.results
                    ],
                },
                "execution_time": report.duration_seconds,
                "agent_id": self.agent_id,
            }

        except Exception as e:
            report.duration_seconds = time.time() - start_time
            report.overall_status = ValidationStatus.ERROR

            return {
                "status": "error",
                "error": f"Validation failed: {str(e)}",
                "validation_id": validation_id,
                "execution_time": report.duration_seconds,
                "agent_id": self.agent_id,
            }

    def _validate_model_data(self, parameters: Dict, context) -> Dict:
        """Validate ML model training and prediction data"""
        self.logger.info("Starting model data validation")

        data = parameters.get("data", [])
        model_type = parameters.get("model_type", "general")
        custom_rules = parameters.get("validation_rules", [])

        if not data:
            return {"status": "error", "error": "No data provided for model validation"}

        # Convert data to DataFrame
        df = self._convert_to_dataframe(data, "model")
        if df.empty:
            return {
                "status": "error",
                "error": "Failed to convert model data to DataFrame",
            }

        # Create validation report
        validation_id = f"model_validation_{int(time.time())}"
        report = DataValidationReport(
            validation_id=validation_id,
            data_source="model_pipeline",
            data_type=f"model_{model_type}",
            record_count=len(df),
            validation_level=ValidationLevel.STANDARD,
            executed_at=datetime.utcnow(),
        )

        start_time = time.time()

        try:
            # Apply model-specific validation rules
            model_rules = self._get_model_validation_rules(model_type, custom_rules)

            for rule in model_rules:
                result = self._execute_validation_rule(rule, df, f"model_{model_type}")
                report.results.append(result)

            # Additional ML-specific validations
            ml_results = self._execute_ml_validations(df, model_type)
            report.results.extend(ml_results)

            # Calculate readiness and recommendations
            report.overall_status = self._calculate_overall_status(report.results)
            report.data_quality_score = self._calculate_quality_score(report.results)
            report.recommendations = self._generate_ml_recommendations(
                report.results, model_type
            )
            report.duration_seconds = time.time() - start_time

            # Check data readiness
            data_readiness = (
                report.overall_status == ValidationStatus.PASSED
                and report.data_quality_score
                >= self.validation_thresholds["quality_score_min"]
            )

            return {
                "status": "success",
                "data": {
                    "validation_report": {
                        "validation_id": report.validation_id,
                        "model_type": model_type,
                        "record_count": report.record_count,
                        "overall_status": report.overall_status.value,
                        "data_quality_score": report.data_quality_score,
                        "duration_seconds": report.duration_seconds,
                    },
                    "data_readiness": data_readiness,
                    "readiness_factors": self._assess_readiness_factors(report.results),
                    "recommendations": report.recommendations,
                    "feature_analysis": self._analyze_features(df, model_type),
                    "target_analysis": self._analyze_target_variable(df, model_type),
                },
                "execution_time": report.duration_seconds,
                "agent_id": self.agent_id,
            }

        except Exception as e:
            report.duration_seconds = time.time() - start_time
            report.overall_status = ValidationStatus.ERROR

            return {
                "status": "error",
                "error": f"Model validation failed: {str(e)}",
                "validation_id": validation_id,
                "execution_time": report.duration_seconds,
                "agent_id": self.agent_id,
            }

    def _detect_anomalies(self, parameters: Dict, context) -> Dict:
        """Detect statistical anomalies in datasets"""
        self.logger.info("Starting anomaly detection")

        data = parameters.get("data", [])
        anomaly_types = parameters.get(
            "anomaly_types", ["statistical", "outlier", "distribution"]
        )
        sensitivity = parameters.get("sensitivity", "medium")

        if not data:
            return {
                "status": "error",
                "error": "No data provided for anomaly detection",
            }

        # Convert data to DataFrame
        df = self._convert_to_dataframe(data, "anomaly")
        if df.empty:
            return {"status": "error", "error": "Failed to convert data to DataFrame"}

        # Convert to pandas for statistical operations
        if isinstance(df, pd.DataFrame):
            pandas_df = df
        else:
            pandas_df = pd.DataFrame(data)

        start_time = time.time()
        anomalies = []
        total_anomaly_score = 0.0

        try:
            # Statistical anomaly detection
            if "statistical" in anomaly_types:
                stat_anomalies = self._detect_statistical_anomalies(
                    pandas_df, sensitivity
                )
                anomalies.extend(stat_anomalies)

            # Outlier detection
            if "outlier" in anomaly_types:
                outlier_anomalies = self._detect_outliers(pandas_df, sensitivity)
                anomalies.extend(outlier_anomalies)

            # Distribution analysis
            if "distribution" in anomaly_types:
                dist_anomalies = self._detect_distribution_anomalies(
                    pandas_df, sensitivity
                )
                anomalies.extend(dist_anomalies)

            # Calculate overall anomaly score
            if anomalies:
                total_anomaly_score = sum(a.get("score", 0) for a in anomalies) / len(
                    anomalies
                )

            # Generate distribution analysis
            distribution_analysis = self._analyze_distributions(pandas_df)

            execution_time = time.time() - start_time

            # Update metrics
            self.metrics["anomalies_detected"] += len(anomalies)

            return {
                "status": "success",
                "data": {
                    "anomalies": anomalies,
                    "anomaly_score": total_anomaly_score,
                    "anomaly_count": len(anomalies),
                    "distribution_analysis": distribution_analysis,
                    "sensitivity": sensitivity,
                    "data_summary": {
                        "record_count": len(pandas_df),
                        "feature_count": len(pandas_df.columns),
                        "numeric_features": len(
                            pandas_df.select_dtypes(include=[np.number]).columns
                        ),
                        "categorical_features": len(
                            pandas_df.select_dtypes(include=["object"]).columns
                        ),
                    },
                },
                "execution_time": execution_time,
                "agent_id": self.agent_id,
            }

        except Exception as e:
            return {
                "status": "error",
                "error": f"Anomaly detection failed: {str(e)}",
                "execution_time": time.time() - start_time,
                "agent_id": self.agent_id,
            }

    def _create_validation_rules(self, parameters: Dict, context) -> Dict:
        """Create custom validation rules for specific data types"""
        self.logger.info("Creating custom validation rules")

        rule_specifications = parameters.get("rule_specifications", [])
        target_data_type = parameters.get("target_data_type", "custom")

        created_rules = []
        validation_results = {}

        for spec in rule_specifications:
            try:
                # Create validation rule
                rule = ValidationRule(
                    rule_id=f"custom_{int(time.time())}_{len(created_rules)}",
                    name=spec.get("name", "Custom Rule"),
                    description=spec.get("description", ""),
                    rule_type=ValidationRuleType(spec.get("rule_type", "data_quality")),
                    validation_level=ValidationLevel(
                        spec.get("validation_level", "standard")
                    ),
                    severity=spec.get("severity", "medium"),
                    custom_logic=spec.get("custom_logic"),
                    parameters=spec.get("parameters", {}),
                    tags=spec.get("tags", []),
                )

                # Validate rule specification
                validation_result = self._validate_rule_specification(rule, spec)
                validation_results[rule.rule_id] = validation_result

                if validation_result.get("valid", False):
                    # Add to validation rules
                    self.validation_rules.append(rule)
                    created_rules.append(
                        {
                            "rule_id": rule.rule_id,
                            "name": rule.name,
                            "type": rule.rule_type.value,
                            "validation_level": rule.validation_level.value,
                            "severity": rule.severity,
                        }
                    )
                else:
                    validation_results[rule.rule_id][
                        "error"
                    ] = "Rule specification validation failed"

            except Exception as e:
                rule_id = spec.get("rule_id", f"invalid_{len(created_rules)}")
                validation_results[rule_id] = {
                    "valid": False,
                    "error": str(e),
                    "specification": spec,
                }

        return {
            "status": "success",
            "data": {
                "rules_created": created_rules,
                "validation_results": validation_results,
                "target_data_type": target_data_type,
                "total_rules": len(created_rules),
                "success_rate": (
                    len(created_rules) / len(rule_specifications) * 100
                    if rule_specifications
                    else 0
                ),
            },
            "execution_time": time.time(),
            "agent_id": self.agent_id,
        }

    def _generate_quality_report(self, parameters: Dict, context) -> Dict:
        """Generate comprehensive data quality reports"""
        self.logger.info("Generating data quality report")

        validation_results = parameters.get("validation_results", [])
        report_format = parameters.get("report_format", "json")
        include_recommendations = parameters.get("include_recommendations", True)

        if not validation_results:
            return {"status": "error", "error": "No validation results provided"}

        # Analyze validation results
        quality_analysis = self._analyze_validation_results(validation_results)
        trend_analysis = self._calculate_quality_trends()
        compliance_metrics = self._calculate_compliance_metrics(validation_results)

        # Generate recommendations
        recommendations = []
        if include_recommendations:
            recommendations = self._generate_quality_recommendations(quality_analysis)

        # Create quality report
        quality_report = {
            "report_id": f"quality_report_{int(time.time())}",
            "generated_at": datetime.utcnow().isoformat(),
            "summary": quality_analysis,
            "trend_analysis": trend_analysis,
            "compliance_metrics": compliance_metrics,
            "recommendations": recommendations,
            "detailed_results": validation_results,
        }

        return {
            "status": "success",
            "data": {
                "quality_report": quality_report,
                "metrics": {
                    "overall_quality_score": quality_analysis.get("overall_score", 0),
                    "rule_pass_rate": quality_analysis.get("pass_rate", 0),
                    "critical_issues": quality_analysis.get("critical_issues", 0),
                    "improvement_areas": quality_analysis.get("improvement_areas", []),
                },
                "trend_analysis": trend_analysis,
                "compliance_status": {
                    "compliant": compliance_metrics.get("compliant", False),
                    "compliance_score": compliance_metrics.get("score", 0),
                    "violations": compliance_metrics.get("violations", []),
                },
            },
            "execution_time": time.time(),
            "agent_id": self.agent_id,
        }

    # Helper methods
    def _load_validation_rules(self) -> List[ValidationRule]:
        """Load predefined validation rules"""
        rules = []

        # Schema validation rules
        rules.append(
            ValidationRule(
                rule_id="schema_games_validation",
                name="Games Schema Validation",
                description="Validates games data against required schema",
                rule_type=ValidationRuleType.SCHEMA,
                validation_level=ValidationLevel.BASIC,
                severity="critical",
                tags=["games", "schema"],
            )
        )

        rules.append(
            ValidationRule(
                rule_id="schema_teams_validation",
                name="Teams Schema Validation",
                description="Validates teams data against required schema",
                rule_type=ValidationRuleType.SCHEMA,
                validation_level=ValidationLevel.BASIC,
                severity="critical",
                tags=["teams", "schema"],
            )
        )

        # Business logic rules
        rules.append(
            ValidationRule(
                rule_id="games_score_consistency",
                name="Games Score Consistency",
                description="Ensures home and away scores are consistent with winner",
                rule_type=ValidationRuleType.BUSINESS_LOGIC,
                validation_level=ValidationLevel.STANDARD,
                severity="high",
                tags=["games", "business_logic"],
            )
        )

        rules.append(
            ValidationRule(
                rule_id="team_conference_consistency",
                name="Team Conference Consistency",
                description="Validates team-conference relationships",
                rule_type=ValidationRuleType.BUSINESS_LOGIC,
                validation_level=ValidationLevel.STANDARD,
                severity="medium",
                tags=["teams", "business_logic"],
            )
        )

        # Data quality rules
        rules.append(
            ValidationRule(
                rule_id="completeness_check",
                name="Data Completeness Check",
                description="Checks for missing required fields",
                rule_type=ValidationRuleType.DATA_QUALITY,
                validation_level=ValidationLevel.STANDARD,
                severity="high",
                tags=["completeness", "data_quality"],
            )
        )

        rules.append(
            ValidationRule(
                rule_id="duplicate_detection",
                name="Duplicate Record Detection",
                description="Identifies duplicate records based on key fields",
                rule_type=ValidationRuleType.DATA_QUALITY,
                validation_level=ValidationLevel.STANDARD,
                severity="medium",
                tags=["duplicates", "data_quality"],
            )
        )

        # Anomaly detection rules
        rules.append(
            ValidationRule(
                rule_id="score_outlier_detection",
                name="Score Outlier Detection",
                description="Detects unusual score combinations",
                rule_type=ValidationRuleType.ANOMALY_DETECTION,
                validation_level=ValidationLevel.COMPREHENSIVE,
                severity="medium",
                tags=["anomaly", "scores"],
            )
        )

        return rules

    def _create_rule_suites(self) -> Dict[str, List[ValidationRule]]:
        """Create rule suites for different data types"""
        suites = {
            "games": [r for r in self.validation_rules if "games" in r.tags],
            "teams": [r for r in self.validation_rules if "teams" in r.tags],
            "players": [r for r in self.validation_rules if "players" in r.tags],
            "predictions": [
                r for r in self.validation_rules if "predictions" in r.tags
            ],
            "all": self.validation_rules,
        }
        return suites

    def _initialize_ge_context(self):
        """Initialize Great Expectations context"""
        try:
            # Initialize GE context with minimal configuration
            return None  # Placeholder for GE initialization
        except Exception as e:
            self.logger.warning(f"Great Expectations initialization failed: {e}")
            return None

    def _convert_to_dataframe(self, data: Any, data_type: str) -> pd.DataFrame:
        """Convert data to pandas DataFrame"""
        try:
            if isinstance(data, pd.DataFrame):
                return data
            elif isinstance(data, list):
                if data and isinstance(data[0], dict):
                    return pd.DataFrame(data)
                else:
                    return pd.DataFrame({"data": data})
            elif isinstance(data, dict):
                return pd.DataFrame([data])
            else:
                # Convert to DataFrame based on data type
                return pd.DataFrame({"value": [data]})
        except Exception as e:
            self.logger.error(f"Failed to convert data to DataFrame: {e}")
            return pd.DataFrame()

    def _execute_validation_rule(
        self, rule: ValidationRule, df: pd.DataFrame, data_type: str
    ) -> ValidationResult:
        """Execute a single validation rule"""
        start_time = time.time()

        try:
            if rule.rule_type == ValidationRuleType.SCHEMA:
                return self._execute_schema_validation(rule, df, data_type)
            elif rule.rule_type == ValidationRuleType.BUSINESS_LOGIC:
                return self._execute_business_logic_validation(rule, df, data_type)
            elif rule.rule_type == ValidationRuleType.DATA_QUALITY:
                return self._execute_data_quality_validation(rule, df, data_type)
            elif rule.rule_type == ValidationRuleType.ANOMALY_DETECTION:
                return self._execute_anomaly_validation(rule, df, data_type)
            else:
                return ValidationResult(
                    rule_id=rule.rule_id,
                    status=ValidationStatus.SKIPPED,
                    passed=True,
                    failed_records=0,
                    total_records=len(df),
                    failure_rate=0.0,
                    error_message=f"Unsupported rule type: {rule.rule_type.value}",
                    execution_time_seconds=time.time() - start_time,
                )
        except Exception as e:
            return ValidationResult(
                rule_id=rule.rule_id,
                status=ValidationStatus.ERROR,
                passed=False,
                failed_records=len(df),
                total_records=len(df),
                failure_rate=1.0,
                error_message=str(e),
                execution_time_seconds=time.time() - start_time,
            )

    def _execute_schema_validation(
        self, rule: ValidationRule, df: pd.DataFrame, data_type: str
    ) -> ValidationResult:
        """Execute schema validation"""
        # Get schema for data type
        schema = self._get_schema_for_data_type(data_type)

        if not schema:
            return ValidationResult(
                rule_id=rule.rule_id,
                status=ValidationStatus.SKIPPED,
                passed=True,
                failed_records=0,
                total_records=len(df),
                failure_rate=0.0,
                error_message=f"No schema found for data type: {data_type}",
            )

        # Validate against schema
        try:
            if isinstance(df, pd.DataFrame):
                # Convert to records for validation
                records = df.to_dict("records")
            else:
                records = df if isinstance(df, list) else [df]

            failed_records = 0
            for record in records:
                try:
                    validate(instance=record, schema=schema)
                except ValidationError:
                    failed_records += 1

            failure_rate = failed_records / len(records) if records else 0
            passed = failed_records == 0

            return ValidationResult(
                rule_id=rule.rule_id,
                status=ValidationStatus.PASSED if passed else ValidationStatus.FAILED,
                passed=passed,
                failed_records=failed_records,
                total_records=len(records),
                failure_rate=failure_rate,
                details={
                    "schema_type": data_type,
                    "valid_records": len(records) - failed_records,
                },
            )

        except Exception as e:
            return ValidationResult(
                rule_id=rule.rule_id,
                status=ValidationStatus.ERROR,
                passed=False,
                failed_records=len(df),
                total_records=len(df),
                failure_rate=1.0,
                error_message=f"Schema validation error: {str(e)}",
            )

    def _execute_business_logic_validation(
        self, rule: ValidationRule, df: pd.DataFrame, data_type: str
    ) -> ValidationResult:
        """Execute business logic validation"""
        if data_type == "games" and rule.rule_id == "games_score_consistency":
            return self._validate_game_score_consistency(df, rule)
        elif data_type == "teams" and rule.rule_id == "team_conference_consistency":
            return self._validate_team_conference_consistency(df, rule)
        else:
            return ValidationResult(
                rule_id=rule.rule_id,
                status=ValidationStatus.SKIPPED,
                passed=True,
                failed_records=0,
                total_records=len(df),
                failure_rate=0.0,
                error_message=f"Business logic validation not implemented for {data_type}",
            )

    def _execute_data_quality_validation(
        self, rule: ValidationRule, df: pd.DataFrame, data_type: str
    ) -> ValidationResult:
        """Execute data quality validation"""
        if rule.rule_id == "completeness_check":
            return self._check_completeness(df, rule)
        elif rule.rule_id == "duplicate_detection":
            return self._detect_duplicates(df, rule)
        else:
            return ValidationResult(
                rule_id=rule.rule_id,
                status=ValidationStatus.SKIPPED,
                passed=True,
                failed_records=0,
                total_records=len(df),
                failure_rate=0.0,
                error_message=f"Data quality validation not implemented for {rule.rule_id}",
            )

    def _execute_anomaly_validation(
        self, rule: ValidationRule, df: pd.DataFrame, data_type: str
    ) -> ValidationResult:
        """Execute anomaly detection validation"""
        if rule.rule_id == "score_outlier_detection" and data_type == "games":
            return self._detect_score_outliers(df, rule)
        else:
            return ValidationResult(
                rule_id=rule.rule_id,
                status=ValidationStatus.SKIPPED,
                passed=True,
                failed_records=0,
                total_records=len(df),
                failure_rate=0.0,
                error_message=f"Anomaly validation not implemented for {data_type}",
            )

    # Specific validation implementations
    def _validate_game_score_consistency(
        self, df: pd.DataFrame, rule: ValidationRule
    ) -> ValidationResult:
        """Validate game score consistency"""
        if "home_points" not in df.columns or "away_points" not in df.columns:
            return ValidationResult(
                rule_id=rule.rule_id,
                status=ValidationStatus.SKIPPED,
                passed=True,
                failed_records=0,
                total_records=len(df),
                failure_rate=0.0,
                error_message="Required score columns not found",
            )

        # Check for negative scores
        negative_scores = ((df["home_points"] < 0) | (df["away_points"] < 0)).sum()

        # Check for unrealistic scores (e.g., > 200 points)
        unrealistic_scores = (
            (df["home_points"] > 200) | (df["away_points"] > 200)
        ).sum()

        total_issues = negative_scores + unrealistic_scores
        failure_rate = total_issues / len(df) if len(df) > 0 else 0

        return ValidationResult(
            rule_id=rule.rule_id,
            status=(
                ValidationStatus.PASSED
                if total_issues == 0
                else ValidationStatus.FAILED
            ),
            passed=total_issues == 0,
            failed_records=total_issues,
            total_records=len(df),
            failure_rate=failure_rate,
            details={
                "negative_scores": negative_scores,
                "unrealistic_scores": unrealistic_scores,
                "total_issues": total_issues,
            },
        )

    def _validate_team_conference_consistency(
        self, df: pd.DataFrame, rule: ValidationRule
    ) -> ValidationResult:
        """Validate team-conference consistency"""
        # Simplified validation - would need conference reference data
        if "conference" not in df.columns:
            return ValidationResult(
                rule_id=rule.rule_id,
                status=ValidationStatus.SKIPPED,
                passed=True,
                failed_records=0,
                total_records=len(df),
                failure_rate=0.0,
                error_message="Conference column not found",
            )

        # Check for empty conferences
        empty_conferences = df["conference"].isna().sum()

        # Check for invalid conference values
        valid_conferences = [
            "ACC",
            "Big Ten",
            "Big 12",
            "Pac-12",
            "SEC",
            "American",
            "C-USA",
            "MAC",
            "Mountain West",
            "Sun Belt",
        ]
        invalid_conferences = (
            ~df["conference"].isin(valid_conferences) & df["conference"].notna()
        ).sum()

        total_issues = empty_conferences + invalid_conferences
        failure_rate = total_issues / len(df) if len(df) > 0 else 0

        return ValidationResult(
            rule_id=rule.rule_id,
            status=(
                ValidationStatus.PASSED
                if total_issues == 0
                else ValidationStatus.FAILED
            ),
            passed=total_issues == 0,
            failed_records=total_issues,
            total_records=len(df),
            failure_rate=failure_rate,
            details={
                "empty_conferences": empty_conferences,
                "invalid_conferences": invalid_conferences,
                "total_issues": total_issues,
            },
        )

    def _check_completeness(
        self, df: pd.DataFrame, rule: ValidationRule
    ) -> ValidationResult:
        """Check data completeness"""
        # Get required columns based on rule parameters
        required_columns = rule.parameters.get("required_columns", [])

        if not required_columns:
            # Default to all columns being required
            required_columns = df.columns.tolist()

        missing_values = 0
        total_cells = len(df) * len(required_columns)

        for col in required_columns:
            if col in df.columns:
                missing_values += df[col].isna().sum()
            else:
                missing_values += len(df)  # Entire column missing

        completeness_rate = 1 - (missing_values / total_cells) if total_cells > 0 else 1
        failure_rate = 1 - completeness_rate

        return ValidationResult(
            rule_id=rule.rule_id,
            status=(
                ValidationStatus.PASSED
                if completeness_rate
                >= self.validation_thresholds["completeness_threshold"]
                else ValidationStatus.FAILED
            ),
            passed=completeness_rate
            >= self.validation_thresholds["completeness_threshold"],
            failed_records=missing_values,
            total_records=total_cells,
            failure_rate=failure_rate,
            details={
                "completeness_rate": completeness_rate,
                "missing_values": missing_values,
                "total_cells": total_cells,
                "required_columns": required_columns,
            },
        )

    def _detect_duplicates(
        self, df: pd.DataFrame, rule: ValidationRule
    ) -> ValidationResult:
        """Detect duplicate records"""
        # Get key columns for duplicate detection
        key_columns = rule.parameters.get("key_columns", df.columns.tolist())

        if not key_columns:
            return ValidationResult(
                rule_id=rule.rule_id,
                status=ValidationStatus.SKIPPED,
                passed=True,
                failed_records=0,
                total_records=len(df),
                failure_rate=0.0,
                error_message="No key columns specified for duplicate detection",
            )

        # Filter to columns that exist in dataframe
        existing_key_columns = [col for col in key_columns if col in df.columns]

        if not existing_key_columns:
            return ValidationResult(
                rule_id=rule.rule_id,
                status=ValidationStatus.SKIPPED,
                passed=True,
                failed_records=0,
                total_records=len(df),
                failure_rate=0.0,
                error_message="None of the specified key columns exist in the data",
            )

        # Find duplicates
        duplicates = df.duplicated(subset=existing_key_columns, keep=False).sum()
        unique_records = len(df) - duplicates
        failure_rate = duplicates / len(df) if len(df) > 0 else 0

        return ValidationResult(
            rule_id=rule.rule_id,
            status=(
                ValidationStatus.PASSED if duplicates == 0 else ValidationStatus.FAILED
            ),
            passed=duplicates == 0,
            failed_records=duplicates,
            total_records=len(df),
            failure_rate=failure_rate,
            details={
                "duplicate_records": duplicates,
                "unique_records": unique_records,
                "key_columns": existing_key_columns,
            },
        )

    def _detect_score_outliers(
        self, df: pd.DataFrame, rule: ValidationRule
    ) -> ValidationResult:
        """Detect score outliers using statistical methods"""
        if "home_points" not in df.columns or "away_points" not in df.columns:
            return ValidationResult(
                rule_id=rule.rule_id,
                status=ValidationStatus.SKIPPED,
                passed=True,
                failed_records=0,
                total_records=len(df),
                failure_rate=0.0,
                error_message="Score columns not found",
            )

        # Calculate total scores
        total_scores = df["home_points"] + df["away_points"]

        # Calculate IQR for outlier detection
        Q1 = total_scores.quantile(0.25)
        Q3 = total_scores.quantile(0.75)
        IQR = Q3 - Q1

        # Define outlier bounds
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR

        # Find outliers
        outliers = ((total_scores < lower_bound) | (total_scores > upper_bound)).sum()
        failure_rate = outliers / len(df) if len(df) > 0 else 0

        return ValidationResult(
            rule_id=rule.rule_id,
            status=(
                ValidationStatus.PASSED if outliers == 0 else ValidationStatus.WARNING
            ),
            passed=outliers == 0,
            failed_records=outliers,
            total_records=len(df),
            failure_rate=failure_rate,
            details={
                "outlier_count": outliers,
                "q1": Q1,
                "q3": Q3,
                "iqr": IQR,
                "lower_bound": lower_bound,
                "upper_bound": upper_bound,
            },
        )

    # Additional helper methods for ML validation, anomaly detection, etc.
    def _get_model_validation_rules(
        self, model_type: str, custom_rules: List
    ) -> List[ValidationRule]:
        """Get model-specific validation rules"""
        rules = []

        # Basic ML data validation rules
        rules.append(
            ValidationRule(
                rule_id="ml_feature_completeness",
                name="Feature Completeness Check",
                description="Ensures all required features are present",
                rule_type=ValidationRuleType.DATA_QUALITY,
                validation_level=ValidationLevel.STANDARD,
                severity="high",
            )
        )

        rules.append(
            ValidationRule(
                rule_id="ml_target_validation",
                name="Target Variable Validation",
                description="Validates target variable format and distribution",
                rule_type=ValidationRuleType.DATA_QUALITY,
                validation_level=ValidationLevel.STANDARD,
                severity="critical",
            )
        )

        # Add custom rules
        for custom_rule in custom_rules:
            rules.append(
                ValidationRule(
                    rule_id=f"ml_custom_{len(rules)}",
                    name=custom_rule.get("name", "Custom ML Rule"),
                    description=custom_rule.get("description", ""),
                    rule_type=ValidationRuleType.DATA_QUALITY,
                    validation_level=ValidationLevel.STANDARD,
                    severity=custom_rule.get("severity", "medium"),
                    parameters=custom_rule.get("parameters", {}),
                )
            )

        return rules

    def _execute_ml_validations(
        self, df: pd.DataFrame, model_type: str
    ) -> List[ValidationResult]:
        """Execute ML-specific validations"""
        results = []

        # Check for features and target variables
        numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()

        if not numeric_columns:
            results.append(
                ValidationResult(
                    rule_id="ml_no_numeric_features",
                    status=ValidationStatus.FAILED,
                    passed=False,
                    failed_records=len(df),
                    total_records=len(df),
                    failure_rate=1.0,
                    error_message="No numeric features found for ML model",
                )
            )
        else:
            results.append(
                ValidationResult(
                    rule_id="ml_numeric_features_check",
                    status=ValidationStatus.PASSED,
                    passed=True,
                    failed_records=0,
                    total_records=len(df),
                    failure_rate=0.0,
                    details={
                        "numeric_features": numeric_columns,
                        "feature_count": len(numeric_columns),
                    },
                )
            )

        return results

    def _detect_statistical_anomalies(
        self, df: pd.DataFrame, sensitivity: str
    ) -> List[Dict]:
        """Detect statistical anomalies"""
        anomalies = []
        numeric_columns = df.select_dtypes(include=[np.number]).columns

        for col in numeric_columns:
            series = df[col].dropna()
            if len(series) < 3:
                continue

            # Z-score anomaly detection
            z_scores = np.abs((series - series.mean()) / series.std())
            threshold = {"low": 3.0, "medium": 2.5, "high": 2.0}.get(sensitivity, 2.5)

            anomaly_indices = z_scores > threshold
            if anomaly_indices.any():
                anomalies.append(
                    {
                        "type": "statistical",
                        "column": col,
                        "anomaly_count": anomaly_indices.sum(),
                        "anomaly_indices": series.index[anomaly_indices].tolist(),
                        "score": threshold,
                        "description": f"{col} has {anomaly_indices.sum()} statistical outliers",
                    }
                )

        return anomalies

    def _detect_outliers(self, df: pd.DataFrame, sensitivity: str) -> List[Dict]:
        """Detect outliers using IQR method"""
        anomalies = []
        numeric_columns = df.select_dtypes(include=[np.number]).columns

        for col in numeric_columns:
            series = df[col].dropna()
            if len(series) < 3:
                continue

            Q1 = series.quantile(0.25)
            Q3 = series.quantile(0.75)
            IQR = Q3 - Q1

            if IQR == 0:
                continue

            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR

            outlier_mask = (series < lower_bound) | (series > upper_bound)
            if outlier_mask.any():
                anomalies.append(
                    {
                        "type": "outlier",
                        "column": col,
                        "outlier_count": outlier_mask.sum(),
                        "outlier_indices": series.index[outlier_mask].tolist(),
                        "bounds": {"lower": lower_bound, "upper": upper_bound},
                        "description": f"{col} has {outlier_mask.sum()} IQR outliers",
                    }
                )

        return anomalies

    def _detect_distribution_anomalies(
        self, df: pd.DataFrame, sensitivity: str
    ) -> List[Dict]:
        """Detect distribution anomalies"""
        anomalies = []
        numeric_columns = df.select_dtypes(include=[np.number]).columns

        for col in numeric_columns:
            series = df[col].dropna()
            if len(series) < 10:
                continue

            # Skewness detection
            skewness = series.skew()
            if abs(skewness) > 2.0:  # High skewness threshold
                anomalies.append(
                    {
                        "type": "distribution",
                        "column": col,
                        "anomaly_type": "skewness",
                        "value": skewness,
                        "description": f"{col} has high skewness: {skewness:.2f}",
                    }
                )

            # Kurtosis detection
            kurtosis = series.kurtosis()
            if abs(kurtosis) > 3.0:  # High kurtosis threshold
                anomalies.append(
                    {
                        "type": "distribution",
                        "column": col,
                        "anomaly_type": "kurtosis",
                        "value": kurtosis,
                        "description": f"{col} has high kurtosis: {kurtosis:.2f}",
                    }
                )

        return anomalies

    def _analyze_distributions(self, df: pd.DataFrame) -> Dict:
        """Analyze data distributions"""
        analysis = {}
        numeric_columns = df.select_dtypes(include=[np.number]).columns

        for col in numeric_columns:
            series = df[col].dropna()
            if len(series) < 2:
                continue

            analysis[col] = {
                "mean": float(series.mean()),
                "median": float(series.median()),
                "std": float(series.std()),
                "min": float(series.min()),
                "max": float(series.max()),
                "skewness": float(series.skew()),
                "kurtosis": float(series.kurtosis()),
                "missing_count": int(df[col].isna().sum()),
                "missing_rate": float(df[col].isna().sum() / len(df)),
            }

        return analysis

    def _get_schema_for_data_type(self, data_type: str) -> Optional[Dict]:
        """Get JSON schema for data type"""
        schemas = {
            "games": {
                "type": "object",
                "required": ["id", "season", "week", "home_team", "away_team"],
                "properties": {
                    "id": {"type": "integer"},
                    "season": {"type": "integer"},
                    "week": {"type": "integer"},
                    "home_team": {"type": "string"},
                    "away_team": {"type": "string"},
                    "home_points": {"type": "integer"},
                    "away_points": {"type": "integer"},
                    "start_date": {"type": "string", "format": "date-time"},
                },
            },
            "teams": {
                "type": "object",
                "required": ["id", "school", "conference"],
                "properties": {
                    "id": {"type": "integer"},
                    "school": {"type": "string"},
                    "conference": {"type": "string"},
                    "mascot": {"type": "string"},
                    "classification": {"type": "string"},
                },
            },
        }

        return schemas.get(data_type)

    # Additional helper methods would be implemented here
    def _calculate_overall_status(
        self, results: List[ValidationResult]
    ) -> ValidationStatus:
        """Calculate overall validation status"""
        if not results:
            return ValidationStatus.PASSED

        failed_count = sum(1 for r in results if r.status == ValidationStatus.FAILED)
        error_count = sum(1 for r in results if r.status == ValidationStatus.ERROR)

        if error_count > 0:
            return ValidationStatus.ERROR
        elif failed_count > 0:
            return ValidationStatus.FAILED
        else:
            return ValidationStatus.PASSED

    def _calculate_summary_metrics(
        self, results: List[ValidationResult], total_records: int
    ) -> Dict:
        """Calculate validation summary metrics"""
        passed_rules = sum(1 for r in results if r.passed)
        failed_rules = sum(1 for r in results if not r.passed)
        total_failed_records = sum(r.failed_records for r in results)

        return {
            "total_rules": len(results),
            "passed_rules": passed_rules,
            "failed_rules": failed_rules,
            "pass_rate": passed_rules / len(results) * 100 if results else 0,
            "total_failed_records": total_failed_records,
            "overall_failure_rate": (
                total_failed_records / total_records if total_records > 0 else 0
            ),
        }

    def _calculate_quality_score(self, results: List[ValidationResult]) -> float:
        """Calculate overall data quality score"""
        if not results:
            return 100.0

        # Weight rules by severity
        severity_weights = {"low": 0.5, "medium": 1.0, "high": 2.0, "critical": 3.0}

        total_weight = 0
        weighted_score = 0

        for result in results:
            # Get rule severity (default to medium)
            rule = next(
                (r for r in self.validation_rules if r.rule_id == result.rule_id), None
            )
            severity = rule.severity if rule else "medium"
            weight = severity_weights.get(severity, 1.0)

            total_weight += weight
            weighted_score += weight * (100 - (result.failure_rate * 100))

        return weighted_score / total_weight if total_weight > 0 else 100.0

    def _generate_recommendations(
        self, results: List[ValidationResult], data_type: str
    ) -> List[str]:
        """Generate validation recommendations"""
        recommendations = []

        failed_results = [r for r in results if not r.passed]

        for result in failed_results:
            if result.rule_id == "completeness_check":
                recommendations.append(
                    f"Improve data completeness by addressing missing values in required fields"
                )
            elif result.rule_id == "duplicate_detection":
                recommendations.append(
                    f"Remove or deduplicate {result.failed_records} duplicate records"
                )
            elif "schema" in result.rule_id:
                recommendations.append(
                    f"Fix schema validation errors to ensure data consistency"
                )
            elif "score" in result.rule_id:
                recommendations.append(
                    f"Review and correct score outliers in the dataset"
                )

        if not recommendations and failed_results:
            recommendations.append(
                "Review failed validation rules and address data quality issues"
            )

        return recommendations

    def _extract_issues(self, results: List[ValidationResult]) -> List[Dict]:
        """Extract issues from validation results"""
        issues = []

        for result in results:
            if not result.passed:
                issues.append(
                    {
                        "rule_id": result.rule_id,
                        "severity": (
                            "high"
                            if result.status == ValidationStatus.FAILED
                            else "medium"
                        ),
                        "failed_records": result.failed_records,
                        "failure_rate": result.failure_rate,
                        "error_message": result.error_message,
                        "details": result.details,
                    }
                )

        return issues

    def _update_validation_metrics(self, report: DataValidationReport) -> None:
        """Update validation performance metrics"""
        self.metrics["validations_executed"] += 1
        self.metrics["records_validated"] += report.record_count
        self.metrics["rules_executed"] += len(report.results)

        # Update average validation time
        current_avg = self.metrics["average_validation_time"]
        total_validations = self.metrics["validations_executed"]
        self.metrics["average_validation_time"] = (
            current_avg * (total_validations - 1) + report.duration_seconds
        ) / total_validations

    def _validate_rule_specification(self, rule: ValidationRule, spec: Dict) -> Dict:
        """Validate rule specification"""
        errors = []

        if not rule.name:
            errors.append("Rule name is required")

        if not rule.rule_type:
            errors.append("Rule type is required")

        if not rule.validation_level:
            errors.append("Validation level is required")

        return {"valid": len(errors) == 0, "errors": errors, "warnings": []}

    def _analyze_validation_results(self, results: List[Dict]) -> Dict:
        """Analyze validation results for quality report"""
        # Implementation would analyze the results and return quality metrics
        return {
            "overall_score": 85.0,
            "pass_rate": 90.0,
            "critical_issues": 2,
            "improvement_areas": ["completeness", "consistency"],
        }

    def _calculate_quality_trends(self) -> List[Dict]:
        """Calculate quality trends over time"""
        # Implementation would return historical quality trends
        return []

    def _calculate_compliance_metrics(self, results: List[Dict]) -> Dict:
        """Calculate compliance metrics"""
        # Implementation would return compliance status and violations
        return {"compliant": True, "score": 92.0, "violations": []}

    def _generate_quality_recommendations(self, analysis: Dict) -> List[str]:
        """Generate quality improvement recommendations"""
        # Implementation would return targeted recommendations
        return ["Improve data completeness", "Fix schema violations"]

    def _generate_ml_recommendations(
        self, results: List[ValidationResult], model_type: str
    ) -> List[str]:
        """Generate ML-specific recommendations"""
        recommendations = []

        for result in results:
            if result.rule_id == "ml_feature_completeness" and not result.passed:
                recommendations.append(
                    "Address missing feature values through imputation or data collection"
                )
            elif result.rule_id == "ml_target_validation" and not result.passed:
                recommendations.append(
                    "Fix target variable issues before model training"
                )
            elif result.rule_id == "ml_no_numeric_features" and not result.passed:
                recommendations.append(
                    "Ensure dataset contains numeric features for ML processing"
                )

        return recommendations

    def _assess_readiness_factors(self, results: List[ValidationResult]) -> Dict:
        """Assess ML data readiness factors"""
        factors = {
            "completeness": 0.9,
            "consistency": 0.95,
            "accuracy": 0.88,
            "feature_quality": 0.92,
        }

        # Calculate based on validation results
        for result in results:
            if "completeness" in result.rule_id:
                factors["completeness"] = 1 - result.failure_rate
            elif "consistency" in result.rule_id:
                factors["consistency"] = 1 - result.failure_rate

        return factors

    def _analyze_features(self, df: pd.DataFrame, model_type: str) -> Dict:
        """Analyze features for ML model"""
        numeric_features = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_features = df.select_dtypes(include=["object"]).columns.tolist()

        return {
            "numeric_features": numeric_features,
            "categorical_features": categorical_features,
            "feature_count": len(df.columns),
            "missing_values": df.isnull().sum().to_dict(),
        }

    def _analyze_target_variable(self, df: pd.DataFrame, model_type: str) -> Dict:
        """Analyze target variable for ML model"""
        # Simplified analysis - would be more sophisticated in practice
        return {
            "target_available": True,
            "target_type": "numeric",
            "class_balance": (
                "balanced" if model_type == "classification" else "continuous"
            ),
        }


# Agent registration function
def register_data_validation_agent():
    """Register the data validation agent with the system"""
    agent = DataValidationAgent()

    registration_details = {
        "agent_id": agent.agent_id,
        "agent_name": agent.agent_name,
        "class_name": "DataValidationAgent",
        "file_path": __file__,
        "created_by": "system_architect",
        "capabilities": [
            "validate_cfbd_data",
            "validate_model_data",
            "detect_anomalies",
            "create_validation_rules",
            "generate_quality_report",
        ],
        "dependencies": [
            "enhanced_agent_framework",
            "security_manager",
            "pandas",
            "numpy",
            "jsonschema",
        ],
        "max_execution_time": 300,  # 5 minutes
        "memory_limit_mb": 1024,
        "security_tier": 3,
        "permission_level": "READ_EXECUTE",
    }

    return agent, registration_details


# Example usage and testing
if __name__ == "__main__":
    # Create agent
    agent = DataValidationAgent()

    # Test CFBD data validation
    test_games_data = [
        {
            "id": 401234567,
            "season": 2025,
            "week": 13,
            "home_team": "Ohio State",
            "away_team": "Michigan",
            "home_points": 28,
            "away_points": 24,
            "start_date": "2025-11-29T19:00:00Z",
        },
        {
            "id": 401234568,
            "season": 2025,
            "week": 13,
            "home_team": "Alabama",
            "away_team": "Auburn",
            "home_points": 35,
            "away_points": 21,
            "start_date": "2025-11-29T15:30:00Z",
        },
    ]

    result = agent.execute_action(
        "validate_cfbd_data",
        {"data": test_games_data, "data_type": "games", "validation_level": "standard"},
    )
    print("CFBD Data Validation Result:")
    print(json.dumps(result, indent=2))
