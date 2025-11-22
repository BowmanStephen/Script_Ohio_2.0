#!/usr/bin/env python3
"""
Generate Calculation Verification Report
========================================

Generates comprehensive markdown and JSON reports from calculation verification results.

Usage:
    python scripts/generate_calculation_verification_report.py
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Output directory
REPORTS_DIR = PROJECT_ROOT / "reports"
REPORTS_DIR.mkdir(exist_ok=True)


class CalculationVerificationReportGenerator:
    """Generate comprehensive calculation verification reports"""
    
    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.reports_dir = REPORTS_DIR
        self.verification_report_json = self.reports_dir / "calculation_verification_report.json"
    
    def load_verification_results(self) -> Dict[str, Any]:
        """Load verification results from JSON"""
        if not self.verification_report_json.exists():
            print(f"⚠️  Verification report not found: {self.verification_report_json}")
            print("   Run verify_all_calculations.py first")
            return None
        
        with open(self.verification_report_json, 'r') as f:
            return json.load(f)
    
    def generate_markdown_report(self, results: Dict[str, Any]) -> str:
        """Generate markdown report"""
        checks = results.get("checks", {})
        summary = results.get("summary", {})
        
        report = f"""# Calculation Verification Report

**Generated:** {results.get('verification_date', 'Unknown')}  
**Season:** {results.get('season', 'Unknown')}  
**Overall Status:** {summary.get('overall_status', 'unknown').upper()}

## Executive Summary

- **Checks Passed:** {summary.get('checks_passed', 0)}/{summary.get('total_checks', 0)}
- **EPA Calculations:** {summary.get('epa_calculations', 'unknown')}
- **Opponent Adjustments:** {summary.get('opponent_adjustments', 'unknown')}
- **Feature Engineering:** {summary.get('feature_engineering', 'unknown')}
- **Model Compatibility:** {summary.get('model_compatibility', 'unknown')}
- **Temporal Consistency:** {summary.get('temporal_consistency', 'unknown')}
- **Data Leakage:** {summary.get('data_leakage', 'unknown')}

---

## 1. EPA Calculations Verification

"""
        
        epa_check = checks.get("epa_calculations", {})
        if epa_check:
            report += f"""**Status:** {epa_check.get('status', 'unknown').upper()}

### Results

- **Columns Checked:** {epa_check.get('columns_checked', 0)}
- **All Within Range:** {epa_check.get('all_within_range', False)}

### Historical Comparison

"""
            historical_comparison = epa_check.get("historical_comparison", {})
            if historical_comparison:
                report += "| Feature | Historical Mean | 2025 Mean | Deviation | Status |\n"
                report += "|---------|----------------|-----------|-----------|--------|\n"
                for feature, data in historical_comparison.items():
                    report += f"| {feature} | {data.get('historical_mean', 0):.4f} | {data.get('current_mean', 0):.4f} | {data.get('deviation_sigma', 0):.2f}σ | {data.get('status', 'unknown')} |\n"
            
            issues = epa_check.get("issues", [])
            if issues:
                report += "\n### Issues Found\n\n"
                for issue in issues:
                    report += f"- **{issue.get('column', 'unknown')}**: {issue.get('issue', 'unknown')}\n"
        
        report += "\n---\n\n## 2. Opponent Adjustments Verification\n\n"
        
        opponent_check = checks.get("opponent_adjustments", {})
        if opponent_check:
            report += f"""**Status:** {opponent_check.get('status', 'unknown').upper()}

### Results

- **Adjusted Features Found:** {opponent_check.get('adjusted_features_count', 0)}
- **Key Features Checked:** {opponent_check.get('key_features_checked', 0)}
- **Methodology Correct:** {opponent_check.get('methodology_correct', False)}

### Methodology

- **Method:** Subtraction-based opponent adjustments
- **Formula:** `Adjusted_Metric = Team_Raw_Metric - Opponent_Average_Allowed`

### Key Features

"""
            methodology_checks = opponent_check.get("methodology_checks", {})
            if methodology_checks:
                report += "| Feature | Mean | Std Dev | Min | Max |\n"
                report += "|---------|------|---------|-----|-----|\n"
                for feature, data in list(methodology_checks.items())[:10]:  # Show first 10
                    report += f"| {feature} | {data.get('mean', 0):.4f} | {data.get('std', 0):.4f} | {data.get('min', 0):.4f} | {data.get('max', 0):.4f} |\n"
        
        report += "\n---\n\n## 3. Feature Engineering Verification\n\n"
        
        feature_check = checks.get("feature_engineering", {})
        if feature_check:
            report += f"""**Status:** {feature_check.get('status', 'unknown').upper()}

### Results

- **Total Columns:** {feature_check.get('total_columns', 0)}
- **All Features Present:** {feature_check.get('all_features_present', False)}
- **No Data Type Issues:** {feature_check.get('no_data_type_issues', False)}
- **No Missing Values:** {feature_check.get('no_missing_values', False)}

### Feature Groups

