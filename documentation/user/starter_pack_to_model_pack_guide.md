# 🔗 Bridge from Starter Pack to Model Pack

This guide helps you transition from starter pack analytics to model pack machine learning.

## 🎯 Overview

The starter pack teaches you **analytics concepts**. Model pack shows you how those concepts become **86 ML features** that power predictions with 65-70% accuracy.

---

## 📊 Your Journey Map

| Starter Pack Notebook | What You Learn | Model Pack Equivalent | Weekly Training Data |
|----------------------|----------------|----------------------|---------------------|
| **05_matchup_predictor** | Basic prediction with simple stats | `01_linear_regression_margin.ipynb` | `training_data_2025_week01.csv` |
| **09_opponent_adjustments** | Opponent adjustment technique | **ALL notebooks** (86 features) | `training_data_2025_week05.csv` |
| **10_srs_adjusted_metrics** | Rating systems | `06_shap_interpretability.ipynb` | `training_data_2025_week05.csv` |

---

## 🚀 Quick Bridge Steps

### Step 1: Understand the Feature Connection

**In starter pack** (Notebook 05), you calculate:
```python
ppa_diff = home_offense_ppa - away_defense_ppa
```

**In model pack**, this becomes opponent-adjusted:
```python
# Load weekly training data to see:
import pandas as pd
weekly = pd.read_csv('../training_data_2025_week01.csv')
print(weekly[['home_adjusted_epa', 'away_adjusted_epa_allowed']].head())
```

### Step 2: Explore Weekly Training Data

Each `training_data_2025_week*.csv` file shows the 86 features:

```python
from starter_pack.utils.weekly_data_explorer import explore_weekly_features

# See Week 1 features
features = explore_weekly_features(week=1)
print(f"Week 1: {features['total_games']} games")
print(f"Total features: {features['total_features']}")
print(f"Feature categories: {list(features['feature_categories'].keys())}")

# See how starter pack concepts map to ML features
print("\nStarter Pack → ML Mapping:")
for concept, mapping in features['feature_mapping'].items():
    print(f"  {concept}: {mapping}")
```

### Step 3: Try Your First ML Model

```python
# Open model_pack/01_linear_regression_margin.ipynb
# Uses your concepts but with 86 opponent-adjusted features
# Better accuracy: 55% → 65-70%
```

---

## 🔍 Feature Deep Dive

### From 4 Features to 86 Features

**Starter Pack** (Notebook 05):
- 4 basic features: `ppa_diff`, `ppa_allowed_diff`, `successRate_diff`, `successRate_allowed_diff`
- 55% accuracy

**Model Pack**:
- 86 opponent-adjusted features
- 65-70% accuracy

### What Are the 86 Features?

1. **Basic Game Info** (8 features): season, week, teams, neutral_site, etc.
2. **Strength Metrics** (4 features): home_elo, away_elo, home_talent, away_talent
3. **Adjusted EPA** (8 features): total, rushing, passing (offense + defense)
4. **Adjusted Success Rates** (12 features): standard downs, passing downs (offense + defense)
5. **Adjusted Explosiveness** (12 features): rush, pass, total (offense + defense)
6. **Adjusted Line Yards** (4 features): offense + defense
7. **Adjusted Second-Level Yards** (4 features): offense + defense
8. **Adjusted Open Field Yards** (4 features): offense + defense
9. **Havoc Metrics** (12 features): total, front seven, DB (offense + defense)
10. **Points & Margin** (4 features): home_points, away_points, margin, spread
11. **Field Position** (8 features): avg_start, points_per_opportunity (offense + defense)
12. **Plus 6 more specialized features**

**Total: 86 features** (all opponent-adjusted using Notebook 09 technique)

---

## 🤖 Using the Agent System

The Learning Navigator Agent can guide you:

```python
from agents.analytics_orchestrator import AnalyticsOrchestrator, AnalyticsRequest

orchestrator = AnalyticsOrchestrator()

# Get personalized bridge guidance
request = AnalyticsRequest(
    user_id='your_id',
    query='Bridge me from matchup predictor to model pack',
    query_type='learning',
    parameters={'current_notebook': '05_matchup_predictor.ipynb'},
    context_hints={'role': 'data_scientist'}
)

response = orchestrator.process_analytics_request(request)
print(response.insights)
```

**Agent Capabilities**:
- ✅ Map starter pack notebooks to model pack notebooks
- ✅ Show feature connections and mappings
- ✅ Preview weekly training data structure
- ✅ Provide personalized learning paths
- ✅ Explain concepts at your skill level

