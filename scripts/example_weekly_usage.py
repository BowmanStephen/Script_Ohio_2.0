#!/usr/bin/env python3
"""
Example Usage of Weekly Analysis Agents
Demonstrates various ways to use the weekly analysis system
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def example_1_complete_pipeline():
    """Example 1: Run complete analysis pipeline using orchestrator"""
    print("=" * 70)
    print("Example 1: Complete Analysis Pipeline")
    print("=" * 70)
    
    from agents.weekly_analysis_orchestrator import WeeklyAnalysisOrchestrator
    
    # Initialize orchestrator for Week 13
    orchestrator = WeeklyAnalysisOrchestrator(week=13, season=2025)
    
    # Run complete pipeline
    result = orchestrator.run_complete_analysis()
    
    print(f"\nStatus: {result.get('final_status')}")
    print(f"Steps Completed: {result.get('steps_completed', [])}")
    print(f"Completion Rate: {result.get('completion_rate', 0):.1%}")
    
    return result


def example_2_individual_agents():
    """Example 2: Use individual agents separately"""
    print("\n" + "=" * 70)
    print("Example 2: Individual Agents")
    print("=" * 70)
    
    from agents.weekly_matchup_analysis_agent import WeeklyMatchupAnalysisAgent
    from agents.weekly_model_validation_agent import WeeklyModelValidationAgent
    from agents.weekly_prediction_generation_agent import WeeklyPredictionGenerationAgent
    
    week = 13
    season = 2025
    
    # Step 1: Validate models
    print("\n1. Validating models...")
    validation_agent = WeeklyModelValidationAgent(week=week, season=season)
    validation_result = validation_agent.execute_task({})
    print(f"   Validation Status: {validation_result.get('status')}")
    
    # Step 2: Analyze matchups
    print("\n2. Analyzing matchups...")
    matchup_agent = WeeklyMatchupAnalysisAgent(week=week, season=season)
    matchup_result = matchup_agent.execute_task({})
    print(f"   Matchups Analyzed: {matchup_result.get('matchups_analyzed', 0)}")
    
    # Step 3: Generate predictions
    print("\n3. Generating predictions...")
    prediction_agent = WeeklyPredictionGenerationAgent(week=week, season=season)
    prediction_result = prediction_agent.execute_task({})
    print(f"   Games Predicted: {prediction_result.get('games_predicted', 0)}")
    
    return {
        'validation': validation_result,
        'matchup': matchup_result,
        'prediction': prediction_result
    }


def example_3_backward_compatibility():
    """Example 3: Using Week 12 agents (backward compatible)"""
    print("\n" + "=" * 70)
    print("Example 3: Backward Compatibility (Week 12 Agents)")
    print("=" * 70)
    
    from agents.week12_matchup_analysis_agent import Week12MatchupAnalysisAgent
    
    # Week 12 agents work exactly as before
    agent = Week12MatchupAnalysisAgent()
    result = agent.execute_task({
        'operation': 'analyze_matchups',
        'target_week': 12,
        'season': 2025
    })
    
    print(f"Status: {result.get('status')}")
    print(f"Matchups Analyzed: {result.get('matchups_analyzed', 0)}")
    print("\n✅ Week 12 agents still work - they delegate to weekly agents internally")
    
    return result


def example_4_multiple_weeks():
    """Example 4: Analyze multiple weeks"""
    print("\n" + "=" * 70)
    print("Example 4: Analyzing Multiple Weeks")
    print("=" * 70)
    
    from agents.weekly_analysis_orchestrator import WeeklyAnalysisOrchestrator
    
    weeks = [13, 14, 15]
    results = {}
    
    for week in weeks:
        print(f"\nAnalyzing Week {week}...")
        orchestrator = WeeklyAnalysisOrchestrator(week=week, season=2025)
        result = orchestrator.run_complete_analysis()
        results[week] = result
        print(f"  Status: {result.get('final_status')}")
    
    return results


def example_5_custom_week():
    """Example 5: Analyze any custom week"""
    print("\n" + "=" * 70)
    print("Example 5: Custom Week Analysis")
    print("=" * 70)
    
    from agents.weekly_matchup_analysis_agent import WeeklyMatchupAnalysisAgent
    
    # Analyze Week 10 for 2024 season
    agent = WeeklyMatchupAnalysisAgent(week=10, season=2024)
    result = agent.execute_task({})
    
    print(f"Week: {agent.week}, Season: {agent.season}")
    print(f"Status: {result.get('status')}")
    
    return result


def main():
    """Run all examples"""
    print("\n" + "=" * 70)
    print("Weekly Analysis Agents - Usage Examples")
    print("=" * 70)
    print("\nThese examples demonstrate various ways to use the weekly analysis system.")
    print("Note: Some examples may fail if data files don't exist yet.")
    print()
    
    examples = [
        ("Complete Pipeline", example_1_complete_pipeline),
        ("Individual Agents", example_2_individual_agents),
        ("Backward Compatibility", example_3_backward_compatibility),
        ("Multiple Weeks", example_4_multiple_weeks),
        ("Custom Week", example_5_custom_week),
    ]
    
    import argparse
    parser = argparse.ArgumentParser(description="Run weekly analysis examples")
    parser.add_argument('--example', type=int, choices=range(1, 6),
                       help='Run specific example (1-5)')
    parser.add_argument('--all', action='store_true',
                       help='Run all examples')
    args = parser.parse_args()
    
    if args.example:
        name, func = examples[args.example - 1]
        print(f"\nRunning: {name}")
        try:
            func()
        except Exception as e:
            print(f"\n❌ Example failed: {e}")
            import traceback
            traceback.print_exc()
    elif args.all:
        for name, func in examples:
            print(f"\n{'='*70}")
            print(f"Running: {name}")
            print('='*70)
            try:
                func()
            except Exception as e:
                print(f"\n❌ Example failed: {e}")
    else:
        print("Usage:")
        print("  python scripts/example_weekly_usage.py --example 1  # Run example 1")
        print("  python scripts/example_weekly_usage.py --all        # Run all examples")
        print("\nAvailable examples:")
        for i, (name, _) in enumerate(examples, 1):
            print(f"  {i}. {name}")


if __name__ == "__main__":
    main()

