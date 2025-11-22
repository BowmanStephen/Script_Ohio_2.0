# Week 13 Training Data - Comprehensive Analysis Report

**Generated:** November 21, 2025  
**Dataset:** `training_data_2025_week13.csv`  
**System:** Script Ohio 2.0

---

## Executive Summary

This report provides a comprehensive analysis of Week 13 college football training data, featuring **47 games** across **7 conferences** with **86 analytical features** per game. The data represents real CFBD (College Football Data) integration and forms the foundation for Script Ohio 2.0's prediction models.

### Key Findings

- **Average ELO Rating:** 1558.8 (σ = 241.9)
- **Average Spread:** -6.78 points (home teams favored)
- **EPA Performance:** 62.8% of teams show positive adjusted EPA
- **Strongest Correlation:** Talent vs ELO (r = 0.649)

---

## Dataset Overview

| Metric | Value |
|--------|-------|
| Total Games | 47 |
| Conferences | 7 |
| Neutral Site Games | 1 |
| Feature Dimensions | 86 |
| Data Types | Metadata (9), Outcomes (3), Performance (74) |

### Conference Representation

The dataset includes teams from the following conferences:

- **SEC** - Southeastern Conference
- **Big Ten** - Big Ten Conference
- **Big 12** - Big 12 Conference
- **ACC** - Atlantic Coast Conference
- **Mountain West** - Mountain West Conference
- **Sun Belt** - Sun Belt Conference
- **Independent** - Independent teams

---

## Statistical Analysis

### ELO Ratings

The ELO rating system provides a comprehensive team strength metric:

```
Mean:     1558.81
Median:   1534.00
Std Dev:  241.88
Range:    [1004.0, 2189.0]
```

**Top 5 Teams by ELO:**
1. Oregon - 1940
2. Texas - 1917
3. Ohio State - 1903
4. Texas A&M - 1896
5. Miami - 1914

### Betting Spreads

Point spread distribution reveals home field advantage and team disparity:

```
Mean:     -6.78 (home teams favored)
Median:   -6.50
Std Dev:  12.70
Range:    [-43.5, 17.5]
```

**Largest Spreads (Home Favored):**
- Ohio - Akron: -43.5
- Kansas State - Cincinnati: -30.5
- Florida - LSU: -28.0

### Expected Points Added (EPA)

EPA measures offensive and defensive efficiency:

```
Mean:     0.0548
Median:   0.0602
Std Dev:  0.1335
Positive: 62.8% of teams
```

**Top 5 Offensive EPA:**
1. Cincinnati: 0.3090
2. Oregon: 0.2818
3. Texas: 0.2456
4. Ohio State: 0.2509
5. Ole Miss: 0.2223

---

## Advanced Analytics

### The Four Factors

Script Ohio 2.0 incorporates SP+'s four key factors:

#### 1. **Efficiency** (Success Rates)
- Standard down success rates
- Passing down success rates
- Overall play success metrics

#### 2. **Explosiveness**
- Overall explosiveness metrics
- Rush explosiveness
- Pass explosiveness
- Big play generation

#### 3. **Finishing Drives** (Points Per Opportunity)
```
Mean:     4.06 points/opportunity
Median:   4.02
Range:    [2.20, 5.64]
```

Top Scoring Efficiency:
- Oregon: 5.64 PPO
- Notre Dame: 5.34 PPO
- Texas: 5.03 PPO

#### 4. **Field Position**
- Average starting field position (offense)
- Average starting field position (defense)
- Field position advantage metrics

### Havoc Metrics

Disruptive plays on defense:

- **Total Havoc:** Combined disruption rate
- **Front Seven Havoc:** DL/LB disruption
- **DB Havoc:** Secondary disruption

---

## Correlation Analysis

Understanding relationships between key metrics:

| Metric Pair | Correlation | Interpretation |
|-------------|-------------|----------------|
| Talent vs ELO | **0.649** | Strong positive - talent predicts ELO |
| EPA vs ELO | **0.381** | Moderate positive - performance matters |
| EPA vs Talent | **0.180** | Weak - talent doesn't guarantee execution |

