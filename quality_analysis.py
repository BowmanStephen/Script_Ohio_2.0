#!/usr/bin/env python3
"""
Comprehensive Code Quality Analysis for Script Ohio 2.0
Identifies naming conventions, hardcoded values, and code style issues
"""

import os
import re
from pathlib import Path


def run_quality_analysis():
    """Run comprehensive code quality checks"""

    issues_found = {
        "naming_conventions": [],
        "hardcoded_values": [],
        "code_style": [],
        "import_organization": [],
        "todo_comments": [],
    }

    # Key files to analyze
    key_files = [
        "src/cfbd_client/unified_client.py",
        "agents/meta_agent.py",
        "agents/project_management_agent.py",
        "scripts/run_weekly_analysis.py",
        "scripts/predict_bowls_2025.py",
    ]

    for file_path in key_files:
        if os.path.exists(file_path):
            print(f"Analyzing {file_path}...")

            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

                for i, line in enumerate(lines, 1):
                    line_stripped = line.strip()

                    # Check function names for camelCase
                    if line_stripped.startswith("def "):
                        func_match = re.search(r"def\s+([a-zA-Z_][a-zA-Z0-9_]*)", line)
                        if func_match:
                            func_name = func_match.group(1)
                            if re.match(r"[a-z]+[A-Z][a-zA-Z]*", func_name):
                                issues_found["naming_conventions"].append(
                                    f"{file_path}:{i}: Function uses camelCase: {func_name}"
                                )

                    # Check class names for snake_case
                    elif line_stripped.startswith("class "):
                        class_match = re.search(r"class\s+([A-Z][a-zA-Z0-9_]*)", line)
                        if class_match:
                            class_name = class_match.group(1)
                            if re.match(r"[a-z]+_[a-z]+", class_name):
                                issues_found["naming_conventions"].append(
                                    f"{file_path}:{i}: Class uses snake_case: {class_name}"
                                )

                    # Check TODO/FIXME comments
                    if re.search(r"\b(TODO|FIXME|XXX|HACK)\b", line, re.IGNORECASE):
                        issues_found["todo_comments"].append(
                            f"{file_path}:{i}: {line_stripped}"
                        )

                    # Check for hardcoded URLs
                    if "http" in line and '"' in line:
                        issues_found["hardcoded_values"].append(
                            f"{file_path}:{i}: URL: {line_stripped}"
                        )

                    # Check for hardcoded paths
                    if (
                        '"' in line
                        and (".py" in line or ".csv" in line or ".json" in line)
                    ) and ("/src/" in line or "/scripts/" in line):
                        issues_found["hardcoded_values"].append(
                            f"{file_path}:{i}: Path: {line_stripped}"
                        )

                    # Check for trailing whitespace
                    if line.rstrip() != line and not line_stripped.startswith("#"):
                        issues_found["code_style"].append(
                            f"{file_path}:{i}: Trailing whitespace"
                        )

                    # Check for magic numbers
                    if re.search(
                        r"\b[0-9]+\.[0-9]+\s*\*\s*[0-9]+\.[0-9]+\b", line_stripped
                    ):
                        issues_found["hardcoded_values"].append(
                            f"{file_path}:{i}: Magic number: {line_stripped}"
                        )

                    # Check for hardcoded sleep times
                    if "time.sleep(" in line_stripped:
                        issues_found["hardcoded_values"].append(
                            f"{file_path}:{i}: Sleep time: {line_stripped}"
                        )

    return issues_found


def generate_quality_report():
    """Generate comprehensive quality report"""

    print("=== COMPREHENSIVE CODE QUALITY ANALYSIS ===\n")

    issues = run_quality_analysis()

    # Report on each category
    for category, issues_list in issues.items():
        if issues_list:
            print(
                f'❌ {category.replace("_", " ").title()} ({len(issues_list)} issues):'
            )
            for issue in issues_list[:10]:  # Show first 10 of each type
                print(f"   • {issue}")
            if len(issues_list) > 10:
                print(f"   ... and {len(issues_list) - 10} more")
            print()
        else:
            print(f'✅ {category.replace("_", " ").title()}: No issues found\n')

    # Summary
    total_issues = sum(len(issues_list) for issues_list in issues.values())
    print(f"Total issues found: {total_issues}")

    # Priority assessment
    critical_issues = len(issues["hardcoded_values"]) + len(
        issues["naming_conventions"]
    )
    medium_issues = len(issues["code_style"]) + len(issues["import_organization"])
    documentation_issues = len(issues["todo_comments"])

    print(f"\nPriority Assessment:")
    print(f"Critical (Hardcoded values, Naming): {critical_issues}")
    print(f"Medium (Code style, Imports): {medium_issues}")
    print(f"Documentation (TODOs): {documentation_issues}")

    # Generate action plan
    print(f"\n=== ACTION PLAN ===")
    if critical_issues > 0:
        print(f"1. Address critical issues (Priority 1):")
        for issue in issues["hardcoded_values"][:5]:
            print(f"   - Fix: {issue}")
        for issue in issues["naming_conventions"][:5]:
            print(f"   - Fix: {issue}")

    if medium_issues > 0:
        print(f"2. Address medium issues (Priority 2):")
        for issue in issues["code_style"][:5]:
            print(f"   - Fix: {issue}")
        for issue in issues["import_organization"]:
            print(f"   - Fix: {issue}")

    if documentation_issues > 0:
        print(f"3. Address documentation issues (Priority 3):")
        for issue in issues["todo_comments"][:5]:
            print(f"   - Fix: {issue}")

    return issues


if __name__ == "__main__":
    generate_quality_report()
