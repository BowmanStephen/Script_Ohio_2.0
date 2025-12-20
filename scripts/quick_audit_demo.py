#!/usr/bin/env python3
"""
Quick Audit Demo - Demonstrates core audit functionality
Simple version without complex coordination issues
"""

import sys
from datetime import datetime
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
    """Run a quick demonstration of the audit system."""

    print("🎯 Quick Audit System Demo")
    print("=" * 40)

    try:
        from agents.audit.core_audit_contracts import AuditReport, AuditStatus
        from agents.audit.data_pipeline_audit_agent import DataPipelineAuditAgent
        from agents.audit.model_validation_audit_agent import ModelValidationAuditAgent
        from agents.audit.reporting_engine import AuditReportingEngine
        from agents.audit.system_integrity_agent import SystemIntegrityAuditAgent

        # Create audit report
        audit_start = datetime.now()
        report = AuditReport(
            audit_name=f"Quick System Audit Demo {audit_start.strftime('%Y-%m-%d %H:%M:%S')}",
            start_time=audit_start.isoformat(),
        )

        print("\n🔍 Running System Integrity Checks...")
        sys_agent = SystemIntegrityAuditAgent()

        # Test file structure
        structure_result = sys_agent._audit_file_structure({}, {})
        for check_data in structure_result.get("checks", []):
            from agents.audit.core_audit_contracts import AuditCheck

            check = AuditCheck(
                category=check_data["category"],
                title=check_data["title"],
                description=check_data.get("description", ""),
                validation_command=check_data["validation_command"],
                expected_pattern=check_data["expected_pattern"],
                critical=check_data["critical"],
            )
            check.status = AuditStatus(check_data["status"])
            check.score = check_data["score"]
            report.add_check(check)

        print(
            f"✅ System Integrity: {structure_result['summary']['passed_checks']}/{structure_result['summary']['total_checks']} checks passed"
        )

        print("\n🔍 Running Data Pipeline Checks...")
        data_agent = DataPipelineAuditAgent()

        # Test CFBD integration
        cfbd_result = data_agent._audit_cfbd_integration({}, {})
        for check_data in cfbd_result.get("checks", []):
            from agents.audit.core_audit_contracts import AuditCheck

            check = AuditCheck(
                category=check_data["category"],
                title=check_data["title"],
                description=check_data.get("description", ""),
                validation_command=check_data["validation_command"],
                expected_pattern=check_data["expected_pattern"],
                critical=check_data["critical"],
            )
            check.status = AuditStatus(check_data["status"])
            check.score = check_data["score"]
            report.add_check(check)

        print(
            f"✅ Data Pipeline: {cfbd_result['summary']['passed_checks']}/{cfbd_result['summary']['total_checks']} checks passed"
        )

        print("\n🔍 Running Model Validation Checks...")
        model_agent = ModelValidationAuditAgent()

        # Test model loading
        loading_result = model_agent._audit_model_loading({}, {})
        for check_data in loading_result.get("checks", []):
            from agents.audit.core_audit_contracts import AuditCheck

            check = AuditCheck(
                category=check_data["category"],
                title=check_data["title"],
                description=check_data.get("description", ""),
                validation_command=check_data["validation_command"],
                expected_pattern=check_data["expected_pattern"],
                critical=check_data["critical"],
            )
            check.status = AuditStatus(check_data["status"])
            check.score = check_data["score"]
            report.add_check(check)

        print(
            f"✅ Model Validation: {loading_result['summary']['passed_checks']}/{loading_result['summary']['total_checks']} checks passed"
        )

        # Finalize report
        report.finalize_report()

        # Generate recommendations
        recommendations = []
        if report.critical_failures > 0:
            recommendations.append(
                f"🚨 {report.critical_failures} critical issues need immediate attention"
            )
        if report.failed_checks > 0:
            recommendations.append(
                f"⚠️ {report.failed_checks} issues found that should be addressed"
            )
        if report.passed_checks == report.total_checks:
            recommendations.append(
                "🎉 All checks passed! System is operating optimally."
            )

        # Generate reports
        print("\n📊 Generating Reports...")
        engine = AuditReportingEngine("demo_reports")

        toon_file = engine.generate_toon_report(report)
        json_file = engine.generate_json_report(report)

        print(f"✅ TOON report: {toon_file}")
        print(f"✅ JSON report: {json_file}")

        # Display results
        print(f"\n📋 AUDIT RESULTS")
        print("=" * 40)
        print(f"Total Checks: {report.total_checks}")
        print(f"Passed: {report.passed_checks}")
        print(f"Failed: {report.failed_checks}")
        print(f"Warnings: {report.warning_checks}")
        print(f"Critical Failures: {report.critical_failures}")
        print(f"Overall Score: {report.overall_score:.1f}%")
        print(f"Status: {report.overall_status.value.upper()}")

        if recommendations:
            print(f"\n💡 Recommendations:")
            for i, rec in enumerate(recommendations, 1):
                print(f"{i}. {rec}")

        # Exit code based on results
        if report.critical_failures > 0:
            print(f"\n🚨 AUDIT COMPLETED WITH CRITICAL FAILURES")
            sys.exit(2)
        elif report.failed_checks > 0:
            print(f"\n⚠️ AUDIT COMPLETED WITH FAILURES")
            sys.exit(1)
        else:
            print(f"\n✅ AUDIT COMPLETED SUCCESSFULLY")
            sys.exit(0)

    except Exception as e:
        print(f"\n❌ Audit failed: {str(e)}")
        import traceback

        traceback.print_exc()
        sys.exit(3)


if __name__ == "__main__":
    main()
