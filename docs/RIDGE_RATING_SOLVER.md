# Ridge Rating Solver (Phase 0.1)

The Ridge Rating Solver extends the existing Massey foundation with talent
priors, ridge regularization, and explicit time-decay weighting. It unlocks the
rest of the roadmap (tempo normalization, walk-forward validation, betting
metrics) by providing a flexible, bias-aware baseline.

## Components

- `src/ratings/talent_prior_blender.py`
  - Builds zero-centered talent priors from Script Ohio 2.0 historical data
  - Supports smoothing for low-sample teams and exposes caching helpers
- `src/ratings/ridge_rating_solver.py`
  - Solves for team ratings + home-field advantage via weighted Ridge
  - Honors per-game sample weights, recency halflife, and prior anchoring
- Tests
  - `tests/test_talent_prior_blender.py`
  - `tests/test_ridge_rating_solver.py`

## Usage

```python
from src.ratings.talent_prior_blender import TalentPriorConfig, compute_talent_priors
from src.ratings.ridge_rating_solver import RidgeRatingConfig, compute_ridge_ratings

prior_cfg = TalentPriorConfig(season=2025, week=13)
priors = compute_talent_priors(prior_cfg)

ridge_cfg = RidgeRatingConfig(season=2025, week=13, alpha=3.0, prior_strength=2.5)
ratings = compute_ridge_ratings(ridge_cfg, priors_df=priors)
ratings.to_csv("src/ratings/ridge_ratings_2025.csv", index=False)
```

## Key Behaviors

- **Talent Priors**
  - Uses offense/defense talent composites plus light margin context
  - Shrinks low-sample teams toward zero while enforcing zero-mean priors
- **Ridge Solver**
  - Weighted least squares with Ridge penalty and explicit zero-sum constraint
  - Sample weights default to exponential recency decay (configurable column
    override supported)
  - Priors enter as pseudo-observations with `prior_strength` weight
  - Home-field term is automatically bounded and falls back to the configured
    prior if the estimate collapses
- **Outputs**
  - CSV at `src/ratings/ridge_ratings_<season>.csv`
  - Columns: `team`, `season`, `week`, `rating`, `games_played`, `talent_prior`,
    `solver_version`, `hfa`, `ratings_sum`, `last_updated`

## Next Steps

- Plug ratings into the walk-forward validator + ROI/ATS simulator (Phase 1)
- Layer tempo normalization features on top of the same dataset (Phase 0.2)
- Register ridge ratings inside `rating_library.py` once validation is complete

