# Model Audit Report
**Audit Date:** 2025-11-19T20:58:13.622456
**Project Root:** /Users/stephen_bowman/Documents/GitHub/Script_Ohio_2.0

## Summary

- **Total Model Files Found:** 25
- **Total Code References:** 11
- **Production Models:** 5
- **Referenced Models:** 6
- **Legacy Models:** 9
- **Outdated Models (with _fixed suffix):** 3
- **Orphaned Models:** 2
- **Backup Models:** 7
- **Files to Archive:** 12
- **Missing Files:** 7

## Production Models

- `model_pack/fastai_home_win_model_2025.pkl` (0.2 MB, modified: 2025-11-19T19:47:34.465105)
- `model_pack/ridge_model_2025.joblib` (0.0 MB, modified: 2025-11-19T19:47:31.698942)
- `model_pack/xgb_home_win_model_2025.pkl` (0.31 MB, modified: 2025-11-19T19:47:31.871726)
- `model_pack/backups/models/critical/models_backup_20251114_135815/fastai_home_win_model_2025.pkl` (0.0 MB, modified: 2025-11-14T13:58:15.449863)
- `model_pack/backups/models/critical/models_backup_20251114_135815/xgb_home_win_model_2025.pkl` (0.31 MB, modified: 2025-11-14T13:58:15.452664)

## Files to Archive

The following files should be archived (legacy and outdated variants):

- `model_pack/archived_models/20251119/fastai_home_win_model.pkl` (0.2 MB)
- `model_pack/archived_models/20251119/fastai_home_win_model_2025_fixed.pkl` (0.22 MB)
- `model_pack/archived_models/20251119/fastai_home_win_model_copy.pkl` (0.2 MB)
- `model_pack/archived_models/20251119/ridge_model.joblib` (0.0 MB)
- `model_pack/archived_models/20251119/ridge_model_2025_fixed.joblib` (0.0 MB)
- `model_pack/archived_models/20251119/ridge_model_copy.joblib` (0.0 MB)
- `model_pack/archived_models/20251119/xgb_home_win_model.pkl` (0.28 MB)
- `model_pack/archived_models/20251119/xgb_home_win_model_2025_fixed.pkl` (0.3 MB)
- `model_pack/archived_models/20251119/xgb_home_win_model_copy.pkl` (0.28 MB)
- `model_pack/rf_components/random_forest_away.joblib` (35.42 MB)
- `model_pack/rf_components/random_forest_features.joblib` (0.0 MB)
- `model_pack/rf_components/random_forest_home.joblib` (35.93 MB)

## Missing Files

- **model_name.pkl**
  - Referenced in: agents/model_execution_engine.py
