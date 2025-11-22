"""
Legacy-compatible simplified orchestrator used by notebooks and QA scripts.

The modern platform revolves around ``AnalyticsOrchestrator`` but several
notebooks still expect a light-weight facade that can answer two common
requests:

1. Generate a quick matchup prediction using the fixed 2025 dataset.
2. Provide notebook recommendations / explanations for learning questions.

This module rebuilds that surface so data validation notebooks no longer
crash during import.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


NUMERIC_FEATURES: Tuple[Tuple[str, str, str], ...] = (
    ("talent", "home_talent", "away_talent"),
    ("elo", "home_elo", "away_elo"),
    ("adjusted_epa", "home_adjusted_epa", "away_adjusted_epa"),
    ("adjusted_success", "home_adjusted_success", "away_adjusted_success"),
    ("adjusted_rush_epa", "home_adjusted_rushing_epa", "away_adjusted_rushing_epa"),
    ("adjusted_pass_epa", "home_adjusted_passing_epa", "away_adjusted_passing_epa"),
)

LEARNING_NOTEBOOKS = [
    "model_pack/01_linear_regression_margin.ipynb",
    "model_pack/03_xgboost_win_probability.ipynb",
    "model_pack/06_shap_interpretability.ipynb",
    "model_pack/12_update_training_data.ipynb",
]


@dataclass
class PredictionSummary:
    """Structured representation of the simplified prediction output."""

    matchup: str
    models: Dict[str, Dict[str, float]]
    recommendation: str
    explanation: str
    data_sample_used: Dict[str, Any]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "matchup": self.matchup,
            "models": self.models,
            "recommendation": self.recommendation,
            "explanation": self.explanation,
            "data_sample_used": self.data_sample_used,
        }


class SimplifiedOrchestrator:
    """Minimal façade that keeps historical notebooks/tests functional."""

    def __init__(self, dataset_path: str = "model_pack/updated_training_data.csv"):
        self.dataset_path = Path(dataset_path)
        self._dataset = None
        self._team_metrics: Dict[str, Dict[str, float]] = {}
        self._defaults: Dict[str, float] = {}
        self._recent_seasons: Tuple[int, int] = (0, 0)
        self._load_dataset()

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------
    def process_request(self, query: str, **kwargs: Any) -> Dict[str, Any]:
        """Route the lightweight request to the appropriate helper."""
        query_type = kwargs.get("query_type") or self._detect_query_type(query)

        if query_type == "prediction":
            home_team = kwargs.get("home_team")
            away_team = kwargs.get("away_team")
            if not home_team or not away_team:
                home_team, away_team = self._parse_matchup_from_query(query)
            if not home_team or not away_team:
                return {"error": "Unable to determine home and away teams for prediction request."}
            try:
                summary = self._predict_matchup(home_team, away_team)
                return summary.as_dict()
            except Exception as exc:  # pragma: no cover - defensive
                return {"error": f"Prediction failed: {exc}"}

        if query_type == "learning":
            return self._handle_learning_request(query)

        return {"error": f"Unsupported query type '{query_type}' for simplified orchestrator."}

    # ---------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------
    def _load_dataset(self) -> None:
        """Load training data and build rolling team metrics."""
        if not self.dataset_path.exists():
            self._dataset = None
            self._defaults = {
                "talent": 800.0,
                "elo": 1500.0,
                "adjusted_epa": 0.0,
                "adjusted_success": 0.0,
                "avg_margin": 0.0,
                "spread": 0.0,
            }
            self._recent_seasons = (0, 0)
            return

        df = pd.read_csv(self.dataset_path)
        self._dataset = df

        if "season" in df.columns and not df["season"].empty:
            self._recent_seasons = (int(df["season"].min()), int(df["season"].max()))

        team_metrics: Dict[str, Dict[str, float]] = {}
        teams = sorted(set(df.get("home_team", [])) | set(df.get("away_team", [])))

        for team in teams:
            metrics = self._aggregate_team_metrics(df, team)
            team_metrics[team] = metrics

        self._team_metrics = team_metrics
        self._defaults = self._compute_defaults(team_metrics)

    def _aggregate_team_metrics(self, df: pd.DataFrame, team: str) -> Dict[str, float]:
        """Aggregate numeric features for a single team."""
        metrics: Dict[str, float] = {}
        for metric, home_col, away_col in NUMERIC_FEATURES:
            values: List[float] = []
            if home_col in df.columns:
                values.extend(df.loc[df["home_team"] == team, home_col].dropna().tolist())
            if away_col in df.columns:
                values.extend(df.loc[df["away_team"] == team, away_col].dropna().tolist())
            if values:
                metrics[metric] = float(np.mean(values))

        margin_values: List[float] = []
        if "margin" in df.columns:
            margin_values.extend(df.loc[df["home_team"] == team, "margin"].dropna().tolist())
            margin_values.extend((-df.loc[df["away_team"] == team, "margin"]).dropna().tolist())
        metrics["avg_margin"] = float(np.mean(margin_values)) if margin_values else 0.0

        if "spread" in df.columns:
            spreads = df.loc[df["home_team"] == team, "spread"].dropna().tolist()
            metrics["spread"] = float(np.mean(spreads)) if spreads else 0.0

        return metrics

    def _compute_defaults(self, team_metrics: Dict[str, Dict[str, float]]) -> Dict[str, float]:
        """Compute safe fallback values for each feature."""
        defaults: Dict[str, float] = {}
        for metric in ["talent", "elo", "adjusted_epa", "adjusted_success", "avg_margin", "spread"]:
            values = [stats.get(metric) for stats in team_metrics.values() if metric in stats]
            defaults[metric] = float(np.nanmedian(values)) if values else 0.0
        return defaults

    def _detect_query_type(self, query: str) -> str:
        query_l = (query or "").lower()
        if any(keyword in query_l for keyword in ["predict", "vs", "matchup", "line"]):
            return "prediction"
        if any(keyword in query_l for keyword in ["explain", "learn", "notebook", "how do i"]):
            return "learning"
        return "prediction"

    def _parse_matchup_from_query(self, query: str) -> Tuple[Optional[str], Optional[str]]:
        """Parse 'Team A vs Team B' style text."""
        if not query:
            return None, None
        lowered = query.lower()
        for delimiter in (" vs ", " versus ", " at "):
            if delimiter in lowered:
                idx = lowered.index(delimiter)
                home_raw = query[:idx].strip()
                away_raw = query[idx + len(delimiter) :].strip()
                for prefix in ("predict", "who wins", "analysis"):
                    if home_raw.lower().startswith(prefix):
                        home_raw = home_raw[len(prefix) :].strip(" :,-")
                return home_raw or None, away_raw or None
        return None, None

    def _resolve_team_stats(self, team: str) -> Dict[str, float]:
        stats = self._team_metrics.get(team)
        if not stats:
            return dict(self._defaults)
        combined = dict(self._defaults)
        combined.update(stats)
        return combined

    def _predict_matchup(self, home_team: str, away_team: str) -> PredictionSummary:
        home_stats = self._resolve_team_stats(home_team)
        away_stats = self._resolve_team_stats(away_team)

        talent_diff = home_stats["talent"] - away_stats["talent"]
        elo_diff = home_stats["elo"] - away_stats["elo"]
        epa_diff = home_stats["adjusted_epa"] - away_stats["adjusted_epa"]
        success_diff = home_stats["adjusted_success"] - away_stats["adjusted_success"]

        base_margin = (
            0.02 * talent_diff
            + 0.03 * elo_diff
            + 8.0 * epa_diff
            + 5.0 * success_diff
            + 0.5 * (home_stats["avg_margin"] - away_stats["avg_margin"])
            + 1.5  # home field advantage
        )
        ridge_margin = base_margin
        ridge_prob = 1 / (1 + math.exp(-ridge_margin / 10.0))
        xgb_prob = 1 / (1 + math.exp(-(0.05 * elo_diff + 12.0 * epa_diff)))
        ensemble_prob = (ridge_prob + xgb_prob) / 2

        recommendation = self._craft_recommendation(home_team, away_team, ensemble_prob, ridge_margin)
        explanation = (
            f"Used 2025 cleaned dataset ({self._recent_seasons[0]}-{self._recent_seasons[1]}) to "
            f"compare team talent (+{talent_diff:.1f}), ELO (+{elo_diff:.1f}), and efficiency deltas."
        )

        models = {
            "ridge": {
                "predicted_margin": ridge_margin,
                "home_win_probability": ridge_prob,
                "confidence_interval": (ridge_margin - 6.0, ridge_margin + 6.0),
            },
            "xgb": {
                "home_win_probability": xgb_prob,
                "predicted_margin": ridge_margin * 0.8,
            },
            "ensemble": {
                "home_win_probability": ensemble_prob,
                "predicted_margin": (ridge_margin * 0.7),
            },
        }

        data_used = {
            "season_span": self._recent_seasons,
            "teams_in_dataset": len(self._team_metrics),
            "features_considered": ["talent", "elo", "adjusted_epa", "adjusted_success", "avg_margin"],
        }

        return PredictionSummary(
            matchup=f"{home_team} vs {away_team}",
            models=models,
            recommendation=recommendation,
            explanation=explanation,
            data_sample_used=data_used,
        )

    def _craft_recommendation(self, home_team: str, away_team: str, prob: float, margin: float) -> str:
        if prob > 0.6:
            return f"Lean {home_team} on the moneyline; projected margin {margin:+.1f}."
        if prob < 0.4:
            return f"Lean {away_team} as the upset pick; projected margin {margin:+.1f}."
        return f"Tight matchup projected. Consider avoiding a side unless new info surfaces."

    def _handle_learning_request(self, query: str) -> Dict[str, Any]:
        topic = (query or "").lower()
        notebooks = LEARNING_NOTEBOOKS
        if "epa" in topic:
            notebooks = [
                "model_pack/03_xgboost_win_probability.ipynb",
                "model_pack/06_shap_interpretability.ipynb",
            ]
        elif "talent" in topic or "recruit" in topic:
            notebooks = [
                "model_pack/01_linear_regression_margin.ipynb",
                "model_pack/12_update_training_data.ipynb",
            ]
        explanation = (
            "Pulled curated notebook references covering the requested concept using the "
            "latest Script Ohio 2.0 starter pack. Each notebook includes cleaned datasets "
            "and commentary on how the feature feeds the production models."
        )
        return {
            "recommended_notebooks": notebooks,
            "explanation": explanation,
            "resources": [{"type": "notebook", "path": nb} for nb in notebooks],
        }


__all__ = ["SimplifiedOrchestrator", "PredictionSummary"]
