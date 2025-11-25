#!/usr/bin/env python3
"""
Comprehensive Week 14 enhancement workflow.

This script chains feature generation, weekly analysis, model predictions, and
optional SP+ enrichment into a single, logged command.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple

# Ensure project root and scripts directory are importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from agents.weekly_analysis_orchestrator import WeeklyAnalysisOrchestrator
from generate_week14_enhanced_features import generate_week14_enhanced_features
from predict_week14_proper import run_prediction_pipeline
from enhance_week14_with_sp import main as enhance_with_sp_main

LOG_FILE = PROJECT_ROOT / "logs" / "enhance_week14_comprehensive.log"
WEEK14_METADATA = (
    PROJECT_ROOT / "data" / "weekly" / "week14" / "enhanced" / "enhancement_metadata.json"
)
WEEK14_PREDICTIONS_DIR = PROJECT_ROOT / "predictions" / "week14"

StepRunner = Callable[[], Tuple[int, Dict[str, Any]]]


def setup_logging(verbose: bool) -> logging.Logger:
    """Configure console + file logging for the workflow."""
    LOG_FILE.parent.mkdir(exist_ok=True)
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
        force=True,
    )
    return logging.getLogger("week14_enhancement")


def load_metadata(path: Path) -> Dict[str, Any]:
    """Load JSON metadata if it exists."""
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return {}


def run_feature_generation_step() -> Tuple[int, Dict[str, Any]]:
    """Generate Week 14 enhanced features and capture metadata."""
    exit_code = generate_week14_enhanced_features()
    details: Dict[str, Any] = {}
    if exit_code == 0:
        details["metadata"] = load_metadata(WEEK14_METADATA)
    return exit_code, details


def run_weekly_analysis_step(
    week: int, season: int, analysis_step: str
) -> Tuple[int, Dict[str, Any]]:
    """Execute the requested WeeklyAnalysisOrchestrator step."""
    orchestrator = WeeklyAnalysisOrchestrator(week=week, season=season)

    if analysis_step == "all":
        result = orchestrator.run_complete_analysis()
        success = result.get("final_status", "").lower() == "success"
    elif analysis_step == "validation":
        result = orchestrator.validate_models()
        success = result.get("status") == "success"
    elif analysis_step == "matchup":
        result = orchestrator.analyze_matchups()
        success = result.get("status") == "success"
    else:  # predictions
        result = orchestrator.generate_predictions()
        success = result.get("status") == "success"

    return (0 if success else 1), {"result": result, "analysis_step": analysis_step}


def run_predictions_step(tune_hyperparameters: bool) -> Tuple[int, Dict[str, Any]]:
    """Run the Week 14 prediction pipeline."""
    exit_code = run_prediction_pipeline(tune_hyperparameters=tune_hyperparameters)
    outputs: Dict[str, Any] = {}
    if exit_code == 0:
        outputs["prediction_csv"] = str(WEEK14_PREDICTIONS_DIR / "week14_model_predictions.csv")
        outputs["prediction_json"] = str(WEEK14_PREDICTIONS_DIR / "week14_model_predictions.json")
    return exit_code, outputs


def run_sp_enhancement_step() -> Tuple[int, Dict[str, Any]]:
    """Enhance predictions with SP+ context."""
    exit_code = enhance_with_sp_main()
    outputs: Dict[str, Any] = {}
    if exit_code == 0:
        outputs["enhanced_predictions"] = str(
            WEEK14_PREDICTIONS_DIR / "week14_predictions_enhanced.csv"
        )
    return exit_code, outputs


def execute_step(
    name: str,
    enabled: bool,
    runner: StepRunner,
    *,
    continue_on_error: bool,
    logger: logging.Logger,
    results: List[Dict[str, Any]],
) -> Tuple[bool, bool]:
    """
    Execute a single workflow step.

    Returns:
        (should_continue, failed_this_step)
    """
    if not enabled:
        results.append({"name": name, "status": "skipped", "duration": 0.0, "details": {}})
        logger.info("⏭️  Skipping %s (disabled via flag)", name)
        return True, False

    logger.info("🚀 Starting step: %s", name)
    start = time.perf_counter()
    exit_code = 1
    details: Dict[str, Any] = {}

    try:
        exit_code, details = runner()
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("❌ Step %s raised an exception: %s", name, exc)

    duration = time.perf_counter() - start
    status = "success" if exit_code == 0 else "failed"
    logger.info("✅ Completed %s in %.2fs", name, duration) if exit_code == 0 else logger.error(
        "❌ %s failed in %.2fs (exit code %s)", name, duration, exit_code
    )

    results.append(
        {
            "name": name,
            "status": status,
            "duration": duration,
            "details": details,
        }
    )

    failed = exit_code != 0
    should_continue = (not failed) or continue_on_error
    return should_continue, failed


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Run the complete Week 14 enhancement workflow in one command."
    )
    parser.add_argument("--week", type=int, default=14, help="Week to process (default: 14)")
    parser.add_argument("--season", type=int, default=2025, help="Season year (default: 2025)")
    parser.add_argument(
        "--analysis-step",
        choices=["all", "validation", "matchup", "predictions"],
        default="all",
        help="Which WeeklyAnalysisOrchestrator step to execute.",
    )
    parser.add_argument("--skip-features", action="store_true", help="Skip feature generation.")
    parser.add_argument("--skip-analysis", action="store_true", help="Skip weekly analysis.")
    parser.add_argument("--skip-predictions", action="store_true", help="Skip prediction step.")
    parser.add_argument(
        "--include-sp",
        action="store_true",
        help="Run the optional SP+ enhancement step after predictions.",
    )
    parser.add_argument(
        "--tune-hyperparameters",
        action="store_true",
        help="Tune models before generating predictions.",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Attempt remaining steps even if one fails.",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging.")
    return parser.parse_args()


def summarize(results: List[Dict[str, Any]], logger: logging.Logger) -> None:
    """Emit a friendly summary of all step results."""
    logger.info("\n" + "=" * 80)
    logger.info("WEEK 14 ENHANCEMENT SUMMARY")
    logger.info("=" * 80)
    for entry in results:
        icon = {"success": "✅", "failed": "❌", "skipped": "⏭️ "}.get(entry["status"], "•")
        logger.info(
            "%s %-20s %-8s (%.2fs)",
            icon,
            entry["name"],
            entry["status"].upper(),
            entry["duration"],
        )
    logger.info("=" * 80 + "\n")


def main() -> int:
    args = parse_args()
    logger = setup_logging(args.verbose)

    if args.week != 14:
        logger.warning(
            "This workflow is purpose-built for Week 14. Provided week=%s may not be fully supported.",
            args.week,
        )

    results: List[Dict[str, Any]] = []
    had_failure = False

    step_plan = [
        (
            "Enhanced Features",
            not args.skip_features,
            run_feature_generation_step,
        ),
        (
            "Weekly Analysis",
            not args.skip_analysis,
            lambda: run_weekly_analysis_step(args.week, args.season, args.analysis_step),
        ),
        (
            "Model Predictions",
            not args.skip_predictions,
            lambda: run_predictions_step(args.tune_hyperparameters),
        ),
    ]

    if args.include_sp:
        step_plan.append(("SP+ Enhancement", True, run_sp_enhancement_step))

    for name, enabled, runner in step_plan:
        should_continue, failed = execute_step(
            name,
            enabled,
            runner,
            continue_on_error=args.continue_on_error,
            logger=logger,
            results=results,
        )
        if failed:
            had_failure = True
        if not should_continue:
            break

    summarize(results, logger)
    final_status = 1 if had_failure else 0
    if final_status == 0:
        logger.info("🎉 Week 14 enhancement workflow completed successfully!")
    else:
        logger.error("⚠️  Workflow completed with failures. See log for details.")
    logger.info("Log file: %s", LOG_FILE)

    return final_status


if __name__ == "__main__":
    sys.exit(main())

