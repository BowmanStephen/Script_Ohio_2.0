#!/usr/bin/env python3
"""Generate a bowl betting *evaluation guide* (compare your model vs others).

This script upgrades the existing bowl guide into a comparison-first evaluation:
- Normalizes every spread into a single canonical **home spread** representation:
  - `home_spread < 0` => home favored
  - `home_spread > 0` => home underdog
- Compares your model to:
  - DK market (from the slate)
  - Market open/current + consensus stats (from the systems file)
  - Selected system lines (Sagarin, Massey, Elo, FEI, FPI if available)
- Produces standardized diagnostics, flags, and explainable tier logic.
"""

from __future__ import annotations

import argparse
import glob
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Sequence

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.bowl_guide_utils import (  # noqa: E402
    compute_agreement_rate,
    compute_tier_and_reasons,
    infer_and_normalize_system_columns,
    normalize_team_name,
    validate_totals,
)


def _resolve_latest(pattern: str) -> Path:
    matches = sorted(glob.glob(pattern))
    if not matches:
        path = Path(pattern)
        if path.exists():
            return path
        raise FileNotFoundError(f"No files match: {pattern}")
    return Path(matches[-1]).resolve()


def _parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--slate",
        default="predictions/draftkings_slate_2025/dk_slate_predictions_*.csv",
        help="Path or glob to Script Ohio slate predictions CSV (default: latest DK slate).",
    )
    parser.add_argument(
        "--systems",
        default="predictions/ncaapredictions.csv",
        help="Path to multi-system lines CSV (default: predictions/ncaapredictions.csv).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "reports",
        help="Output directory (default: reports/).",
    )
    parser.add_argument(
        "--out-md", type=Path, default=None, help="Optional output markdown path."
    )
    parser.add_argument(
        "--out-csv", type=Path, default=None, help="Optional output CSV path."
    )
    return parser.parse_args(argv)


def _format_md_table(df: pd.DataFrame) -> str:
    if df.empty:
        return ""
    headers = [str(c) for c in df.columns]
    rows = df.astype(object).where(pd.notna(df), "").values.tolist()
    rows = [[str(v).replace("|", "\\|") for v in row] for row in rows]
    widths = [
        max(len(h), max((len(r[i]) for r in rows), default=0))
        for i, h in enumerate(headers)
    ]
    header = (
        "| "
        + " | ".join(headers[i].ljust(widths[i]) for i in range(len(headers)))
        + " |"
    )
    sep = "| " + " | ".join("-" * widths[i] for i in range(len(headers))) + " |"
    body = [
        "| "
        + " | ".join(rows[r][i].ljust(widths[i]) for i in range(len(headers)))
        + " |"
        for r in range(len(rows))
    ]
    return "\n".join([header, sep, *body])


def _dk_home_spread(row: pd.Series) -> float:
    """Convert DK favorite spread into home-spread convention."""
    spread = float(row["dk_spread"])
    favorite = normalize_team_name(row.get("favorite", ""))
    home = normalize_team_name(row.get("home_team", ""))
    # dk_spread is negative for favorite; if favorite is away => home is underdog (+)
    return spread if favorite == home else -spread


def _panel_candidates() -> list[str]:
    # Rating sources only (exclude linehow - it's market-like)
    return ["linesag", "linemassey", "lineelo", "linefei", "linefpi", "linemoore"]


