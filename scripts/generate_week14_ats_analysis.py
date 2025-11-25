#!/usr/bin/env python3
"""
Generate Week 14 ATS (Against The Spread) Analysis

Creates a comprehensive ATS analysis table with picks, confidence grades,
and human-readable summaries from model predictions.
"""

import sys
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

PROJECT_ROOT = Path(__file__).parent.parent
PREDICTIONS_DIR = PROJECT_ROOT / "predictions" / "week14"
CALIBRATED_PATH = PREDICTIONS_DIR / "week14_predictions_enhanced_calibrated.csv"
ENHANCED_PATH = PREDICTIONS_DIR / "week14_predictions_enhanced.csv"
JSON_PATH = PREDICTIONS_DIR / "week14_model_predictions.json"
ATS_OUT_PATH = PREDICTIONS_DIR / "week14_ats_full_table.csv"
ATS_JSON_OUT = PROJECT_ROOT / "web_app" / "public" / "week14_ats_data.json"
ATS_CSV_PUBLIC = PROJECT_ROOT / "web_app" / "public" / "week14_ats_full_table.csv"


def pick_side(row: pd.Series) -> str:
    """
    Determine ATS pick team based on edge calculation.

    Args:
        row: DataFrame row with ats_edge_home field

    Returns:
        Team name to pick or "No Edge" if edge is too small
    """
    if row["ats_edge_home"] > 0.25:  # Small buffer to avoid true coin flips
        return row["home_team"]
    elif row["ats_edge_home"] < -0.25:
        return row["away_team"]
    else:
        return "No Edge"


def ats_pick_str(row: pd.Series) -> str:
    """
    Build human-readable ATS pick string.

    Args:
        row: DataFrame row with ATS pick information

    Returns:
        Formatted ATS pick string (e.g., "Ohio State +9.5")
    """
    home_line = row["spread"]
    if row["ats_pick_team"] == "No Edge":
        return "Pass / No Edge"
    if row["ats_pick_team"] == row["home_team"]:
        # Home line is the actual Vegas line displayed for this bet
        sign = "+" if home_line > 0 else ""
        return f"{row['home_team']} {sign}{home_line:.1f}"
    else:
        # Away line is the opposite of home line
        away_line = -home_line
        sign = "+" if away_line > 0 else ""
        return f"{row['away_team']} {sign}{away_line:.1f}"


def confidence_grade(row: pd.Series) -> str:
    """
    Calculate confidence grade based on edge, ensemble confidence, and agreement.

    Args:
        row: DataFrame row with model_edge_pts, ensemble_confidence, model_agreement

    Returns:
        Confidence grade: "High", "Medium", or "Low"
    """
    edge = row["model_edge_pts"]
    conf = row["ensemble_confidence"]
    agree = row["model_agreement"]

    if edge >= 7 and conf >= 0.7 and agree == "high":
        return "High"
    if edge >= 4 and conf >= 0.6:
        return "Medium"
    return "Low"


def make_summary(row: pd.Series) -> str:
    """
    Create a compact advanced-summary field with key insights.

    Args:
        row: DataFrame row with prediction data

    Returns:
        Human-readable summary string
    """
    side = row["ats_pick_team"]
    if side == "No Edge":
        return "Models and market are closely aligned; spread looks efficient."

    home = row["home_team"]
    away = row["away_team"]
    margin = row["predicted_margin"]
    edge = row["model_edge_pts"]
    agree = row["model_agreement"]
    conf = row["ensemble_confidence"]
    home_prob = row["home_win_prob"]
    spread = row["spread"]
    spread_str = f"{home} {spread:+.1f} (home line)"

    dir_desc = "home" if margin > 0 else "away"

    return (
        f"Models see the {dir_desc} side stronger than market: "
        f"predicted margin {margin:+.1f}, line {spread_str}, giving about "
        f"{edge:.1f} pts of value on {side}. Home win prob {home_prob:.0%}, "
        f"agreement {agree}, model confidence {conf:.2f}."
    )


