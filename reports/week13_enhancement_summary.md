# Week 13 Predictions Enhancement Summary

**Generated:** 2025-11-20 20:00:23

## Overview

This report summarizes the enhancement of Week 13 predictions with SP+/FPI
ratings and calibrated ensemble predictions.

## Calibration Weights

- **Ohio Model Weight:** 0.510
- **SP+ Weight:** 0.490
- **FPI Weight:** 0.000

## Coverage

- **Total Games:** 60
- **SP+ Predictions:** 56 (93.3%)
- **FPI Predictions:** 56 (93.3%)
- **Calibrated Predictions:** 56 (93.3%)

## Divergence Analysis

### Ohio Model vs SP+

- **Mean Difference:** -5.06 points
- **Std Dev:** 21.16 points
- **Games with SP+:** 56

### Ohio Model vs FPI

- **Mean Difference:** -6.45 points
- **Std Dev:** 17.28 points
- **Games with FPI:** 56

### Calibrated vs Ohio Model

- **Mean Difference:** 2.48 points
- **Std Dev:** 10.38 points
- **Games Calibrated:** 56

## Key Insights

1. **Calibration Impact:** The calibrated ensemble adjusts Ohio Model
   predictions based on SP+ and FPI ratings.

2. **System Agreement:** Large divergences between systems may indicate
   games with higher uncertainty.

3. **Weight Distribution:** Current weights favor Ohio Model predictions
   (51%) with SP+ and FPI providing
   calibration signals.

## Usage

The enhanced predictions include:

- `sp_predicted_margin`: SP+ predicted spread
- `fpi_predicted_margin`: FPI predicted spread
- `calibrated_margin`: Optimal blend prediction
- `calibrated_home_win_prob`: Calibrated win probability
- Divergence columns for analysis

Use `calibrated_margin` and `calibrated_home_win_prob` for final predictions.