- **learn.export('model_name.pkl**
  - Referenced in: agents/model_execution_engine.py
- **'ridge_model_2025.joblib**
  - Referenced in: agents/model_execution_engine.py, model_pack/model_training_agent.py, model_pack/model_training_agent.py, scripts/retrain_models_full_features.py
- **'xgb_home_win_model_2025.pkl**
  - Referenced in: agents/model_execution_engine.py, model_pack/model_training_agent.py, model_pack/model_training_agent.py, scripts/retrain_models_full_features.py
- **'fastai_home_win_model_2025.pkl**
  - Referenced in: agents/model_execution_engine.py, model_pack/model_training_agent.py, scripts/retrain_models_full_features.py
- **'random_forest_model_2025.pkl**
  - Referenced in: agents/model_execution_engine.py
- **Path('fastai_home_win_model_2025.pkl**
  - Referenced in: model_pack/model_training_agent.py

## Configuration Mismatches

✅ No `_fixed` suffix references found

## Detailed Model Files

### All Model Files

- `model_pack/archived_models/20251119/fastai_home_win_model.pkl`
  - Size: 0.2 MB
  - Modified: 2025-08-10T00:34:26
  - Directory: model_pack
- `model_pack/archived_models/20251119/fastai_home_win_model_2025_fixed.pkl`
  - Size: 0.22 MB
  - Modified: 2025-11-18T15:54:21.712335
  - Directory: model_pack
- `model_pack/archived_models/20251119/fastai_home_win_model_2025_full_features.pkl`
  - Size: 0.19 MB
  - Modified: 2025-11-18T15:53:28.990220
  - Directory: model_pack
- `model_pack/archived_models/20251119/fastai_home_win_model_2025_original.pkl`
  - Size: 0.2 MB
  - Modified: 2025-11-10T15:44:46.739884
  - Directory: model_pack
- `model_pack/archived_models/20251119/fastai_home_win_model_copy.pkl`
  - Size: 0.2 MB
  - Modified: 2025-08-10T00:34:26
  - Directory: model_pack
- `model_pack/archived_models/20251119/ridge_model.joblib`
  - Size: 0.0 MB
  - Modified: 2025-08-10T00:52:10
  - Directory: model_pack
- `model_pack/archived_models/20251119/ridge_model_2025_fixed.joblib`
  - Size: 0.0 MB
  - Modified: 2025-11-18T15:48:23.161381
  - Directory: model_pack
- `model_pack/archived_models/20251119/ridge_model_copy.joblib`
  - Size: 0.0 MB
  - Modified: 2025-08-10T00:52:10
  - Directory: model_pack
- `model_pack/archived_models/20251119/xgb_home_win_model.pkl`
  - Size: 0.28 MB
  - Modified: 2025-08-10T00:54:42
  - Directory: model_pack
- `model_pack/archived_models/20251119/xgb_home_win_model_2025_fixed.pkl`
  - Size: 0.3 MB
  - Modified: 2025-11-18T15:48:23.386569
  - Directory: model_pack
- `model_pack/archived_models/20251119/xgb_home_win_model_copy.pkl`
  - Size: 0.28 MB
  - Modified: 2025-08-10T00:54:42
  - Directory: model_pack
- `model_pack/backups/models/critical/models_backup_20251114_135815/fastai_home_win_model.pkl`
  - Size: 0.2 MB
  - Modified: 2025-11-14T13:58:15.449387
  - Directory: model_pack
- `model_pack/backups/models/critical/models_backup_20251114_135815/fastai_home_win_model_2025.pkl`
  - Size: 0.0 MB
  - Modified: 2025-11-14T13:58:15.449863
  - Directory: model_pack
- `model_pack/backups/models/critical/models_backup_20251114_135815/fastai_home_win_model_2025_fixed.pkl`
  - Size: 0.21 MB
  - Modified: 2025-11-14T13:58:15.450907
  - Directory: model_pack
- `model_pack/backups/models/critical/models_backup_20251114_135815/fastai_home_win_model_2025_original.pkl`
  - Size: 0.2 MB
  - Modified: 2025-11-14T13:58:15.451550
  - Directory: model_pack
- `model_pack/backups/models/critical/models_backup_20251114_135815/xgb_home_win_model.pkl`
  - Size: 0.28 MB
  - Modified: 2025-11-14T13:58:15.452171
  - Directory: model_pack
- `model_pack/backups/models/critical/models_backup_20251114_135815/xgb_home_win_model_2025.pkl`
  - Size: 0.31 MB
  - Modified: 2025-11-14T13:58:15.452664
  - Directory: model_pack
- `model_pack/backups/models/critical/models_backup_20251114_135815/xgb_home_win_model_2025_fixed.pkl`
  - Size: 0.31 MB
  - Modified: 2025-11-14T13:58:15.453196
  - Directory: model_pack
- `model_pack/fastai_home_win_model_2025.pkl`
  - Size: 0.2 MB
  - Modified: 2025-11-19T19:47:34.465105
  - Directory: model_pack
- `model_pack/random_forest_model_2025.pkl`
  - Size: 71.34 MB
  - Modified: 2025-11-19T20:22:26.341645
  - Directory: model_pack
- `model_pack/rf_components/random_forest_away.joblib`
  - Size: 35.42 MB
  - Modified: 2025-11-19T20:22:26.397295
  - Directory: model_pack
- `model_pack/rf_components/random_forest_features.joblib`
  - Size: 0.0 MB
  - Modified: 2025-11-19T20:22:26.400936
  - Directory: model_pack
- `model_pack/rf_components/random_forest_home.joblib`
  - Size: 35.93 MB
  - Modified: 2025-11-19T20:22:26.368283
  - Directory: model_pack
- `model_pack/ridge_model_2025.joblib`
  - Size: 0.0 MB
  - Modified: 2025-11-19T19:47:31.698942
  - Directory: model_pack
- `model_pack/xgb_home_win_model_2025.pkl`
  - Size: 0.31 MB
  - Modified: 2025-11-19T19:47:31.871726
  - Directory: model_pack