"""
            feature_groups = feature_check.get("feature_groups", {})
            if feature_groups:
                report += "| Group | Required | Present | Missing | Status |\n"
                report += "|-------|----------|---------|---------|--------|\n"
                for group, data in feature_groups.items():
                    report += f"| {group} | {data.get('required', 0)} | {data.get('present', 0)} | {data.get('missing', 0)} | {data.get('status', 'unknown')} |\n"
            
            missing_features = feature_check.get("missing_features", {})
            if missing_features:
                report += "\n### Missing Features\n\n"
                for group, features in missing_features.items():
                    report += f"- **{group}**: {', '.join(features[:5])}{'...' if len(features) > 5 else ''}\n"
        
        report += "\n---\n\n## 4. Model Compatibility Verification\n\n"
        
        model_check = checks.get("model_compatibility", {})
        if model_check:
            report += f"""**Status:** {model_check.get('status', 'unknown').upper()}

### Results

- **All Models Exist:** {model_check.get('all_models_exist', False)}
- **Data Types Correct:** {model_check.get('data_types_correct', False)}
- **Metadata Complete:** {model_check.get('metadata_complete', False)}
- **Numeric Features:** {model_check.get('numeric_features_count', 0)}

### Model Status

"""
            models = model_check.get("models", {})
            if models:
                for model_name, data in models.items():
                    status = "✅" if data.get("exists", False) else "❌"
                    report += f"- **{model_name}**: {status}\n"
        
        report += "\n---\n\n## 5. Temporal Consistency Verification\n\n"
        
        temporal_check = checks.get("temporal_consistency", {})
        if temporal_check:
            report += f"""**Status:** {temporal_check.get('status', 'unknown').upper()}

### Results

- **Games Before Week 5:** {temporal_check.get('games_before_week5', 0)}
- **Week 5+ Filter Applied:** {temporal_check.get('week5_plus_filter_applied', False)}

### Week Distribution (2025)

"""
            week_dist = temporal_check.get("2025_week_distribution", {})
            if week_dist:
                for week, count in sorted(week_dist.items()):
                    report += f"- Week {week}: {count} games\n"
        
        report += "\n---\n\n## 6. Data Leakage Verification\n\n"
        
        leakage_check = checks.get("data_leakage", {})
        if leakage_check:
            report += f"""**Status:** {leakage_check.get('status', 'unknown').upper()}

### Results

- **No Data Leakage:** {leakage_check.get('no_data_leakage', False)}
- **Methodology Correct:** {leakage_check.get('methodology_correct', False)}

### Correlation Check

"""
            corr_check = leakage_check.get("correlation_check", {})
            if corr_check:
                correlation = corr_check.get("correlation")
                if correlation is not None:
                    report += f"- **Correlation (home_adjusted_epa vs margin):** {correlation:.4f}\n"
                    report += f"- **Within Expected Range:** {corr_check.get('within_expected_range', False)}\n"
            
            leakage_warning = leakage_check.get("leakage_warning")
            if leakage_warning:
                report += f"\n⚠️  **Warning:** {leakage_warning}\n"
        
        report += "\n---\n\n## Recommendations\n\n"
        
        recommendations = summary.get("recommendations", [])
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                report += f"{i}. {rec}\n"
        else:
            report += "No recommendations - all checks passed.\n"
        
        report += "\n---\n\n## Conclusion\n\n"
        
        overall_status = summary.get("overall_status", "unknown")
        if overall_status == "pass":
            report += "✅ **All calculation verifications passed.** The system follows best practices for:\n"
            report += "- EPA calculations\n"
            report += "- Opponent adjustments (subtraction-based methodology)\n"
            report += "- Feature engineering (86 features)\n"
            report += "- Model compatibility\n"
            report += "- Temporal consistency\n"
            report += "- Data leakage prevention\n"
        else:
            report += "⚠️  **Some verification checks found issues.** Please review the recommendations above.\n"
        
        return report
    
    def save_markdown_report(self, markdown_content: str) -> Path:
        """Save markdown report"""
        report_path = self.reports_dir / "calculation_verification_report.md"
        
        with open(report_path, 'w') as f:
            f.write(markdown_content)
        
        print(f"✅ Markdown report saved to: {report_path}")
        return report_path
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate complete verification report"""
        print("=" * 80)
        print("GENERATING CALCULATION VERIFICATION REPORT")
        print("=" * 80)
        
        # Load verification results
        results = self.load_verification_results()
        if not results:
            return {"status": "error", "message": "No verification results found"}
        
        # Generate markdown report
        markdown_content = self.generate_markdown_report(results)
        report_path = self.save_markdown_report(markdown_content)
        
        return {
            "status": "success",
            "markdown_report": str(report_path),
            "json_report": str(self.verification_report_json),
            "overall_status": results.get("summary", {}).get("overall_status", "unknown")
        }


def main():
    """Main execution"""
    generator = CalculationVerificationReportGenerator()
    results = generator.generate_report()
    
    print("\n" + "=" * 80)
    print("REPORT GENERATION COMPLETE")
    print("=" * 80)
    print(f"Markdown Report: {results.get('markdown_report', 'N/A')}")
    print(f"JSON Report: {results.get('json_report', 'N/A')}")
    print(f"Overall Status: {results.get('overall_status', 'unknown').upper()}")
    
    return 0 if results.get('status') == 'success' else 1


if __name__ == "__main__":
    sys.exit(main())

