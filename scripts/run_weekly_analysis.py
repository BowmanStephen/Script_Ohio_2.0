#!/usr/bin/env python3
"""
Run Weekly Analysis Script
Executes the complete weekly analysis pipeline using the WeeklyAnalysisOrchestrator
"""

import sys
import argparse
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging with file handler
logs_dir = Path(__file__).parent.parent / "logs"
logs_dir.mkdir(exist_ok=True)

log_file = logs_dir / "weekly_analysis.log"
log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Create handlers
file_handler = logging.FileHandler(log_file, encoding='utf-8')
file_handler.setFormatter(log_format)

console_handler = logging.StreamHandler()
console_handler.setFormatter(log_format)

# Configure logging with formatted handlers
logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, console_handler]
)

logger = logging.getLogger(__name__)

from agents.weekly_analysis_orchestrator import WeeklyAnalysisOrchestrator


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(
        description="Run complete weekly analysis pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run Week 13 analysis
  python scripts/run_weekly_analysis.py --week 13

  # Run Week 14 analysis for 2025 season
  python scripts/run_weekly_analysis.py --week 14 --season 2025

  # Run only model validation
  python scripts/run_weekly_analysis.py --week 13 --step validation

  # Run only matchup analysis
  python scripts/run_weekly_analysis.py --week 13 --step matchup

  # Run only predictions
  python scripts/run_weekly_analysis.py --week 13 --step predictions
        """
    )
    parser.add_argument('--week', type=int, required=True,
                       help='Week number to analyze')
    parser.add_argument('--season', type=int, default=2025,
                       help='Season year (default: 2025)')
    parser.add_argument('--step', choices=['all', 'validation', 'matchup', 'predictions'],
                       default='all',
                       help='Which step to run (default: all)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--massey-only', action='store_true',
                       help='Run only the Massey ratings solver and exit')
    parser.add_argument('--refresh-massey-cache', action='store_true',
                       help='Force recomputation of Massey ratings cache')
    parser.add_argument('--massey-output', type=Path,
                       help='Optional override path for Massey ratings CSV output')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    print("=" * 70)
    print(f"Week {args.week} Analysis Pipeline - Season {args.season}")
    print("=" * 70)
    print()
    
    try:
        if args.massey_only:
            from src.ratings.massey_ratings import MasseyConfig
            from src.ratings.rating_library import (
                build_rating_library,
                load_massey_ratings,
            )

            config_kwargs = {"season": args.season, "week": args.week}
            if args.massey_output:
                config_kwargs["cache_path"] = args.massey_output
            config = MasseyConfig(**config_kwargs)

            logger.info("Running Massey ratings solver...")
            ratings_df = load_massey_ratings(
                config=config,
                refresh=args.refresh_massey_cache,
                persist=True,
            )
            build_rating_library(
                season=args.season,
                refresh=False,
                massey_config=config,
                massey_df=ratings_df,
            )

            print("\n" + "=" * 70)
            print(f"Massey Ratings - Season {args.season}, Week {args.week}")
            print("=" * 70)
            print(f"Games solved: {len(ratings_df)}")
            print(f"Estimated HFA: {ratings_df['hfa'].iloc[0]:.2f} points")
            print("\nTop 5 teams:")
            for _, row in ratings_df.head(5).iterrows():
                print(f"  {row['team']:<20} {row['rating']:>6.2f}")
            print("\nRatings saved to:", config.resolved_cache_path())
            return 0

        logger.info("=" * 70)
        logger.info(f"Week {args.week} Analysis Pipeline - Season {args.season}")
        logger.info("=" * 70)
        logger.info("START: Weekly analysis initiated")
        
        # Initialize orchestrator
        logger.info("Initializing orchestrator...")
        orchestrator = WeeklyAnalysisOrchestrator(
            week=args.week,
            season=args.season
        )
        logger.info("✅ Orchestrator initialized")
        
        if args.step == 'all':
            # Run complete analysis pipeline
            print("🚀 Running complete analysis pipeline...")
            logger.info("Running complete analysis pipeline...")
            result = orchestrator.run_complete_analysis()
            
            print("\n" + "=" * 70)
            print("Analysis Results Summary")
            print("=" * 70)
            print(f"Status: {result.get('final_status', 'unknown')}")
            print(f"Completion Rate: {result.get('completion_rate', 0):.1%}")
            print(f"Steps Completed: {len(result.get('steps_completed', []))}/3")
            print(f"Steps Failed: {len(result.get('steps_failed', []))}")
            
            if result.get('steps_completed'):
                print("\n✅ Completed Steps:")
                for step in result['steps_completed']:
                    print(f"   - {step}")
            
            if result.get('steps_failed'):
                print("\n❌ Failed Steps:")
                for step in result['steps_failed']:
                    print(f"   - {step}")
            
            # Show detailed results
            if 'validation' in result:
                val_status = result['validation'].get('status', 'unknown')
                print(f"\n📊 Model Validation: {val_status}")
            
            if 'matchup_analysis' in result:
                matchup_status = result['matchup_analysis'].get('status', 'unknown')
                matchups = result['matchup_analysis'].get('matchups_analyzed', 0)
                print(f"📊 Matchup Analysis: {matchup_status} ({matchups} matchups)")
            
            if 'predictions' in result:
                pred_status = result['predictions'].get('status', 'unknown')
                games = result['predictions'].get('games_predicted', 0)
                print(f"📊 Predictions: {pred_status} ({games} games)")
            
        elif args.step == 'validation':
            print("🔍 Running model validation...")
            result = orchestrator.validate_models()
            print(f"\nValidation Status: {result.get('status', 'unknown')}")
            if result.get('models_ready_for_predictions'):
                print("✅ Models ready for predictions")
            else:
                print("⚠️  Models not ready for predictions")
            
        elif args.step == 'matchup':
            print("📊 Running matchup analysis...")
            result = orchestrator.analyze_matchups()
            print(f"\nMatchup Analysis Status: {result.get('status', 'unknown')}")
            print(f"Matchups Analyzed: {result.get('matchups_analyzed', 0)}")
            if result.get('status') == 'success':
                print(f"Analysis saved to: analysis/week{args.week}/")
            
        elif args.step == 'predictions':
            print("🎯 Generating predictions...")
            result = orchestrator.generate_predictions()
            print(f"\nPrediction Status: {result.get('status', 'unknown')}")
            print(f"Games Predicted: {result.get('games_predicted', 0)}")
            if result.get('status') == 'success':
                print(f"Predictions saved to: predictions/week{args.week}/")
        
        print("\n" + "=" * 70)
        print("✅ Analysis complete!")
        print("=" * 70)
        logger.info("END: Weekly analysis completed successfully")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error running analysis: {e}")
        logger.error(f"❌ Weekly analysis failed: {e}", exc_info=True)
        import traceback
        if args.verbose:
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

