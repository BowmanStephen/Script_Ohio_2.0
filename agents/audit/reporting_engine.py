"""
Multi-format audit reporting engine supporting TOON, JSON, HTML, and Dashboard formats.
Integrates with existing TOON format system and provides comprehensive visualization.
"""

import json
import html
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import base64
import io
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from .core_audit_contracts import AuditReport, AuditCheck, AuditStatus

class AuditReportingEngine:
    """Comprehensive audit reporting with multiple output formats."""

    def __init__(self, output_dir: str = "audit_reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def generate_toon_report(self, report: AuditReport) -> str:
        """Generate TOON format report for maximum token efficiency."""

        # System Information
        system_info = [
            ["audit_id", "audit_name", "start_time", "overall_status", "overall_score"],
            [report.audit_id[:8], report.audit_name, report.start_time[:19],
             report.overall_status.value, f"{report.overall_score:.1f}"]
        ]

        # Summary Statistics
        summary_stats = [
            ["metric", "value"],
            ["total_checks", str(report.total_checks)],
            ["passed_checks", str(report.passed_checks)],
            ["failed_checks", str(report.failed_checks)],
            ["warning_checks", str(report.warning_checks)],
            ["critical_failures", str(report.critical_failures)]
        ]

        # Check Results
        check_results = []
        if report.checks:
            check_results.append(["check_id", "category", "title", "status", "score", "critical"])
            for check in report.checks:
                check_results.append([
                    check.check_id[:8], check.category, check.title[:30],
                    check.status.value, f"{check.score:.1f}", str(check.critical)
                ])

        # Recommendations
        recommendations = [["recommendation"]]
        for rec in report.recommendations:
            recommendations.append([rec[:80]])

        # Combine all sections
        toon_data = {
            "system_info": system_info,
            "summary_stats": summary_stats,
            "check_results": check_results,
            "recommendations": recommendations
        }

        # Convert to TOON format
        toon_lines = []
        for section_name, section_data in toon_data.items():
            toon_lines.append(f"# {section_name.upper().replace('_', ' ')}")
            for row in section_data:
                toon_lines.append(" | ".join(str(item) for item in row))
            toon_lines.append("")  # Empty line between sections

        toon_content = "\n".join(toon_lines)

        # Save to file
        toon_file = self.output_dir / f"audit_report_{report.audit_id[:8]}_toon.txt"
        with open(toon_file, 'w') as f:
            f.write(toon_content)

        return str(toon_file)

    def generate_json_report(self, report: AuditReport) -> str:
        """Generate detailed JSON report."""

        json_data = {
            "audit_metadata": {
                "audit_id": report.audit_id,
                "audit_name": report.audit_name,
                "start_time": report.start_time,
                "end_time": report.end_time,
                "generated_at": datetime.now().isoformat()
            },
            "summary": {
                "overall_status": report.overall_status.value,
                "overall_score": report.overall_score,
                "total_checks": report.total_checks,
                "passed_checks": report.passed_checks,
                "failed_checks": report.failed_checks,
                "warning_checks": report.warning_checks,
                "critical_failures": report.critical_failures,
                "pass_rate": (report.passed_checks / report.total_checks * 100) if report.total_checks > 0 else 0
            },
            "system_info": report.system_info,
            "checks": []
        }

        # Add detailed check information
        for check in report.checks:
            check_data = {
                "check_id": check.check_id,
                "category": check.category,
                "title": check.title,
                "description": check.description,
                "status": check.status.value,
                "score": check.score,
                "max_score": check.max_score,
                "critical": check.critical,
                "validation_command": check.validation_command,
                "expected_pattern": check.expected_pattern,
                "evidence_count": len(check.evidence)
            }
            json_data["checks"].append(check_data)

        # Add recommendations
        json_data["recommendations"] = report.recommendations

        # Save to file
        json_file = self.output_dir / f"audit_report_{report.audit_id[:8]}_json.json"
        with open(json_file, 'w') as f:
            json.dump(json_data, f, indent=2)

        return str(json_file)

    def generate_html_report(self, report: AuditReport) -> str:
        """Generate comprehensive HTML report with charts and visualizations."""

        # Create charts
        self._create_audit_charts(report)

        # Generate HTML content
        html_content = self._generate_html_template(report)

        # Save to file
        html_file = self.output_dir / f"audit_report_{report.audit_id[:8]}_html.html"
        with open(html_file, 'w') as f:
            f.write(html_content)

        return str(html_file)

    def generate_dashboard_data(self, report: AuditReport) -> str:
        """Generate dashboard-ready data structure."""

        dashboard_data = {
            "overview": {
                "status": report.overall_status.value,
                "score": report.overall_score,
                "checks_analyzed": report.total_checks,
                "critical_issues": report.critical_failures
            },
            "category_breakdown": self._calculate_category_breakdown(report),
            "timeline": {
                "start": report.start_time,
                "end": report.end_time,
                "duration": (
                    datetime.fromisoformat(report.end_time) - datetime.fromisoformat(report.start_time)
                ).total_seconds() if report.end_time else None
            },
            "alerts": self._generate_alerts(report),
            "recommendations": report.recommendations[:5],  # Top 5 recommendations
            "charts": {
                "status_distribution": self._get_status_chart_data(report),
                "category_performance": self._get_category_chart_data(report),
                "score_trend": []  # Would need historical data
            }
        }

        # Save dashboard data
        dashboard_file = self.output_dir / f"audit_report_{report.audit_id[:8]}_dashboard.json"
        with open(dashboard_file, 'w') as f:
            json.dump(dashboard_data, f, indent=2)

        return str(dashboard_file)

    def _create_audit_charts(self, report: AuditReport) -> None:
        """Create visualization charts for the audit report."""

        # Set up the plotting style
        plt.style.use('default')

        # Chart 1: Status Distribution
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))

        # Status pie chart
        status_counts = {
            'Passed': report.passed_checks,
            'Failed': report.failed_checks,
            'Warning': report.warning_checks
        }
        # Remove zero values
        status_counts = {k: v for k, v in status_counts.items() if v > 0}

        if status_counts:
            ax1.pie(status_counts.values(), labels=status_counts.keys(), autopct='%1.1f%%')
            ax1.set_title('Audit Check Status Distribution')
        else:
            ax1.text(0.5, 0.5, 'No Data', ha='center', va='center')
            ax1.set_title('Audit Check Status Distribution')

        # Category performance bar chart
        category_scores = self._calculate_category_breakdown(report)
        if category_scores:
            categories = list(category_scores.keys())
            scores = list(category_scores.values())
            ax2.bar(categories, scores)
            ax2.set_title('Performance by Category')
            ax2.set_ylabel('Score')
            ax2.tick_params(axis='x', rotation=45)
        else:
            ax2.text(0.5, 0.5, 'No Data', ha='center', va='center')
            ax2.set_title('Performance by Category')

        # Critical vs Non-critical
        critical_checks = sum(1 for check in report.checks if check.critical)
        non_critical_checks = len(report.checks) - critical_checks
        if critical_checks + non_critical_checks > 0:
            ax3.bar(['Critical', 'Non-Critical'], [critical_checks, non_critical_checks])
            ax3.set_title('Critical vs Non-Critical Checks')
        else:
            ax3.text(0.5, 0.5, 'No Data', ha='center', va='center')
            ax3.set_title('Critical vs Non-Critical Checks')

        # Score distribution histogram
        scores = [check.score for check in report.checks if check.score > 0]
        if scores:
            ax4.hist(scores, bins=10, alpha=0.7)
            ax4.set_title('Score Distribution')
            ax4.set_xlabel('Score')
            ax4.set_ylabel('Frequency')
        else:
            ax4.text(0.5, 0.5, 'No Data', ha='center', va='center')
            ax4.set_title('Score Distribution')

        plt.tight_layout()

        # Save chart
        chart_file = self.output_dir / f"audit_charts_{report.audit_id[:8]}.png"
        plt.savefig(chart_file, dpi=300, bbox_inches='tight')
        plt.close()

    def _generate_html_template(self, report: AuditReport) -> str:
        """Generate the HTML template for the audit report."""

        # Read the chart file if it exists
        chart_file = self.output_dir / f"audit_charts_{report.audit_id[:8]}.png"
        chart_base64 = ""
        if chart_file.exists():
            with open(chart_file, "rb") as img_file:
                chart_base64 = base64.b64encode(img_file.read()).decode()

        status_color = {
            AuditStatus.PASSED: "#28a745",
            AuditStatus.FAILED: "#dc3545",
            AuditStatus.WARNING: "#ffc107",
            AuditStatus.PENDING: "#6c757d"
        }.get(report.overall_status, "#6c757d")

        html_template = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Audit Report: {html.escape(report.audit_name)}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f8f9fa; }}
                .container {{ max-width: 1200px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .status-badge {{ background-color: {status_color}; color: white; padding: 8px 16px; border-radius: 20px; font-weight: bold; }}
                .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
                .summary-card {{ background-color: #f8f9fa; padding: 15px; border-radius: 6px; text-align: center; }}
                .summary-card h3 {{ margin: 0 0 10px 0; color: #495057; }}
                .summary-card .value {{ font-size: 2em; font-weight: bold; color: #007bff; }}
                .chart-container {{ text-align: center; margin: 30px 0; }}
                .chart-container img {{ max-width: 100%; height: auto; }}
                .checks-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                .checks-table th, .checks-table td {{ border: 1px solid #dee2e6; padding: 12px; text-align: left; }}
                .checks-table th {{ background-color: #f8f9fa; font-weight: bold; }}
                .status-passed {{ color: #28a745; font-weight: bold; }}
                .status-failed {{ color: #dc3545; font-weight: bold; }}
                .status-warning {{ color: #ffc107; font-weight: bold; }}
                .recommendations {{ background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; }}
                .critical {{ background-color: #f8d7da; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Audit Report: {html.escape(report.audit_name)}</h1>
                    <p><strong>Audit ID:</strong> {report.audit_id}</p>
                    <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <div class="status-badge">Overall Status: {report.overall_status.value.upper()}</div>
                </div>

                <div class="summary">
                    <div class="summary-card">
                        <h3>Overall Score</h3>
                        <div class="value">{report.overall_score:.1f}%</div>
                    </div>
                    <div class="summary-card">
                        <h3>Total Checks</h3>
                        <div class="value">{report.total_checks}</div>
                    </div>
                    <div class="summary-card">
                        <h3>Passed</h3>
                        <div class="value" style="color: #28a745;">{report.passed_checks}</div>
                    </div>
                    <div class="summary-card">
                        <h3>Failed</h3>
                        <div class="value" style="color: #dc3545;">{report.failed_checks}</div>
                    </div>
                    <div class="summary-card">
                        <h3>Critical Issues</h3>
                        <div class="value" style="color: #dc3545;">{report.critical_failures}</div>
                    </div>
                </div>

                {f'<div class="chart-container"><img src="data:image/png;base64,{chart_base64}" alt="Audit Charts"></div>' if chart_base64 else ''}

                <h2>Check Results</h2>
                <table class="checks-table">
                    <thead>
                        <tr>
                            <th>Category</th>
                            <th>Title</th>
                            <th>Status</th>
                            <th>Score</th>
                            <th>Critical</th>
                        </tr>
                    </thead>
                    <tbody>
                        {self._generate_check_rows(report.checks)}
                    </tbody>
                </table>

                {f'<div class="recommendations"><h3>Recommendations</h3><ul>' + ''.join(f'<li>{html.escape(rec)}</li>' for rec in report.recommendations) + '</ul></div>' if report.recommendations else ''}
            </div>
        </body>
        </html>
        """

        return html_template

    def _generate_check_rows(self, checks: List[AuditCheck]) -> str:
        """Generate HTML table rows for audit checks."""
        rows = []
        for check in checks:
            status_class = f"status-{check.status.value}"
            critical_class = "critical" if check.critical else ""

            row = f"""
            <tr class="{critical_class}">
                <td>{html.escape(check.category)}</td>
                <td>{html.escape(check.title)}</td>
                <td class="{status_class}">{check.status.value.upper()}</td>
                <td>{check.score:.1f}/{check.max_score:.1f}</td>
                <td>{'YES' if check.critical else 'NO'}</td>
            </tr>
            """
            rows.append(row)

        return "".join(rows)

    def _calculate_category_breakdown(self, report: AuditReport) -> Dict[str, float]:
        """Calculate performance breakdown by category."""
        category_scores = {}

        for check in report.checks:
            if check.category not in category_scores:
                category_scores[check.category] = []
            category_scores[check.category].append(check.score)

        # Calculate average score per category
        for category in category_scores:
            scores = category_scores[category]
            category_scores[category] = sum(scores) / len(scores) if scores else 0.0

        return category_scores

    def _generate_alerts(self, report: AuditReport) -> List[Dict[str, Any]]:
        """Generate critical alerts from audit results."""
        alerts = []

        for check in report.checks:
            if check.status == AuditStatus.FAILED and check.critical:
                alerts.append({
                    "type": "critical_failure",
                    "message": f"Critical check failed: {check.title}",
                    "category": check.category,
                    "check_id": check.check_id
                })
            elif check.status == AuditStatus.FAILED:
                alerts.append({
                    "type": "failure",
                    "message": f"Check failed: {check.title}",
                    "category": check.category,
                    "check_id": check.check_id
                })

        return alerts

    def _get_status_chart_data(self, report: AuditReport) -> Dict[str, Any]:
        """Get data for status distribution chart."""
        return {
            "passed": report.passed_checks,
            "failed": report.failed_checks,
            "warning": report.warning_checks
        }

    def _get_category_chart_data(self, report: AuditReport) -> Dict[str, Any]:
        """Get data for category performance chart."""
        category_data = {}
        for check in report.checks:
            if check.category not in category_data:
                category_data[check.category] = {"total": 0, "passed": 0, "failed": 0, "warning": 0}

            category_data[check.category]["total"] += 1
            if check.status == AuditStatus.PASSED:
                category_data[check.category]["passed"] += 1
            elif check.status == AuditStatus.FAILED:
                category_data[check.category]["failed"] += 1
            elif check.status == AuditStatus.WARNING:
                category_data[check.category]["warning"] += 1

        return category_data