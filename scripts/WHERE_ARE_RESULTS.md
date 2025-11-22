# Where to Find Weekly Analysis Results

After running weekly analysis, results are saved to specific directories based on the week number.

## 📁 Result Locations

### Week 13 Results (Example)

When you run `python scripts/run_weekly_analysis.py --week 13`, results are saved to:

```
Script_Ohio_2.0/
├── analysis/week13/              # Matchup analysis results
│   ├── week13_comprehensive_analysis.json
│   ├── week13_strategic_recommendations.csv
│   ├── week13_power_rankings.csv
│   └── week13_upset_alerts.csv
│
├── predictions/week13/           # Prediction results
│   ├── week13_comprehensive_predictions.csv
│   ├── week13_predictions.json
│   ├── week13_recommendations.csv
│   ├── prediction_insights.json
│   └── week13_prediction_summary.json
│
└── validation/week13/            # Model validation reports
    ├── week13_model_validation_report.json
    └── validation_summary.csv
```

## 🔍 Quick Access Commands

### View All Week 13 Results
```bash
# List all analysis files
ls -lh analysis/week13/

# List all prediction files
ls -lh predictions/week13/

# List all validation files
ls -lh validation/week13/
```

### View Specific Result Types

#### Analysis Results
```bash
# View comprehensive analysis (JSON)
cat analysis/week13/week13_comprehensive_analysis.json | python3 -m json.tool

# View strategic recommendations (CSV)
cat analysis/week13/week13_strategic_recommendations.csv

# View power rankings (CSV)
cat analysis/week13/week13_power_rankings.csv

# View upset alerts (CSV)
cat analysis/week13/week13_upset_alerts.csv
```

#### Prediction Results
```bash
# View comprehensive predictions (CSV)
cat predictions/week13/week13_comprehensive_predictions.csv

# View predictions (JSON)
cat predictions/week13/week13_predictions.json | python3 -m json.tool

# View recommendations (CSV)
cat predictions/week13/week13_recommendations.csv

# View prediction insights (JSON)
cat predictions/week13/prediction_insights.json | python3 -m json.tool

# View summary (JSON)
cat predictions/week13/week13_prediction_summary.json | python3 -m json.tool
```

#### Validation Results
```bash
# View validation report (JSON)
cat validation/week13/week13_model_validation_report.json | python3 -m json.tool

# View validation summary (CSV)
cat validation/week13/validation_summary.csv
```

## 📊 Understanding the Files

### Analysis Files (`analysis/week13/`)

1. **`week13_comprehensive_analysis.json`**
   - Complete matchup analysis data
   - Team comparisons, strengths/weaknesses
   - Strategic insights for each matchup

2. **`week13_strategic_recommendations.csv`**
   - Actionable recommendations per game
   - Key factors to watch
   - Betting/analysis insights

3. **`week13_power_rankings.csv`**
   - Team power rankings for the week
   - Ranking changes from previous week
   - Strength metrics

4. **`week13_upset_alerts.csv`**
   - Potential upsets identified
   - Risk factors and probabilities
   - Underdog opportunities

### Prediction Files (`predictions/week13/`)

1. **`week13_comprehensive_predictions.csv`**
   - All game predictions in tabular format
   - Spread predictions, win probabilities
   - Confidence scores

2. **`week13_predictions.json`**
   - Structured prediction data
   - Model outputs and ensemble results
   - Detailed per-game predictions

3. **`week13_recommendations.csv`**
   - Actionable betting/analysis recommendations
   - Best value picks
   - Risk assessments

4. **`prediction_insights.json`**
   - Key insights from predictions
   - Notable trends and patterns
   - Model confidence levels

5. **`week13_prediction_summary.json`**
   - High-level summary statistics
   - Overall prediction confidence
   - Model performance metrics

### Validation Files (`validation/week13/`)

1. **`week13_model_validation_report.json`**
   - Complete model validation results
   - Model compatibility checks
   - Data quality assessments

2. **`validation_summary.csv`**
   - Summary of validation results
   - Model readiness status
   - Issues identified

## 🖥️ Viewing Results in Python

### Load and View Analysis Results
```python
import json
import pandas as pd

# Load comprehensive analysis
with open('analysis/week13/week13_comprehensive_analysis.json', 'r') as f:
    analysis = json.load(f)
print(json.dumps(analysis, indent=2))

# Load strategic recommendations
recommendations = pd.read_csv('analysis/week13/week13_strategic_recommendations.csv')
print(recommendations.head())

# Load power rankings
rankings = pd.read_csv('analysis/week13/week13_power_rankings.csv')
print(rankings)
```

### Load and View Predictions
```python
import json
import pandas as pd

# Load comprehensive predictions
predictions = pd.read_csv('predictions/week13/week13_comprehensive_predictions.csv')
print(predictions.head())

# Load prediction summary
with open('predictions/week13/week13_prediction_summary.json', 'r') as f:
    summary = json.load(f)
print(json.dumps(summary, indent=2))
```

## 📍 Finding Results for Any Week

Replace `week13` with your target week number:

```bash
# Week 14 results
ls -lh analysis/week14/
ls -lh predictions/week14/
ls -lh validation/week14/

# Week 15 results
ls -lh analysis/week15/
ls -lh predictions/week15/
ls -lh validation/week15/
```

## 🔍 Check if Results Exist

```bash
# Check if Week 13 analysis was completed
if [ -f "analysis/week13/week13_comprehensive_analysis.json" ]; then
    echo "✅ Week 13 analysis complete"
else
    echo "❌ Week 13 analysis not found - run analysis first"
fi

# Check if Week 13 predictions were generated
if [ -f "predictions/week13/week13_comprehensive_predictions.csv" ]; then
    echo "✅ Week 13 predictions complete"
else
    echo "❌ Week 13 predictions not found - run analysis first"
fi
```

## 📝 Quick Summary

**After running analysis for Week X:**

1. **Analysis results** → `analysis/weekX/`
2. **Predictions** → `predictions/weekX/`
3. **Validation reports** → `validation/weekX/`

**Most important files:**
- `analysis/weekX/weekX_comprehensive_analysis.json` - Full analysis
- `predictions/weekX/weekX_comprehensive_predictions.csv` - All predictions
- `predictions/weekX/weekX_recommendations.csv` - Actionable recommendations