---

## 📚 Recommended Learning Paths

### Path 1: Basic Prediction → ML (For Beginners)

1. ✅ Complete `05_matchup_predictor.ipynb`
2. Explore `training_data_2025_week01.csv` to see feature format
3. Try `model_pack/01_linear_regression_margin.ipynb`
4. Compare your 55% accuracy to ML's 65-70%

**Time**: ~2 hours

### Path 2: Opponent Adjustments → Feature Engineering (For Intermediate)

1. ✅ Complete `09_opponent_adjustments.ipynb`
2. Explore `training_data_2025_week05.csv` to see all 86 adjusted features
3. Try `model_pack/03_xgboost_win_probability.ipynb`
4. Understand feature importance

**Time**: ~3 hours

### Path 3: Complete Understanding (For Advanced)

1. Complete all starter pack notebooks (00-12)
2. Explore weekly training data for multiple weeks
3. Try all model pack notebooks (01-07)
4. Understand SHAP interpretability (notebook 06)

**Time**: ~10-15 hours

---

## 💡 Key Concepts

### Temporal Validation (Week 5+)

Model pack uses **Week 5+ only** (not Week 1-4). Why?

- **Prevents data leakage**: Can't use future games to predict past games
- **Meaningful sample sizes**: Opponent adjustments need multiple games
- **Real-world accuracy**: Matches how predictions work in practice

```python
# See why Week 5+ matters
for week in [1, 5, 10]:
    weekly = pd.read_csv(f'../training_data_2025_week{week:02d}.csv')
    print(f"Week {week}: {len(weekly)} games")
    # Week 5+ has more reliable opponent adjustments
```

### Opponent Adjustment = Foundation

Every single feature in model pack uses the opponent adjustment technique from Notebook 09:

```python
# Your technique (Notebook 09):
adj_offense_ppa = offense_ppa - opponent_avg_def_ppa

# Applied to 86 features in model pack:
home_adjusted_epa = home_epa - avg_opponent_def_epa_allowed
home_adjusted_rushing_epa = home_rush_epa - avg_opponent_def_rush_epa_allowed
# ... and 84 more features using the same principle
```

---

## 🛠️ Tools & Resources

### Weekly Data Explorer

```python
from starter_pack.utils.weekly_data_explorer import explore_weekly_features

# Explore any week
features = explore_weekly_features(week=5)
print(features['feature_categories'])
print(features['starter_pack_connections'])
```

### Agent System

Ask the Learning Navigator Agent:
- "Show me how starter pack EPA becomes model pack features"
- "Bridge me from opponent adjustments to ML"
- "What's the difference between starter pack and model pack features?"

### Documentation

- **Starter Pack README**: `starter_pack/README.md`
- **Model Pack Info**: `model_pack/info_sheet_notebooks.md`
- **CFBD API Guide**: `documentation/user/cfbd_api_guide.md`
- **Agent Guide**: `AGENTS.md`

---

## ❓ FAQ

### Q: Why does model pack have 86 features when starter pack uses 4?

**A**: Model pack applies the opponent adjustment technique to **every metric**:
- Starter pack: Adjust 2 metrics (PPA, success rate) = 4 features
- Model pack: Adjust 43 metrics × 2 (offense/defense) = 86 features

### Q: Can I use Week 1-4 data?

**A**: Model pack uses Week 5+ for temporal validation. Week 1-4 games are available but not recommended for training because:
- Small sample sizes for opponent adjustments
- Teams still developing identity
- Higher prediction error

### Q: How do I know which features matter most?

**A**: Try `model_pack/06_shap_interpretability.ipynb` to see feature importance rankings.

### Q: Can I use starter pack data directly for ML?

**A**: Not directly. Starter pack data needs transformation to the 86-feature format. Use `model_pack/migrate_starter_pack_data.py` or the weekly training data files.

---

## 🎓 Next Steps

1. **Explore Weekly Data**: Use `explore_weekly_features()` to see the 86 features
2. **Try Model Pack**: Start with `01_linear_regression_margin.ipynb`
3. **Ask the Agent**: Get personalized guidance from Learning Navigator Agent
4. **Understand Features**: Use SHAP notebook to see which features matter most

---

**Ready to bridge?** Start with exploring your weekly training data files!

```python
from starter_pack.utils.weekly_data_explorer import explore_weekly_features
features = explore_weekly_features(week=5)
print(features)
```

