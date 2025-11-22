#!/usr/bin/env python3
"""
Week 12 prediction pipeline.

Loads the refreshed 2025 feature dataset, runs the 2025 ridge regression (margin)
and XGBoost (win probability) models, and writes structured outputs plus summary
stats for downstream reporting.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "model_pack" / "2025_raw_games_enhanced.csv"
TRAINING_DATA_PATH = PROJECT_ROOT / "model_pack" / "updated_training_data.csv"
RIDGE_MODEL_PATH = PROJECT_ROOT / "model_pack" / "ridge_model_2025.joblib"
XGB_MODEL_PATH = PROJECT_ROOT / "model_pack" / "xgb_home_win_model_2025.pkl"
OUTPUT_DIR = PROJECT_ROOT / "reports"
PREDICTIONS_CSV = OUTPUT_DIR / "week12_predictions.csv"
SUMMARY_JSON = OUTPUT_DIR / "week12_prediction_summary.json"
ASSETS_DIR = OUTPUT_DIR / "week12_assets"


@dataclass
class GamePrediction:
    game_key: str
    start_date: str
    season: int
    week: int
    home_team: str
    away_team: str
    neutral_site: bool
    spread: float
    predicted_margin: float
    margin_winner: str
    ats_recommendation: str
    home_win_probability: float
    away_win_probability: float
    probability_winner: str
    ridge_features: Dict[str, float]
    xgb_features: Dict[str, float]

    def to_row(self) -> Dict[str, object]:
        """Flatten for CSV export."""
        base = asdict(self)
        base.pop("ridge_features", None)
        base.pop("xgb_features", None)
        return base


def _safe_float(value: object, default: float = 0.0) -> float:
    """Convert values to float without raising."""
    try:
        if value is None or (isinstance(value, float) and np.isnan(value)):
            return float(default)
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def load_models() -> Tuple[object, object]:
    ridge = joblib.load(RIDGE_MODEL_PATH)
    xgb = joblib.load(XGB_MODEL_PATH)
    return ridge, xgb


def build_feature_defaults(training_df: pd.DataFrame, feature_names: Iterable[str]) -> Dict[str, float]:
    medians = training_df[list(feature_names)].median(numeric_only=True)
    return {col: float(medians.get(col, 0.0)) for col in feature_names}


def build_feature_vector(row: pd.Series, feature_names: Iterable[str], defaults: Dict[str, float]) -> Dict[str, float]:
    feature_values = {}
    for name in feature_names:
        value = row.get(name)
        if pd.isna(value):
            value = defaults.get(name, 0.0)
        feature_values[name] = _safe_float(value, defaults.get(name, 0.0))
    return feature_values


def run_predictions(week: int = 12, season: int = 2025) -> Tuple[List[GamePrediction], Dict[str, object]]:
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Feature dataset not found at {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)
    target_games = df[(df["season"] == season) & (df["week"] == week) & (df["season_type"] == "regular")].copy()

    if target_games.empty:
        raise ValueError(f"No games found for season {season} week {week} in {DATA_PATH.name}")

    ridge_model, xgb_model = load_models()
    ridge_features_needed = list(ridge_model.feature_names_in_)
    xgb_features_needed = list(xgb_model.feature_names_in_)

    training_df = pd.read_csv(TRAINING_DATA_PATH)
    ridge_defaults = build_feature_defaults(training_df, ridge_features_needed)
    xgb_defaults = build_feature_defaults(training_df, xgb_features_needed)

    predictions: List[GamePrediction] = []

    for _, row in target_games.iterrows():
        ridge_feat = build_feature_vector(row, ridge_features_needed, ridge_defaults)
        xgb_feat = build_feature_vector(row, xgb_features_needed, xgb_defaults)

        ridge_vector = pd.DataFrame([ridge_feat], columns=ridge_features_needed)
        xgb_vector = pd.DataFrame([xgb_feat], columns=xgb_features_needed)

        margin_pred = float(ridge_model.predict(ridge_vector)[0])
        ats_pick = "Home ATS" if margin_pred > row.get("spread", 0.0) else "Away ATS"
        xgb_probs = xgb_model.predict_proba(xgb_vector)[0]
        home_win_prob = float(xgb_probs[1])
        away_win_prob = float(xgb_probs[0])
        probability_winner = row["home_team"] if home_win_prob >= 0.5 else row["away_team"]

        prediction = GamePrediction(
            game_key=row.get("game_key", f"{row['home_team']}_{row['away_team']}"),
            start_date=str(row.get("start_date")),
            season=int(row.get("season", season)),
            week=int(row.get("week", week)),
            home_team=row.get("home_team"),
            away_team=row.get("away_team"),
            neutral_site=bool(row.get("neutral_site", False)),
            spread=_safe_float(row.get("spread")),
            predicted_margin=margin_pred,
            margin_winner=row["home_team"] if margin_pred >= 0 else row["away_team"],
            ats_recommendation=ats_pick,
            home_win_probability=home_win_prob,
            away_win_probability=away_win_prob,
            probability_winner=probability_winner,
            ridge_features=ridge_feat,
            xgb_features=xgb_feat,
        )
        predictions.append(prediction)

    summary = build_summary(predictions)
    return predictions, summary


def build_summary(predictions: List[GamePrediction]) -> Dict[str, object]:
    df = pd.DataFrame([p.to_row() for p in predictions])
    high_conf_mask = (df["home_win_probability"] - 0.5).abs() >= 0.2
    upset_mask = (df["home_win_probability"] < 0.45) & (df["margin_winner"] == df["home_team"])
    ats_split = df["ats_recommendation"].value_counts().to_dict()

    summary = {
        "total_games": len(df),
        "high_confidence_games": int(high_conf_mask.sum()),
        "high_confidence_examples": df.loc[high_conf_mask, ["home_team", "away_team", "home_win_probability"]]
        .sort_values("home_win_probability", ascending=False)
        .head(5)
        .to_dict(orient="records"),
        "potential_upsets": df.loc[upset_mask, ["home_team", "away_team", "home_win_probability"]]
        .sort_values("home_win_probability")
        .to_dict(orient="records"),
        "ats_recommendation_split": ats_split,
        "average_margin": float(df["predicted_margin"].mean()),
        "average_home_win_probability": float(df["home_win_probability"].mean()),
    }
    return summary


def write_outputs(predictions: List[GamePrediction], summary: Dict[str, object]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([p.to_row() for p in predictions]).to_csv(PREDICTIONS_CSV, index=False)
    SUMMARY_JSON.write_text(json.dumps(summary, indent=2))


def generate_visuals(predictions: List[GamePrediction]) -> List[Path]:
    """Create visual artifacts for Week 12 analysis."""
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame([p.to_row() for p in predictions])
    sns.set_theme(style="whitegrid")

    assets: List[Path] = []

    # Histogram of predicted margins
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.histplot(df["predicted_margin"], bins=10, kde=True, ax=ax, color="#d62728")
    ax.set_title("Week 12 Predicted Margin Distribution")
    ax.set_xlabel("Predicted Margin (home - away)")
    ax.set_ylabel("Game Count")
    margin_path = ASSETS_DIR / "margin_distribution.png"
    fig.tight_layout()
    fig.savefig(margin_path, dpi=200)
    plt.close(fig)
    assets.append(margin_path)

    # Top confidence bar chart
    df["confidence_gap"] = (df["home_win_probability"] - 0.5).abs()
    top_conf = df.sort_values("confidence_gap", ascending=False).head(10)
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.barplot(
        data=top_conf,
        y="game_key",
        x="confidence_gap",
        hue="probability_winner",
        dodge=False,
        palette="dark:salmon"
    )
    ax.set_title("Top 10 Confidence Games (|Win Prob - 50%|)")
    ax.set_xlabel("Confidence Gap")
    ax.set_ylabel("Game")
    ax.legend(title="Predicted Winner")
    conf_path = ASSETS_DIR / "top_confidence_games.png"
    fig.tight_layout()
    fig.savefig(conf_path, dpi=200)
    plt.close(fig)
    assets.append(conf_path)

    # Margin vs probability scatter
    fig, ax = plt.subplots(figsize=(7, 5))
    sns.scatterplot(
        data=df,
        x="predicted_margin",
        y="home_win_probability",
        size="confidence_gap",
        hue="probability_winner",
        palette="colorblind",
        ax=ax,
        sizes=(50, 250)
    )
    ax.axhline(0.5, ls="--", color="gray", alpha=0.5)
    ax.axvline(0, ls="--", color="gray", alpha=0.5)
    ax.set_title("Predicted Margin vs Home Win Probability")
    ax.set_xlabel("Predicted Margin (home - away)")
    ax.set_ylabel("Home Win Probability")
    scatter_path = ASSETS_DIR / "margin_vs_probability.png"
    fig.tight_layout()
    fig.savefig(scatter_path, dpi=200)
    plt.close(fig)
    assets.append(scatter_path)

    return assets


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Week 12 predictions.")
    parser.add_argument("--week", type=int, default=12, help="Target week number (default: 12)")
    parser.add_argument("--season", type=int, default=2025, help="Target season (default: 2025)")
    args = parser.parse_args()

    predictions, summary = run_predictions(week=args.week, season=args.season)
    write_outputs(predictions, summary)
    assets = generate_visuals(predictions)

    print(f"✅ Generated {len(predictions)} predictions for season {args.season} week {args.week}")
    print(f"• Output CSV : {PREDICTIONS_CSV}")
    print(f"• Summary    : {SUMMARY_JSON}")
    for img in assets:
        print(f"• Plot       : {img}")


if __name__ == "__main__":
    main()

