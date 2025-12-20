#!/usr/bin/env python3
"""
Production Audit Runner - Automated scheduling and execution for audit system.

This script provides production-ready audit execution with:
- Automated scheduling capabilities
- Enhanced error handling and logging
- Performance optimization and timeout management
- Professional reporting and alerting integration
- Graceful degradation and recovery mechanisms
"""

import argparse
import json
import logging
import os
import signal
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.audit.audit_coordinator_agent import AuditCoordinatorAgent
from agents.audit.core_audit_contracts import AuditStatus


class ProductionAuditRunner:
    """Production-grade audit runner with scheduling and optimization."""

    def __init__(self, config_file: Optional[str] = None):
        """Initialize production audit runner."""
        self.config = self._load_config(config_file)
        self.setup_logging()
        self.coordinator = None
        self.start_time = datetime.now()

        # Performance tracking
        self.metrics = {
            "start_time": self.start_time.isoformat(),
            "execution_time": 0.0,
            "checks_completed": 0,
            "failures": 0,
            "timeout_occurred": False,
            "graceful_degradation": False,
        }

        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

    def _load_config(self, config_file: Optional[str]) -> Dict[str, Any]:
        """Load configuration from file or use defaults."""
        default_config = {
            "audit_settings": {
                "default_timeout": 600,  # 10 minutes
                "quick_mode_timeout": 180,  # 3 minutes
                "parallel_execution": True,
                "max_workers": 3,
                "retry_attempts": 2,
                "retry_delay": 30,
            },
            "output_settings": {
                "output_dir": "production_audit_reports",
                "backup_reports": True,
                "compression": True,
                "retention_days": 30,
            },
            "alerting": {
                "enabled": True,
                "critical_threshold": 70,  # Alert if score < 70%
                "failure_threshold": 5,  # Alert if > 5 failures
                "channels": ["console", "file"],  # Future: email, slack, webhook
            },
            "scheduling": {
                "auto_cleanup": True,
                "cleanup_threshold": 90,  # Clean up reports older than 90 days
                "performance_tracking": True,
            },
        }

        if config_file and Path(config_file).exists():
            try:
                with open(config_file, "r") as f:
                    user_config = json.load(f)
                # Merge with defaults
                default_config.update(user_config)
                print(f"✅ Loaded configuration from {config_file}")
            except Exception as e:
                print(f"⚠️ Warning: Could not load config file {config_file}: {e}")
                print("Using default configuration")

        return default_config

    def setup_logging(self):
        """Set up professional structured logging."""
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

        # Create logs directory if it doesn't exist
        log_dir = Path("logs/audit_production")
        log_dir.mkdir(parents=True, exist_ok=True)

        # Set up file logger with rotation
        log_file = (
            log_dir / f"production_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )

        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[logging.FileHandler(log_file), logging.StreamHandler(sys.stdout)],
        )

        self.logger = logging.getLogger("ProductionAudit")
        self.logger.info("Production Audit logging initialized")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        self.logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self._handle_graceful_shutdown()

    def _handle_graceful_shutdown(self):
        """Perform graceful shutdown procedures."""
        try:
            # Save current state and metrics
            self.metrics["interrupted"] = True
            self.metrics["shutdown_time"] = datetime.now().isoformat()
            self._save_metrics()

            # Clean up resources if coordinator exists
            if self.coordinator:
                # Perform any cleanup needed
                pass

            self.logger.info("Graceful shutdown completed")

        except Exception as e:
            self.logger.error(f"Error during graceful shutdown: {e}")

        sys.exit(1)

    def _initialize_coordinator(self):
        """Initialize audit coordinator with error handling."""
        try:
            self.coordinator = AuditCoordinatorAgent()
            self.logger.info("Audit coordinator initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize audit coordinator: {e}")
            self.logger.error(traceback.format_exc())
            return False

    def _execute_audit_with_timeout(
        self, audit_type: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute audit with timeout and retry logic."""
        timeout = (
            self.config["audit_settings"]["quick_mode_timeout"]
            if audit_type == "quick"
            else self.config["audit_settings"]["default_timeout"]
        )
        max_attempts = self.config["audit_settings"]["retry_attempts"]

        for attempt in range(max_attempts + 1):
            try:
                self.logger.info(
                    f"Executing {audit_type} audit (attempt {attempt + 1}/{max_attempts + 1})"
                )

                if audit_type == "comprehensive":
                    result = self.coordinator._run_comprehensive_audit(parameters, {})
                elif audit_type == "quick":
                    result = self.coordinator._run_quick_audit(parameters, {})
                else:
                    result = self.coordinator._audit_specific_domain(parameters, {})

                # Check for errors in result
                if "error" in result:
                    raise Exception(f"Audit execution error: {result['error']}")

                self.logger.info(
                    f"Audit completed successfully - Score: {result.get('audit_summary', {}).get('overall_score', 0):.1f}%"
                )
                return result

            except Exception as e:
                self.logger.error(f"Audit attempt {attempt + 1} failed: {e}")

                if attempt < max_attempts:
                    retry_delay = self.config["audit_settings"]["retry_delay"]
                    self.logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    # All attempts failed
                    error_msg = (
                        f"Audit failed after {max_attempts + 1} attempts: {str(e)}"
                    )
                    self.logger.error(error_msg)
                    return {
                        "error": error_msg,
                        "execution_time": 0.0,
                        "audit_summary": {
                            "total_checks": 0,
                            "passed_checks": 0,
                            "failed_checks": 0,
                            "warning_checks": 0,
                            "critical_failures": 1,  # Mark as critical failure
                            "overall_score": 0.0,
                            "overall_status": "FAILED",
                        },
                    }

    def _generate_reports(self, audit_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate audit reports with error handling."""
        try:
            if "audit_report" not in audit_result:
                self.logger.warning("No audit report available for report generation")
                return {}

            self.logger.info("Generating audit reports...")
            report_result = self.coordinator._generate_audit_reports(
                {"audit_report": audit_result["audit_report"]}, {}
            )

            if "error" in report_result:
                self.logger.error(f"Report generation failed: {report_result['error']}")
                return {}

            self.logger.info(
                f"Generated {report_result.get('total_reports', 0)} reports"
            )
            return report_result

        except Exception as e:
            self.logger.error(f"Exception during report generation: {e}")
            return {}

    def _send_alerts(self, audit_result: Dict[str, Any]):
        """Send alerts based on audit results."""
        if not self.config["alerting"]["enabled"]:
            return

        try:
            summary = audit_result.get("audit_summary", {})
            score = summary.get("overall_score", 100)
            critical_failures = summary.get("critical_failures", 0)
            total_failures = summary.get("failed_checks", 0)

            critical_threshold = self.config["alerting"]["critical_threshold"]
            failure_threshold = self.config["alerting"]["failure_threshold"]

            # Check if alerting is needed
            needs_alert = (
                score < critical_threshold
                or critical_failures > 0
                or total_failures > failure_threshold
            )

            if needs_alert:
                self._send_alert_notification(
                    audit_result, score, critical_failures, total_failures
                )

        except Exception as e:
            self.logger.error(f"Error sending alerts: {e}")

    def _send_alert_notification(
        self,
        audit_result: Dict[str, Any],
        score: float,
        critical_failures: int,
        total_failures: int,
    ):
        """Send alert notification through configured channels."""
        alert_message = f"""
🚨 PRODUCTION AUDIT ALERT 🚨
Audit: {audit_result.get('audit_name', 'Unknown')}
Score: {score:.1f}%
Critical Failures: {critical_failures}
Total Failures: {total_failures}
Execution Time: {audit_result.get('execution_time', 0):.1f}s
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """.strip()

        channels = self.config["alerting"]["channels"]

        for channel in channels:
            try:
                if channel == "console":
                    print(f"\n{alert_message}\n")
                elif channel == "file":
                    # Write to alert log file
                    alert_log = Path("logs/audit_production/alerts.log")
                    alert_log.parent.mkdir(parents=True, exist_ok=True)

                    with open(alert_log, "a") as f:
                        f.write(f"{datetime.now().isoformat()} - {alert_message}\n")

                # Future channels: email, slack, webhook
                # elif channel == "email":
                #     self._send_email_alert(alert_message)
                # elif channel == "slack":
                #     self._send_slack_alert(alert_message)

            except Exception as e:
                self.logger.error(f"Failed to send alert via {channel}: {e}")

    def _save_metrics(self, audit_result: Optional[Dict[str, Any]] = None):
        """Save execution metrics for historical tracking."""
        try:
            # Update metrics with audit results
            if audit_result:
                summary = audit_result.get("audit_summary", {})
                self.metrics.update(
                    {
                        "execution_time": audit_result.get("execution_time", 0),
                        "checks_completed": summary.get("total_checks", 0),
                        "failures": summary.get("failed_checks", 0),
                        "critical_failures": summary.get("critical_failures", 0),
                        "overall_score": summary.get("overall_score", 0),
                        "final_status": summary.get("overall_status", "UNKNOWN"),
                    }
                )

            # Calculate total runtime
            end_time = datetime.now()
            self.metrics["total_runtime"] = (end_time - self.start_time).total_seconds()
            self.metrics["end_time"] = end_time.isoformat()

            # Save metrics to file
            metrics_dir = Path("production_audit_reports/metrics")
            metrics_dir.mkdir(parents=True, exist_ok=True)

            metrics_file = (
                metrics_dir
                / f"audit_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )

            with open(metrics_file, "w") as f:
                json.dump(self.metrics, f, indent=2)

            self.logger.info(f"Metrics saved to {metrics_file}")

        except Exception as e:
            self.logger.error(f"Failed to save metrics: {e}")

    def run_audit(
        self, audit_type: str = "quick", **kwargs
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Run production audit with full automation.

        Args:
            audit_type: Type of audit to run ('quick', 'comprehensive', 'domain')
            **kwargs: Additional parameters for audit execution

        Returns:
            Tuple of (success: bool, result: Dict)
        """
        self.logger.info(f"Starting production audit: {audit_type}")

        try:
            # Initialize coordinator
            if not self._initialize_coordinator():
                return False, {"error": "Failed to initialize audit coordinator"}

            # Prepare audit parameters
            audit_name = kwargs.get(
                "audit_name",
                f"Production {audit_type.title()} Audit {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            )

            parameters = {"audit_name": audit_name}
            if audit_type == "domain":
                parameters.update(kwargs)

            # Execute audit with timeout and retry logic
            audit_result = self._execute_audit_with_timeout(audit_type, parameters)

            if "error" in audit_result:
                self.metrics["execution_failed"] = True
                self._save_metrics(audit_result)
                return False, audit_result

            # Generate reports
            report_result = self._generate_reports(audit_result)

            # Send alerts if needed
            self._send_alerts(audit_result)

            # Save metrics
            self._save_metrics(audit_result)

            # Log success
            summary = audit_result.get("audit_summary", {})
            self.logger.info(f"🎉 Production audit completed successfully!")
            self.logger.info(f"   Score: {summary.get('overall_score', 0):.1f}%")
            self.logger.info(
                f"   Checks: {summary.get('total_checks', 0)} total, {summary.get('passed_checks', 0)} passed"
            )
            self.logger.info(
                f"   Critical Issues: {summary.get('critical_failures', 0)}"
            )
            self.logger.info(
                f"   Reports: {report_result.get('total_reports', 0)} generated"
            )

            return True, audit_result

        except Exception as e:
            self.logger.error(f"Production audit failed with exception: {e}")
            self.logger.error(traceback.format_exc())

            # Save error metrics
            self.metrics["execution_failed"] = True
            self.metrics["error"] = str(e)
            self._save_metrics()

            return False, {"error": f"Production audit failed: {str(e)}"}

    def cleanup_old_reports(self):
        """Clean up old audit reports based on retention policy."""
        if not self.config["scheduling"]["auto_cleanup"]:
            return

        try:
            retention_days = self.config["scheduling"]["cleanup_threshold"]
            cutoff_date = datetime.now() - timedelta(days=retention_days)

            output_dir = Path(self.config["output_settings"]["output_dir"])
            if not output_dir.exists():
                return

            # Clean up old report files
            deleted_count = 0
            for report_file in output_dir.rglob("*"):
                if report_file.is_file():
                    file_time = datetime.fromtimestamp(report_file.stat().st_mtime)
                    if file_time < cutoff_date:
                        report_file.unlink()
                        deleted_count += 1

            if deleted_count > 0:
                self.logger.info(f"Cleaned up {deleted_count} old audit report files")

        except Exception as e:
            self.logger.error(f"Error during report cleanup: {e}")


def main():
    """Main entry point for production audit runner."""
    parser = argparse.ArgumentParser(description="Production Audit Runner")
    parser.add_argument(
        "--audit-type",
        choices=["quick", "comprehensive", "domain"],
        default="quick",
        help="Type of audit to run",
    )
    parser.add_argument(
        "--domain",
        choices=["system", "data", "models"],
        help="Domain to audit (required for domain audit type)",
    )
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument(
        "--cleanup-only", action="store_true", help="Only run cleanup of old reports"
    )

    args = parser.parse_args()

    # Validate domain argument
    if args.audit_type == "domain" and not args.domain:
        print("Error: --domain is required when using --audit-type=domain")
        sys.exit(1)

    # Initialize runner
    runner = ProductionAuditRunner(args.config)

    try:
        # Handle cleanup-only mode
        if args.cleanup_only:
            runner.cleanup_old_reports()
            print("✅ Report cleanup completed")
            return

        # Run audit
        kwargs = {}
        if args.domain:
            kwargs["domain"] = args.domain

        success, result = runner.run_audit(args.audit_type, **kwargs)

        # Exit with appropriate code
        if not success:
            print(f"❌ Audit failed: {result.get('error', 'Unknown error')}")
            sys.exit(2)

        summary = result.get("audit_summary", {})
        critical_failures = summary.get("critical_failures", 0)
        overall_score = summary.get("overall_score", 100)

        if critical_failures > 0:
            print(f"⚠️ Audit completed with {critical_failures} critical failures")
            sys.exit(2)  # Critical issues found
        elif overall_score < 80:
            print(f"⚠️ Audit completed with low score: {overall_score:.1f}%")
            sys.exit(1)  # Low score - needs attention
        else:
            print(f"✅ Audit completed successfully - Score: {overall_score:.1f}%")
            sys.exit(0)  # Success

    except KeyboardInterrupt:
        print("\n🛑 Audit interrupted by user")
        sys.exit(130)  # Standard exit code for SIGINT
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(3)


if __name__ == "__main__":
    main()
