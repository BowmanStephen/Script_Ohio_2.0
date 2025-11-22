#!/usr/bin/env python3
"""
COMPREHENSIVE 2025 DATA VALIDATION EXECUTOR
Main script to run all validation agents and generate final certification

Usage: python run_comprehensive_validation.py

This script will:
1. Execute all 5 validation agents
2. Generate comprehensive validation report
3. Provide final data readiness certification
4. Save all results for documentation

Created: 2025-11-13
Purpose: Execute complete 2025 college football data validation pipeline
"""

import sys
import os
import json
from datetime import datetime, timezone
from pathlib import Path

# Add current directory to Python path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

try:
    from data_authenticity_orchestrator import DataAuthenticityOrchestrator
except ImportError as e:
    print(f"❌ Failed to import orchestrator: {e}")
    print("Make sure you're running this script from the DATA_VALIDATION directory")
    sys.exit(1)

def main():
    """Main execution function"""
    print("="*80)
    print("🏈 COMPREHENSIVE 2025 COLLEGE FOOTBALL DATA VALIDATION")
    print("="*80)
    print(f"📅 Execution Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Target Validation: November 13, 2025 (Week 12)")
    print("="*80)

    # Initialize orchestrator
    try:
        project_root = current_dir.parent.parent
        orchestrator = DataAuthenticityOrchestrator(str(project_root))
        print("✅ Data Authenticity Orchestrator initialized")
    except Exception as e:
        print(f"❌ Failed to initialize orchestrator: {e}")
        sys.exit(1)

    # Execute comprehensive validation
    try:
        print("\n🚀 Starting comprehensive validation pipeline...")
        validation_results = orchestrator.orchestrate_validation()
        print("✅ Validation pipeline completed")
    except Exception as e:
        print(f"❌ Validation pipeline failed: {e}")
        sys.exit(1)

    # Display results summary
    print("\n" + "="*80)
    print("📊 VALIDATION RESULTS SUMMARY")
    print("="*80)

    overall_score = validation_results.get("data_authenticity_score", 0.0)
    ready_for_models = validation_results.get("ready_for_models", False)
    blocking_issues = validation_results.get("blocking_issues", [])
    total_duration = validation_results.get("total_duration_seconds", 0)

    print(f"🎯 Overall Data Authenticity Score: {overall_score:.1%}")
    print(f"🤖 Ready for Model Retraining: {'✅ YES' if ready_for_models else '❌ NO'}")
    print(f"⏱️ Total Validation Time: {total_duration:.1f} seconds")
    print(f"🚨 Blocking Issues: {len(blocking_issues)}")

    # Display round-by-round results
    print(f"\n📋 Validation Rounds:")
    for round_result in validation_results.get("validation_rounds", []):
        round_name = round_result.get("round_name", "Unknown")
        round_success = "✅ Success" if round_result.get("success", False) else "❌ Issues"
        round_duration = round_result.get("duration_seconds", 0)
        agents_executed = round_result.get("agents_executed", [])

        print(f"   🔸 {round_name}: {round_success} ({round_duration:.1f}s)")
        print(f"      Agents: {', '.join(agents_executed)}")

        # Show specific round issues
        round_issues = round_result.get("blocking_issues", [])
        if round_issues:
            for issue in round_issues[:2]:  # Show first 2 issues
                print(f"      ❌ {issue}")

    # Display critical issues
    if blocking_issues:
        print(f"\n🚨 CRITICAL BLOCKING ISSUES:")
        for i, issue in enumerate(blocking_issues, 1):
            print(f"   {i}. {issue}")

    # Generate final recommendation
    print(f"\n💡 FINAL RECOMMENDATION:")
    if ready_for_models:
        print("   ✅ DATA IS READY FOR MODEL RETRAINING")
        print("   ✅ All critical validations passed")
        print("   ✅ Data authenticity confirmed")
    else:
        print("   ❌ DATA IS NOT READY FOR MODEL RETRAINING")
        print("   ❌ Critical issues must be resolved first")
        print("   ❌ Review blocking issues above")

    # Additional insights
    print(f"\n🔍 KEY INSIGHTS:")

    # API Authentication insights
    api_round = next((r for r in validation_results.get("validation_rounds", [])
                     if "API" in r.get("round_name", "")), None)
    if api_round:
        api_results = api_round.get("results", {})
        api_agent = next((v for k, v in api_results.items() if "API" in k), {})
        if api_agent.get("tested_endpoints"):
            successful_endpoints = sum(1 for ep in api_agent.get("tested_endpoints", [])
                                     if ep.get("status") == "success")
            total_endpoints = len(api_agent.get("tested_endpoints", []))
            print(f"   📡 CFBD API: {successful_endpoints}/{total_endpoints} endpoints successful")

    # Temporal validation insights
    temporal_round = next((r for r in validation_results.get("validation_rounds", [])
                          if "Temporal" in r.get("round_name", "")), None)
    if temporal_round:
        temporal_results = temporal_round.get("results", {})
        temporal_agent = next((v for k, v in temporal_results.items() if "Temporal" in k), {})
        if temporal_agent.get("currency_checks", {}).get("current_week", {}).get("games_found", 0) > 0:
            week_12_games = temporal_agent.get("currency_checks", {}).get("current_week", {}).get("games_found", 0)
            print(f"   📅 Week 12 Data: {week_12_games} games found")

    # Data structure insights
    structure_round = next((r for r in validation_results.get("validation_rounds", [])
                           if "Structure" in r.get("round_name", "")), None)
    if structure_round:
        structure_results = structure_round.get("results", {})
        structure_agent = next((v for k, v in structure_results.items() if "Structure" in k), {})
        fixes_applied = structure_agent.get("column_fixes_applied", [])
        if fixes_applied:
            print(f"   🔧 Column Fixes: {len(fixes_applied)} fixes applied")

    # Save comprehensive report
    try:
        results_dir = current_dir
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Save JSON results
        json_file = results_dir / f"comprehensive_validation_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(validation_results, f, indent=2, default=str)

        # Save human-readable summary
        summary_file = results_dir / f"validation_summary_{timestamp}.md"
        with open(summary_file, 'w') as f:
            f.write("# 2025 College Football Data Validation Report\n\n")
            f.write(f"**Validation Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Target Date:** November 13, 2025 (Week 12)\n\n")

            f.write("## Executive Summary\n\n")
            f.write(f"- **Overall Authenticity Score:** {overall_score:.1%}\n")
            f.write(f"- **Ready for Models:** {'Yes ✅' if ready_for_models else 'No ❌'}\n")
            f.write(f"- **Validation Duration:** {total_duration:.1f} seconds\n")
            f.write(f"- **Blocking Issues:** {len(blocking_issues)}\n\n")

            if blocking_issues:
                f.write("## 🚨 Critical Issues\n\n")
                for i, issue in enumerate(blocking_issues, 1):
                    f.write(f"{i}. {issue}\n")
                f.write("\n")

            f.write("## Validation Rounds\n\n")
            for round_result in validation_results.get("validation_rounds", []):
                f.write(f"### {round_result.get('round_name', 'Unknown')}\n")
                f.write(f"- **Status:** {'Success ✅' if round_result.get('success', False) else 'Issues ❌'}\n")
                f.write(f"- **Duration:** {round_result.get('duration_seconds', 0):.1f} seconds\n")
                f.write(f"- **Agents:** {', '.join(round_result.get('agents_executed', []))}\n\n")

            f.write("---\n")
            f.write("*Generated by Comprehensive Data Validation System*")

        print(f"\n📄 Reports saved:")
        print(f"   📊 Detailed JSON: {json_file.name}")
        print(f"   📋 Summary Report: {summary_file.name}")

    except Exception as e:
        print(f"\n⚠️ Warning: Could not save reports: {e}")

    print("\n" + "="*80)
    print("🏈 VALIDATION COMPLETE")
    print("="*80)

    # Return appropriate exit code
    if ready_for_models:
        print("✅ Your 2025 data is ready for model retraining!")
        return 0
    else:
        print("❌ Please resolve blocking issues before proceeding with model retraining.")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️ Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        sys.exit(1)