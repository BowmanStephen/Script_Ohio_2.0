"""
Audit Coordinator Agent - orchestrates comprehensive system audits.
Coordinates multiple audit agents and generates consolidated reports.
"""

import time
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from agents.core.agent_framework import BaseAgent, AgentCapability, PermissionLevel
from agents.audit.core_audit_contracts import (
    AuditReport, AuditCheck, AuditStatus, EvidenceType, AuditContract
)
from agents.audit.reporting_engine import AuditReportingEngine
from agents.audit.system_integrity_agent import SystemIntegrityAuditAgent
from agents.audit.data_pipeline_audit_agent import DataPipelineAuditAgent
from agents.audit.model_validation_audit_agent import ModelValidationAuditAgent

class AuditCoordinatorAgent(BaseAgent):
    """Master coordinator for comprehensive system audits."""

    def __init__(self, agent_id: str = "audit_coordinator_agent"):
        super().__init__(
            agent_id,
            "Audit Coordinator Agent",
            PermissionLevel.READ_EXECUTE_WRITE  # Needs higher permissions to coordinate other agents
        )

        # Initialize specialized audit agents
        self.system_integrity_agent = SystemIntegrityAuditAgent()
        self.data_pipeline_agent = DataPipelineAuditAgent()
        self.model_validation_agent = ModelValidationAuditAgent()
        self.reporting_engine = AuditReportingEngine()

    def _define_capabilities(self) -> List[AgentCapability]:
        """Define coordinator capabilities."""
        return [
            AgentCapability(
                name="run_comprehensive_audit",
                description="Execute complete system audit across all domains",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=["python3", "audit_agents", "reporting_engine"],
                data_access=["all_system_components", "audit_results"],
                execution_time_estimate=300.0  # 5 minutes for comprehensive audit
            ),
            AgentCapability(
                name="run_quick_audit",
                description="Execute quick audit focusing on critical components",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=["python3", "audit_agents"],
                data_access=["critical_system_components"],
                execution_time_estimate=120.0  # 2 minutes for quick audit
            ),
            AgentCapability(
                name="generate_audit_reports",
                description="Generate multi-format audit reports",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["reporting_engine", "file_system"],
                data_access=["audit_data", "report_templates"],
                execution_time_estimate=60.0  # 1 minute for report generation
            ),
            AgentCapability(
                name="audit_specific_domain",
                description="Audit specific system domain (system, data, models)",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=["python3", "domain_agents"],
                data_access=["domain_specific_components"],
                execution_time_estimate=180.0  # 3 minutes for domain-specific audit
            )
        ]

    def _execute_action(self, action: str, parameters: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute audit coordination action."""

        if action == "run_comprehensive_audit":
            return self._run_comprehensive_audit(parameters, user_context)
        elif action == "run_quick_audit":
            return self._run_quick_audit(parameters, user_context)
        elif action == "generate_audit_reports":
            return self._generate_audit_reports(parameters, user_context)
        elif action == "audit_specific_domain":
            return self._audit_specific_domain(parameters, user_context)
        else:
            return {"error": f"Unknown action: {action}"}

    def _run_comprehensive_audit(self, parameters: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Run comprehensive audit across all system domains."""

        audit_start_time = datetime.now()
        audit_name = parameters.get("audit_name", f"Comprehensive System Audit {audit_start_time.strftime('%Y-%m-%d %H:%M:%S')}")

        # Initialize comprehensive audit report
        audit_report = AuditReport(
            audit_name=audit_name,
            start_time=audit_start_time.isoformat()
        )

        all_checks = []
        agent_results = {}

        try:
            # Phase 1: System Integrity Audit
            print("🔍 Starting System Integrity Audit...")
            system_start = time.time()

            system_checks = []

            # Python Environment
            env_result = self.system_integrity_agent._audit_python_environment({}, {})
            system_checks.extend(env_result.get("checks", []))

            # File Structure
            structure_result = self.system_integrity_agent._audit_file_structure({}, {})
            system_checks.extend(structure_result.get("checks", []))

            # Permissions
            perm_result = self.system_integrity_agent._audit_permissions({}, {})
            system_checks.extend(perm_result.get("checks", []))

            # System Resources
            resource_result = self.system_integrity_agent._audit_system_resources({}, {})
            system_checks.extend(resource_result.get("checks", []))

            agent_results["system_integrity"] = {
                "execution_time": round(time.time() - system_start, 2),
                "checks_completed": len(system_checks),
                "summary": env_result.get("summary", {})
            }

            for check_data in system_checks:
                # Reconstruct AuditCheck object from serialized data
                check = AuditCheck(
                    check_id=check_data.get("check_id", ""),
                    category=check_data["category"],
                    title=check_data["title"],
                    description=check_data.get("description", ""),
                    validation_command=check_data["validation_command"],
                    expected_pattern=check_data["expected_pattern"],
                    critical=check_data["critical"]
                )
                check.status = AuditStatus(check_data["status"])
                check.score = check_data["score"]
                audit_report.add_check(check)
                all_checks.append(check)

            print(f"✅ System Integrity Audit completed - {len(system_checks)} checks")

            # Phase 2: Data Pipeline Audit
            print("🔍 Starting Data Pipeline Audit...")
            data_start = time.time()

            data_checks = []

            # CFBD Integration
            cfbd_result = self.data_pipeline_agent._audit_cfbd_integration({}, {})
            data_checks.extend(cfbd_result.get("checks", []))

            # Training Data
            training_result = self.data_pipeline_agent._audit_training_data({}, {})
            data_checks.extend(training_result.get("checks", []))

            # Feature Engineering
            feature_result = self.data_pipeline_agent._audit_feature_engineering({}, {})
            data_checks.extend(feature_result.get("checks", []))

            # Data Quality
            quality_result = self.data_pipeline_agent._audit_data_quality({}, {})
            data_checks.extend(quality_result.get("checks", []))

            agent_results["data_pipeline"] = {
                "execution_time": round(time.time() - data_start, 2),
                "checks_completed": len(data_checks),
                "summary": cfbd_result.get("summary", {})
            }

            for check_data in data_checks:
                check = AuditCheck(
                    check_id=check_data["check_id"],
                    category=check_data["category"],
                    title=check_data["title"],
                    description=check_data.get("description", ""),
                    validation_command=check_data["validation_command"],
                    expected_pattern=check_data["expected_pattern"],
                    status=AuditStatus(check_data["status"]),
                    score=check_data["score"],
                    max_score=check_data["max_score"],
                    critical=check_data["critical"]
                )
                audit_report.add_check(check)
                all_checks.append(check)

            print(f"✅ Data Pipeline Audit completed - {len(data_checks)} checks")

            # Phase 3: Model Validation Audit
            print("🔍 Starting Model Validation Audit...")
            model_start = time.time()

            model_checks = []

            # Model Loading
            loading_result = self.model_validation_agent._audit_model_loading({}, {})
            model_checks.extend(loading_result.get("checks", []))

            # Model Predictions
            pred_result = self.model_validation_agent._audit_model_predictions({}, {})
            model_checks.extend(pred_result.get("checks", []))

            # Model Performance
            perf_result = self.model_validation_agent._audit_model_performance({}, {})
            model_checks.extend(perf_result.get("checks", []))

            # Ensemble Integration
            ensemble_result = self.model_validation_agent._audit_ensemble_integration({}, {})
            model_checks.extend(ensemble_result.get("checks", []))

            agent_results["model_validation"] = {
                "execution_time": round(time.time() - model_start, 2),
                "checks_completed": len(model_checks),
                "summary": loading_result.get("summary", {})
            }

            for check_data in model_checks:
                check = AuditCheck(
                    check_id=check_data["check_id"],
                    category=check_data["category"],
                    title=check_data["title"],
                    description=check_data.get("description", ""),
                    validation_command=check_data["validation_command"],
                    expected_pattern=check_data["expected_pattern"],
                    status=AuditStatus(check_data["status"]),
                    score=check_data["score"],
                    max_score=check_data["max_score"],
                    critical=check_data["critical"]
                )
                audit_report.add_check(check)
                all_checks.append(check)

            print(f"✅ Model Validation Audit completed - {len(model_checks)} checks")

            # Finalize audit report
            audit_report.finalize_report()

            # Generate recommendations based on failed checks
            audit_report.recommendations = self._generate_recommendations(all_checks)

            # Add system information
            audit_report.system_info = {
                "audit_coordinator_version": "1.0.0",
                "agents_used": ["system_integrity_agent", "data_pipeline_agent", "model_validation_agent"],
                "total_execution_time": time.time() - system_start,
                "environment": {
                    "python_version": "3.13+",
                    "platform": "comprehensive"
                }
            }

            print(f"🎉 Comprehensive Audit completed!")
            print(f"   Total Checks: {audit_report.total_checks}")
            print(f"   Overall Score: {audit_report.overall_score:.1f}%")
            print(f"   Status: {audit_report.overall_status.value}")
            print(f"   Critical Failures: {audit_report.critical_failures}")

            execution_time = round(time.time() - system_start, 2)
            return {
                "agent_id": self.agent_id,
                "action": "run_comprehensive_audit",
                "audit_id": audit_report.audit_id,
                "audit_name": audit_report.audit_name,
                "execution_time": execution_time,
                "audit_summary": {
                    "total_checks": audit_report.total_checks,
                    "passed_checks": audit_report.passed_checks,
                    "failed_checks": audit_report.failed_checks,
                    "warning_checks": audit_report.warning_checks,
                    "critical_failures": audit_report.critical_failures,
                    "overall_score": audit_report.overall_score,
                    "overall_status": audit_report.overall_status.value
                },
                "agent_results": agent_results,
                "recommendations": audit_report.recommendations,
                "audit_report": audit_report  # Full audit report object for report generation
            }

        except Exception as e:
            error_msg = f"Comprehensive audit failed: {str(e)}"
            print(f"❌ {error_msg}")

            return {
                "agent_id": self.agent_id,
                "action": "run_comprehensive_audit",
                "error": error_msg,
                "partial_results": agent_results,
                "execution_time": round(time.time() - system_start, 2) if 'system_start' in locals() else 0.0
            }

    def _run_quick_audit(self, parameters: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Run quick audit focusing on critical components only."""

        audit_start_time = datetime.now()
        audit_name = parameters.get("audit_name", f"Quick System Audit {audit_start_time.strftime('%Y-%m-%d %H:%M:%S')}")

        audit_report = AuditReport(
            audit_name=audit_name,
            start_time=audit_start_time.isoformat()
        )

        all_checks = []

        try:
            print("⚡ Starting Quick Audit (Critical Components Only)...")

            # Track execution start time
            quick_start = time.time()

            # Critical System Integrity Checks
            system_checks = []

            # Python Environment (critical)
            env_result = self.system_integrity_agent._audit_python_environment({}, {})
            critical_env_checks = [check for check in env_result.get("checks", []) if check.get("critical", False)]
            system_checks.extend(critical_env_checks)

            # File Structure (critical)
            structure_result = self.system_integrity_agent._audit_file_structure({}, {})
            critical_structure_checks = [check for check in structure_result.get("checks", []) if check.get("critical", False)]
            system_checks.extend(critical_structure_checks)

            # Add to audit report
            for check_data in system_checks:
                check = AuditCheck(
                    check_id=check_data["check_id"],
                    category=check_data["category"],
                    title=check_data["title"],
                    description=check_data.get("description", ""),
                    validation_command=check_data["validation_command"],
                    expected_pattern=check_data["expected_pattern"],
                    status=AuditStatus(check_data["status"]),
                    score=check_data["score"],
                    max_score=check_data["max_score"],
                    critical=check_data["critical"]
                )
                audit_report.add_check(check)
                all_checks.append(check)

            # Critical Data Pipeline Checks
            data_checks = []

            # CFBD Integration (critical)
            cfbd_result = self.data_pipeline_agent._audit_cfbd_integration({}, {})
            critical_cfbd_checks = [check for check in cfbd_result.get("checks", []) if check.get("critical", False)]
            data_checks.extend(critical_cfbd_checks)

            # Training Data (critical)
            training_result = self.data_pipeline_agent._audit_training_data({}, {})
            critical_training_checks = [check for check in training_result.get("checks", []) if check.get("critical", False)]
            data_checks.extend(critical_training_checks)

            # Add to audit report
            for check_data in data_checks:
                check = AuditCheck(
                    check_id=check_data["check_id"],
                    category=check_data["category"],
                    title=check_data["title"],
                    description=check_data.get("description", ""),
                    validation_command=check_data["validation_command"],
                    expected_pattern=check_data["expected_pattern"],
                    status=AuditStatus(check_data["status"]),
                    score=check_data["score"],
                    max_score=check_data["max_score"],
                    critical=check_data["critical"]
                )
                audit_report.add_check(check)
                all_checks.append(check)

            # Critical Model Validation Checks
            model_checks = []

            # Model Loading (critical)
            loading_result = self.model_validation_agent._audit_model_loading({}, {})
            critical_loading_checks = [check for check in loading_result.get("checks", []) if check.get("critical", False)]
            model_checks.extend(critical_loading_checks)

            # Add to audit report
            for check_data in model_checks:
                check = AuditCheck(
                    check_id=check_data["check_id"],
                    category=check_data["category"],
                    title=check_data["title"],
                    description=check_data.get("description", ""),
                    validation_command=check_data["validation_command"],
                    expected_pattern=check_data["expected_pattern"],
                    status=AuditStatus(check_data["status"]),
                    score=check_data["score"],
                    max_score=check_data["max_score"],
                    critical=check_data["critical"]
                )
                audit_report.add_check(check)
                all_checks.append(check)

            # Finalize quick audit
            audit_report.finalize_report()
            audit_report.recommendations = self._generate_recommendations(all_checks)

            # Calculate execution time properly
            execution_time = round(time.time() - quick_start, 2)

            print(f"⚡ Quick Audit completed!")
            print(f"   Critical Checks: {audit_report.total_checks}")
            print(f"   Overall Score: {audit_report.overall_score:.1f}%")
            print(f"   Status: {audit_report.overall_status.value}")
            print(f"   Execution Time: {execution_time:.1f}s")

            return {
                "agent_id": self.agent_id,
                "action": "run_quick_audit",
                "audit_id": audit_report.audit_id,
                "audit_name": audit_report.audit_name,
                "execution_time": execution_time,
                "audit_summary": {
                    "total_checks": audit_report.total_checks,
                    "passed_checks": audit_report.passed_checks,
                    "failed_checks": audit_report.failed_checks,
                    "warning_checks": audit_report.warning_checks,
                    "critical_failures": audit_report.critical_failures,
                    "overall_score": audit_report.overall_score,
                    "overall_status": audit_report.overall_status.value
                },
                "recommendations": audit_report.recommendations,
                "audit_report": audit_report
            }

        except Exception as e:
            error_msg = f"Quick audit failed: {str(e)}"
            print(f"❌ {error_msg}")

            return {
                "agent_id": self.agent_id,
                "action": "run_quick_audit",
                "error": error_msg,
                "execution_time": time.time() - audit_start_time
            }

    def _generate_audit_reports(self, parameters: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate multi-format audit reports."""

        audit_report = parameters.get("audit_report")
        if not audit_report:
            return {
                "agent_id": self.agent_id,
                "action": "generate_audit_reports",
                "error": "No audit_report provided in parameters"
            }

        try:
            print("📊 Generating Audit Reports...")

            report_files = {}

            # Generate TOON format report
            toon_file = self.reporting_engine.generate_toon_report(audit_report)
            report_files["toon"] = toon_file
            print(f"   ✅ TOON report generated: {toon_file}")

            # Generate JSON format report
            json_file = self.reporting_engine.generate_json_report(audit_report)
            report_files["json"] = json_file
            print(f"   ✅ JSON report generated: {json_file}")

            # Generate HTML format report
            html_file = self.reporting_engine.generate_html_report(audit_report)
            report_files["html"] = html_file
            print(f"   ✅ HTML report generated: {html_file}")

            # Generate Dashboard data
            dashboard_file = self.reporting_engine.generate_dashboard_data(audit_report)
            report_files["dashboard"] = dashboard_file
            print(f"   ✅ Dashboard data generated: {dashboard_file}")

            print(f"🎉 All reports generated successfully!")

            return {
                "agent_id": self.agent_id,
                "action": "generate_audit_reports",
                "audit_id": audit_report.audit_id,
                "report_files": report_files,
                "total_reports": len(report_files),
                "generation_time": time.time()
            }

        except Exception as e:
            error_msg = f"Report generation failed: {str(e)}"
            print(f"❌ {error_msg}")

            return {
                "agent_id": self.agent_id,
                "action": "generate_audit_reports",
                "error": error_msg
            }

    def _generate_recommendations(self, checks: List[AuditCheck]) -> List[str]:
        """Generate recommendations based on audit results."""

        recommendations = []

        # Analyze failed critical checks
        critical_failures = [check for check in checks if check.status == AuditStatus.FAILED and check.critical]

        if critical_failures:
            recommendations.append("🚨 CRITICAL ISSUES REQUIRE IMMEDIATE ATTENTION:")
            for check in critical_failures:
                recommendations.append(f"  • Fix {check.title}: {check.description}")

        # Analyze failed non-critical checks
        non_critical_failures = [check for check in checks if check.status == AuditStatus.FAILED and not check.critical]

        if non_critical_failures:
            recommendations.append("⚠️ RECOMMENDED IMPROVEMENTS:")
            for check in non_critical_failures[:3]:  # Top 3 recommendations
                recommendations.append(f"  • Address {check.title}: {check.description}")
            if len(non_critical_failures) > 3:
                recommendations.append(f"  • Plus {len(non_critical_failures) - 3} additional non-critical issues")

        # Analyze warnings
        warnings = [check for check in checks if check.status == AuditStatus.WARNING]

        if warnings:
            recommendations.append("💡 OPTIMIZATION OPPORTUNITIES:")
            for check in warnings[:2]:  # Top 2 recommendations
                recommendations.append(f"  • Consider {check.title}: {check.description}")

        # General recommendations based on patterns
        if len(critical_failures) == 0 and len(non_critical_failures) == 0:
            recommendations.append("🎉 EXCELLENT: No critical issues found. System is operating optimally.")

        if len(checks) > 0:
            overall_score = sum(check.score for check in checks) / len(checks)
            if overall_score >= 95:
                recommendations.append("🏆 OUTSTANDING: System demonstrates exceptional quality and reliability.")
            elif overall_score >= 85:
                recommendations.append("✅ STRONG: System shows good performance with minor improvements possible.")
            elif overall_score >= 70:
                recommendations.append("📈 DEVELOPING: System has solid foundation but needs attention to several areas.")
            else:
                recommendations.append("🔧 NEEDS WORK: System requires significant improvements to meet standards.")

        return recommendations

    def _audit_specific_domain(self, parameters: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Audit a specific system domain (system, data, or models)."""

        domain = parameters.get("domain", "system")
        audit_start_time = datetime.now()
        audit_name = parameters.get("audit_name", f"Domain Audit - {domain.title()} {audit_start_time.strftime('%Y-%m-%d %H:%M:%S')}")

        audit_report = AuditReport(
            audit_name=audit_name,
            start_time=audit_start_time.isoformat()
        )

        all_checks = []
        agent_results = {}

        try:
            print(f"🎯 Starting Domain Audit for: {domain.upper()}")

            domain_start = time.time()

            if domain == "system":
                # Run all system integrity audits
                system_checks = []

                # Python Environment
                env_result = self.system_integrity_agent._audit_python_environment({}, {})
                system_checks.extend(env_result.get("checks", []))

                # File Structure
                structure_result = self.system_integrity_agent._audit_file_structure({}, {})
                system_checks.extend(structure_result.get("checks", []))

                # Permissions
                perm_result = self.system_integrity_agent._audit_permissions({}, {})
                system_checks.extend(perm_result.get("checks", []))

                # System Resources
                resource_result = self.system_integrity_agent._audit_system_resources({}, {})
                system_checks.extend(resource_result.get("checks", []))

                agent_results["system_integrity"] = {
                    "execution_time": round(time.time() - domain_start, 2),
                    "checks_completed": len(system_checks),
                    "summary": env_result.get("summary", {})
                }

                for check_data in system_checks:
                    check = AuditCheck(
                        check_id=check_data["check_id"],
                        category=check_data["category"],
                        title=check_data["title"],
                        description=check_data.get("description", ""),
                        validation_command=check_data["validation_command"],
                        expected_pattern=check_data["expected_pattern"],
                        status=AuditStatus(check_data["status"]),
                        score=check_data["score"],
                        max_score=check_data["max_score"],
                        critical=check_data["critical"]
                    )
                    audit_report.add_check(check)
                    all_checks.append(check)

                print(f"✅ System Domain Audit completed - {len(system_checks)} checks")

            elif domain == "data":
                # Run all data pipeline audits
                data_checks = []

                # CFBD Integration
                cfbd_result = self.data_pipeline_agent._audit_cfbd_integration({}, {})
                data_checks.extend(cfbd_result.get("checks", []))

                # Training Data
                training_result = self.data_pipeline_agent._audit_training_data({}, {})
                data_checks.extend(training_result.get("checks", []))

                # Feature Engineering
                feature_result = self.data_pipeline_agent._audit_feature_engineering({}, {})
                data_checks.extend(feature_result.get("checks", []))

                # Data Quality
                quality_result = self.data_pipeline_agent._audit_data_quality({}, {})
                data_checks.extend(quality_result.get("checks", []))

                agent_results["data_pipeline"] = {
                    "execution_time": round(time.time() - domain_start, 2),
                    "checks_completed": len(data_checks),
                    "summary": cfbd_result.get("summary", {})
                }

                for check_data in data_checks:
                    check = AuditCheck(
                        check_id=check_data["check_id"],
                        category=check_data["category"],
                        title=check_data["title"],
                        description=check_data.get("description", ""),
                        validation_command=check_data["validation_command"],
                        expected_pattern=check_data["expected_pattern"],
                        status=AuditStatus(check_data["status"]),
                        score=check_data["score"],
                        max_score=check_data["max_score"],
                        critical=check_data["critical"]
                    )
                    audit_report.add_check(check)
                    all_checks.append(check)

                print(f"✅ Data Domain Audit completed - {len(data_checks)} checks")

            elif domain == "models":
                # Run all model validation audits
                model_checks = []

                # Model Loading
                loading_result = self.model_validation_agent._audit_model_loading({}, {})
                model_checks.extend(loading_result.get("checks", []))

                # Model Predictions
                pred_result = self.model_validation_agent._audit_model_predictions({}, {})
                model_checks.extend(pred_result.get("checks", []))

                # Model Performance
                perf_result = self.model_validation_agent._audit_model_performance({}, {})
                model_checks.extend(perf_result.get("checks", []))

                # Ensemble Integration
                ensemble_result = self.model_validation_agent._audit_ensemble_integration({}, {})
                model_checks.extend(ensemble_result.get("checks", []))

                agent_results["model_validation"] = {
                    "execution_time": round(time.time() - domain_start, 2),
                    "checks_completed": len(model_checks),
                    "summary": loading_result.get("summary", {})
                }

                for check_data in model_checks:
                    check = AuditCheck(
                        check_id=check_data["check_id"],
                        category=check_data["category"],
                        title=check_data["title"],
                        description=check_data.get("description", ""),
                        validation_command=check_data["validation_command"],
                        expected_pattern=check_data["expected_pattern"],
                        status=AuditStatus(check_data["status"]),
                        score=check_data["score"],
                        max_score=check_data["max_score"],
                        critical=check_data["critical"]
                    )
                    audit_report.add_check(check)
                    all_checks.append(check)

                print(f"✅ Models Domain Audit completed - {len(model_checks)} checks")

            else:
                return {
                    "agent_id": self.agent_id,
                    "action": "audit_specific_domain",
                    "error": f"Unknown domain: {domain}. Valid domains: system, data, models"
                }

            # Finalize domain audit
            audit_report.finalize_report()
            audit_report.recommendations = self._generate_recommendations(all_checks)

            execution_time = round(time.time() - domain_start, 2)

            print(f"🎉 Domain Audit completed!")
            print(f"   Domain: {domain.upper()}")
            print(f"   Total Checks: {audit_report.total_checks}")
            print(f"   Overall Score: {audit_report.overall_score:.1f}%")
            print(f"   Status: {audit_report.overall_status.value}")

            return {
                "agent_id": self.agent_id,
                "action": "audit_specific_domain",
                "audit_id": audit_report.audit_id,
                "audit_name": audit_report.audit_name,
                "domain": domain,
                "execution_time": execution_time,
                "audit_summary": {
                    "total_checks": audit_report.total_checks,
                    "passed_checks": audit_report.passed_checks,
                    "failed_checks": audit_report.failed_checks,
                    "warning_checks": audit_report.warning_checks,
                    "critical_failures": audit_report.critical_failures,
                    "overall_score": audit_report.overall_score,
                    "overall_status": audit_report.overall_status.value
                },
                "agent_results": agent_results,
                "recommendations": audit_report.recommendations,
                "audit_report": audit_report
            }

        except Exception as e:
            error_msg = f"Domain audit failed for {domain}: {str(e)}"
            print(f"❌ {error_msg}")

            return {
                "agent_id": self.agent_id,
                "action": "audit_specific_domain",
                "domain": domain,
                "error": error_msg,
                "partial_results": agent_results,
                "execution_time": round(time.time() - audit_start_time.timestamp(), 2) if hasattr(audit_start_time, 'timestamp') else 0.0
            }