#!/usr/bin/env python3
"""Compare Script Ohio predictions vs other modeling systems (PredictionTracker-style).

This script aligns a Script Ohio predictions CSV (e.g., DK slate output) against
an external "systems" CSV that contains one row per game and many model spread
columns (e.g., `lineopen`, `linefpi`, `linemassey`, ...).

It produces:
- A merged CSV with side-by-side spreads and computed deltas
- A markdown report summarizing agreement and largest disagreements

Sign convention:
- System columns are assumed to be "home margin" (home - away). In the common
  PredictionTracker format, positive means the home team is favored.

Usage:
  python3 scripts/compare_predictions_to_systems.py \\
    --predictions predictions/draftkings_slate_2025/dk_slate_predictions_*.csv \\
    --systems reports/Prediction_Tracker_week13.csv
"""

from __future__ import annotations

import argparse
import glob
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, Optional, Sequence

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def normalize_team_name(team_name: str) -> str:
    """Normalize team names to improve cross-source matching."""
    if pd.isna(team_name) or not team_name:
        return ""

    team = str(team_name).strip()
    variations = {
        "Ohio St.": "Ohio State",
        "Ohio St": "Ohio State",
        "Miami-FL": "Miami",
        "Miami (FL)": "Miami",
        "Miami-Florida": "Miami",
        "Miami-OH": "Miami OH",
        "Miami (OH)": "Miami OH",
        "Miami Ohio": "Miami OH",
        "UL-Lafayette": "Louisiana",
        "Louisiana-Lafayette": "Louisiana",
        "UL-Monroe": "Louisiana Monroe",
        "Louisiana-Monroe": "Louisiana Monroe",
        "Appalachian State": "Appalachian State",
        "Appalachian St.": "Appalachian State",
        "App State": "Appalachian State",
        "Florida Atlantic": "FAU",
        "Florida International": "FIU",
        "San Jose St.": "San Jose State",
        "Boise St.": "Boise State",
        "Colorado St.": "Colorado State",
        "Oklahoma St.": "Oklahoma State",
        "Oregon St.": "Oregon State",
        "Washington St.": "Washington State",
        "Michigan St.": "Michigan State",
        "Iowa St.": "Iowa State",
        "Kansas St.": "Kansas State",
        "Kent St.": "Kent State",
        "NC St.": "NC State",
        "Penn St.": "Penn State",
        "Fresno St.": "Fresno State",
        "Utah St.": "Utah State",
        "Sam Houston St.": "Sam Houston State",
        "Middle Tenn.": "Middle Tennessee",
        "Northern Ill.": "Northern Illinois",
        "Western Mich.": "Western Michigan",
        "Central Mich.": "Central Michigan",
        "Texas-San Antonio": "UTSA",
        "LA Tech": "Louisiana Tech",
        "South Florida": "USF",
    }
    if team in variations:
        return variations[team]

    if "-" in team:
        parts = team.split("-")
        if len(parts) == 2:
            name, suffix = parts
            if suffix.upper() == "FL" and "Miami" in name:
                return "Miami"
            if suffix.upper() == "OH" and "Miami" in name:
                return "Miami OH"

    return team


def _parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--predictions",
        required=True,
        help="Path or glob to your predictions CSV (must include home_team/away_team).",
    )
    parser.add_argument(
        "--systems",
        required=True,
        help="Path to systems CSV (PredictionTracker-style).",
    )
    parser.add_argument(
        "--market-column",
        default="line",
        help="Which column in systems file is the market/consensus line (default: line).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "reports",
        help="Directory for outputs (default: reports/).",
    )
    return parser.parse_args(argv)


def _resolve_single_path(pattern: str) -> Path:
    matches = sorted(glob.glob(pattern))
    if not matches:
        path = Path(pattern)
        if path.exists():
            return path
        raise FileNotFoundError(f"No files match: {pattern}")
    return Path(matches[-1]).resolve()


def _normalize_team_series(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).map(normalize_team_name)


