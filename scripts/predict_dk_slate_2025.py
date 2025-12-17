#!/usr/bin/env python3
"""Generate picks for a DraftKings slate using the current trained models.

This script is tailored to the bowl/CFP slate pasted into the chat. It:
- Loads `data/training/weekly/training_data_2025_postseason.csv`
- Predicts home win probability + margin using the production models
- Joins a hardcoded DraftKings market line/O-U list (from the pasted slate)
- Computes "edge" vs spread (favorite implied margin)
- Writes a markdown + CSV output you can share

Usage:
  python3 scripts/predict_dk_slate_2025.py
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Sequence

import joblib
import pandas as pd
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

from src.ratings.massey_ratings import MasseyConfig  # noqa: E402
from src.ratings.rating_library import load_massey_ratings, load_rating_library  # noqa: E402


def _load_feature_lists() -> tuple[list[str], list[str]]:
    import importlib.util

    path = PROJECT_ROOT / "config" / "model_config.py"
    spec = importlib.util.spec_from_file_location("local_model_config", str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load feature config from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[assignment]
    return list(module.RIDGE_FEATURES), list(module.XGB_FEATURES)


RIDGE_FEATURES, XGB_FEATURES = _load_feature_lists()


def _ensure_features(df: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    missing = [name for name in features if name not in df.columns]
    if missing:
        df = df.copy()
        for name in missing:
            df[name] = 0
    return df


def _norm_team(name: str) -> str:
    lowered = name.strip().lower()
    lowered = lowered.replace("&", "and")
    lowered = lowered.replace("’", "'")
    lowered = lowered.replace("'", "")
    lowered = re.sub(r"[^a-z0-9]+", "", lowered)
    return lowered


@dataclass(frozen=True)
class DKGame:
    kickoff_date: str
    matchup: str
    team_a: str
    team_b: str
    favorite: str
    spread: float
    total: Optional[float]


def _dk_slate() -> list[DKGame]:
    return [
        DKGame("2025-12-17", "Cure Bowl", "Old Dominion", "South Florida", "South Florida", -2.5, 52.5),
        DKGame("2025-12-17", "68 Ventures Bowl", "Louisiana", "Delaware", "Louisiana", -3.0, 61.5),
        DKGame("2025-12-18", "Xbox Bowl", "Missouri State", "Arkansas State", "Arkansas State", -1.5, 54.5),
        DKGame("2025-12-19", "Myrtle Beach Bowl", "Kennesaw State", "Western Michigan", "Western Michigan", -3.5, 48.5),
        DKGame("2025-12-19", "Gasparilla Bowl", "Memphis", "NC State", "NC State", -4.5, 58.5),
        DKGame("2025-12-19", "CFP First Round", "Alabama", "Oklahoma", "Alabama", -1.5, 40.5),
        DKGame("2025-12-20", "CFP First Round", "Miami", "Texas A&M", "Texas A&M", -3.5, 50.5),
        DKGame("2025-12-20", "CFP First Round", "Tulane", "Ole Miss", "Ole Miss", -17.5, 56.5),
        DKGame("2025-12-20", "CFP First Round", "James Madison", "Oregon", "Oregon", -21.0, 47.5),
        DKGame("2025-12-22", "Potato Bowl", "Washington State", "Utah State", "Utah State", -2.5, 50.5),
        DKGame("2025-12-23", "Boca Raton Bowl", "Toledo", "Louisville", "Louisville", -6.5, 45.5),
        DKGame("2025-12-23", "New Orleans Bowl", "Western Kentucky", "Southern Miss", "Western Kentucky", -4.5, 57.5),
        DKGame("2025-12-23", "Frisco Bowl", "UNLV", "Ohio", "UNLV", -5.5, 65.5),
        DKGame("2025-12-24", "Hawai'i Bowl", "California", "Hawai'i", "California", -1.5, 54.5),
        DKGame("2025-12-26", "GameAbove Sports Bowl", "Central Michigan", "Northwestern", "Northwestern", -10.5, 43.5),
        DKGame("2025-12-26", "Rate Bowl", "New Mexico", "Minnesota", "Minnesota", -2.5, 45.5),
        DKGame("2025-12-26", "First Responder Bowl", "Florida International", "UTSA", "UTSA", -9.5, 59.5),
        DKGame("2025-12-27", "Military Bowl", "Pittsburgh", "East Carolina", "Pittsburgh", -8.5, 57.5),
        DKGame("2025-12-27", "Pinstripe Bowl", "Penn State", "Clemson", "Clemson", -3.5, 48.5),
        DKGame("2025-12-27", "Fenway Bowl", "UConn", "Army", "Army", -8.5, 44.5),
        DKGame("2025-12-27", "Pop-Tarts Bowl", "Georgia Tech", "BYU", "BYU", -4.5, 56.5),
        DKGame("2025-12-27", "Arizona Bowl", "Miami (OH)", "Fresno State", "Fresno State", -4.5, 42.5),
        DKGame("2025-12-27", "New Mexico Bowl", "North Texas", "San Diego State", "North Texas", -3.0, 54.5),
        DKGame("2025-12-27", "Gator Bowl", "Virginia", "Missouri", "Missouri", -7.0, 47.5),
        DKGame("2025-12-27", "Texas Bowl", "LSU", "Houston", "Houston", -3.0, 41.5),
        DKGame("2025-12-29", "Birmingham Bowl", "Georgia Southern", "App State", "Georgia Southern", -7.0, 59.5),
        DKGame("2025-12-30", "Independence Bowl", "Coastal Carolina", "Louisiana Tech", "Louisiana Tech", -8.5, 50.5),
        DKGame("2025-12-30", "Music City Bowl", "Tennessee", "Illinois", "Tennessee", -2.5, 61.5),
        DKGame("2025-12-30", "Alamo Bowl", "USC", "TCU", "USC", -4.5, 57.5),
        DKGame("2025-12-31", "ReliaQuest Bowl", "Iowa", "Vanderbilt", "Vanderbilt", -5.5, 47.5),
        DKGame("2025-12-31", "Sun Bowl", "Arizona State", "Duke", "Duke", -2.5, 49.5),
        DKGame("2025-12-31", "Citrus Bowl", "Michigan", "Texas", "Texas", -7.5, 46.5),
        DKGame("2025-12-31", "Las Vegas Bowl", "Nebraska", "Utah", "Utah", -16.5, 50.5),
        DKGame("2026-01-02", "Armed Forces Bowl", "Rice", "Texas State", "Texas State", -10.5, 59.5),
        DKGame("2026-01-02", "Liberty Bowl", "Navy", "Cincinnati", "Navy", -6.5, 53.5),
        DKGame("2026-01-02", "Holiday Bowl", "Arizona", "SMU", "Arizona", -3.0, 51.5),
        DKGame("2026-01-02", "Duke's Mayo Bowl", "Wake Forest", "Mississippi State", "Mississippi State", -4.0, 56.5),
    ]


def _find_game_row(df: pd.DataFrame, team_a: str, team_b: str) -> Optional[pd.Series]:
    a = _norm_team(team_a)
    b = _norm_team(team_b)
    home_norm = df["home_team"].astype(str).map(_norm_team)
    away_norm = df["away_team"].astype(str).map(_norm_team)

    direct = (home_norm == a) & (away_norm == b)
    if direct.any():
        return df.loc[direct].iloc[0]
    swapped = (home_norm == b) & (away_norm == a)
    if swapped.any():
        return df.loc[swapped].iloc[0]
    return None


def _favorite_view(row: pd.Series, *, favorite: str) -> tuple[float, float]:
    fav = _norm_team(favorite)
    home = _norm_team(str(row["home_team"]))

    predicted_margin = float(row["predicted_margin"])
    home_win_prob = float(row["home_win_prob"])

    if fav == home:
        return predicted_margin, home_win_prob
    return -predicted_margin, 1.0 - home_win_prob


def _favorite_prob(row: pd.Series, prob_column: str, *, favorite: str) -> float:
    """Return favorite win probability from a home-team probability column."""
    fav = _norm_team(favorite)
    home = _norm_team(str(row["home_team"]))
    value = float(row[prob_column])
    return value if fav == home else 1.0 - value


def _favorite_margin(row: pd.Series, margin_column: str, *, favorite: str) -> float:
    """Return favorite margin from a home-margin column (home minus away)."""
    fav = _norm_team(favorite)
    home = _norm_team(str(row["home_team"]))
    value = float(row[margin_column])
    return value if fav == home else -value


def _parse_args(argv: Optional[Sequence[str]] = None) -> "argparse.Namespace":
    """Parse CLI args."""
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--with-fastai",
        action="store_true",
        help="Include FastAI win probabilities (slower on some setups).",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parse_args(argv)
    model_dir = PROJECT_ROOT / "model_pack"
    ridge = joblib.load(model_dir / "ridge_model_2025.joblib")
    xgb = joblib.load(model_dir / "xgb_home_win_model_2025.pkl")
    rf_predictor = None
    rf_path = model_dir / "random_forest_model_2025.pkl"
    if rf_path.exists():
        try:
            rf_predictor = joblib.load(rf_path)
        except Exception:
            rf_predictor = None

    fastai_learner = None
    if args.with_fastai:
        fastai_path = model_dir / "fastai_home_win_model_2025.pkl"
        if fastai_path.exists():
            try:
                from fastai.learner import load_learner  # type: ignore

                fastai_learner = load_learner(fastai_path)
            except Exception:
                fastai_learner = None

    postseason_path = PROJECT_ROOT / "data" / "training" / "weekly" / "training_data_2025_postseason.csv"
    df = pd.read_csv(postseason_path, low_memory=False).dropna(how="all")
    df = _ensure_features(df, sorted(set(RIDGE_FEATURES) | set(XGB_FEATURES)))

    df = df.copy()
    df["predicted_margin"] = ridge.predict(df[list(RIDGE_FEATURES)].fillna(0))
    df["home_win_prob"] = xgb.predict_proba(df[list(XGB_FEATURES)].fillna(0))[:, 1]
    rf_feature_names = [
        "home_adjusted_success",
        "home_adjusted_success_allowed",
        "away_adjusted_success",
        "away_adjusted_success_allowed",
        "home_adjusted_rushing_epa",
        "home_adjusted_rushing_epa_allowed",
        "away_adjusted_rushing_epa",
        "away_adjusted_rushing_epa_allowed",
        "home_adjusted_passing_epa",
        "home_adjusted_passing_epa_allowed",
        "away_adjusted_passing_epa",
        "away_adjusted_passing_epa_allowed",
    ]
    present_rf_features = [name for name in rf_feature_names if name in df.columns]
    if present_rf_features:
        df["adv_stats_coverage"] = (
            1.0
            - df[present_rf_features].isna().sum(axis=1).astype(float) / float(len(present_rf_features))
        ).round(3)
    else:
        df["adv_stats_coverage"] = pd.NA
    df["fastai_home_win_prob"] = pd.NA
    if fastai_learner is not None:
        try:
            import numpy as np

            cat_names = ["week", "home_conference", "away_conference", "neutral_site"]
            cont_names = sorted(list(set(RIDGE_FEATURES + XGB_FEATURES)))
            working = df.copy()
            for col in cat_names:
                if col not in working.columns:
                    working[col] = "Unknown"
            working["week"] = pd.to_numeric(working["week"], errors="coerce").fillna(0).astype(int)
            working["home_conference"] = working["home_conference"].fillna("Unknown").astype(str)
            working["away_conference"] = working["away_conference"].fillna("Unknown").astype(str)
            working["neutral_site"] = working["neutral_site"].fillna(False).astype(bool)
            working = _ensure_features(working, cont_names)
            # Force single-process dataloading; avoids hangs on some macOS setups.
            import torch

            fastai_learner.model.to(torch.device("cpu"))
            fastai_learner.dls.num_workers = 0
            fastai_learner.dls.device = torch.device("cpu")
            dl = fastai_learner.dls.test_dl(working, bs=256, num_workers=0)
            with fastai_learner.no_bar(), fastai_learner.no_logging():
                preds, _ = fastai_learner.get_preds(dl=dl)
            if preds.ndim == 2 and preds.shape[1] == 1:
                # BCEWithLogitsLoss path: single logit -> sigmoid probability.
                df["fastai_home_win_prob"] = (1.0 / (1.0 + np.exp(-preds[:, 0].numpy()))).astype(float)
            elif preds.ndim == 2 and preds.shape[1] >= 2:
                df["fastai_home_win_prob"] = preds[:, 1].numpy().astype(float)
        except Exception:
            df["fastai_home_win_prob"] = pd.NA

    df["ensemble_home_win_prob"] = pd.to_numeric(df["home_win_prob"], errors="coerce").astype(float)
    fastai_numeric = pd.to_numeric(df["fastai_home_win_prob"], errors="coerce")
    df.loc[fastai_numeric.notna(), "ensemble_home_win_prob"] = (
        df.loc[fastai_numeric.notna(), "home_win_prob"].astype(float)
        + fastai_numeric[fastai_numeric.notna()].astype(float)
    ) / 2.0

    df["rf_home_points"] = pd.NA
    df["rf_away_points"] = pd.NA
    df["rf_total"] = pd.NA
    df["rf_margin"] = pd.NA
    if rf_predictor is not None:
        try:
            rf_features = getattr(rf_predictor, "features", None)
            if rf_features:
                rf_input = df.copy()
                rf_input[list(rf_features)] = rf_input[list(rf_features)].fillna(0)
                rf_pred = rf_predictor.predict(rf_input)
                df["rf_home_points"] = rf_pred["predicted_home_points"]
                df["rf_away_points"] = rf_pred["predicted_away_points"]
                df["rf_total"] = rf_pred["predicted_home_points"] + rf_pred["predicted_away_points"]
                df["rf_margin"] = rf_pred["predicted_home_points"] - rf_pred["predicted_away_points"]
        except Exception:
            pass

    massey_map: dict[str, float] = {}
    massey_hfa = 2.3
    try:
        massey_df = load_massey_ratings(
            config=MasseyConfig(season=2025, week=15),
            refresh=True,
            persist=True,
        )
        massey_map = {
            _norm_team(str(team)): float(rating)
            for team, rating in zip(massey_df["team"], massey_df["rating"], strict=False)
        }
        massey_hfa = float(massey_df["hfa"].iloc[0])
    except Exception:
        massey_map = {}

    rating_maps: dict[str, dict[str, float]] = {}
    try:
        # Avoid long-running metamodel training here; pull only CFBD rating feeds.
        library_df = load_rating_library(
            season=2025,
            refresh=False,
            include_systems=["sp_plus", "fpi", "elo", "srs"],
        )
        for system in ["sp_plus", "fpi", "elo", "srs"]:
            subset = library_df[library_df["system"] == system]
            rating_maps[system] = {
                _norm_team(str(team)): float(rating)
                for team, rating in zip(subset["team"], subset["rating"], strict=False)
                if pd.notna(rating)
            }
    except Exception:
        rating_maps = {}

    slate = _dk_slate()
    rows: list[dict] = []
    missing: list[str] = []
    for game in slate:
        row = _find_game_row(df, game.team_a, game.team_b)
        if row is None:
            missing.append(f"{game.team_a} vs {game.team_b}")
            continue

        fav_margin, fav_win_prob = _favorite_view(row, favorite=game.favorite)
        edge = fav_margin - abs(float(game.spread))
        recommendation = game.favorite if edge >= 0 else ("{}/{}".format(game.team_a, game.team_b))
        if recommendation == "{}/{}".format(game.team_a, game.team_b):
            underdog = game.team_b if _norm_team(game.favorite) == _norm_team(game.team_a) else game.team_a
            recommendation = underdog

        ens_prob = _favorite_prob(row, "ensemble_home_win_prob", favorite=game.favorite)

        massey_margin = pd.NA
        massey_edge = pd.NA
        fav_norm = _norm_team(game.favorite)
        other_team = game.team_b if fav_norm == _norm_team(game.team_a) else game.team_a
        other_norm = _norm_team(other_team)
        if fav_norm in massey_map and other_norm in massey_map:
            neutral = bool(row.get("neutral_site", False))
            massey_margin_val = float(massey_map[fav_norm] - massey_map[other_norm])
            if not neutral:
                massey_margin_val += massey_hfa
            massey_margin = round(massey_margin_val, 2)
            massey_edge = round(massey_margin_val - abs(float(game.spread)), 2)

        rating_diffs: dict[str, object] = {}
        for system, mapping in rating_maps.items():
            if fav_norm in mapping and other_norm in mapping:
                rating_diffs[f"{system}_diff"] = round(float(mapping[fav_norm] - mapping[other_norm]), 2)
            else:
                rating_diffs[f"{system}_diff"] = pd.NA

        rows.append(
            {
                "date": game.kickoff_date,
                "bowl": game.matchup,
                "team_a": game.team_a,
                "team_b": game.team_b,
                "away_team": str(row.get("away_team", "")),
                "home_team": str(row.get("home_team", "")),
                "neutral_site": bool(row.get("neutral_site", False)),
                "favorite": game.favorite,
                "dk_spread": float(game.spread),
                "dk_total": game.total,
                "adv_stats_coverage": row.get("adv_stats_coverage", pd.NA),
                "model_home_margin": round(float(row["predicted_margin"]), 2),
                "model_home_winprob": round(float(row["home_win_prob"]), 4),
                "model_margin_fav": round(float(fav_margin), 2),
                "model_winprob_fav": round(float(fav_win_prob), 4),
                "fastai_winprob_fav": round(
                    float(_favorite_prob(row, "fastai_home_win_prob", favorite=game.favorite)),
                    4,
                )
                if pd.notna(row.get("fastai_home_win_prob", pd.NA))
                else pd.NA,
                "ensemble_winprob_fav": round(float(ens_prob), 4),
                "edge_vs_spread": round(float(edge), 2),
                "pick_against_spread": recommendation,
                "massey_margin_fav": massey_margin,
                "massey_edge_vs_spread": massey_edge,
                "rf_total": row.get("rf_total", pd.NA),
                "rf_margin_fav": round(
                    float(_favorite_margin(row, "rf_margin", favorite=game.favorite)), 2
                )
                if pd.notna(row.get("rf_margin", pd.NA))
                else pd.NA,
                **rating_diffs,
            }
        )

    out_df = pd.DataFrame(rows).sort_values(
        ["date", "bowl", "edge_vs_spread"], ascending=[True, True, False]
    )

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = PROJECT_ROOT / "predictions" / "draftkings_slate_2025"
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / f"dk_slate_predictions_{ts}.csv"
    out_df.to_csv(csv_path, index=False)

    report_dir = PROJECT_ROOT / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    md_path = report_dir / f"draftkings_slate_2025_{ts}.md"

    lines: list[str] = []
    lines.append("# DraftKings Slate Picks (2025 postseason)\n")
    lines.append(f"Generated: {datetime.now().isoformat(timespec='seconds')}\n")
    lines.append("")
    lines.append("Columns:")
    lines.append("- `model_margin_fav`: model predicted margin for the favorite")
    lines.append("- `edge_vs_spread`: `model_margin_fav - abs(dk_spread)` (positive favors favorite)\n")
    lines.append("- `adv_stats_coverage`: fraction of core EPA/success features present\n")
    lines.append("- `fastai_winprob_fav`: FastAI home-win model (if available)\n")
    lines.append("- `ensemble_winprob_fav`: avg(XGB, FastAI) when FastAI is available\n")
    lines.append("- `massey_*`: ratings-based margin/edge (regular season only)\n")

    if missing:
        lines.append("## Missing Matchups")
        for item in missing:
            lines.append(f"- {item}")
        lines.append("")

    if out_df.empty:
        lines.append("No games matched the postseason dataset.")
    else:
        lines.append("## Picks")
        lines.append(_format_markdown_table(out_df))

    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"✅ Wrote {csv_path}")
    print(f"✅ Wrote {md_path}")
    if missing:
        print(f"⚠️  Missing {len(missing)} matchups (not found in postseason CSV)")
    return 0


def _format_markdown_table(df: pd.DataFrame) -> str:
    """Render a small DataFrame to a GitHub-flavored markdown table.

    Avoids the optional `tabulate` dependency required by `DataFrame.to_markdown()`.
    """
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

    header_line = "| " + " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers)) + " |"
    sep_line = "| " + " | ".join("-" * widths[i] for i in range(len(headers))) + " |"
    body_lines = [
        "| " + " | ".join(str_rows[r][i].ljust(widths[i]) for i in range(len(headers))) + " |"
        for r in range(len(str_rows))
    ]
    return "\n".join([header_line, sep_line, *body_lines])


if __name__ == "__main__":
    raise SystemExit(main())
