# Calculation Methodology Documentation

**Last Updated:** 2025-11-19  
**Version:** 1.0

## Overview

This document describes the calculation methodology used in the Script Ohio 2.0 college football analytics system. All calculations follow best practices to ensure accuracy, consistency, and prevent data leakage.

## Opponent Adjustment Methodology

### Core Principle

All advanced metrics use **subtraction-based opponent adjustments** to normalize team performance against opponent strength.

### Formula

```
Adjusted_Metric = Team_Raw_Metric - Opponent_Average_Allowed
```

### Example

For EPA (Expected Points Added):
- Team A's raw EPA: 0.25
- Opponent's average EPA allowed: 0.15
- Team A's adjusted EPA: 0.25 - 0.15 = 0.10

### Implementation

The opponent adjustment is calculated using historical data to determine what an average opponent would allow. This ensures:

1. **No Data Leakage**: Only past games are used to calculate opponent averages
2. **Consistency**: Same methodology applied across all metrics
3. **Normalization**: Teams are compared on equal footing

## EPA (Expected Points Added) Calculations

### Definition

EPA measures the expected point value added (or lost) on each play compared to the baseline expectation.

### Calculation

EPA is calculated from play-by-play data using:
- Down and distance
- Field position
- Expected points model

### Opponent Adjustment

```
home_adjusted_epa = home_team_epa - opponent_avg_epa_allowed
away_adjusted_epa = away_team_epa - opponent_avg_epa_allowed
```

### Validation

- EPA values typically range from -2 to +2 for adjusted metrics
- Values outside this range may indicate calculation errors
- Historical mean should be close to 0 for adjusted EPA

## Success Rate Calculations

### Definition

Success rate measures the percentage of plays that gain meaningful yardage (typically 50% of needed yards on 1st down, 70% on 2nd down, 100% on 3rd/4th down).

### Opponent Adjustment

```
home_adjusted_success = home_team_success_rate - opponent_avg_success_allowed
away_adjusted_success = away_team_success_rate - opponent_avg_success_allowed
```

## Feature Engineering

### 86-Feature Model Schema

The training data includes 86 features organized into categories:

1. **EPA Metrics** (6 features)
   - home_adjusted_epa, away_adjusted_epa
   - home_adjusted_rushing_epa, away_adjusted_rushing_epa
   - home_adjusted_passing_epa, away_adjusted_passing_epa

2. **Success Rates** (6 features)
   - home_adjusted_success, away_adjusted_success
   - home_adjusted_standard_down_success, away_adjusted_standard_down_success
   - home_adjusted_passing_down_success, away_adjusted_passing_down_success

3. **Explosiveness** (6 features)
   - home_adjusted_explosiveness, away_adjusted_explosiveness
   - home_adjusted_rush_explosiveness, away_adjusted_rush_explosiveness
   - home_adjusted_pass_explosiveness, away_adjusted_pass_explosiveness

4. **Line Yards** (6 features)
   - home_adjusted_line_yards, away_adjusted_line_yards
   - home_adjusted_second_level_yards, away_adjusted_second_level_yards
   - home_adjusted_open_field_yards, away_adjusted_open_field_yards

5. **Havoc Rates** (12 features)
   - home_total_havoc_offense, away_total_havoc_offense
   - home_total_havoc_defense, away_total_havoc_defense
   - Plus front seven and DB havoc rates

6. **Points Per Opportunity** (4 features)
   - home_points_per_opportunity_offense, away_points_per_opportunity_offense
   - home_points_per_opportunity_defense, away_points_per_opportunity_defense

7. **Average Starting Field Position** (4 features)
   - home_avg_start_offense, away_avg_start_offense
   - home_avg_start_defense, away_avg_start_defense

8. **Metadata** (42+ features)
   - Game identifiers, teams, conferences, Elo ratings, talent ratings, etc.

## Temporal Consistency

### Week 5+ Requirement

Opponent adjustments require sufficient data to be meaningful. Therefore:

- **Week 5+ Filter**: Only games from Week 5 onwards are used for opponent-adjusted features
- **Rationale**: Early season games don't have enough opponent data for reliable adjustments
- **Implementation**: All training data filters to `week >= 5` for opponent-adjusted calculations

## Data Leakage Prevention

### Principles

1. **No Future Data**: Opponent averages only use games played before the current game
2. **Temporal Ordering**: Games are processed in chronological order
3. **Validation**: Correlation checks ensure no perfect predictions (which would indicate leakage)

### Validation Checks

- Adjusted EPA correlation with margin should be positive but < 0.9
- No perfect predictions in historical data
- Opponent averages calculated only from past games

## Calculation Verification Process

### Automated Verification

The system includes automated verification scripts:

1. **EPA Calculations**: Verify formulas and value ranges
2. **Opponent Adjustments**: Verify subtraction methodology
3. **Feature Engineering**: Verify all 86 features present and correct
4. **Model Compatibility**: Verify data types and schema match
5. **Temporal Consistency**: Verify Week 5+ filtering
6. **Data Leakage**: Verify no future data used

### Running Verification

```bash
# Run comprehensive calculation verification
python scripts/verify_all_calculations.py

# Generate verification report
python scripts/generate_calculation_verification_report.py
```

## Best Practices

### 1. Always Use Opponent-Adjusted Metrics

Raw metrics are not comparable across teams. Always use adjusted metrics for:
- Model training
- Team comparisons
- Predictions

### 2. Validate Against Historical Patterns

- Compare current season metrics to historical means
- Flag deviations > 2 standard deviations
- Investigate extreme values

### 3. Maintain Temporal Consistency

- Use Week 5+ filter for opponent adjustments
- Process games in chronological order
- Never use future data in calculations

### 4. Regular Verification

- Run verification scripts after data updates
- Review verification reports
- Address any issues immediately

## References

- **Metrics Calculation Agent**: `model_pack/metrics_calculation_agent.py`
- **Verification Script**: `scripts/verify_all_calculations.py`
- **Verification Report**: `reports/calculation_verification_report.md`
- **Historical Methodology**: `model_pack/metrics_calculation_report.md`

