#!/usr/bin/env python3
"""
Calibrate model-predicted margins against market spreads.

Loads a predictions CSV (with columns: predicted_margin, spread) and reports the
average edge (predicted_margin + spread). Applies a simple bias correction to
recentre edges around zero and saves an adjusted CSV with new columns:
`market_adjusted_margin` and `market_adjusted_edge`.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Literal, Tuple

import pandas as pd


def compute_bias(df: pd.DataFrame) -> Tuple[float, float, float]:
    """Compute mean/median/std of edge (model vs market).

    Args:
        df: DataFrame with columns `predicted_margin` and `spread`.

    Returns:
        Tuple of (mean_edge, median_edge, std_edge).
    """
    edges = df["predicted_margin"] + df["spread"]
    return float(edges.mean()), float(edges.median()), float(edges.std())


def apply_bias_correction(df: pd.DataFrame, bias: float) -> pd.DataFrame:
    """Apply a bias correction to predicted margins.

    Args:
        df: Predictions DataFrame.
        bias: Bias to remove (mean edge). New margin = predicted_margin - bias.

    Returns:
        DataFrame with added `market_adjusted_margin` and `market_adjusted_edge`.
    """
    adjusted = df.copy()
    adjusted["market_adjusted_margin"] = adjusted["predicted_margin"] - bias
    adjusted["market_adjusted_edge"] = (
        adjusted["market_adjusted_margin"] + adjusted["spread"]
    )
    return adjusted


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Calibrate predicted margins vs market spreads."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("predictions/week14/week14_predictions_enhanced.csv"),
        help="Path to predictions CSV (must include predicted_margin, spread).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("predictions/week14/week14_predictions_enhanced_calibrated.csv"),
        help="Where to write calibrated CSV.",
    )
    parser.add_argument(
        "--method",
        choices=["mean", "median"],
        default="median",
        help="Bias estimator to use (mean or median).",
    )
    return parser.parse_args()


def main() -> int:
    """Entrypoint for calibration."""
    args = parse_args()
    if not args.input.exists():
        raise FileNotFoundError(f"Input file not found: {args.input}")

    df = pd.read_csv(args.input)
    mean_edge, median_edge, std_edge = compute_bias(df)

    print("Current edge vs market (predicted_margin + spread):")
    print(f"  mean   : {mean_edge:+.3f}")
    print(f"  median : {median_edge:+.3f}")
    print(f"  std    : {std_edge:.3f}")

    bias_value = median_edge if args.method == "median" else mean_edge

    adjusted = apply_bias_correction(df, bias_value)
    new_mean, new_median, new_std = compute_bias(
        adjusted.assign(predicted_margin=adjusted["market_adjusted_margin"])
    )

    print("\nAfter bias correction (edges recomputed with adjusted margin):")
    print(f"  mean   : {new_mean:+.3f}")
    print(f"  median : {new_median:+.3f}")
    print(f"  std    : {new_std:.3f}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    adjusted.to_csv(args.output, index=False)
    print(f"\n✅ Saved calibrated predictions to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
