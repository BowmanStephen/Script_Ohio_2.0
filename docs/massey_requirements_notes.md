# Massey Ratings Requirements Notes

**Author:** system  
**Date:** 2025-11-24  
**Version:** 0.1

## Objective
Document the functional and data requirements for implementing a Massey style
power rating solver that:

1. Uses Script Ohio 2.0 canonical datasets (Week 5+, 2016-2025) as the source of
   truth.
2. Produces team strength ratings centered on zero (sum of ratings equals zero).
3. Explicitly models home-field advantage (HFA) as an additive constant.
4. Integrates cleanly with the rating library so downstream agents and scripts
   can consume the outputs.

## Data Inputs
- **Primary Source:** `model_pack/updated_training_data.csv`
  - Contains 4,989 FBS games (2016-2025 seasons, week ≥ 5).
  - Includes `season`, `week`, `home_team`, `away_team`, `home_points`,
    `away_points`, `neutral_site`, `game_id`, and 80+ engineered features.
- **Alternate Sources (optional):**
  - `starter_pack/data/` reference CSVs (read-only) for cross-checking.
  - Future GraphQL pulls (SP+, FPI, SRS) via CFBD Integration Agent to augment
    benchmarking.
- **Derived Fields Needed:**
  - `point_diff = home_points - away_points`
  - `home_field_flag = 0` for neutral-site games, `1` otherwise.
  - `team_index` mapping for all unique FBS teams present.

## Core Requirements
1. **Linear System Setup**
   - Each game contributes one equation: rating difference + HFA (if
     applicable) equals observed point differential.
   - Matrix `A` has one row per game, columns per team plus optional slack for
     regularization.
   - Add one normalization equation enforcing `∑ ratings = 0`.
2. **Home-Field Advantage**
   - Scalar constant `hfa` representing average home boost.
   - Estimated jointly by including an extra column in `A` or by augmenting the
     `b` vector using `home_field_flag * hfa`.
   - Default prior: 2.3 points (per internal benchmarking), override via
     shared inputs.
3. **Regularization**
   - Light ridge-style penalty to stabilize ill-conditioned matrices (λ ≈ 0.001
     configurable via shared inputs).
4. **Handling Incomplete Seasons**
   - Use all available games up to the current date; no future leakage.
   - During weekly runs, limit dataset to completed games before the target
     week to avoid circularity.
5. **Outputs**
   - DataFrame keyed by `team`, `season`, `rating`, `hfa`, `games_played`,
     `last_game_date`.
   - Persisted artifact: `src/ratings/massey_ratings_2025.csv` (≤5 MB) or merged
     into `src/ratings/rating_library_2025.csv`.
6. **Integration Points**
   - `src/ratings/rating_library.py` must expose `load_massey_ratings()` and a
     combined `load_all_ratings()` helper returning long-form table.
   - Agents (Model Execution, Insight Generator) can request Massey ratings via
     workflow shared inputs.

## Validation & QA
1. **Numerical Checks**
   - Sum of all team ratings must be approximately zero (|∑ rating| < 1e-6).
   - HFA estimate must be positive (≥ 0.5) unless neutral-only dataset.
2. **Sanity Metrics**
   - Correlation between ratings and observed margin should be ≥ 0.5.
   - Top teams (e.g., Georgia, Ohio State) should have positive ratings greater
     than lower-tier teams.
3. **Unit Tests**
   - `tests/test_massey_ratings.py`
     - Confirms solver reproduces known toy examples.
     - Ensures normalization & HFA behavior.
4. **Benchmarks**
   - Compare against CFBD Elo or SP+ to ensure order-of-magnitude alignment.
   - Compute MAE on held-out games.

## Tooling & Performance
- Prefer NumPy / SciPy for solving (sparse least squares if available).
- Batch matrix assembly to avoid Python loops where possible.
- Provide deterministic RNG seeds for reproducibility when shuffling.

## Open Questions / Follow-ups
1. Should we include margin caps (e.g., ±35) to reduce blowout influence?
2. Do we need conference-level normalization for cross-conference balance?
3. How often should ratings be recalculated (weekly vs on-demand)?
4. Should HFA vary by team or remain global? (Phase 1 assumes global constant.)

## Next Actions
1. Draft `docs/massey_linear_system_spec.md` with explicit matrices/equations.
2. Scaffold `src/ratings/massey_ratings.py` with dataclasses for config.
3. Prepare fixtures for unit tests (`tests/fixtures/massey_sample_games.csv`).

