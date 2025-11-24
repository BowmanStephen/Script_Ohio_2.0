# Massey Linear System Specification

**Author:** system  
**Date:** 2025-11-24  
**Version:** 0.1

This document defines the exact linear algebra formulation for the Script Ohio
2.0 Massey ratings solver, including notation, constraints, and implementation
guidelines.

## Notation
- `n`: number of unique teams in the dataset.
- `m`: number of games included in the solve.
- `r ∈ ℝ^n`: vector of team ratings ordered by team index.
- `h`: scalar home-field advantage (HFA) parameter, positive for home teams.
- `A ∈ ℝ^{(m+1) × (n+1)}`: design matrix with one column per team plus one
  column for the HFA parameter.
- `b ∈ ℝ^{m+1}`: observed target vector (point differentials plus constraint).
- `λ`: ridge regularization strength (default 0.001).
- `W ∈ ℝ^{(m+1) × (m+1)}`: diagonal weighting matrix (identity by default).

## Row Construction
For each game `g`:

```
home_team = i
away_team = j
point_diff = home_points - away_points
neutral_flag = 1 if neutral site else 0
```

Row `g` of `A` and `b` are populated as:

```
A[g, i] =  1
A[g, j] = -1
A[g, n] =  (1 - neutral_flag)   # HFA column
b[g]    =  point_diff
```

All other entries in row `g` are zero. For neutral games the HFA column receives
zero.

## Normalization Constraint
To anchor the system, append one additional row enforcing the sum of ratings to
zero:

```
A[m, 0:n] = 1
A[m, n]   = 0
b[m]      = 0
```

This prevents arbitrary shifts in `r` and keeps the ratings centered so the
average team has a rating of zero.

## Regularized Least Squares Solution
Solve the system using ridge-regularized normal equations:

```
minimize ||W^(1/2) (A x - b)||_2^2 + λ ||x||_2^2
where x = [r; h]
```

Closed-form solution:

```
(Aᵀ W A + λ I) x = Aᵀ W b
```

where `I` is the identity matrix of size `(n+1)`. For large systems prefer a
numerically stable solver (QR, Cholesky, or `scipy.sparse.linalg.lsqr`).

## Home-Field Advantage Estimation
- `h` is estimated jointly with team ratings.
- Expected magnitude: 1.5–3.0 points depending on season.
- Clamp to `[0, 7]` after solving to avoid pathological values.
- Allow overriding via configuration: `home_field_override` disables estimation
  and injects fixed HFA.

## Data Filtering Rules
1. Include only games with non-null scores.
2. Filter to FBS vs FBS games unless specifically requested.
3. Apply week and season bounds based on caller inputs (e.g., `season=2025`,
   `week <= 12` for pre-week-13 ratings).
4. Remove duplicate neutral designations by ensuring `neutral_flag` matches
   CFBD metadata.

## Output Schema
- `team`: team name (string)
- `season`: season (int)
- `rating`: solved rating (float, centered on zero)
- `games_played`: count of games included for the team
- `hfa`: estimated scalar applied globally
- `solver_version`: semantic version of implementation (e.g., "v1.0.0")
- `last_updated`: ISO timestamp of solve

## Validation Checklist
1. **Zero Sum:** `abs(r.sum()) < 1e-6`
2. **HFA Positive:** `h >= 0.5`
3. **Residuals:** Median residual magnitude ≤ 12 points.
4. **Benchmark:** Correlation between `r` and historical margin ≥ 0.5.
5. **Regression Test:** Inject synthetic schedule where true ratings are known;
   solver must recover within ±0.25 points.

## Implementation Notes
- Use deterministic team indexing (sorted list of team names).
- Provide dataclass `MasseyConfig` with fields:
  `season`, `week`, `regularization`, `home_field_prior`, `max_games`.
- Cache solved ratings per `(season, week)` tuple to avoid recompute.
- Expose CLI flag `--massey-only` for scripts to run just this solver.

