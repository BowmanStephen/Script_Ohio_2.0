# SP+ and FPI Blend Weight Validation Report

**Generated:** 2025-11-20 18:57:26
**Status:** success

## Executive Summary

Optimal blend weights were calculated using Weeks 1-12 historical data.

## Optimal Weights

- **Ohio Model Weight:** 0.510
- **SP+ Weight:** 0.490
- **FPI Weight:** 0.000

## Validation Metrics

- **Validation Games:** 495
- **Validation MAE:** 12.12 points
- **Validation RMSE:** 16.12 points
- **Validation Accuracy:** 77.0%

## Baseline Comparison

- **Baseline MAE (Ohio Model Only):** 12.79 points
- **Baseline Accuracy:** 78.6%

- **MAE Improvement:** 0.67 points
- **Accuracy Improvement:** -1.6% points

## Usage

These weights should be used in `enhance_predictions_with_ratings.py`
to create calibrated ensemble predictions for future weeks.

```python
calibrated_margin = (
    ohio_model_weight * ensemble_margin +
    sp_weight * sp_predicted_margin +
    fpi_weight * fpi_predicted_margin
)
```
