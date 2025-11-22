# How to Get Results - Step by Step

## Current Status

The Week 13 directories exist but are **empty** - you need to run the analysis first!

## ✅ Quick Solution

### Step 1: Run the Analysis
```bash
python scripts/run_weekly_analysis.py --week 13
```

This will:
1. Validate models
2. Analyze matchups
3. Generate predictions
4. Save all results to the directories

### Step 2: Check Results
```bash
# Use the check script
python scripts/check_results.py --week 13

# Or manually check
ls -lh analysis/week13/
ls -lh predictions/week13/
```

## 📊 Example: Week 12 Results

Week 12 already has results you can look at as an example:

```bash
# View Week 12 predictions
cat predictions/week12/week12_comprehensive_predictions.csv

# View Week 12 analysis
cat analysis/week12/week12_comprehensive_analysis.json | python3 -m json.tool | head -50
```

**Week 12 files that exist:**
- `analysis/week12/week12_comprehensive_analysis.json` (93KB)
- `analysis/week12/week12_strategic_recommendations.csv` (6.4KB)
- `analysis/week12/week12_power_rankings.csv` (1.3KB)
- `predictions/week12/week12_comprehensive_predictions.csv` (7.8KB)
- `predictions/week12/week12_predictions.json` (16KB)
- And more...

## 🔍 Check What's Available

```bash
# Check specific week
python scripts/check_results.py --week 13

# List all weeks with results
python scripts/check_results.py --list
```

## ⚠️ Before Running Analysis

Make sure you have:

1. **Week 13 data prepared:**
   ```bash
   python scripts/prepare_week13_analysis.py
   ```

2. **Week 13 features generated:**
   - Check: `data/week13/enhanced/week13_features_86.csv`
   - If missing, you'll need to generate features first

3. **Models available:**
   - Check: `model_pack/ridge_model_2025.joblib`
   - Check: `model_pack/xgb_home_win_model_2025.pkl`

## 🚀 Full Workflow

```bash
# 1. Prepare Week 13
python scripts/prepare_week13_analysis.py

# 2. (If needed) Generate features
# This depends on your data pipeline

# 3. Run analysis
python scripts/run_weekly_analysis.py --week 13

# 4. Check results
python scripts/check_results.py --week 13

# 5. View results
cat predictions/week13/week13_comprehensive_predictions.csv
```

## 📍 Where Files Will Appear

After running analysis, files will be in:

```
Script_Ohio_2.0/
├── analysis/week13/
│   ├── week13_comprehensive_analysis.json
│   ├── week13_strategic_recommendations.csv
│   ├── week13_power_rankings.csv
│   └── week13_upset_alerts.csv
│
├── predictions/week13/
│   ├── week13_comprehensive_predictions.csv  ← Most important!
│   ├── week13_predictions.json
│   ├── week13_recommendations.csv
│   ├── prediction_insights.json
│   └── week13_prediction_summary.json
│
└── validation/week13/
    ├── week13_model_validation_report.json
    └── validation_summary.csv
```

## 🆘 Troubleshooting

**If analysis fails:**
1. Check the error message in the console
2. Verify data files exist: `ls -lh data/week13/enhanced/`
3. Verify models exist: `ls -lh model_pack/*_2025.*`
4. Run with verbose: `python scripts/run_weekly_analysis.py --week 13 --verbose`

**If files still don't appear:**
1. Check you're in the right directory: `pwd` should show `Script_Ohio_2.0`
2. Check permissions: `ls -ld analysis/week13/`
3. Check disk space: `df -h .`