def generate_ats_analysis() -> int:
    """
    Generate Week 14 ATS analysis from model predictions.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    print("📊 Generating Week 14 ATS Analysis...")
    print("=" * 60)

    # Load predictions, preferring calibrated enhanced CSV if present.
    df: Optional[pd.DataFrame] = None
    source: Path

    if CALIBRATED_PATH.exists():
        source = CALIBRATED_PATH
        df = pd.read_csv(CALIBRATED_PATH)
        margin_col = "market_adjusted_margin"
        print(f"✅ Loaded calibrated predictions from {source}")
    elif ENHANCED_PATH.exists():
        source = ENHANCED_PATH
        df = pd.read_csv(ENHANCED_PATH)
        margin_col = "predicted_margin"
        print(f"✅ Loaded enhanced predictions from {source}")
    elif JSON_PATH.exists():
        source = JSON_PATH
        df = pd.read_json(JSON_PATH)
        margin_col = "predicted_margin"
        print(f"✅ Loaded JSON predictions from {source}")
    else:
        print("❌ Predictions file not found (checked calibrated, enhanced, and JSON).")
        return 1

    print(f"Total games loaded: {len(df)}")
    if margin_col not in df.columns:
        print(f"❌ Required margin column '{margin_col}' missing in {source}")
        return 1

    # Normalize column names used below
    df = df.copy()
    df["predicted_margin"] = df[margin_col]

    # Basic derived fields
    df["matchup"] = df["away_team"] + " @ " + df["home_team"]

    # Use ensemble home win prob already in home_win_probability, away_win_probability
    df["home_win_prob"] = df["home_win_probability"]
    df["away_win_prob"] = df["away_win_probability"]

    # ATS edge: expected ATS margin for the HOME side
    # Formula: ATS_home = predicted_margin + spread
    # (margin = home - away, spread is home line)
    df["ats_edge_home"] = df["predicted_margin"] + df["spread"]

    # Determine ATS pick team
    df["ats_pick_team"] = df.apply(pick_side, axis=1)

    # Build human-readable ATS pick string
    df["ats_pick"] = df.apply(ats_pick_str, axis=1)

    # Edge magnitude in points vs spread
    df["model_edge_pts"] = df["ats_edge_home"].abs()

    # Confidence grade based on edge size + ensemble_confidence + model_agreement
    df["confidence_grade"] = df.apply(confidence_grade, axis=1)

    # Create a compact advanced-summary field
    df["model_summary"] = df.apply(make_summary, axis=1)

    # Build final, user-facing table
    final_cols = [
        "matchup",
        "spread",  # Vegas spread (home)
        "predicted_margin",
        "home_win_prob",
        "away_win_prob",
        "ats_pick",
        "model_edge_pts",
        "confidence_grade",
        "model_agreement",
        "ensemble_confidence",
        "model_summary",
    ]
    final_df = df[final_cols].copy()

    # Sort by biggest edges first for usability, but keep all games
    final_df = final_df.sort_values("model_edge_pts", ascending=False)

    # Save to CSV
    ATS_OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    final_df.to_csv(ATS_OUT_PATH, index=False)
    ATS_CSV_PUBLIC.parent.mkdir(parents=True, exist_ok=True)
    final_df.to_csv(ATS_CSV_PUBLIC, index=False)
    final_df.to_json(ATS_JSON_OUT, orient="records", indent=2)

    print(f"✅ ATS analysis saved to {ATS_OUT_PATH}")
    print(f"✅ Public CSV saved to {ATS_CSV_PUBLIC}")
    print(f"✅ Public JSON saved to {ATS_JSON_OUT}")
    print(f"\n📈 Top 10 ATS Picks by Edge:")
    print("=" * 60)
    print(final_df.head(10).to_string(index=False))

    return 0


if __name__ == "__main__":
    sys.exit(generate_ats_analysis())