def _load_predictions(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, low_memory=False).dropna(how="all")
    required = {"home_team", "away_team", "model_home_margin"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            f"Predictions file {path} missing required columns: {sorted(missing)}"
        )

    out = df.copy()
    out["home_team_norm"] = _normalize_team_series(out["home_team"])
    out["away_team_norm"] = _normalize_team_series(out["away_team"])
    out["model_home_margin"] = pd.to_numeric(out["model_home_margin"], errors="coerce")
    return out


def _load_systems(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, low_memory=False).dropna(how="all")
    if {"home_team", "away_team"}.issubset(df.columns):
        home = df["home_team"]
        away = df["away_team"]
    elif {"home", "road"}.issubset(df.columns):
        home = df["home"]
        away = df["road"]
    else:
        raise ValueError(
            f"Systems file {path} must contain (home_team, away_team) or (home, road)."
        )

    out = df.copy()
    out["home_team_norm"] = _normalize_team_series(home)
    out["away_team_norm"] = _normalize_team_series(away)
    return out


def _candidate_system_columns(df: pd.DataFrame, *, market_column: str) -> list[str]:
    ignore = {
        "road",
        "home",
        "away_team",
        "home_team",
        "away_team_norm",
        "home_team_norm",
        market_column,
        "neutral",
        "neutral_site",
        "phcover",
        "phwin",
        # Dispersion metadata, not a prediction system.
        "linestd",
    }
    candidates: list[str] = []
    for col in df.columns:
        if col in ignore:
            continue
        if col.startswith("line") or col.startswith("ph"):
            candidates.append(col)
    return sorted(set(candidates))


@dataclass(frozen=True)
class SystemSummary:
    system: str
    n: int
    mae_vs_model: float
    bias_vs_model: float
    corr_vs_model: float
    mae_vs_market: float


def _safe_corr(a: pd.Series, b: pd.Series) -> float:
    mask = a.notna() & b.notna()
    if int(mask.sum()) < 3:
        return float("nan")
    return float(np.corrcoef(a[mask].astype(float), b[mask].astype(float))[0, 1])


def _summarize_systems(
    merged: pd.DataFrame,
    system_columns: Iterable[str],
    *,
    market_column: str,
) -> list[SystemSummary]:
    summaries: list[SystemSummary] = []
    model = merged["model_home_margin"]
    market = pd.to_numeric(merged.get(market_column), errors="coerce")
    for col in system_columns:
        series = pd.to_numeric(merged.get(col), errors="coerce")
        mask = model.notna() & series.notna()
        if int(mask.sum()) == 0:
            continue
        diff = (series - model).astype(float)
        mae_vs_model = float(diff[mask].abs().mean())
        bias_vs_model = float(diff[mask].mean())
        corr_vs_model = _safe_corr(series, model)

        mae_vs_market = float("nan")
        if market_column in merged.columns:
            mask_market = market.notna() & series.notna()
            if int(mask_market.sum()) > 0:
                mae_vs_market = float((series - market)[mask_market].abs().mean())

        summaries.append(
            SystemSummary(
                system=col,
                n=int(mask.sum()),
                mae_vs_model=mae_vs_model,
                bias_vs_model=bias_vs_model,
                corr_vs_model=corr_vs_model,
                mae_vs_market=mae_vs_market,
            )
        )
    summaries.sort(key=lambda s: (np.nan_to_num(s.mae_vs_model, nan=1e9), -s.n))
    return summaries


