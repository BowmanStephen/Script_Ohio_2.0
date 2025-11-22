# METRICS CALCULATION AND VALIDATION REPORT

**Generated:** 2025-11-14 01:15:35

## EXECUTIVE SUMMARY

- **Mission Status:** SUCCESS
- **2025 Games Processed:** 354
- **Historical Games:** 4520
- **Combined Dataset:** 4874 games
- **Features Validated:** 10

## METHODOLOGY VALIDATION

### Opponent Adjustment Approach
- **Method:** Subtraction-based opponent adjustments
- **Formula:** Adjusted_Metric = Team_Raw_Metric - Opponent_Average_Allowed
- **Validation:** All features follow historical patterns

### Quality Assurance Results
- **Missing Values:** None detected
- **Data Consistency:** All checks passed
- **Week Filtering:** Applied Week 5+ requirement
- **Range Validation:** All metrics within historical bounds

## FEATURE VALIDATION RESULTS

| Feature | Historical Mean | 2025 Mean | Deviation | Status |
|---------|----------------|-----------|-----------|--------|
| home_adjusted_epa | 0.1712 | 0.1548 | 0.25σ | ✓ OK |
| away_adjusted_epa | 0.1677 | 0.1541 | 0.21σ | ✓ OK |
| home_adjusted_success | 0.4268 | 0.4266 | 0.00σ | ✓ OK |
| away_adjusted_success | 0.4249 | 0.4231 | 0.04σ | ✓ OK |
| home_adjusted_explosiveness | 1.2343 | 1.2037 | 0.63σ | ✓ OK |
| away_adjusted_explosiveness | 1.2340 | 1.2067 | 0.57σ | ✓ OK |
| home_adjusted_line_yards | 2.9689 | 2.8816 | 0.43σ | ✓ OK |
| away_adjusted_line_yards | 2.9595 | 2.9024 | 0.28σ | ✓ OK |
| home_total_havoc_offense | 0.1720 | 0.1724 | 0.01σ | ✓ OK |
| away_total_havoc_offense | 0.1719 | 0.1710 | 0.02σ | ✓ OK |
