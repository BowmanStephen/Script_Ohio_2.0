## Week 14 Ensemble Prediction Summary (2025)

Artifacts generated:
- Predictions: `predictions/week14/week14_model_predictions.csv` and `.json`
- Tuned models: `model_pack/ridge_model_2025.joblib`, `model_pack/xgb_home_win_model_2025.pkl`, existing `model_pack/fastai_home_win_model_2025.pkl`
- Tuning script: `scripts/tune_ridge_xgb.py`

Model blend (weighted):
- Weights: XGB 0.50, Ridge 0.30, FastAI 0.20 (renormalized on available signals)
- Ridge margin → logistic win prob (scale=14), XGB win prob, FastAI win prob (clipped to [0,1])
- Ensemble: weighted average; `home_win_probability` mirrors ensemble

Overall counts:
- Games predicted: 65
- Columns include: ridge margin + prob, xgb prob, fastai prob, ensemble prob, predicted winner

Top confidence plays (ensemble | home probability):
1) Purdue vs Indiana — 0.08 (away-favored)
2) Oklahoma State vs Iowa State — 0.08 (away-favored)
3) Coastal Carolina vs James Madison — 0.08 (away-favored)
4) Stanford vs Notre Dame — 0.09 (away-favored)
5) Massachusetts vs Bowling Green — 0.09 (away-favored)

Toss-up range (0.45–0.55 ensemble):
- Arizona @ Arizona State — 0.47 home
- Clemson @ South Carolina — 0.52 home
- Louisiana Tech @ Missouri State — 0.48 home
- Arkansas State @ App State — 0.48 home
- Wake Forest @ Duke — 0.52 home
- Texas A&M @ Texas — 0.53 home
- Missouri @ Arkansas — 0.46 home
- Vanderbilt @ Tennessee — 0.53 home

Selected headline games:
- Michigan vs Ohio State: home prob 0.02 (OSU heavy away lean), ensemble margin ~ -16.9
- Texas vs Texas A&M: home prob 0.53 (slight Texas lean)
- Clemson @ South Carolina: home prob 0.52 (slight SC lean)
- Washington @ Oregon State: home prob 0.24 (Beavers favored at home)
- Florida @ Florida State: home prob 0.10 (FSU favored away)

How to reproduce/update:
```bash
# Re-run tuning (Ridge/XGB)
python3 scripts/tune_ridge_xgb.py

# Re-run Week 14 predictions with ensemble
python3 scripts/predict_week14_proper.py
```

Notes:
- FastAI predictions are clipped to [0,1] to avoid negative probs.
- Ensemble is equal-weighted; can reweight (e.g., favor XGB) if desired.
- Ridge margin still provided for spread-style analysis.***
