#!/usr/bin/env python3
"""
One-Command System Audit Script
Executes comprehensive system audit with multi-format reporting
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
    parser = argparse.ArgumentParser(description="Run comprehensive system audit")
    parser.add_argument(
        "--type",
        choices=["comprehensive", "quick", "domain"],
        default="comprehensive",
        help="Type of audit to run",
    )
    parser.add_argument(
        "--domain",
        choices=["system", "data", "models"],
        help="Domain to audit (only for domain type)",
    )
    parser.add_argument("--name", help="Custom audit name")
    parser.add_argument(
        "--reports",
        action="store_true",
        default=True,
        help="Generate multi-format reports",
    )
    parser.add_argument(
        "--no-reports", action="store_true", help="Skip report generation"
    )
    parser.add_argument(
        "--output-dir", default="audit_reports", help="Output directory for reports"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Determine if reports should be generated
    generate_reports = args.reports and not args.no_reports

    try:
        # Import audit coordinator
        from agents.audit.audit_coordinator_agent import AuditCoordinatorAgent

        # Initialize coordinator
        coordinator = AuditCoordinatorAgent()

        # Prepare audit parameters
        audit_params = {
            "audit_name": args.name
            or f"{args.type.title()} System Audit {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "output_dir": args.output_dir,
        }

        print("🔍 Starting System Audit...")
        print(f"   Type: {args.type}")
        if args.domain:
            print(f"   Domain: {args.domain}")
        print(f"   Reports: {'Enabled' if generate_reports else 'Disabled'}")
        print()

        # Execute audit based on type
        if args.type == "comprehensive":
            result = coordinator._execute_action(
                "run_comprehensive_audit", audit_params, {}
            )

        elif args.type == "quick":
            result = coordinator._execute_action("run_quick_audit", audit_params, {})

        elif args.type == "domain":
            if not args.domain:
                print("❌ Error: --domain required for domain audit type")
                sys.exit(1)

            audit_params["domain"] = args.domain
            result = coordinator._execute_action(
                "audit_specific_domain", audit_params, {}
            )

        # Handle audit execution result
        if "error" in result:
            print(f"❌ Audit failed: {result['error']}")
            sys.exit(1)

        # Display audit summary
        summary = result["audit_summary"]
        execution_time = result.get("execution_time", 0)

        print()
        print("📊 AUDIT RESULTS")
        print("=" * 50)
        print(f"Audit ID: {result.get('audit_id', 'N/A')}")
        print(f"Audit Name: {result.get('audit_name', 'N/A')}")
        print(f"Execution Time: {execution_time:.1f} seconds")
        print()
        print(f"Total Checks: {summary['total_checks']}")
        print(
            f"Passed: {summary['passed_checks']} ({summary['passed_checks']/summary['total_checks']*100:.1f}%)"
        )
        print(
            f"Failed: {summary['failed_checks']} ({summary['failed_checks']/summary['total_checks']*100:.1f}%)"
        )
        print(
            f"Warnings: {summary['warning_checks']} ({summary['warning_checks']/summary['total_checks']*100:.1f}%)"
        )
        print(f"Critical Failures: {summary['critical_failures']}")
        print(f"Overall Score: {summary['overall_score']:.1f}%")
        print(f"Status: {summary['overall_status'].upper()}")

        # Display recommendations
        recommendations = result.get("recommendations", [])
        if recommendations:
            print()
            print("💡 RECOMMENDATIONS")
            print("=" * 50)
            for i, rec in enumerate(recommendations, 1):
                print(f"{i}. {rec}")

        # Generate reports if requested
        if generate_reports and "audit_report" in result:
            print()
            print("📄 GENERATING REPORTS")
            print("=" * 50)

            report_params = {"audit_report": result["audit_report"]}

            report_result = coordinator._execute_action(
                "generate_audit_reports", report_params, {}
            )

            if "error" in report_result:
                print(f"❌ Report generation failed: {report_result['error']}")
            else:
                report_files = report_result["report_files"]
                print(f"Generated {len(report_files)} reports:")
                for report_type, file_path in report_files.items():
                    print(f"  {report_type.upper()}: {file_path}")

        # Exit with appropriate code based on audit results
        if summary.get("critical_failures", 0) > 0:
            print()
            print("🚨 AUDIT COMPLETED WITH CRITICAL FAILURES")
            sys.exit(2)  # Critical failures
        elif summary.get("failed_checks", 0) > 0:
            print()
            print("⚠️ AUDIT COMPLETED WITH FAILURES")
            sys.exit(1)  # Non-critical failures
        else:
            print()
            print("✅ AUDIT COMPLETED SUCCESSFULLY")
            sys.exit(0)  # Success

    except KeyboardInterrupt:
        print("\n❌ Audit interrupted by user")
        sys.exit(130)

    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
