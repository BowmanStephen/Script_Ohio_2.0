#!/usr/bin/env python3
"""
Comprehensive Integration Demo (Compatibility Wrapper)

This script preserves the legacy CLI entrypoint used throughout the
documentation while delegating to the modern demonstration in
`agents/demo_agent_system.py`.  It also exposes optional hooks for
seasonal (Week 12) workflows so the comprehensive demo remains a
single place to exercise production agents.
"""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path
from typing import Callable, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.append(str(REPO_ROOT))

from agents.demo_agent_system import run_demo as run_modern_demo


def _resolve_optional_runner(module_path: str, attr: str) -> Optional[Callable[[], bool]]:
    """
    Attempt to import an optional Week 12 analysis runner.

    Parameters
    ----------
    module_path: str
        Dotted path to the module that exposes the runner.
    attr: str
        Attribute on the module that should be executed.
    """
    try:
        module = importlib.import_module(module_path)
        runner = getattr(module, attr)
        if not callable(runner):
            raise TypeError(f"{module_path}.{attr} is not callable")
        return runner
    except ModuleNotFoundError:
        return None
    except Exception as exc:  # pragma: no cover - defensive logging
        print(f"[WARN] Failed to import optional runner {module_path}.{attr}: {exc}")
        return None


def run_week12_workflows() -> bool:
    """Execute optional Week 12 specialist workflows when available."""
    runners = [
        ("week12_digestible_analysis.scripts.generate_predictions", "run"),
        ("week12_digestible_analysis.scripts.generate_digestible_summary", "run"),
    ]

    results = []
    for module, attr in runners:
        runner = _resolve_optional_runner(module, attr)
        if runner is None:
            continue
        print(f"\n📊 Running Week 12 workflow: {module}.{attr}")
        try:
            result = runner()
            results.append(bool(result))
        except Exception as exc:  # pragma: no cover - logging helper
            results.append(False)
            print(f"[ERROR] Week 12 workflow {module}.{attr} failed: {exc}")

    if not results:
        print("ℹ️  No Week 12 workflow modules detected; skipping specialist runs.")
        return True

    success = all(results)
    summary = f"{results.count(True)}/{len(results)}"
    print(f"\nWeek 12 workflows completed: {summary} succeeded.")
    return success


def run_demo(include_week12: bool = False) -> bool:
    """Run the comprehensive demo (modern demo + optional Week 12 flows)."""
    print("🚀 SCRIPT OHIO 2.0 - COMPREHENSIVE INTEGRATION DEMO")
    print("=" * 70)

    success = run_modern_demo()

    if include_week12:
        success = run_week12_workflows() and success

    print("\nComprehensive demo finished:", "✅ SUCCESS" if success else "⚠️ CHECK LOGS")
    return success


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the Script Ohio 2.0 comprehensive integration demo."
    )
    parser.add_argument(
        "--include-week12",
        action="store_true",
        help="Attempt to run optional Week 12 specialist workflows if modules are present.",
    )
    args = parser.parse_args()

    success = run_demo(include_week12=args.include_week12)
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())