def _vet_consensus_sources(
    merged: pd.DataFrame,
    *,
    candidate_bases: Sequence[str],
    market_col: str = "current_home_spread",
    corr_threshold: float = 0.25,
    mae_threshold: float = 10.0,
    min_rows: int = 8,
) -> tuple[list[str], list[str]]:
    """Vet system sources vs market and return kept home-spread columns.

    Args:
        merged: Merged slate+systems dataframe containing normalized home spreads.
        candidate_bases: Base column names like "linesag" (expects "<base>_home_spread").
        market_col: Market home-spread column to vet against.
        corr_threshold: Minimum correlation to keep a source.
        mae_threshold: Maximum MAE to keep a source.
        min_rows: Minimum overlapping rows required for vetting.

    Returns:
        Tuple of (kept_home_cols, kept_base_names).
    """
    market = pd.to_numeric(merged.get(market_col), errors="coerce")
    rows: list[dict[str, object]] = []
    kept_home_cols: list[str] = []
    kept_bases: list[str] = []

    for base in candidate_bases:
        col = f"{base}_home_spread"
        if col not in merged.columns:
            continue
        series = pd.to_numeric(merged[col], errors="coerce")
        mask = market.notna() & series.notna()
        n = int(mask.sum())
        corr = float("nan")
        mae = float("nan")
        keep = False
        if n >= min_rows:
            corr = float(
                np.corrcoef(
                    series[mask].astype(float),
                    market[mask].astype(float),
                )[0, 1]
            )
            mae = float(
                np.mean(np.abs(series[mask].astype(float) - market[mask].astype(float)))
            )
            keep = (
                (not np.isnan(corr)) and corr >= corr_threshold and mae <= mae_threshold
            )
        rows.append({"source": base, "n": n, "corr": corr, "mae": mae, "keep": keep})
        if keep:
            kept_home_cols.append(col)
            kept_bases.append(base)

    if rows:
        table = pd.DataFrame(rows).sort_values(
            ["keep", "corr"], ascending=[False, False]
        )
        with pd.option_context("display.max_rows", 200, "display.width", 160):
            logging.info(
                "Consensus source vetting vs %s (keep if corr>=%.2f and MAE<=%.1f):\n%s",
                market_col,
                corr_threshold,
                mae_threshold,
                table.to_string(index=False),
            )
    else:
        logging.info("Consensus source vetting: no candidate sources found.")

    return kept_home_cols, kept_bases


