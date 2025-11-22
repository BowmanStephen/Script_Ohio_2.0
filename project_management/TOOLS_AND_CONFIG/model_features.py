"""
Model feature definitions shared across training and inference scripts.

Source of truth synchronized with project_management/TOOLS_AND_CONFIG/backup
assets to keep legacy scripts functional.
"""

from typing import Iterable, List, Sequence, Union

RIDGE_FEATURES = [
    "home_talent", "away_talent", "home_elo", "away_elo",
    "home_adjusted_epa", "home_adjusted_epa_allowed",
    "away_adjusted_epa", "away_adjusted_epa_allowed",
    "home_adjusted_rushing_epa", "home_adjusted_rushing_epa_allowed",
    "away_adjusted_rushing_epa", "away_adjusted_rushing_epa_allowed",
    "home_adjusted_passing_epa", "home_adjusted_passing_epa_allowed",
    "away_adjusted_passing_epa", "away_adjusted_passing_epa_allowed",
    "home_adjusted_success", "home_adjusted_success_allowed",
    "away_adjusted_success", "away_adjusted_success_allowed",
    "home_adjusted_standard_down_success",
    "home_adjusted_standard_down_success_allowed",
    "away_adjusted_standard_down_success",
    "away_adjusted_standard_down_success_allowed",
    "home_adjusted_passing_down_success",
    "home_adjusted_passing_down_success_allowed",
    "away_adjusted_passing_down_success",
    "away_adjusted_passing_down_success_allowed",
    "home_adjusted_line_yards", "home_adjusted_line_yards_allowed",
    "away_adjusted_line_yards", "away_adjusted_line_yards_allowed",
    "home_adjusted_explosiveness", "home_adjusted_explosiveness_allowed",
    "away_adjusted_explosiveness", "away_adjusted_explosiveness_allowed",
    "home_total_havoc_offense", "home_total_havoc_defense",
    "away_total_havoc_offense", "away_total_havoc_defense",
    "home_points_per_opportunity_offense",
    "home_points_per_opportunity_defense",
    "away_points_per_opportunity_offense",
    "away_points_per_opportunity_defense",
    "home_avg_start_offense", "home_avg_start_defense",
    "away_avg_start_offense", "away_avg_start_defense",
    "spread",
]

XGB_FEATURES = [
    "home_talent", "away_talent", "home_elo", "away_elo",
    "home_adjusted_epa", "home_adjusted_epa_allowed",
    "away_adjusted_epa", "away_adjusted_epa_allowed",
    "home_adjusted_rushing_epa", "home_adjusted_rushing_epa_allowed",
    "away_adjusted_rushing_epa", "away_adjusted_rushing_epa_allowed",
    "home_adjusted_passing_epa", "home_adjusted_passing_epa_allowed",
    "away_adjusted_passing_epa", "away_adjusted_passing_epa_allowed",
    "home_adjusted_success", "home_adjusted_success_allowed",
    "away_adjusted_success", "away_adjusted_success_allowed",
    "home_adjusted_standard_down_success",
    "home_adjusted_standard_down_success_allowed",
    "away_adjusted_standard_down_success",
    "away_adjusted_standard_down_success_allowed",
    "home_adjusted_passing_down_success",
    "home_adjusted_passing_down_success_allowed",
    "away_adjusted_passing_down_success",
    "away_adjusted_passing_down_success_allowed",
    "home_adjusted_line_yards", "home_adjusted_line_yards_allowed",
    "away_adjusted_line_yards", "away_adjusted_line_yards_allowed",
    "home_adjusted_explosiveness", "home_adjusted_explosiveness_allowed",
    "away_adjusted_explosiveness", "away_adjusted_explosiveness_allowed",
    "home_total_havoc_offense", "home_total_havoc_defense",
    "away_total_havoc_offense", "away_total_havoc_defense",
    "home_points_per_opportunity_offense",
    "home_points_per_opportunity_defense",
    "away_points_per_opportunity_offense",
    "away_points_per_opportunity_defense",
    "home_avg_start_offense", "home_avg_start_defense",
    "away_avg_start_offense", "away_avg_start_defense",
    "spread",
]

SHARED_FEATURES = sorted(set(RIDGE_FEATURES) & set(XGB_FEATURES))
FEATURE_SETS = {
    "ridge": RIDGE_FEATURES,
    "xgb": XGB_FEATURES,
}

def get_model_features(model_type: str = "ridge") -> List[str]:
    """
    Return the ordered feature list for the requested model.

    Args:
        model_type: Either 'ridge' or 'xgb' (case insensitive).

    Raises:
        ValueError: If an unknown model type is provided.
    """
    key = (model_type or "").lower()
    if key not in FEATURE_SETS:
        raise ValueError(f"Unknown model type '{model_type}'. Available: {sorted(FEATURE_SETS)}")
    return FEATURE_SETS[key]

def _extract_columns(dataset: Union["pd.DataFrame", Sequence[str], Iterable[str]]) -> List[str]:
    """Extract a column/index list from either a DataFrame or iterable."""
    if hasattr(dataset, "columns"):
        return list(dataset.columns)
    if isinstance(dataset, dict):
        return list(dataset.keys())
    return list(dataset)

def validate_features(dataset: Union["pd.DataFrame", Sequence[str], Iterable[str]], model_type: str = "ridge") -> List[str]:
    """
    Ensure that the provided dataset exposes every feature required by a model.

    Args:
        dataset: pandas DataFrame or column-like iterable.
        model_type: Which model's feature checklist should be enforced.

    Returns:
        The ordered feature list for convenience.

    Raises:
        ValueError: If any required feature is missing.
    """
    required = get_model_features(model_type)
    available = set(_extract_columns(dataset))
    missing = [feature for feature in required if feature not in available]
    if missing:
        raise ValueError(f"Missing features for {model_type} model: {missing}")
    return required

def describe_features() -> None:
    """Print feature summary for quick debugging."""
    print(f"Ridge ({len(RIDGE_FEATURES)} features): {RIDGE_FEATURES}")
    print(f"XGBoost ({len(XGB_FEATURES)} features): {XGB_FEATURES}")
    print(f"Shared ({len(SHARED_FEATURES)} features): {SHARED_FEATURES}")


if __name__ == "__main__":
    describe_features()
