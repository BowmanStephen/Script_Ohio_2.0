#!/usr/bin/env python3
"""
Verify Weekly Agents Script
Quick verification that all weekly agents are properly configured
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def verify_imports():
    """Verify all weekly agents can be imported"""
    print("🔍 Verifying agent imports...")

    try:
        from agents.weekly_matchup_analysis_agent import WeeklyMatchupAnalysisAgent

        print("✅ WeeklyMatchupAnalysisAgent imported successfully")
    except Exception as e:
        print(f"❌ Failed to import WeeklyMatchupAnalysisAgent: {e}")
        return False

    try:
        from agents.weekly_prediction_generation_agent import (
            WeeklyPredictionGenerationAgent,
        )

        print("✅ WeeklyPredictionGenerationAgent imported successfully")
    except Exception as e:
        print(f"❌ Failed to import WeeklyPredictionGenerationAgent: {e}")
        return False

    try:
        from agents.weekly_model_validation_agent import WeeklyModelValidationAgent

        print("✅ WeeklyModelValidationAgent imported successfully")
    except Exception as e:
        print(f"❌ Failed to import WeeklyModelValidationAgent: {e}")
        return False

    try:
        from agents.weekly_analysis_orchestrator import WeeklyAnalysisOrchestrator

        print("✅ WeeklyAnalysisOrchestrator imported successfully")
    except Exception as e:
        print(f"❌ Failed to import WeeklyAnalysisOrchestrator: {e}")
        return False

    return True


def verify_agent_initialization():
    """Verify agents can be initialized"""
    print("\n🔍 Verifying agent initialization...")

    try:
        from agents.weekly_analysis_orchestrator import WeeklyAnalysisOrchestrator
        from agents.weekly_matchup_analysis_agent import WeeklyMatchupAnalysisAgent
        from agents.weekly_model_validation_agent import WeeklyModelValidationAgent
        from agents.weekly_prediction_generation_agent import (
            WeeklyPredictionGenerationAgent,
        )

        # Test Week 13 initialization
        matchup_agent = WeeklyMatchupAnalysisAgent(week=13, season=2025)
        print(
            f"✅ WeeklyMatchupAnalysisAgent initialized: {matchup_agent.week}, {matchup_agent.season}"
        )

        prediction_agent = WeeklyPredictionGenerationAgent(week=13, season=2025)
        print(
            f"✅ WeeklyPredictionGenerationAgent initialized: {prediction_agent.week}, {prediction_agent.season}"
        )

        validation_agent = WeeklyModelValidationAgent(week=13, season=2025)
        print(
            f"✅ WeeklyModelValidationAgent initialized: {validation_agent.week}, {validation_agent.season}"
        )

        orchestrator = WeeklyAnalysisOrchestrator(week=13, season=2025)
        print(
            f"✅ WeeklyAnalysisOrchestrator initialized: {orchestrator.week}, {orchestrator.season}"
        )

        return True
    except Exception as e:
        print(f"❌ Failed to initialize agents: {e}")
        import traceback

        traceback.print_exc()
        return False


def verify_backward_compatibility():
    """Verify Week 12 agents still work"""
    print("\n🔍 Verifying backward compatibility (Week 12 agents)...")

    try:
        from agents.week12_matchup_analysis_agent import Week12MatchupAnalysisAgent
        from agents.week12_model_validation_agent import Week12ModelValidationAgent
        from agents.week12_prediction_generation_agent import (
            Week12PredictionGenerationAgent,
        )

        week12_matchup = Week12MatchupAnalysisAgent()
        print("✅ Week12MatchupAnalysisAgent initialized")

        week12_prediction = Week12PredictionGenerationAgent()
        print("✅ Week12PredictionGenerationAgent initialized")

        week12_validation = Week12ModelValidationAgent()
        print("✅ Week12ModelValidationAgent initialized")

        return True
    except Exception as e:
        print(f"❌ Failed to initialize Week 12 agents: {e}")
        import traceback

        traceback.print_exc()
        return False


def verify_directories():
    """Verify Week 13 directories exist"""
    print("\n🔍 Verifying Week 13 directory structure...")

    directories = [
        project_root / "data" / "week13" / "enhanced",
        project_root / "analysis" / "week13",
        project_root / "predictions" / "week13",
        project_root / "validation" / "week13",
    ]

    all_exist = True
    for directory in directories:
        if directory.exists():
            print(f"✅ {directory}")
        else:
            print(f"⚠️  {directory} (will be created when needed)")
            all_exist = False

    return True  # Directories will be created automatically


def main():
    """Main verification function"""
    print("=" * 70)
    print("Weekly Agents Verification")
    print("=" * 70)
    print()

    results = {
        "imports": verify_imports(),
        "initialization": verify_agent_initialization(),
        "backward_compatibility": verify_backward_compatibility(),
        "directories": verify_directories(),
    }

    print("\n" + "=" * 70)
    print("Verification Summary")
    print("=" * 70)

    all_passed = all(results.values())

    for check, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {check}")

    if all_passed:
        print("\n✅ All verifications passed! Weekly agents are ready to use.")
        return 0
    else:
        print("\n⚠️  Some verifications failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