### Key Insights

1. **Talent Composite** is the strongest predictor of team strength (ELO)
2. **EPA Performance** moderately correlates with team strength, suggesting coaching/execution matters
3. **Talent vs EPA** weak correlation highlights the "talent doesn't always win" phenomenon

---

## Model Training Implications

### Feature Importance (Estimated)

Based on correlation analysis and domain knowledge:

1. **ELO Rating** (35-40%) - Overall team strength
2. **Talent Composite** (30-35%) - Player quality
3. **EPA Metrics** (20-25%) - Performance efficiency
4. **Situation-Specific** (10-15%) - Context factors

### Missing Components (vs SP+)

**Critical Gap:** Tempo Adjustment
- SP+ adjusts for pace of play
- Script Ohio 2.0 lacks per-possession normalization
- **Impact:** High-tempo teams may be overvalued

**Recommendation:** Implement plays-per-game normalization for EPA metrics

### Data Quality Assessment

✅ **Strengths:**
- Comprehensive feature set (86 dimensions)
- Real CFBD data integration
- Opponent-adjusted metrics
- Multiple performance dimensions

⚠️ **Concerns:**
- No tempo adjustment
- Equal model weighting (vs performance-based)
- Limited historical depth for some metrics

---

## Prediction Opportunities

### High-Confidence Picks (ELO Diff > 200)

Based on ELO disparities, these games show strong prediction signals:

1. **Ohio vs Akron** (ELO Δ: 467)
   - Spread: -43.5
   - Confidence: Very High
   
2. **Oregon vs Washington** (ELO Δ: 186)
   - Spread: -19.5
   - Confidence: High

3. **Texas vs Kentucky** (ELO Δ: 385)
   - Spread: -20.5
   - Confidence: Very High

### Value Opportunities

Games where model consensus might differ from betting lines:

- Look for EPA performance exceeding ELO expectations
- Identify tempo-adjusted efficiency mismatches
- Consider home field advantage deviations

---

## Technical Specifications

### Data Schema

**Game Metadata** (9 columns):
- Identifiers, dates, location
- Team names and conferences
- Pre-game metrics (ELO, talent)

**Outcomes** (3 columns):
- Home/away points
- Margin of victory
- Betting spread

**Performance Metrics** (74 columns):
- EPA (overall, rushing, passing)
- Success rates (standard, passing downs)
- Rushing analytics (line yards, second level, open field)
- Explosiveness (overall, rush, pass)
- Havoc (total, front seven, DB)
- Scoring efficiency
- Field position

---

## Recommendations

### Immediate Actions

1. **Extend Training Data**
   - Incorporate Week 13 into historical datasets
   - Retrain Ridge, XGBoost, FastAI models
   
2. **Implement Tempo Adjustment**
   - Calculate plays-per-game averages
   - Normalize EPA to per-possession basis
   
3. **Performance-Based Weighting**
   - Track model accuracy by game
   - Weight ensemble by historical performance

### Strategic Improvements

1. **SP+ Validation**
   - Compare predictions with SP+ ratings
   - Identify systematic biases
   - Calibrate ensemble weights

2. **Conference Championship Preparation**
   - Special handling for rematch games
   - Injury status integration
   - Momentum/recent performance weighting

3. **Bowl Season Adaptations**
   - Long layoff adjustments
   - Opt-out impact modeling
   - Motivation factor considerations

---

## Conclusion

The Week 13 training data represents a robust foundation for Script Ohio 2.0's prediction system. With 47 games and 86 features per game, the dataset captures the multifaceted nature of college football performance.

**Key Strengths:**
- Comprehensive feature engineering
- Real data integration
- Multiple performance dimensions

**Critical Next Steps:**
- Tempo adjustment implementation
- Performance-based model weighting
- Extended historical training

The system is positioned for continued improvement through systematic enhancement of the missing components identified in comparison with top-tier systems like SP+ and Big 200.

---

*Generated by Script Ohio 2.0 Analytics Engine*  
*For WCFL Competition - Stephen Bowman*