def _format_float(value: float) -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return ""
    return f"{value:.3f}"


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parse_args(argv)
    predictions_path = _resolve_single_path(str(args.predictions))
    systems_path = Path(args.systems).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    pred_df = _load_predictions(predictions_path)
    systems_df = _load_systems(systems_path)

    merged = pred_df.merge(
        systems_df,
        on=["away_team_norm", "home_team_norm"],
        how="left",
        suffixes=("", "_systems"),
    )

    market_column = str(args.market_column)
    system_columns = _candidate_system_columns(systems_df, market_column=market_column)
    if market_column in systems_df.columns and market_column not in system_columns:
        # Keep market column separate; it is treated as "truth" for edge calcs.
        pass

    merged["market_home_margin"] = pd.to_numeric(
        merged.get(market_column), errors="coerce"
    )
    merged["edge_vs_market"] = (
        merged["model_home_margin"] - merged["market_home_margin"]
    )

    summaries = _summarize_systems(merged, system_columns, market_column=market_column)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    merged_path = output_dir / f"prediction_system_comparison_{ts}.csv"
    merged.to_csv(merged_path, index=False)

    report_path = output_dir / f"prediction_system_comparison_{ts}.md"
    lines: list[str] = []
    lines.append("# Prediction Comparison Report\n")
    lines.append(f"Generated: {datetime.now().isoformat(timespec='seconds')}\n")
    lines.append(f"- Predictions: `{predictions_path}`")
    lines.append(f"- Systems: `{systems_path}`")
    lines.append(f"- Market column: `{market_column}`\n")

    matched = (
        int(merged["market_home_margin"].notna().sum())
        if market_column in merged.columns
        else int(merged["home_team_norm"].notna().sum())
    )
    lines.append(f"Matched rows: {matched} / {len(merged)}\n")

    if market_column in merged.columns:
        lines.append("## Your Model vs Market")
        edges = merged["edge_vs_market"].dropna()
        if not edges.empty:
            lines.append(
                f"- Mean edge (home margin): {_format_float(float(edges.mean()))}"
            )
            lines.append(
                f"- Mean abs edge: {_format_float(float(edges.abs().mean()))}\n"
            )

    if summaries:
        lines.append("## System Agreement (vs your model)")
        top = pd.DataFrame([s.__dict__ for s in summaries]).head(20)
        top = top.rename(
            columns={
                "system": "system_column",
                "mae_vs_model": "mae_vs_your_model",
                "bias_vs_model": "bias_vs_your_model",
                "corr_vs_model": "corr_vs_your_model",
                "mae_vs_market": "mae_vs_market",
            }
        )
        lines.append(_format_markdown_table(top))
        lines.append("")

    lines.append("## Biggest Disagreements (vs market)")
    if market_column in merged.columns:
        biggest = merged.loc[
            merged["edge_vs_market"].abs().sort_values(ascending=False).head(15).index
        ]
        view_cols = [
            c
            for c in [
                "date",
                "bowl",
                "away_team",
                "home_team",
                "model_home_margin",
                "market_home_margin",
                "edge_vs_market",
            ]
            if c in biggest.columns
        ]
        if view_cols:
            lines.append(_format_markdown_table(biggest[view_cols]))
        else:
            lines.append("No comparable rows.")

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"✅ Wrote {merged_path}")
    print(f"✅ Wrote {report_path}")
    return 0


def _format_markdown_table(df: pd.DataFrame) -> str:
    """Render a DataFrame to a markdown table without optional deps."""
    if df.empty:
        return ""

    headers = [str(col) for col in df.columns.tolist()]
    rows = df.astype(object).where(pd.notna(df), "").values.tolist()

    def stringify(value: object) -> str:
        text = str(value)
        return text.replace("|", "\\|")

    str_rows = [[stringify(v) for v in row] for row in rows]

    widths = [
        max(len(h), max((len(r[i]) for r in str_rows), default=0))
        for i, h in enumerate(headers)
    ]

    header_line = (
        "| " + " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers)) + " |"
    )
    sep_line = "| " + " | ".join("-" * widths[i] for i in range(len(headers))) + " |"
    body_lines = [
        "| "
        + " | ".join(str_rows[r][i].ljust(widths[i]) for i in range(len(headers)))
        + " |"
        for r in range(len(str_rows))
    ]
    return "\n".join([header_line, sep_line, *body_lines])


if __name__ == "__main__":
    raise SystemExit(main())
