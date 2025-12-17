#!/usr/bin/env python3
"""Utilities for generating the bowl betting evaluation guide."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def normalize_team_name(team_name: Any) -> str:
    """Normalize team names for matching across sources."""
    if team_name is None or (isinstance(team_name, float) and np.isnan(team_name)):
        return ""

    team = str(team_name).strip()
    if not team:
        return ""

    replacements = {
        "Appalachian St.": "Appalachian State",
        "Appalachian St": "Appalachian State",
        "App State": "Appalachian State",
        "Louisiana-Lafayette": "Louisiana",
        "UL-Lafayette": "Louisiana",
        "Miami (OH)": "Miami OH",
        "Miami-OH": "Miami OH",
        "Miami Ohio": "Miami OH",
        "Miami-FL": "Miami",
        "Miami (FL)": "Miami",
        "South Florida": "USF",
        "Florida International": "FIU",
        "Florida Intl.": "FIU",
        "Texas-San Antonio": "UTSA",
        "NC St.": "NC State",
        "Penn St.": "Penn State",
        "Fresno St.": "Fresno State",
        "Utah St.": "Utah State",
        "Washington St.": "Washington State",
        "Hawai'i": "Hawaii",
    }
    team = replacements.get(team, team)
    # remove punctuation / spacing for stable joins
    slug = team.lower().replace("’", "'").replace("&", "and").replace("'", "")
    slug = re.sub(r"[^a-z0-9]+", "", slug)
    return slug


def to_home_spread(road_spread: float) -> float:
    """Convert road-spread to home-spread."""
    return -float(road_spread)


@dataclass(frozen=True)
class ColumnOrientation:
    """Metadata for a system column orientation inference."""

    column: str
    correlation_to_line: float
    chosen_mode: str
    num_rows_used: int


def infer_and_normalize_system_columns(
    df: pd.DataFrame,
    *,
    market_road_col: str = "line",
    candidates: Optional[Sequence[str]] = None,
    corr_positive_road_threshold: float = 0.25,
    corr_negative_home_threshold: float = -0.25,
    min_rows: int = 8,
) -> Tuple[pd.DataFrame, list[ColumnOrientation]]:
    """Infer per-column orientation and compute *_home_spread columns.

    Assumption:
    - market_road_col is a road-spread (negative => road favored).
    - candidate columns are also road-spread by default.

    Heuristic:
    - Compute corr(candidate, market_road_col) on overlapping non-null rows.
    - If corr >= corr_positive_road_threshold => candidate is a road spread
      (home = -road).
    - If corr <= corr_negative_home_threshold => candidate is already a home
      spread (home = +home).
    - If corr is weak/NA or there are too few rows => default to road spread.
    """
    out = df.copy()
    orientations: list[ColumnOrientation] = []
    new_cols: dict[str, pd.Series] = {}

    if market_road_col not in out.columns:
        logger.warning(
            "Market road column %s not in dataframe; skipping inference",
            market_road_col,
        )
        return out, orientations

    market = pd.to_numeric(out[market_road_col], errors="coerce")
    if candidates is None:
        candidates = [
            c
            for c in out.columns
            if c.startswith("line") and c not in {market_road_col, "linestd"}
        ]

    for col in candidates:
        series = pd.to_numeric(out[col], errors="coerce")
        mask = market.notna() & series.notna()
        corr = float("nan")
        chosen_mode = "road"
        rows_used = int(mask.sum())
        if rows_used >= min_rows:
            corr = float(
                np.corrcoef(
                    market[mask].astype(float),
                    series[mask].astype(float),
                )[0, 1]
            )
            if not np.isnan(corr) and corr <= corr_negative_home_threshold:
                chosen_mode = "home"
            elif not np.isnan(corr) and corr >= corr_positive_road_threshold:
                chosen_mode = "road"
        out_col = f"{col}_road_aligned"
        aligned = series if chosen_mode == "road" else -series
        new_cols[out_col] = aligned

        orientations.append(
            ColumnOrientation(
                column=col,
                correlation_to_line=corr,
                chosen_mode=chosen_mode,
                num_rows_used=rows_used,
            )
        )
        new_cols[f"{col}_home_spread"] = (-aligned).where(aligned.notna(), pd.NA)

    # Normalize market/open as home spreads as well (assumed road spreads).
    for base in ["lineopen", "line"]:
        if base in out.columns:
            series = pd.to_numeric(out[base], errors="coerce")
            new_cols[f"{base}_home_spread"] = series.map(
                lambda v: to_home_spread(v) if pd.notna(v) else pd.NA,
            )

    if new_cols:
        out = pd.concat([out, pd.DataFrame(new_cols, index=out.index)], axis=1)

    if orientations:
        table = pd.DataFrame(
            [
                {
                    "column": meta.column,
                    "corr": meta.correlation_to_line,
                    "chosen_mode": meta.chosen_mode,
                    "n": meta.num_rows_used,
                }
                for meta in orientations
            ]
        )
        with pd.option_context("display.max_rows", 200, "display.width", 160):
            logger.info(
                "Spread polarity inference vs %s (corr>=%.2f => road, corr<=%.2f => home):\n%s",
                market_road_col,
                corr_positive_road_threshold,
                corr_negative_home_threshold,
                table.to_string(index=False),
            )

    return out, orientations


def pick_side_vs_dk(*, model_home_spread: float, dk_home_spread: float) -> str:
    """Pick ATS side based on whether model is more pro-home than DK."""
    if np.isnan(model_home_spread) or np.isnan(dk_home_spread):
        return "NA"
    if model_home_spread < dk_home_spread:
        return "HOME"
    if model_home_spread > dk_home_spread:
        return "AWAY"
    return "PASS"


def compute_agreement_rate(
    row: pd.Series,
    *,
    panel_cols_home: Sequence[str],
    dk_home_spread_col: str,
    your_home_spread_col: str,
) -> Tuple[float, int, list[str]]:
    """Compute agreement rate across panel sources and list disagreeing sources."""
    dk_val = row.get(dk_home_spread_col)
    your_val = row.get(your_home_spread_col)
    if pd.isna(dk_val) or pd.isna(your_val):
        return float("nan"), 0, []

    your_pick = pick_side_vs_dk(
        model_home_spread=float(your_val),
        dk_home_spread=float(dk_val),
    )
    if your_pick in {"NA", "PASS"}:
        return float("nan"), 0, []

    picks: list[Tuple[str, str]] = []
    for col in panel_cols_home:
        val = row.get(col)
        if pd.isna(val):
            continue
        src_pick = pick_side_vs_dk(model_home_spread=float(val), dk_home_spread=float(dk_val))
        if src_pick in {"NA", "PASS"}:
            continue
        picks.append((col, src_pick))

    if not picks:
        return float("nan"), 0, []

    agree = [1 if src == your_pick else 0 for _, src in picks]
    disagree_sources = [name for name, src in picks if src != your_pick]
    return float(np.mean(agree)), len(picks), disagree_sources


def compute_tier_and_reasons(
    row: pd.Series,
    *,
    edge_vs_dk_col: str = "edge_vs_dk",
    abs_edge_vs_dk_col: str = "abs_edge_vs_dk",
    edge_vs_market_col: str = "edge_vs_market",
    abs_edge_vs_market_col: str = "abs_edge_vs_market",
) -> Tuple[str, list[str]]:
    """Compute tier and human-readable reasons based on market edge primarily."""
    reasons: list[str] = []
    
    edge_dk = row.get(edge_vs_dk_col)
    abs_edge_dk = row.get(abs_edge_vs_dk_col)
    edge_mkt = row.get(edge_vs_market_col)
    abs_edge_mkt = row.get(abs_edge_vs_market_col)
    
    # Add reasons
    if pd.notna(edge_dk):
        reasons.append(f"EDGE_DK={float(edge_dk):.2f}")
    if pd.notna(edge_mkt):
        reasons.append(f"EDGE_MKT={float(edge_mkt):.2f}")
    
    # Flags
    move_data_issue = bool(row.get("flag_move_data_issue", False))
    dk_vs_mkt_conflict = bool(row.get("dk_vs_market_conflict", False))
    outlier_market = bool(row.get("flag_outlier_market", False))
    big_move = bool(row.get("flag_big_move", False))
    ratings_z = row.get("ratings_z")
    
    if move_data_issue:
        reasons.append("MOVE_DATA_ISSUE")
    if dk_vs_mkt_conflict:
        reasons.append("DK_VS_MKT_CONFLICT")
    if outlier_market:
        reasons.append("OUTLIER_MKT")
    if big_move and pd.notna(row.get("move_from_open")):
        reasons.append(f"BIG_MOVE={float(row.get('move_from_open')):.2f}")
    elif big_move:
        reasons.append("BIG_MOVE")
    if pd.notna(ratings_z):
        reasons.append(f"RATINGS_Z={float(ratings_z):.2f}")
    
    # X-REVIEW overrides (betting-relevant only)
    if move_data_issue:
        return "X-REVIEW", reasons
    if dk_vs_mkt_conflict:
        return "X-REVIEW", reasons
    if pd.notna(abs_edge_mkt) and float(abs_edge_mkt) >= 6.0:
        return "X-REVIEW", reasons
    if big_move and pd.notna(row.get("move_from_open")):
        move_val = abs(float(row.get("move_from_open")))
        if move_val >= 4.0:
            return "X-REVIEW", reasons
    # Optional: extreme ratings conflict with market
    if (pd.notna(ratings_z) and pd.notna(abs_edge_mkt) 
        and abs(float(ratings_z)) >= 3.0 
        and float(abs_edge_mkt) >= 3.0):
        return "X-REVIEW", reasons
    
    # Base tiers (market edge primary)
    if pd.isna(abs_edge_dk) or pd.isna(abs_edge_mkt):
        return "C", reasons
    
    abs_edge_dk_val = float(abs_edge_dk)
    abs_edge_mkt_val = float(abs_edge_mkt)
    
    # Tier A: Large edge vs both DK and market
    if abs_edge_dk_val >= 4.0 and abs_edge_mkt_val >= 2.0:
        return "A", reasons
    # Tier B: Moderate edge vs both
    if abs_edge_dk_val >= 2.5 and abs_edge_mkt_val >= 1.0:
        return "B", reasons
    # Tier C: Otherwise
    return "C", reasons


def validate_totals(
    df: pd.DataFrame,
    *,
    rf_total_col: str = "rf_total",
    dk_total_col: str = "dk_total",
) -> Dict[str, Any]:
    """Validate totals model scaling and alignment."""
    result: Dict[str, Any] = {"valid": False, "median": None, "corr": None, "reason": ""}

    if rf_total_col not in df.columns or dk_total_col not in df.columns:
        result["reason"] = "missing_columns"
        return result

    rf = pd.to_numeric(df[rf_total_col], errors="coerce")
    dk = pd.to_numeric(df[dk_total_col], errors="coerce")
    mask = rf.notna() & dk.notna()
    if int(mask.sum()) < 8:
        result["reason"] = "insufficient_data"
        return result

    median = float(rf[mask].median())
    corr = float(np.corrcoef(rf[mask].astype(float), dk[mask].astype(float))[0, 1])
    result["median"] = median
    result["corr"] = corr

    if median < 35.0 or median > 80.0:
        result["reason"] = "median_out_of_range"
        return result
    if np.isnan(corr) or corr < 0.3:
        result["reason"] = "low_correlation"
        return result

    result["valid"] = True
    result["reason"] = "ok"
    return result
