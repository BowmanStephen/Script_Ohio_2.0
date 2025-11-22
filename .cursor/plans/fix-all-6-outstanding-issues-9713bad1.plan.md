<!-- 9713bad1-2f0e-4b6f-8447-ead15b07bb48 a945d22a-ca2f-4d6e-8b14-0f9fd8bf61b4 -->
# Fix FastAI Model Export and Re-run Weekly Predictions

## Issue 1: FastAI Model Export Fix (Critical)

**Problem**: `fastai_home_win_model_2025.pkl` fails to load with `load_learner()` due to incorrect export method. Currently uses pickle.dump which doesn't preserve FastAI DataLoaders structure needed for cat/cont schema recovery.

**Root Cause**: The model was saved with `pickle.dump(learn, f, protocol=4)` instead of FastAI's native `learn.export()` method. FastAI's `export()` method properly saves the learner with DataLoaders, enabling `load_learner()` to recover categorical and continuous feature schemas.

**Location**: `model_pack/fix_fastai_model.py` lines 109-110

**Fix Strategy**:

1. Update `model_pack/fix_fastai_model.py` to use `learn.export('fastai_home_win_model_2025.pkl')` instead of pickle.dump
2. Remove pickle loading test (lines 114-122) since `learn.export()` saves in FastAI format, not pickle
3. Add verification test that loads model with `load_learner()` and verifies cat/cont schema recovery
4. Run the updated script to regenerate `model_pack/fastai_home_win_model_2025.pkl`
5. Verify `FastAIInterface.load_model()` can now successfully load using `load_learner()` and recover schema

**Files to Modify**:

- `model_pack/fix_fastai_model.py` (replace pickle.dump with learn.export, update verification)
- Reference implementation: `model_pack/model_training_agent.py` line 330 shows correct usage

## Issue 2: Re-run Weekly Prediction Workflow

**Problem**: Weekly prediction outputs need to be regenerated with the fixed FastAI model and updated validation scores/metrics.

**Fix Strategy**:

1. Determine current week (use `calculate_current_week()` or user-specified week)
2. Run `scripts/run_weekly_analysis.py --week <WEEK>` to regenerate predictions
3. Verify outputs include updated model metadata with correct schema information
4. Confirm prediction outputs in `predictions/week<WEEK>/` and `analysis/week<WEEK>/` contain updated validation scores

**Files to Execute**:

- `scripts/run_weekly_analysis.py` (command-line script)
- Output locations: `predictions/week<WEEK>/`, `analysis/week<WEEK>/`, `validation/week<WEEK>/`

### To-dos

- [ ] Update model_pack/fix_fastai_model.py to use learn.export() instead of pickle.dump(). Add verification test that loads model with load_learner() and verifies cat/cont schema recovery.
- [ ] Run updated fix_fastai_model.py script to regenerate model_pack/fastai_home_win_model_2025.pkl with proper FastAI export format
- [ ] Verify FastAIInterface.load_model() can successfully load the exported model using load_learner() and recover categorical/continuous schema (not fallback list)
- [ ] Determine which week to run predictions for (use calculate_current_week() or user specification)
- [ ] Execute scripts/run_weekly_analysis.py --week <WEEK> to regenerate predictions with updated model and validation scores
- [ ] Verify prediction outputs in predictions/week<WEEK>/ and analysis/week<WEEK>/ contain updated model metadata with correct schema information and validation scores