def generate_bowl_guide(
    *, slate_path: Path, systems_path: Path, output_dir: Path
) -> tuple[Path, Path]:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    slate = pd.read_csv(slate_path, low_memory=False).dropna(how="all")
    systems = pd.read_csv(systems_path, low_memory=False).dropna(how="all")

    required_slate = {"away_team", "home_team", "dk_spread", "model_home_margin"}
    missing = required_slate - set(slate.columns)
    if missing:
        raise ValueError(f"Slate file missing required columns: {sorted(missing)}")

    if not {"road", "home"}.issubset(systems.columns):
        raise ValueError("Systems file must have 'road' and 'home' columns.")

    slate = slate.copy()
    slate["away_norm"] = slate["away_team"].astype(str).map(normalize_team_name)
    slate["home_norm"] = slate["home_team"].astype(str).map(normalize_team_name)
    slate["your_home_spread"] = -pd.to_numeric(
        slate["model_home_margin"], errors="coerce"
    )
    slate["dk_home_spread"] = slate.apply(_dk_home_spread, axis=1)
    slate["dk_total"] = pd.to_numeric(slate.get("dk_total"), errors="coerce")
    slate["rf_total"] = pd.to_numeric(slate.get("rf_total"), errors="coerce")

    systems = systems.copy()
    systems["away_norm"] = systems["road"].astype(str).map(normalize_team_name)
    systems["home_norm"] = systems["home"].astype(str).map(normalize_team_name)

    # Infer orientation of system columns relative to current road line and compute *_home_spread.
    candidate_cols = [
        c for c in systems.columns if c.startswith("line") and c not in {"linestd"}
    ]
    systems, _ = infer_and_normalize_system_columns(
        systems,
        market_road_col="line",
        candidates=candidate_cols,
    )

    merged = slate.merge(
        systems, on=["away_norm", "home_norm"], how="left", suffixes=("", "_sys")
    )

    merged["edge_vs_dk"] = merged["your_home_spread"] - merged["dk_home_spread"]
    merged["abs_edge_vs_dk"] = merged["edge_vs_dk"].abs()

    merged["open_home_spread"] = -pd.to_numeric(merged.get("lineopen"), errors="coerce")
    merged["current_home_spread"] = -pd.to_numeric(merged.get("line"), errors="coerce")

    merged["edge_vs_market"] = (
        merged["your_home_spread"] - merged["current_home_spread"]
    )
    merged["abs_edge_vs_market"] = merged["edge_vs_market"].abs()

    kept_sources_home, kept_sources_base = _vet_consensus_sources(
        merged,
        candidate_bases=_panel_candidates(),
        market_col="current_home_spread",
    )
    merged["ratings_sources_home"] = "|".join(kept_sources_base)

    ratings_frame = merged[kept_sources_home].apply(pd.to_numeric, errors="coerce")
    merged["ratings_count"] = ratings_frame.notna().sum(axis=1)
    merged["ratings_mean_home"] = ratings_frame.mean(axis=1)
    merged["ratings_median_home"] = ratings_frame.median(axis=1)
    merged["ratings_std"] = ratings_frame.std(axis=1, ddof=0)

    low_panel = merged["ratings_count"] < 3
    merged.loc[
        low_panel,
        ["ratings_mean_home", "ratings_median_home", "ratings_std"],
    ] = np.nan

    valid_z = merged["ratings_std"].notna() & (merged["ratings_std"] > 0)
    merged["ratings_z"] = np.nan
    merged.loc[valid_z, "ratings_z"] = (
        merged["your_home_spread"] - merged["ratings_mean_home"]
    ) / merged["ratings_std"]

    merged["dk_vs_market_conflict"] = (
        (merged["dk_home_spread"] * merged["current_home_spread"] < 0)
        & (merged["dk_home_spread"].abs() >= 2)
        & (merged["current_home_spread"].abs() >= 2)
    )
    merged["flag_high_dispersion"] = merged["ratings_std"] >= 4.0

    # Market-based outlier (betting-relevant)
    merged["flag_outlier_market"] = merged["abs_edge_vs_market"] >= 4.0

    # Ratings-based outlier (informational only)
    valid_ratings_z = (
        merged["ratings_std"].notna()
        & (merged["ratings_std"] > 0)
        & (merged["ratings_count"] >= 3)
    )
    merged["flag_outlier_ratings"] = False
    merged.loc[valid_ratings_z, "flag_outlier_ratings"] = (
        merged.loc[valid_ratings_z, "ratings_z"].abs() >= 2.0
    )
    std_for_robust = merged["ratings_std"]
    merged["robust_edge"] = np.where(
        std_for_robust.notna() & (std_for_robust > 0),
        merged["abs_edge_vs_dk"] / std_for_robust,
        np.nan,
    )

    # Warning: DK vs market mismatch
    dk_mkt_diff = (merged["dk_home_spread"] - merged["current_home_spread"]).abs()
    large_diff = dk_mkt_diff > 7.0
    if large_diff.any():
        logging.warning(
            f"{large_diff.sum()} games have DK vs market spread difference > 7.0 "
            f"(possible data mismatch)"
        )

    # Warning: Missing current_home_spread but dk_home_spread exists
    missing_mkt = (
        merged["current_home_spread"].isna() & merged["dk_home_spread"].notna()
    )
    if missing_mkt.any():
        logging.warning(
            f"{missing_mkt.sum()} games missing current_home_spread but have dk_home_spread"
        )

    # Warning: Ratings std too tight
    tight_std = (merged["ratings_std"] < 0.75) & (merged["ratings_count"] >= 3)
    if tight_std.any():
        logging.warning(
            f"{tight_std.sum()} games have ratings_std < 0.75 with ratings_count >= 3 "
            f"(z-score may be unstable)"
        )

    move_raw = merged["current_home_spread"] - merged["open_home_spread"]
    merged["move_from_open_raw"] = move_raw
    merged["flag_move_data_issue"] = move_raw.abs() > 10
    merged["move_from_open"] = move_raw.mask(merged["flag_move_data_issue"], np.nan)
    merged["flag_big_move"] = merged["move_from_open"].abs() >= 3.0

    panel_cols_home = [c for c in kept_sources_home if c in merged.columns]
    agreement_rates: list[float] = []
    agreement_ns: list[int] = []
    disagree_sources_list: list[list[str]] = []
    for _, row in merged.iterrows():
        rate, n, disagree = compute_agreement_rate(
            row,
            panel_cols_home=panel_cols_home,
            dk_home_spread_col="dk_home_spread",
            your_home_spread_col="your_home_spread",
        )
        if n < 3:
            agreement_rates.append(float("nan"))
            agreement_ns.append(n)
            disagree_sources_list.append([])
        else:
            agreement_rates.append(rate)
            agreement_ns.append(n)
            disagree_sources_list.append(
                [d.replace("_home_spread", "") for d in disagree]
            )

    merged["agreement_rate"] = agreement_rates
    merged["agreement_n"] = agreement_ns
    merged["disagree_sources"] = [", ".join(items) for items in disagree_sources_list]

    dist_open = (merged["your_home_spread"] - merged["open_home_spread"]).abs()
    dist_current = (merged["your_home_spread"] - merged["current_home_spread"]).abs()
    clv = dist_open - dist_current
    merged["clv_direction"] = pd.NA
    clv_valid = (
        merged["your_home_spread"].notna()
        & merged["open_home_spread"].notna()
        & merged["current_home_spread"].notna()
        & (~merged["flag_move_data_issue"].fillna(False))
    )
    merged.loc[clv_valid & (clv > 0), "clv_direction"] = "TOWARD_YOU"
    merged.loc[clv_valid & (clv < 0), "clv_direction"] = "AWAY_FROM_YOU"
    merged.loc[clv_valid & (clv == 0), "clv_direction"] = "NEUTRAL"

    merged["your_vs_median"] = (
        merged["your_home_spread"] - merged["ratings_median_home"]
    )
    for base in kept_sources_base:
        col_home = f"{base}_home_spread"
        if col_home in merged.columns:
            merged[f"your_vs_{base}"] = merged["your_home_spread"] - pd.to_numeric(
                merged[col_home], errors="coerce"
            )

    tiers: list[str] = []
    reasons: list[str] = []
    for _, row in merged.iterrows():
        tier, tier_reasons = compute_tier_and_reasons(
            row,
            edge_vs_dk_col="edge_vs_dk",
            abs_edge_vs_dk_col="abs_edge_vs_dk",
            edge_vs_market_col="edge_vs_market",
            abs_edge_vs_market_col="abs_edge_vs_market",
        )
        tiers.append(tier)
        reasons.append("|".join(tier_reasons))
    merged["tier"] = tiers
    merged["tier_reasons"] = reasons

    flags: list[str] = []
    for _, row in merged.iterrows():
        parts: list[str] = []
        if bool(row.get("flag_outlier_market", False)):
            parts.append("OUTLIER_MARKET")
        if bool(row.get("flag_outlier_ratings", False)):
            parts.append("OUTLIER_RATINGS")
        if bool(row.get("flag_move_data_issue", False)):
            parts.append("MOVE_DATA_ISSUE")
        if bool(row.get("flag_big_move", False)):
            parts.append("BIG_MOVE")
        if bool(row.get("flag_high_dispersion", False)):
            parts.append("HIGH_STD_RATINGS")
        if bool(row.get("dk_vs_market_conflict", False)):
            parts.append("DK_VS_MKT_CONFLICT")
        flags.append("|".join(parts))
    merged["flags"] = flags

    totals_meta = validate_totals(merged)
    merged["total_pick"] = pd.NA
    merged["total_edge"] = pd.NA
    if totals_meta["valid"]:
        merged["total_edge"] = merged["rf_total"] - merged["dk_total"]
        merged.loc[merged["total_edge"] >= 2.0, "total_pick"] = "OVER"
        merged.loc[merged["total_edge"] <= -2.0, "total_pick"] = "UNDER"
        merged.loc[merged["total_edge"].abs() < 2.0, "total_pick"] = "PASS"
    else:
        merged["rf_total"] = pd.NA

    merged = merged.sort_values(["date", "bowl"], ascending=[True, True])

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / f"bowl_betting_guide_{ts}.csv"
    md_path = output_dir / f"bowl_betting_guide_{ts}.md"
    merged.to_csv(csv_path, index=False)

    key_cols = [
        "date",
        "bowl",
        "away_team",
        "home_team",
        "dk_home_spread",
        "your_home_spread",
        "edge_vs_dk",
        "edge_vs_market",
        "abs_edge_vs_market",
        "current_home_spread",
        "open_home_spread",
        "ratings_sources_home",
        "ratings_count",
        "ratings_mean_home",
        "ratings_median_home",
        "ratings_std",
        "ratings_z",
        "agreement_rate",
        "agreement_n",
        "clv_direction",
        "move_from_open",
        "dk_vs_market_conflict",
        "flags",
        "tier",
        "tier_reasons",
        "dk_total",
        "rf_total",
        "total_pick",
        "total_edge",
        "adv_stats_coverage",
    ]
    key_cols = [c for c in key_cols if c in merged.columns]

    summary = merged[key_cols].copy()
    # Make it readable
    for col in [
        "dk_home_spread",
        "your_home_spread",
        "edge_vs_dk",
        "edge_vs_market",
        "abs_edge_vs_market",
        "open_home_spread",
        "current_home_spread",
        "ratings_mean_home",
        "ratings_median_home",
        "ratings_std",
        "ratings_z",
        "move_from_open",
        "robust_edge",
        "total_edge",
        "agreement_rate",
    ]:
        if col in summary.columns:
            summary[col] = pd.to_numeric(summary[col], errors="coerce").round(2)
    for col in ["adv_stats_coverage"]:
        if col in summary.columns:
            summary[col] = pd.to_numeric(summary[col], errors="coerce").round(3)

    lines: list[str] = []
    lines.append("# Bowl Betting Evaluation Guide\n")
    lines.append(f"Generated: {datetime.now().isoformat(timespec='seconds')}\n")
    lines.append(f"- Slate: `{slate_path}`")
    lines.append(f"- Systems: `{systems_path}`\n")
    lines.append("## Spread Orientation\n")
    lines.append(
        "- Canonical: `home_spread < 0` home favored; `home_spread > 0` home underdog"
    )
    lines.append(
        "- Systems lines normalized to canonical home spreads via per-column polarity inference.\n"
    )

    if not totals_meta["valid"]:
        lines.append("## Totals Warning\n")
        lines.append(
            "Totals model appears mis-scaled or mismatched "
            f"(rf_total median={totals_meta.get('median')}, corr={totals_meta.get('corr')}). "
            "Totals edges suppressed.\n"
        )

    lines.append("## Quick Board (sorted by date)\n")
    lines.append(_format_md_table(summary))
    lines.append("")

    lines.append("## Audit / Review Queue\n")
    audit = merged[
        merged["flag_move_data_issue"].fillna(False)
        | merged["dk_vs_market_conflict"].fillna(False)
        | merged["flag_outlier_market"].fillna(False)
        | merged["flag_big_move"].fillna(False)
    ].copy()
    if not audit.empty:
        audit["abs_edge_mkt"] = pd.to_numeric(
            audit["abs_edge_vs_market"], errors="coerce"
        )
        audit["abs_move"] = pd.to_numeric(
            audit["move_from_open"], errors="coerce"
        ).abs()
        # Sort by severity: MOVE_DATA_ISSUE > DK_VS_MKT_CONFLICT > abs_edge_mkt > abs_move
        audit["severity"] = (
            audit["flag_move_data_issue"].fillna(False).astype(int) * 1000
            + audit["dk_vs_market_conflict"].fillna(False).astype(int) * 100
            + audit["abs_edge_mkt"].fillna(0)
            + audit["abs_move"].fillna(0) * 0.1
        )
        audit = audit.sort_values("severity", ascending=False)
        audit_cols = [
            "date",
            "bowl",
            "away_team",
            "home_team",
            "dk_home_spread",
            "your_home_spread",
            "edge_vs_dk",
            "edge_vs_market",
            "current_home_spread",
            "move_from_open",
            "ratings_z",
            "agreement_rate",
            "flags",
            "tier",
            "tier_reasons",
        ]
        audit_cols = [c for c in audit_cols if c in audit.columns]
        lines.append(_format_md_table(audit[audit_cols].head(25)))
    else:
        lines.append("No audit flags triggered.\n")

    lines.append("\n## Tier Summary\n")
    tier_counts = merged["tier"].value_counts(dropna=False).to_dict()
    lines.append(_format_md_table(pd.DataFrame([tier_counts])))
    lines.append("")
    lines.append("## Game-By-Game Notes\n")

    panel_cols_home_all = [c for c in panel_cols_home if c in merged.columns]

    for _, row in merged.iterrows():
        away = str(row.get("away_team", ""))
        home = str(row.get("home_team", ""))
        bowl = str(row.get("bowl", ""))
        date = str(row.get("date", ""))
        tier = str(row.get("tier", ""))
        neutral = bool(row.get("neutral_site", False))

        dk_home = float(row.get("dk_home_spread", np.nan))
        your_home = float(row.get("your_home_spread", np.nan))
        edge_dk = float(row.get("edge_vs_dk", np.nan))
        edge_mkt = float(row.get("edge_vs_market", np.nan))

        lines.append(f"### {date} — {away} @ {home} ({bowl})")
        lines.append(
            f"- Neutral: `{neutral}` | Tier: `{tier}` | Reasons: `{row.get('tier_reasons', '')}`"
        )
        lines.append(
            f"- DK (home spread): `{dk_home:.2f}` | Your (home spread): `{your_home:.2f}`"
        )
        lines.append(f"- DK edge: `{edge_dk:.2f}` | Market edge: `{edge_mkt:.2f}`")

        # Ratings consensus separately
        ratings_mean = row.get("ratings_mean_home", np.nan)
        ratings_std = row.get("ratings_std", np.nan)
        ratings_z = row.get("ratings_z", np.nan)
        if pd.notna(ratings_mean):
            lines.append(
                f"- Ratings: mean `{float(ratings_mean):.2f}` "
                f"std `{float(ratings_std):.2f}` z `{float(ratings_z):.2f}`"
            )

        agree = row.get("agreement_rate")
        disagree_sources = str(row.get("disagree_sources", "")).strip()
        lines.append(
            f"- Agreement (panel): `{'' if pd.isna(agree) else f'{float(agree):.2f}'}`"
            + (f" | Disagree: `{disagree_sources}`" if disagree_sources else "")
        )

        open_home = row.get("open_home_spread", np.nan)
        current_home = row.get("current_home_spread", np.nan)
        move = row.get("move_from_open", np.nan)
        clv_dir = row.get("clv_direction", pd.NA)
        if pd.notna(open_home) or pd.notna(current_home):
            lines.append(
                f"- Market: open `{float(open_home) if pd.notna(open_home) else float('nan'):.2f}` "
                f"current `{float(current_home) if pd.notna(current_home) else float('nan'):.2f}` "
                f"move `{float(move) if pd.notna(move) else float('nan'):.2f}` "
                f"CLV `{clv_dir}`"
            )

        robust_val = row.get("robust_edge", np.nan)
        robust_str = "NA" if pd.isna(robust_val) else f"{float(robust_val):.2f}"
        lines.append(f"- Flags: `{row.get('flags', '')}` | Robust edge: `{robust_str}`")

        # Totals (only when validated)
        if totals_meta["valid"]:
            dk_total = row.get("dk_total", np.nan)
            rf_total = row.get("rf_total", np.nan)
            total_edge = row.get("total_edge", np.nan)
            total_pick = row.get("total_pick", pd.NA)
            if pd.notna(dk_total) and pd.notna(rf_total):
                lines.append(
                    f"- Total: DK `{float(dk_total):.1f}` vs RF `{float(rf_total):.1f}` "
                    f"→ `{total_pick}` (edge `{float(total_edge):.2f}`)"
                )

        # Panel line table (small, readable)
        panel_table: dict[str, object] = {}
        for base_col in [
            "lineopen_home_spread",
            "line_home_spread",
            "lineavg_home_spread",
            "linemedian_home_spread",
        ]:
            if base_col in merged.columns:
                panel_table[base_col.replace("_home_spread", "")] = row.get(base_col)
        for col in panel_cols_home_all:
            panel_table[col.replace("_home_spread", "")] = row.get(col)
        if panel_table:
            lines.append("")
            lines.append(_format_md_table(pd.DataFrame([panel_table])))

        # Outlier decomposition
        decomp_cols = []
        for base in ["your_vs_median"] + [f"your_vs_{c}" for c in kept_sources_base]:
            if base in merged.columns:
                decomp_cols.append(base)
        if decomp_cols:
            lines.append("")
            lines.append(
                _format_md_table(pd.DataFrame([{c: row.get(c) for c in decomp_cols}]))
            )

        lines.append("")
        lines.append("- Notes: _opt-outs / injuries / motivation / weather_")
        lines.append("")

    md_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    return md_path, csv_path


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parse_args(argv)
    slate_path = _resolve_latest(str(args.slate))
    systems_path = Path(args.systems).resolve()
    md_path, csv_path = generate_bowl_guide(
        slate_path=slate_path,
        systems_path=systems_path,
        output_dir=Path(args.output_dir),
    )

    if args.out_md:
        Path(args.out_md).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_md).write_text(
            Path(md_path).read_text(encoding="utf-8"), encoding="utf-8"
        )
        md_path = Path(args.out_md).resolve()
    if args.out_csv:
        Path(args.out_csv).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_csv).write_text(
            Path(csv_path).read_text(encoding="utf-8"), encoding="utf-8"
        )
        csv_path = Path(args.out_csv).resolve()

    print(f"✅ Wrote {md_path}")
    print(f"✅ Wrote {csv_path}")

    df = pd.read_csv(csv_path, low_memory=False).dropna(how="all")
    tier_counts = (
        df["tier"].value_counts(dropna=False).to_dict() if "tier" in df.columns else {}
    )
    flags = {
        "outlier_market": int(
            df.get("flag_outlier_market", pd.Series(dtype=bool)).fillna(False).sum()
        ),
        "outlier_ratings": int(
            df.get("flag_outlier_ratings", pd.Series(dtype=bool)).fillna(False).sum()
        ),
        "big_move": int(
            df.get("flag_big_move", pd.Series(dtype=bool)).fillna(False).sum()
        ),
        "dk_vs_market_conflict": int(
            df.get("dk_vs_market_conflict", pd.Series(dtype=bool)).fillna(False).sum()
        ),
        "high_dispersion": int(
            df.get("flag_high_dispersion", pd.Series(dtype=bool)).fillna(False).sum()
        ),
    }
    print(f"Tiers: {tier_counts}")
    print(f"Audit flags: {flags}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
