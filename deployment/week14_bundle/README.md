# Week 14 Prediction Bundle (Weighted Ensemble)

Contents
- predictions/week14/week14_model_predictions.csv
- predictions/week14/week14_model_predictions.json
- reports/week14_ensemble_summary.md
- model_pack/ridge_model_2025.joblib (tuned)
- model_pack/xgb_home_win_model_2025.pkl (tuned)
- model_pack/fastai_home_win_model_2025.pkl (existing)
- scripts/predict_week14_proper.py (weighted ensemble logic)

Ensemble weights (home-win probability)
- XGBoost: 0.50
- Ridge (margin→prob via logistic scale=14): 0.30
- FastAI: 0.20

How to regenerate
```bash
python3 scripts/tune_ridge_xgb.py           # re-tune ridge/xgb
python3 scripts/predict_week14_proper.py    # rebuild CSV/JSON outputs
```

Deployment hints
- Use the CSV/JSON directly for the web app; `home_win_probability` reflects the weighted ensemble.
- Models are packaged for consistency with the predictor; refresh them after any retraining.
- For verification, spot-check headline games from `reports/week14_ensemble_summary.md`.
