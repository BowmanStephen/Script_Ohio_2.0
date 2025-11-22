# Ohio Model Data Pipeline Status

## Last Updated: 2025-11-19

### Data Coverage
- **Starter Pack:** Weeks 1-13 (2025 season) ✅ Verified
- **Model Pack Plays:** Weeks 1-13 (real CFBD data, mock data removed)
- **Training Data:** Extended through Week 13, 2025 ✅ Synchronized
- **Total Games:** 5,964 games (2016-2025)
- **2025 Games:** 1,444 games across all 13 weeks

### Model Artifacts
- **Ridge Regression:** Retrained with 2025 data through Week 13 ✅
- **XGBoost Classifier:** Retrained with 2025 data through Week 13 ✅
- **FastAI Neural Network:** Retrained with 2025 data through Week 13 ✅
- **Last Training Run:** 2025-11-19 (All weeks 1-13 integrated)

### Known Limitations
1. **Week 13 outcomes:** Some Week 13 games may not have outcomes yet (games still in progress)
2. **Army-Navy game** – not included until played in December
3. **Bowl games** – fetch separately after selections

### Maintenance Schedule
- **Weekly refresh:** Run after weekend games finalize (typically Tuesday)
- **Training extension:** After every 2-4 weeks of new data
- **Model retraining:** When training data grows by 500+ games

### Quick Refresh Commands
```bash
# Fetch latest week data
CFBD_API_KEY=xxx python project_management/TOOLS_AND_CONFIG/fetch_2025_weekXX_data.py

# Rebuild plays file
python project_management/core_tools/rebuild_model_pack_plays.py

# Extend training and retrain models
python project_management/core_tools/data_workflows.py refresh-training     --migrated-file model_pack/2025_weeksXX_migrated.csv
```

### Validation Checklist
- [ ] No "Mock" data in model_pack/2025_plays.csv
- [ ] Training data includes 2025 season rows
- [ ] Model artifacts (.joblib/.pkl) have recent timestamps
- [ ] Integration report shows correct week range
