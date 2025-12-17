#!/usr/bin/env python3
"""
One-command postseason pipeline:
1) Ensure master training data is current (Week 15 + completed outcomes)
2) Retrain production models
3) Generate postseason/bowl projections

Usage:
  python3 scripts/run_postseason_pipeline.py
  python3 scripts/run_postseason_pipeline.py --skip-fastai
  python3 scripts/run_postseason_pipeline.py --allow-incomplete-new-rows
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional, Sequence

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-fastai", action="store_true")
    parser.add_argument("--allow-incomplete-new-rows", action="store_true")
    parser.add_argument("--run-validation-agent", action="store_true")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parse_args(argv)
    from agents.postseason_projection_agent import PostseasonProjectionAgent

    agent = PostseasonProjectionAgent("postseason_projection")
    result = agent._execute_action(
        "run_postseason_pipeline",
        {
            "skip_fastai": args.skip_fastai,
            "allow_incomplete_new_rows": args.allow_incomplete_new_rows,
            "run_validation_agent": args.run_validation_agent,
        },
        {"user_id": "system"},
    )
    print(result["predictions_path"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
