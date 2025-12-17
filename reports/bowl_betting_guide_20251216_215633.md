# Bowl Betting Evaluation Guide

Generated: 2025-12-16T21:56:33

- Slate: `/Users/stephen_bowman/Documents/GitHub/Script_Ohio_2.0/predictions/draftkings_slate_2025/dk_slate_predictions_20251216_214645.csv`
- Systems: `/Users/stephen_bowman/Documents/GitHub/Script_Ohio_2.0/predictions/ncaapredictions.csv`

## Spread Orientation

- Canonical: `home_spread < 0` home favored; `home_spread > 0` home underdog
- Systems file assumed road spreads; converted via `home = -road` with per-column flip inference.

## Totals Warning

Totals model appears mis-scaled or mismatched (rf_total median=17.490000000000002, corr=-0.11256909290652314). Totals edges suppressed.

## Quick Board (sorted by date)

| date       | bowl                  | away_team             | home_team         | dk_home_spread | your_home_spread | edge_vs_dk | agreement_rate | clv_direction | robust_edge | flags                             | tier     | tier_reasons                                               | dk_total | rf_total | total_pick | total_edge | adv_stats_coverage | open_home_spread | current_home_spread | consensus_mean_home | consensus_median_home | consensus_std | move_from_open | z_vs_consensus |
| ---------- | --------------------- | --------------------- | ----------------- | -------------- | ---------------- | ---------- | -------------- | ------------- | ----------- | --------------------------------- | -------- | ---------------------------------------------------------- | -------- | -------- | ---------- | ---------- | ------------------ | ---------------- | ------------------- | ------------------- | --------------------- | ------------- | -------------- | -------------- |
| 2025-12-17 | 68 Ventures Bowl      | Louisiana             | Delaware          | 3.0            | -2.48            | -5.48      | 0.0            | TOWARD_YOU    | 1.58        |                                   | X-REVIEW | AGREE=0.00                                                 | 61.5     |          |            |            | 1.0                | 3.5              | 3.0                 | 4.01                | 3.4                   | 3.46          | -0.5           | -1.87          |
| 2025-12-17 | Cure Bowl             | Old Dominion          | South Florida     | -2.5           | -3.4             | -0.9       | 1.0            | TOWARD_YOU    | 0.24        | BIG_MOVE                          | X-REVIEW | BIG_MOVE=4.50\|AGREE=1.00                                  | 52.5     |          |            |            | 1.0                | -7.5             | -3.0                | -8.47               | -8.68                 | 3.69          | 4.5            | 1.37           |
| 2025-12-18 | Xbox Bowl             | Missouri State        | Arkansas State    | -1.5           | -2.34            | -0.84      |                |               | 840000.0    |                                   | C        |                                                            | 54.5     |          |            |            | 1.0                |                  |                     |                     |                       |               |                |                |
| 2025-12-19 | CFP First Round       | Alabama               | Oklahoma          | 1.5            | -3.14            | -4.64      | 0.75           | TOWARD_YOU    | 1.88        |                                   | A        | AGREE=0.75                                                 | 40.5     |          |            |            | 1.0                | 2.0              | 1.0                 | -1.9                | -1.7                  | 2.46          | -1.0           | -0.5           |
| 2025-12-19 | Gasparilla Bowl       | Memphis               | NC State          | -4.5           | -2.87            | 1.63       | 0.75           | TOWARD_YOU    | 0.42        |                                   | C        | AGREE=0.75                                                 | 58.5     |          |            |            | 1.0                | -5.5             | -4.5                | -2.39               | -2.8                  | 3.91          | 1.0            | -0.12          |
| 2025-12-19 | Myrtle Beach Bowl     | Kennesaw State        | Western Michigan  | -3.5           | -2.69            | 0.81       |                |               | 810000.0    |                                   | C        |                                                            | 48.5     |          |            |            | 1.0                |                  |                     |                     |                       |               |                |                |
| 2025-12-20 | CFP First Round       | Miami                 | Texas A&M         | -3.5           | -3.22            | 0.28       |                |               | 280000.0    |                                   | C        |                                                            | 50.5     |          |            |            | 1.0                |                  |                     |                     |                       |               |                |                |
| 2025-12-20 | CFP First Round       | Tulane                | Ole Miss          | -17.5          | -3.12            | 14.38      |                |               | 14380000.0  |                                   | A        |                                                            | 56.5     |          |            |            | 1.0                |                  |                     |                     |                       |               |                |                |
| 2025-12-20 | CFP First Round       | James Madison         | Oregon            | -21.0          | -3.63            | 17.37      | 0.5            | AWAY_FROM_YOU | 3.09        | OUTLIER\|HIGH_STD                 | X-REVIEW | OUTLIER_Z=2.67\|HIGH_STD=5.62\|AGREE=0.50                  | 47.5     |          |            |            | 1.0                | -21.0            | -21.5               | -18.62              | -20.08                | 5.62          | -0.5           | 2.67           |
| 2025-12-22 | Potato Bowl           | Washington State      | Utah State        | -2.5           | -2.71            | -0.21      | 0.0            | TOWARD_YOU    | 0.07        | OUTLIER\|BIG_MOVE\|SIGN_CONFLICT  | X-REVIEW | SIGN_CONFLICT\|OUTLIER_Z=-2.26\|BIG_MOVE=-3.50\|AGREE=0.00 | 50.5     |          |            |            | 1.0                | 1.0              | -2.5                | 4.26                | 4.99                  | 3.08          | -3.5           | -2.26          |
| 2025-12-23 | Boca Raton Bowl       | Toledo                | Louisville        | -6.5           | -3.28            | 3.22       | 0.33           | TOWARD_YOU    | 0.9         |                                   | B        | AGREE=0.33                                                 | 45.5     |          |            |            | 1.0                | -9.5             | -7.0                | -5.98               | -6.0                  | 3.56          | 2.5            | 0.76           |
| 2025-12-23 | Frisco Bowl           | UNLV                  | Ohio              | 5.5            | -2.92            | -8.42      | 1.0            | AWAY_FROM_YOU | 3.07        | OUTLIER                           | X-REVIEW | OUTLIER_Z=-2.86\|AGREE=1.00                                | 65.5     |          |            |            | 1.0                | 4.0              | 5.0                 | 4.92                | 5.16                  | 2.74          | 1.0            | -2.86          |
| 2025-12-23 | New Orleans Bowl      | Western Kentucky      | Southern Miss     | 4.5            | -2.85            | -7.35      | 0.33           | AWAY_FROM_YOU | 2.33        |                                   | B        | AGREE=0.33                                                 | 57.5     |          |            |            | 1.0                | 3.0              | 4.0                 | 3.15                | 3.08                  | 3.15          | 1.0            | -1.91          |
| 2025-12-24 | Hawai'i Bowl          | California            | Hawai'i           | 1.5            | -2.59            | -4.09      | 0.67           | TOWARD_YOU    | 1.36        |                                   | A        | AGREE=0.67                                                 | 54.5     |          |            |            | 1.0                | 2.5              | 1.5                 | 0.4                 | 0.22                  | 3.0           | -1.0           | -1.0           |
| 2025-12-26 | First Responder Bowl  | Florida International | UTSA              | -9.5           | -2.77            | 6.73       | 0.33           | NEUTRAL       | 1.14        | HIGH_STD                          | B        | HIGH_STD=5.89\|AGREE=0.33                                  | 59.5     |          |            |            | 1.0                | -8.5             | -8.5                | -9.96               | -9.85                 | 5.89          | 0.0            | 1.22           |
| 2025-12-26 | GameAbove Sports Bowl | Central Michigan      | Northwestern      | -10.5          | -2.69            | 7.81       |                |               | 7810000.0   |                                   | A        |                                                            | 43.5     |          |            |            | 1.0                |                  |                     |                     |                       |               |                |                |
| 2025-12-26 | Rate Bowl             | New Mexico            | Minnesota         | -2.5           | -2.65            | -0.15      | 0.67           | TOWARD_YOU    | 0.03        | HIGH_STD                          | C        | HIGH_STD=4.49\|AGREE=0.67                                  | 45.5     |          |            |            | 1.0                | -3.0             | -2.5                | -3.8                | -2.58                 | 4.49          | 0.5            | 0.26           |
| 2025-12-27 | Arizona Bowl          | Miami (OH)            | Fresno State      | -4.5           | -2.7             | 1.8        |                |               | 1800000.0   |                                   | C        |                                                            | 42.5     |          |            |            | 1.0                |                  |                     |                     |                       |               |                |                |
| 2025-12-27 | Fenway Bowl           | UConn                 | Army              | -8.5           | -2.82            | 5.68       |                |               | 5680000.0   |                                   | A        |                                                            | 44.5     |          |            |            | 1.0                |                  |                     |                     |                       |               |                |                |
| 2025-12-27 | Gator Bowl            | Virginia              | Missouri          | -7.0           | -3.14            | 3.86       | 0.33           | TOWARD_YOU    | 1.11        |                                   | B        | AGREE=0.33                                                 | 47.5     |          |            |            | 1.0                | -7.0             | -6.5                | -5.55               | -5.29                 | 3.47          | 0.5            | 0.69           |
| 2025-12-27 | Military Bowl         | Pittsburgh            | East Carolina     | 8.5            | -3.06            | -11.56     | 0.67           | AWAY_FROM_YOU | 3.01        | OUTLIER                           | X-REVIEW | OUTLIER_Z=-2.00\|AGREE=0.67                                | 57.5     |          |            |            | 1.0                | 6.0              | 7.0                 | 4.63                | 5.03                  | 3.84          | 1.0            | -2.0           |
| 2025-12-27 | New Mexico Bowl       | North Texas           | San Diego State   | 3.0            | -3.2             | -6.2       |                |               | 6200000.0   |                                   | A        |                                                            | 54.5     |          |            |            | 1.0                |                  |                     |                     |                       |               |                |                |
| 2025-12-27 | Pinstripe Bowl        | Penn State            | Clemson           | -3.5           | -2.99            | 0.51       | 1.0            | TOWARD_YOU    | 0.14        | BIG_MOVE\|SIGN_CONFLICT           | X-REVIEW | SIGN_CONFLICT\|BIG_MOVE=-4.50\|AGREE=1.00                  | 48.5     |          |            |            | 1.0                | 1.0              | -3.5                | 4.17                | 4.22                  | 3.73          | -4.5           | -1.92          |
| 2025-12-27 | Pop-Tarts Bowl        | Georgia Tech          | BYU               | -4.5           | -3.04            | 1.46       | 0.0            | AWAY_FROM_YOU | 0.32        | HIGH_STD                          | X-REVIEW | HIGH_STD=4.58\|AGREE=0.00                                  | 56.5     |          |            |            | 1.0                | -2.5             | -4.5                | -8.4                | -8.46                 | 4.58          | -2.0           | 1.17           |
| 2025-12-27 | Texas Bowl            | LSU                   | Houston           | -3.0           | -2.65            | 0.35       | 1.0            | NEUTRAL       | 0.1         | SIGN_CONFLICT                     | X-REVIEW | SIGN_CONFLICT\|AGREE=1.00                                  | 41.5     |          |            |            | 1.0                | -3.0             | -3.0                | 3.53                | 3.8                   | 3.49          | 0.0            | -1.77          |
| 2025-12-29 | Birmingham Bowl       | Georgia Southern      | App State         | 7.0            | -2.38            | -9.38      | 1.0            | AWAY_FROM_YOU | 3.39        |                                   | A        | AGREE=1.00                                                 | 59.5     |          |            |            | 1.0                | 2.0              | 4.5                 | 1.62                | 1.95                  | 2.77          | 2.5            | -1.44          |
| 2025-12-30 | Alamo Bowl            | USC                   | TCU               | 4.5            | -3.07            | -7.57      | 0.0            | TOWARD_YOU    | 2.15        | OUTLIER                           | X-REVIEW | OUTLIER_Z=-3.11\|AGREE=0.00                                | 57.5     |          |            |            | 1.0                | 5.5              | 4.5                 | 7.86                | 7.94                  | 3.51          | -1.0           | -3.11          |
| 2025-12-30 | Independence Bowl     | Coastal Carolina      | Louisiana Tech    | -8.5           | -2.57            | 5.93       | 1.0            | AWAY_FROM_YOU | 1.19        | HIGH_STD                          | A        | HIGH_STD=4.99\|AGREE=1.00                                  | 50.5     |          |            |            | 1.0                | -7.0             | -9.0                | -7.65               | -7.49                 | 4.99          | -2.0           | 1.02           |
| 2025-12-30 | Music City Bowl       | Tennessee             | Illinois          | 2.5            | -2.95            | -5.45      | 0.0            | TOWARD_YOU    | 1.84        | OUTLIER\|BIG_MOVE                 | X-REVIEW | OUTLIER_Z=-2.24\|BIG_MOVE=-4.00\|AGREE=0.00                | 61.5     |          |            |            | 1.0                | 6.5              | 2.5                 | 3.68                | 3.62                  | 2.95          | -4.0           | -2.24          |
| 2025-12-31 | Citrus Bowl           | Michigan              | Texas             | -7.5           | -2.93            | 4.57       | 1.0            | AWAY_FROM_YOU | 1.4         | BIG_MOVE                          | X-REVIEW | BIG_MOVE=-3.00\|AGREE=1.00                                 | 46.5     |          |            |            | 1.0                | -4.5             | -7.5                | -2.74               | -2.0                  | 3.27          | -3.0           | -0.06          |
| 2025-12-31 | Las Vegas Bowl        | Nebraska              | Utah              | -16.5          | -3.11            | 13.39      | 0.67           | AWAY_FROM_YOU | 2.52        | OUTLIER\|HIGH_STD                 | X-REVIEW | OUTLIER_Z=2.18\|HIGH_STD=5.31\|AGREE=0.67                  | 50.5     |          |            |            | 1.0                | -14.0            | -16.5               | -14.69              | -15.24                | 5.31          | -2.5           | 2.18           |
| 2025-12-31 | ReliaQuest Bowl       | Iowa                  | Vanderbilt        | -5.5           | -3.2             | 2.3        | 1.0            | AWAY_FROM_YOU | 0.71        |                                   | C        | AGREE=1.00                                                 | 47.5     |          |            |            | 1.0                | -4.0             | -5.0                | -2.22               | -1.75                 | 3.22          | -1.0           | -0.3           |
| 2025-12-31 | Sun Bowl              | Arizona State         | Duke              | -2.5           | -2.74            | -0.24      |                |               | 240000.0    |                                   | C        |                                                            | 49.5     |          |            |            | 1.0                |                  |                     |                     |                       |               |                |                |
| 2026-01-02 | Armed Forces Bowl     | Rice                  | Texas State       | -10.5          | -2.57            | 7.93       |                |               | 7930000.0   |                                   | A        |                                                            | 59.5     |          |            |            | 1.0                |                  |                     |                     |                       |               |                |                |
| 2026-01-02 | Duke's Mayo Bowl      | Wake Forest           | Mississippi State | -4.0           | -2.76            | 1.24       |                |               | 1240000.0   |                                   | C        |                                                            | 56.5     |          |            |            | 1.0                |                  |                     |                     |                       |               |                |                |
| 2026-01-02 | Holiday Bowl          | Arizona               | SMU               | 3.0            | -3.18            | -6.18      | 0.67           | AWAY_FROM_YOU | 1.36        | HIGH_STD                          | A        | HIGH_STD=4.53\|AGREE=0.67                                  | 51.5     |          |            |            | 1.0                | 1.5              | 3.0                 | -0.2                | -0.2                  | 4.53          | 1.5            | -0.66          |
| 2026-01-02 | Liberty Bowl          | Navy                  | Cincinnati        | 6.5            | -2.98            | -9.48      | 1.0            | AWAY_FROM_YOU | 1.91        | BIG_MOVE\|HIGH_STD\|SIGN_CONFLICT | X-REVIEW | SIGN_CONFLICT\|BIG_MOVE=13.50\|HIGH_STD=4.96\|AGREE=1.00   | 53.5     |          |            |            | 1.0                | -6.5             | 7.0                 | -3.18               | -3.86                 | 4.96          | 13.5           | 0.04           |

## Audit / Review Queue

| date       | bowl            | away_team        | home_team     | dk_home_spread | your_home_spread | edge_vs_dk           | current_home_spread | move_from_open | z_vs_consensus       | agreement_rate     | flags                             | tier     | tier_reasons                                               |
| ---------- | --------------- | ---------------- | ------------- | -------------- | ---------------- | -------------------- | ------------------- | -------------- | -------------------- | ------------------ | --------------------------------- | -------- | ---------------------------------------------------------- |
| 2025-12-30 | Alamo Bowl      | USC              | TCU           | 4.5            | -3.07            | -7.57                | 4.5                 | -1.0           | -3.112015309261537   | 0.0                | OUTLIER                           | X-REVIEW | OUTLIER_Z=-3.11\|AGREE=0.00                                |
| 2025-12-23 | Frisco Bowl     | UNLV             | Ohio          | 5.5            | -2.92            | -8.42                | 5.0                 | 1.0            | -2.856879215679745   | 1.0                | OUTLIER                           | X-REVIEW | OUTLIER_Z=-2.86\|AGREE=1.00                                |
| 2025-12-20 | CFP First Round | James Madison    | Oregon        | -21.0          | -3.63            | 17.37                | -21.5               | -0.5           | 2.6653660133130397   | 0.5                | OUTLIER\|HIGH_STD                 | X-REVIEW | OUTLIER_Z=2.67\|HIGH_STD=5.62\|AGREE=0.50                  |
| 2025-12-22 | Potato Bowl     | Washington State | Utah State    | -2.5           | -2.71            | -0.20999999999999996 | -2.5                | -3.5           | -2.264819945677907   | 0.0                | OUTLIER\|BIG_MOVE\|SIGN_CONFLICT  | X-REVIEW | SIGN_CONFLICT\|OUTLIER_Z=-2.26\|BIG_MOVE=-3.50\|AGREE=0.00 |
| 2025-12-30 | Music City Bowl | Tennessee        | Illinois      | 2.5            | -2.95            | -5.45                | 2.5                 | -4.0           | -2.2420238151487633  | 0.0                | OUTLIER\|BIG_MOVE                 | X-REVIEW | OUTLIER_Z=-2.24\|BIG_MOVE=-4.00\|AGREE=0.00                |
| 2025-12-31 | Las Vegas Bowl  | Nebraska         | Utah          | -16.5          | -3.11            | 13.39                | -16.5               | -2.5           | 2.1788893004946646   | 0.6666666666666666 | OUTLIER\|HIGH_STD                 | X-REVIEW | OUTLIER_Z=2.18\|HIGH_STD=5.31\|AGREE=0.67                  |
| 2025-12-27 | Military Bowl   | Pittsburgh       | East Carolina | 8.5            | -3.06            | -11.56               | 7.0                 | 1.0            | -2.0015945578290975  | 0.6666666666666666 | OUTLIER                           | X-REVIEW | OUTLIER_Z=-2.00\|AGREE=0.67                                |
| 2025-12-27 | Pinstripe Bowl  | Penn State       | Clemson       | -3.5           | -2.99            | 0.5099999999999998   | -3.5                | -4.5           | -1.9179823911015115  | 1.0                | BIG_MOVE\|SIGN_CONFLICT           | X-REVIEW | SIGN_CONFLICT\|BIG_MOVE=-4.50\|AGREE=1.00                  |
| 2025-12-27 | Texas Bowl      | LSU              | Houston       | -3.0           | -2.65            | 0.3500000000000001   | -3.0                | 0.0            | -1.7709539008814912  | 1.0                | SIGN_CONFLICT                     | X-REVIEW | SIGN_CONFLICT\|AGREE=1.00                                  |
| 2025-12-17 | Cure Bowl       | Old Dominion     | South Florida | -2.5           | -3.4             | -0.8999999999999999  | -3.0                | 4.5            | 1.3745389720794778   | 1.0                | BIG_MOVE                          | X-REVIEW | BIG_MOVE=4.50\|AGREE=1.00                                  |
| 2025-12-31 | Citrus Bowl     | Michigan         | Texas         | -7.5           | -2.93            | 4.57                 | -7.5                | -3.0           | -0.05838389970270693 | 1.0                | BIG_MOVE                          | X-REVIEW | BIG_MOVE=-3.00\|AGREE=1.00                                 |
| 2026-01-02 | Liberty Bowl    | Navy             | Cincinnati    | 6.5            | -2.98            | -9.48                | 7.0                 | 13.5           | 0.0408559787166783   | 1.0                | BIG_MOVE\|HIGH_STD\|SIGN_CONFLICT | X-REVIEW | SIGN_CONFLICT\|BIG_MOVE=13.50\|HIGH_STD=4.96\|AGREE=1.00   |

## Tier Summary

| X-REVIEW | A  | C | B |
| -------- | -- | - | - |
| 14       | 10 | 9 | 4 |

## Game-By-Game Notes

### 2025-12-17 — Louisiana @ Delaware (68 Ventures Bowl)
- Neutral: `True` | Tier: `X-REVIEW` | Reasons: `AGREE=0.00`
- DK (home spread): `3.00` | Your (home spread): `-2.48` | Edge: `-5.48`
- Consensus: mean `4.01` median `3.40` std `3.46` z `-1.87`
- Agreement (panel): `0.00` | Disagree: `linesag_home_spread, linemassey_home_spread, lineelo_home_spread`
- Market: open `3.50` current `3.00` move `-0.50` CLV `TOWARD_YOU`
- Flags: `` | Robust edge: `1.58`

| lineopen | line | lineavg     | linemedian | linesag | linemassey | lineelo     | linefei | linefpi |
| -------- | ---- | ----------- | ---------- | ------- | ---------- | ----------- | ------- | ------- |
| 3.5      | 3.0  | 4.006348999 | 3.4        | 6.37    | 8.16       | 3.709334409 | 3.0     |         |

| your_vs_median | your_vs_linesag | your_vs_linemassey | your_vs_lineelo    | your_vs_linefei | your_vs_linefpi |
| -------------- | --------------- | ------------------ | ------------------ | --------------- | --------------- |
| -5.88          | -8.85           | -10.64             | -6.189334409000001 | -5.48           |                 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-17 — Old Dominion @ South Florida (Cure Bowl)
- Neutral: `True` | Tier: `X-REVIEW` | Reasons: `BIG_MOVE=4.50|AGREE=1.00`
- DK (home spread): `-2.50` | Your (home spread): `-3.40` | Edge: `-0.90`
- Consensus: mean `-8.47` median `-8.68` std `3.69` z `1.37`
- Agreement (panel): `1.00`
- Market: open `-7.50` current `-3.00` move `4.50` CLV `TOWARD_YOU`
- Flags: `BIG_MOVE` | Robust edge: `0.24`

| lineopen | line | lineavg       | linemedian | linesag | linemassey | lineelo      | linefei | linefpi |
| -------- | ---- | ------------- | ---------- | ------- | ---------- | ------------ | ------- | ------- |
| -7.5     | -3.0 | -8.4725487191 | -8.675     | -9.2    | -7.5       | -9.202252534 | -10.2   |         |

| your_vs_median | your_vs_linesag   | your_vs_linemassey | your_vs_lineelo   | your_vs_linefei   | your_vs_linefpi |
| -------------- | ----------------- | ------------------ | ----------------- | ----------------- | --------------- |
| 5.275          | 5.799999999999999 | 4.1                | 5.802252533999999 | 6.799999999999999 |                 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-18 — Missouri State @ Arkansas State (Xbox Bowl)
- Neutral: `True` | Tier: `C` | Reasons: ``
- DK (home spread): `-1.50` | Your (home spread): `-2.34` | Edge: `-0.84`
- Consensus: mean `nan` median `nan` std `nan` z `nan`
- Agreement (panel): ``
- Flags: `` | Robust edge: `840000.00`

| lineopen | line | lineavg | linemedian | linesag | linemassey | lineelo | linefei | linefpi |
| -------- | ---- | ------- | ---------- | ------- | ---------- | ------- | ------- | ------- |
|          |      |         |            |         |            |         |         |         |

| your_vs_median | your_vs_linesag | your_vs_linemassey | your_vs_lineelo | your_vs_linefei | your_vs_linefpi |
| -------------- | --------------- | ------------------ | --------------- | --------------- | --------------- |
|                |                 |                    |                 |                 |                 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-19 — Alabama @ Oklahoma (CFP First Round)
- Neutral: `False` | Tier: `A` | Reasons: `AGREE=0.75`
- DK (home spread): `1.50` | Your (home spread): `-3.14` | Edge: `-4.64`
- Consensus: mean `-1.90` median `-1.70` std `2.46` z `-0.50`
- Agreement (panel): `0.75` | Disagree: `linemassey_home_spread`
- Market: open `2.00` current `1.00` move `-1.00` CLV `TOWARD_YOU`
- Flags: `` | Robust edge: `1.88`

| lineopen | line | lineavg       | linemedian | linesag | linemassey | lineelo      | linefei | linefpi |
| -------- | ---- | ------------- | ---------- | ------- | ---------- | ------------ | ------- | ------- |
| 2.0      | 1.0  | -1.8997171742 | -1.7       | -1.14   | 2.49       | -4.289692199 | -0.2    |         |

| your_vs_median      | your_vs_linesag | your_vs_linemassey | your_vs_lineelo | your_vs_linefei | your_vs_linefpi |
| ------------------- | --------------- | ------------------ | --------------- | --------------- | --------------- |
| -1.4400000000000002 | -2.0            | -5.630000000000001 | 1.149692199     | -2.94           |                 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-19 — Memphis @ NC State (Gasparilla Bowl)
- Neutral: `True` | Tier: `C` | Reasons: `AGREE=0.75`
- DK (home spread): `-4.50` | Your (home spread): `-2.87` | Edge: `1.63`
- Consensus: mean `-2.39` median `-2.80` std `3.91` z `-0.12`
- Agreement (panel): `0.75` | Disagree: `linesag_home_spread`
- Market: open `-5.50` current `-4.50` move `1.00` CLV `TOWARD_YOU`
- Flags: `` | Robust edge: `0.42`

| lineopen | line | lineavg       | linemedian | linesag | linemassey | lineelo      | linefei | linefpi |
| -------- | ---- | ------------- | ---------- | ------- | ---------- | ------------ | ------- | ------- |
| -5.5     | -4.5 | -2.3896834356 | -2.8       | -6.02   | 0.02       | -4.278950925 | -1.7    |         |

| your_vs_median       | your_vs_linesag    | your_vs_linemassey | your_vs_lineelo | your_vs_linefei     | your_vs_linefpi |
| -------------------- | ------------------ | ------------------ | --------------- | ------------------- | --------------- |
| -0.07000000000000028 | 3.1499999999999995 | -2.89              | 1.408950925     | -1.1700000000000002 |                 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-19 — Kennesaw State @ Western Michigan (Myrtle Beach Bowl)
- Neutral: `True` | Tier: `C` | Reasons: ``
- DK (home spread): `-3.50` | Your (home spread): `-2.69` | Edge: `0.81`
- Consensus: mean `nan` median `nan` std `nan` z `nan`
- Agreement (panel): ``
- Flags: `` | Robust edge: `810000.00`

| lineopen | line | lineavg | linemedian | linesag | linemassey | lineelo | linefei | linefpi |
| -------- | ---- | ------- | ---------- | ------- | ---------- | ------- | ------- | ------- |
|          |      |         |            |         |            |         |         |         |

| your_vs_median | your_vs_linesag | your_vs_linemassey | your_vs_lineelo | your_vs_linefei | your_vs_linefpi |
| -------------- | --------------- | ------------------ | --------------- | --------------- | --------------- |
|                |                 |                    |                 |                 |                 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-20 — Miami @ Texas A&M (CFP First Round)
- Neutral: `False` | Tier: `C` | Reasons: ``
- DK (home spread): `-3.50` | Your (home spread): `-3.22` | Edge: `0.28`
- Consensus: mean `nan` median `nan` std `nan` z `nan`
- Agreement (panel): ``
- Flags: `` | Robust edge: `280000.00`

| lineopen | line | lineavg | linemedian | linesag | linemassey | lineelo | linefei | linefpi |
| -------- | ---- | ------- | ---------- | ------- | ---------- | ------- | ------- | ------- |
|          |      |         |            |         |            |         |         |         |

| your_vs_median | your_vs_linesag | your_vs_linemassey | your_vs_lineelo | your_vs_linefei | your_vs_linefpi |
| -------------- | --------------- | ------------------ | --------------- | --------------- | --------------- |
|                |                 |                    |                 |                 |                 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-20 — Tulane @ Ole Miss (CFP First Round)
- Neutral: `False` | Tier: `A` | Reasons: ``
- DK (home spread): `-17.50` | Your (home spread): `-3.12` | Edge: `14.38`
- Consensus: mean `nan` median `nan` std `nan` z `nan`
- Agreement (panel): ``
- Flags: `` | Robust edge: `14380000.00`

| lineopen | line | lineavg | linemedian | linesag | linemassey | lineelo | linefei | linefpi |
| -------- | ---- | ------- | ---------- | ------- | ---------- | ------- | ------- | ------- |
|          |      |         |            |         |            |         |         |         |

| your_vs_median | your_vs_linesag | your_vs_linemassey | your_vs_lineelo | your_vs_linefei | your_vs_linefpi |
| -------------- | --------------- | ------------------ | --------------- | --------------- | --------------- |
|                |                 |                    |                 |                 |                 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-20 — James Madison @ Oregon (CFP First Round)
- Neutral: `False` | Tier: `X-REVIEW` | Reasons: `OUTLIER_Z=2.67|HIGH_STD=5.62|AGREE=0.50`
- DK (home spread): `-21.00` | Your (home spread): `-3.63` | Edge: `17.37`
- Consensus: mean `-18.62` median `-20.08` std `5.62` z `2.67`
- Agreement (panel): `0.50` | Disagree: `linemassey_home_spread, linefei_home_spread`
- Market: open `-21.00` current `-21.50` move `-0.50` CLV `AWAY_FROM_YOU`
- Flags: `OUTLIER|HIGH_STD` | Robust edge: `3.09`

| lineopen | line  | lineavg       | linemedian | linesag | linemassey | lineelo       | linefei | linefpi |
| -------- | ----- | ------------- | ---------- | ------- | ---------- | ------------- | ------- | ------- |
| -21.0    | -21.5 | -18.620270119 | -20.08     | -18.39  | -24.66     | -16.306133845 | -25.6   |         |

| your_vs_median | your_vs_linesag    | your_vs_linemassey | your_vs_lineelo    | your_vs_linefei    | your_vs_linefpi |
| -------------- | ------------------ | ------------------ | ------------------ | ------------------ | --------------- |
| 16.45          | 14.760000000000002 | 21.03              | 12.676133845000003 | 21.970000000000002 |                 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-22 — Washington State @ Utah State (Potato Bowl)
- Neutral: `True` | Tier: `X-REVIEW` | Reasons: `SIGN_CONFLICT|OUTLIER_Z=-2.26|BIG_MOVE=-3.50|AGREE=0.00`
- DK (home spread): `-2.50` | Your (home spread): `-2.71` | Edge: `-0.21`
- Consensus: mean `4.26` median `4.99` std `3.08` z `-2.26`
- Agreement (panel): `0.00` | Disagree: `linesag_home_spread, linemassey_home_spread, lineelo_home_spread`
- Market: open `1.00` current `-2.50` move `-3.50` CLV `TOWARD_YOU`
- Flags: `OUTLIER|BIG_MOVE|SIGN_CONFLICT` | Robust edge: `0.07`

| lineopen | line | lineavg     | linemedian  | linesag | linemassey | lineelo     | linefei | linefpi |
| -------- | ---- | ----------- | ----------- | ------- | ---------- | ----------- | ------- | ------- |
| 1.0      | -2.5 | 4.262443163 | 4.990707109 | 5.77    | 7.56       | 4.743666999 |         |         |

| your_vs_median | your_vs_linesag | your_vs_linemassey | your_vs_lineelo | your_vs_linefei | your_vs_linefpi |
| -------------- | --------------- | ------------------ | --------------- | --------------- | --------------- |
| -7.700707109   | -8.48           | -10.27             | -7.453666999    |                 |                 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-23 — Toledo @ Louisville (Boca Raton Bowl)
- Neutral: `True` | Tier: `B` | Reasons: `AGREE=0.33`
- DK (home spread): `-6.50` | Your (home spread): `-3.28` | Edge: `3.22`
- Consensus: mean `-5.98` median `-6.00` std `3.56` z `0.76`
- Agreement (panel): `0.33` | Disagree: `linesag_home_spread, linemassey_home_spread`
- Market: open `-9.50` current `-7.00` move `2.50` CLV `TOWARD_YOU`
- Flags: `` | Robust edge: `0.90`

| lineopen | line | lineavg       | linemedian | linesag | linemassey | lineelo      | linefei | linefpi |
| -------- | ---- | ------------- | ---------- | ------- | ---------- | ------------ | ------- | ------- |
| -9.5     | -7.0 | -5.9781326148 | -5.995     | -8.02   | -12.87     | -2.712957008 |         |         |

| your_vs_median     | your_vs_linesag | your_vs_linemassey | your_vs_lineelo     | your_vs_linefei | your_vs_linefpi |
| ------------------ | --------------- | ------------------ | ------------------- | --------------- | --------------- |
| 2.7150000000000003 | 4.74            | 9.59               | -0.5670429919999997 |                 |                 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-23 — UNLV @ Ohio (Frisco Bowl)
- Neutral: `True` | Tier: `X-REVIEW` | Reasons: `OUTLIER_Z=-2.86|AGREE=1.00`
- DK (home spread): `5.50` | Your (home spread): `-2.92` | Edge: `-8.42`
- Consensus: mean `4.92` median `5.17` std `2.74` z `-2.86`
- Agreement (panel): `1.00`
- Market: open `4.00` current `5.00` move `1.00` CLV `AWAY_FROM_YOU`
- Flags: `OUTLIER` | Robust edge: `3.07`

| lineopen | line | lineavg     | linemedian | linesag | linemassey | lineelo     | linefei | linefpi |
| -------- | ---- | ----------- | ---------- | ------- | ---------- | ----------- | ------- | ------- |
| 4.0      | 5.0  | 4.917149225 | 5.165      | 5.04    | 4.59       | 5.009477106 |         |         |

| your_vs_median | your_vs_linesag | your_vs_linemassey | your_vs_lineelo | your_vs_linefei | your_vs_linefpi |
| -------------- | --------------- | ------------------ | --------------- | --------------- | --------------- |
| -8.085         | -7.96           | -7.51              | -7.929477106    |                 |                 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-23 — Western Kentucky @ Southern Miss (New Orleans Bowl)
- Neutral: `True` | Tier: `B` | Reasons: `AGREE=0.33`
- DK (home spread): `4.50` | Your (home spread): `-2.85` | Edge: `-7.35`
- Consensus: mean `3.15` median `3.08` std `3.15` z `-1.91`
- Agreement (panel): `0.33` | Disagree: `linemassey_home_spread, lineelo_home_spread`
- Market: open `3.00` current `4.00` move `1.00` CLV `AWAY_FROM_YOU`
- Flags: `` | Robust edge: `2.33`

| lineopen | line | lineavg     | linemedian | linesag | linemassey | lineelo     | linefei | linefpi |
| -------- | ---- | ----------- | ---------- | ------- | ---------- | ----------- | ------- | ------- |
| 3.0      | 4.0  | 3.151152904 | 3.075      | 2.47    | 8.31       | 4.979566329 |         |         |

| your_vs_median     | your_vs_linesag | your_vs_linemassey | your_vs_lineelo | your_vs_linefei | your_vs_linefpi |
| ------------------ | --------------- | ------------------ | --------------- | --------------- | --------------- |
| -5.925000000000001 | -5.32           | -11.16             | -7.829566329    |                 |                 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-24 — California @ Hawai'i (Hawai'i Bowl)
- Neutral: `False` | Tier: `A` | Reasons: `AGREE=0.67`
- DK (home spread): `1.50` | Your (home spread): `-2.59` | Edge: `-4.09`
- Consensus: mean `0.40` median `0.22` std `3.00` z `-1.00`
- Agreement (panel): `0.67` | Disagree: `linemassey_home_spread`
- Market: open `2.50` current `1.50` move `-1.00` CLV `TOWARD_YOU`
- Flags: `` | Robust edge: `1.36`

| lineopen | line | lineavg     | linemedian | linesag | linemassey | lineelo      | linefei | linefpi |
| -------- | ---- | ----------- | ---------- | ------- | ---------- | ------------ | ------- | ------- |
| 2.5      | 1.5  | 0.396512001 | 0.221      | -0.05   | 5.54       | -2.599491893 |         |         |

| your_vs_median | your_vs_linesag | your_vs_linemassey | your_vs_lineelo      | your_vs_linefei | your_vs_linefpi |
| -------------- | --------------- | ------------------ | -------------------- | --------------- | --------------- |
| -2.811         | -2.54           | -8.129999999999999 | 0.009491893000000307 |                 |                 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-26 — Florida International @ UTSA (First Responder Bowl)
- Neutral: `True` | Tier: `B` | Reasons: `HIGH_STD=5.89|AGREE=0.33`
- DK (home spread): `-9.50` | Your (home spread): `-2.77` | Edge: `6.73`
- Consensus: mean `-9.96` median `-9.85` std `5.89` z `1.22`
- Agreement (panel): `0.33` | Disagree: `linesag_home_spread, linemassey_home_spread`
- Market: open `-8.50` current `-8.50` move `0.00` CLV `NEUTRAL`
- Flags: `HIGH_STD` | Robust edge: `1.14`

| lineopen | line | lineavg       | linemedian | linesag | linemassey | lineelo      | linefei | linefpi |
| -------- | ---- | ------------- | ---------- | ------- | ---------- | ------------ | ------- | ------- |
| -8.5     | -8.5 | -9.9575675047 | -9.85      | -10.37  | -14.22     | -5.571917626 |         |         |

| your_vs_median | your_vs_linesag | your_vs_linemassey | your_vs_lineelo    | your_vs_linefei | your_vs_linefpi |
| -------------- | --------------- | ------------------ | ------------------ | --------------- | --------------- |
| 7.08           | 7.6             | 11.450000000000001 | 2.8019176260000003 |                 |                 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-26 — Central Michigan @ Northwestern (GameAbove Sports Bowl)
- Neutral: `True` | Tier: `A` | Reasons: ``
- DK (home spread): `-10.50` | Your (home spread): `-2.69` | Edge: `7.81`
- Consensus: mean `nan` median `nan` std `nan` z `nan`
- Agreement (panel): ``
- Flags: `` | Robust edge: `7810000.00`

| lineopen | line | lineavg | linemedian | linesag | linemassey | lineelo | linefei | linefpi |
| -------- | ---- | ------- | ---------- | ------- | ---------- | ------- | ------- | ------- |
|          |      |         |            |         |            |         |         |         |

| your_vs_median | your_vs_linesag | your_vs_linemassey | your_vs_lineelo | your_vs_linefei | your_vs_linefpi |
| -------------- | --------------- | ------------------ | --------------- | --------------- | --------------- |
|                |                 |                    |                 |                 |                 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-26 — New Mexico @ Minnesota (Rate Bowl)
- Neutral: `True` | Tier: `C` | Reasons: `HIGH_STD=4.49|AGREE=0.67`
- DK (home spread): `-2.50` | Your (home spread): `-2.65` | Edge: `-0.15`
- Consensus: mean `-3.80` median `-2.58` std `4.49` z `0.26`
- Agreement (panel): `0.67` | Disagree: `lineelo_home_spread`
- Market: open `-3.00` current `-2.50` move `0.50` CLV `TOWARD_YOU`
- Flags: `HIGH_STD` | Robust edge: `0.03`

| lineopen | line | lineavg       | linemedian | linesag | linemassey | lineelo      | linefei | linefpi |
| -------- | ---- | ------------- | ---------- | ------- | ---------- | ------------ | ------- | ------- |
| -3.0     | -2.5 | -3.8032413368 | -2.582     | -8.44   | -11.41     | -0.608899505 |         |         |

| your_vs_median       | your_vs_linesag   | your_vs_linemassey | your_vs_lineelo | your_vs_linefei | your_vs_linefpi |
| -------------------- | ----------------- | ------------------ | --------------- | --------------- | --------------- |
| -0.06800000000000006 | 5.789999999999999 | 8.76               | -2.041100495    |                 |                 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-27 — Miami (OH) @ Fresno State (Arizona Bowl)
- Neutral: `True` | Tier: `C` | Reasons: ``
- DK (home spread): `-4.50` | Your (home spread): `-2.70` | Edge: `1.80`
- Consensus: mean `nan` median `nan` std `nan` z `nan`
- Agreement (panel): ``
- Flags: `` | Robust edge: `1800000.00`

| lineopen | line | lineavg | linemedian | linesag | linemassey | lineelo | linefei | linefpi |
| -------- | ---- | ------- | ---------- | ------- | ---------- | ------- | ------- | ------- |
|          |      |         |            |         |            |         |         |         |

| your_vs_median | your_vs_linesag | your_vs_linemassey | your_vs_lineelo | your_vs_linefei | your_vs_linefpi |
| -------------- | --------------- | ------------------ | --------------- | --------------- | --------------- |
|                |                 |                    |                 |                 |                 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-27 — UConn @ Army (Fenway Bowl)
- Neutral: `True` | Tier: `A` | Reasons: ``
- DK (home spread): `-8.50` | Your (home spread): `-2.82` | Edge: `5.68`
- Consensus: mean `nan` median `nan` std `nan` z `nan`
- Agreement (panel): ``
- Flags: `` | Robust edge: `5680000.00`

| lineopen | line | lineavg | linemedian | linesag | linemassey | lineelo | linefei | linefpi |
| -------- | ---- | ------- | ---------- | ------- | ---------- | ------- | ------- | ------- |
|          |      |         |            |         |            |         |         |         |

| your_vs_median | your_vs_linesag | your_vs_linemassey | your_vs_lineelo | your_vs_linefei | your_vs_linefpi |
| -------------- | --------------- | ------------------ | --------------- | --------------- | --------------- |
|                |                 |                    |                 |                 |                 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-27 — Virginia @ Missouri (Gator Bowl)
- Neutral: `True` | Tier: `B` | Reasons: `AGREE=0.33`
- DK (home spread): `-7.00` | Your (home spread): `-3.14` | Edge: `3.86`
- Consensus: mean `-5.55` median `-5.29` std `3.47` z `0.69`
- Agreement (panel): `0.33` | Disagree: `linemassey_home_spread, lineelo_home_spread`
- Market: open `-7.00` current `-6.50` move `0.50` CLV `TOWARD_YOU`
- Flags: `` | Robust edge: `1.11`

| lineopen | line | lineavg       | linemedian | linesag | linemassey | lineelo      | linefei | linefpi |
| -------- | ---- | ------------- | ---------- | ------- | ---------- | ------------ | ------- | ------- |
| -7.0     | -6.5 | -5.5508217241 | -5.2915    | -5.92   | -9.18      | -8.417849229 |         |         |

| your_vs_median | your_vs_linesag | your_vs_linemassey | your_vs_lineelo   | your_vs_linefei | your_vs_linefpi |
| -------------- | --------------- | ------------------ | ----------------- | --------------- | --------------- |
| 2.1515         | 2.78            | 6.039999999999999  | 5.277849228999999 |                 |                 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-27 — Pittsburgh @ East Carolina (Military Bowl)
- Neutral: `True` | Tier: `X-REVIEW` | Reasons: `OUTLIER_Z=-2.00|AGREE=0.67`
- DK (home spread): `8.50` | Your (home spread): `-3.06` | Edge: `-11.56`
- Consensus: mean `4.63` median `5.03` std `3.84` z `-2.00`
- Agreement (panel): `0.67` | Disagree: `linesag_home_spread`
- Market: open `6.00` current `7.00` move `1.00` CLV `AWAY_FROM_YOU`
- Flags: `OUTLIER` | Robust edge: `3.01`

| lineopen | line | lineavg     | linemedian  | linesag | linemassey | lineelo     | linefei | linefpi |
| -------- | ---- | ----------- | ----------- | ------- | ---------- | ----------- | ------- | ------- |
| 6.0      | 7.0  | 4.632879869 | 5.027318292 | 8.76    | 6.09       | 4.086359493 |         |         |

| your_vs_median | your_vs_linesag | your_vs_linemassey | your_vs_lineelo | your_vs_linefei | your_vs_linefpi |
| -------------- | --------------- | ------------------ | --------------- | --------------- | --------------- |
| -8.087318292   | -11.82          | -9.15              | -7.146359493    |                 |                 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-27 — North Texas @ San Diego State (New Mexico Bowl)
- Neutral: `True` | Tier: `A` | Reasons: ``
- DK (home spread): `3.00` | Your (home spread): `-3.20` | Edge: `-6.20`
- Consensus: mean `nan` median `nan` std `nan` z `nan`
- Agreement (panel): ``
- Flags: `` | Robust edge: `6200000.00`

| lineopen | line | lineavg | linemedian | linesag | linemassey | lineelo | linefei | linefpi |
| -------- | ---- | ------- | ---------- | ------- | ---------- | ------- | ------- | ------- |
|          |      |         |            |         |            |         |         |         |

| your_vs_median | your_vs_linesag | your_vs_linemassey | your_vs_lineelo | your_vs_linefei | your_vs_linefpi |
| -------------- | --------------- | ------------------ | --------------- | --------------- | --------------- |
|                |                 |                    |                 |                 |                 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-27 — Penn State @ Clemson (Pinstripe Bowl)
- Neutral: `True` | Tier: `X-REVIEW` | Reasons: `SIGN_CONFLICT|BIG_MOVE=-4.50|AGREE=1.00`
- DK (home spread): `-3.50` | Your (home spread): `-2.99` | Edge: `0.51`
- Consensus: mean `4.17` median `4.21` std `3.73` z `-1.92`
- Agreement (panel): `1.00`
- Market: open `1.00` current `-3.50` move `-4.50` CLV `TOWARD_YOU`
- Flags: `BIG_MOVE|SIGN_CONFLICT` | Robust edge: `0.14`

| lineopen | line | lineavg     | linemedian | linesag | linemassey | lineelo     | linefei | linefpi |
| -------- | ---- | ----------- | ---------- | ------- | ---------- | ----------- | ------- | ------- |
| 1.0      | -3.5 | 4.169582882 | 4.215      | 4.5     | 8.47       | 3.945146338 |         |         |

| your_vs_median | your_vs_linesag | your_vs_linemassey | your_vs_lineelo | your_vs_linefei | your_vs_linefpi |
| -------------- | --------------- | ------------------ | --------------- | --------------- | --------------- |
| -7.205         | -7.49           | -11.46             | -6.935146338    |                 |                 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-27 — Georgia Tech @ BYU (Pop-Tarts Bowl)
- Neutral: `True` | Tier: `X-REVIEW` | Reasons: `HIGH_STD=4.58|AGREE=0.00`
- DK (home spread): `-4.50` | Your (home spread): `-3.04` | Edge: `1.46`
- Consensus: mean `-8.40` median `-8.46` std `4.58` z `1.17`
- Agreement (panel): `0.00` | Disagree: `linesag_home_spread, linemassey_home_spread, lineelo_home_spread`
- Market: open `-2.50` current `-4.50` move `-2.00` CLV `AWAY_FROM_YOU`
- Flags: `HIGH_STD` | Robust edge: `0.32`

| lineopen | line | lineavg       | linemedian | linesag | linemassey | lineelo       | linefei | linefpi |
| -------- | ---- | ------------- | ---------- | ------- | ---------- | ------------- | ------- | ------- |
| -2.5     | -4.5 | -8.4003641538 | -8.46      | -4.57   | -8.89      | -15.041773596 |         |         |

| your_vs_median    | your_vs_linesag    | your_vs_linemassey | your_vs_lineelo | your_vs_linefei | your_vs_linefpi |
| ----------------- | ------------------ | ------------------ | --------------- | --------------- | --------------- |
| 5.420000000000001 | 1.5300000000000002 | 5.8500000000000005 | 12.001773596    |                 |                 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-27 — LSU @ Houston (Texas Bowl)
- Neutral: `True` | Tier: `X-REVIEW` | Reasons: `SIGN_CONFLICT|AGREE=1.00`
- DK (home spread): `-3.00` | Your (home spread): `-2.65` | Edge: `0.35`
- Consensus: mean `3.53` median `3.80` std `3.49` z `-1.77`
- Agreement (panel): `1.00`
- Market: open `-3.00` current `-3.00` move `0.00` CLV `NEUTRAL`
- Flags: `SIGN_CONFLICT` | Robust edge: `0.10`

| lineopen | line | lineavg    | linemedian  | linesag | linemassey | lineelo     | linefei | linefpi |
| -------- | ---- | ---------- | ----------- | ------- | ---------- | ----------- | ------- | ------- |
| -3.0     | -3.0 | 3.53078727 | 3.800317038 | 5.32    | 5.02       | 2.209484019 |         |         |

| your_vs_median | your_vs_linesag    | your_vs_linemassey | your_vs_lineelo | your_vs_linefei | your_vs_linefpi |
| -------------- | ------------------ | ------------------ | --------------- | --------------- | --------------- |
| -6.450317038   | -7.970000000000001 | -7.67              | -4.859484019    |                 |                 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-29 — Georgia Southern @ App State (Birmingham Bowl)
- Neutral: `True` | Tier: `A` | Reasons: `AGREE=1.00`
- DK (home spread): `7.00` | Your (home spread): `-2.38` | Edge: `-9.38`
- Consensus: mean `1.62` median `1.95` std `2.77` z `-1.44`
- Agreement (panel): `1.00`
- Market: open `2.00` current `4.50` move `2.50` CLV `AWAY_FROM_YOU`
- Flags: `` | Robust edge: `3.39`

| lineopen | line | lineavg     | linemedian | linesag | linemassey | lineelo     | linefei | linefpi |
| -------- | ---- | ----------- | ---------- | ------- | ---------- | ----------- | ------- | ------- |
| 2.0      | 4.5  | 1.617014225 | 1.95       | 3.06    | -0.83      | 2.744878853 | -3.8    |         |

| your_vs_median | your_vs_linesag     | your_vs_linemassey  | your_vs_lineelo | your_vs_linefei | your_vs_linefpi |
| -------------- | ------------------- | ------------------- | --------------- | --------------- | --------------- |
| -4.33          | -5.4399999999999995 | -1.5499999999999998 | -5.124878853    | 1.42            |                 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-30 — USC @ TCU (Alamo Bowl)
- Neutral: `True` | Tier: `X-REVIEW` | Reasons: `OUTLIER_Z=-3.11|AGREE=0.00`
- DK (home spread): `4.50` | Your (home spread): `-3.07` | Edge: `-7.57`
- Consensus: mean `7.86` median `7.95` std `3.51` z `-3.11`
- Agreement (panel): `0.00` | Disagree: `linesag_home_spread, linemassey_home_spread, lineelo_home_spread`
- Market: open `5.50` current `4.50` move `-1.00` CLV `TOWARD_YOU`
- Flags: `OUTLIER` | Robust edge: `2.15`

| lineopen | line | lineavg     | linemedian | linesag | linemassey | lineelo     | linefei | linefpi |
| -------- | ---- | ----------- | ---------- | ------- | ---------- | ----------- | ------- | ------- |
| 5.5      | 4.5  | 7.862746603 | 7.945      | 7.18    | 6.85       | 6.147686169 |         |         |

| your_vs_median | your_vs_linesag | your_vs_linemassey | your_vs_lineelo | your_vs_linefei | your_vs_linefpi |
| -------------- | --------------- | ------------------ | --------------- | --------------- | --------------- |
| -11.015        | -10.25          | -9.92              | -9.217686169    |                 |                 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-30 — Coastal Carolina @ Louisiana Tech (Independence Bowl)
- Neutral: `True` | Tier: `A` | Reasons: `HIGH_STD=4.99|AGREE=1.00`
- DK (home spread): `-8.50` | Your (home spread): `-2.57` | Edge: `5.93`
- Consensus: mean `-7.65` median `-7.49` std `4.99` z `1.02`
- Agreement (panel): `1.00`
- Market: open `-7.00` current `-9.00` move `-2.00` CLV `AWAY_FROM_YOU`
- Flags: `HIGH_STD` | Robust edge: `1.19`

| lineopen | line | lineavg       | linemedian | linesag | linemassey | lineelo      | linefei | linefpi |
| -------- | ---- | ------------- | ---------- | ------- | ---------- | ------------ | ------- | ------- |
| -7.0     | -9.0 | -7.6520938087 | -7.49      | -7.27   | -4.32      | -2.038003874 |         |         |

| your_vs_median | your_vs_linesag   | your_vs_linemassey | your_vs_lineelo     | your_vs_linefei | your_vs_linefpi |
| -------------- | ----------------- | ------------------ | ------------------- | --------------- | --------------- |
| 4.92           | 4.699999999999999 | 1.7500000000000004 | -0.5319961259999997 |                 |                 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-30 — Tennessee @ Illinois (Music City Bowl)
- Neutral: `True` | Tier: `X-REVIEW` | Reasons: `OUTLIER_Z=-2.24|BIG_MOVE=-4.00|AGREE=0.00`
- DK (home spread): `2.50` | Your (home spread): `-2.95` | Edge: `-5.45`
- Consensus: mean `3.68` median `3.62` std `2.95` z `-2.24`
- Agreement (panel): `0.00` | Disagree: `linesag_home_spread, linemassey_home_spread, lineelo_home_spread`
- Market: open `6.50` current `2.50` move `-4.00` CLV `TOWARD_YOU`
- Flags: `OUTLIER|BIG_MOVE` | Robust edge: `1.84`

| lineopen | line | lineavg     | linemedian  | linesag | linemassey | lineelo     | linefei | linefpi |
| -------- | ---- | ----------- | ----------- | ------- | ---------- | ----------- | ------- | ------- |
| 6.5      | 2.5  | 3.675062018 | 3.618783245 | 6.06    | 9.59       | 3.620166489 |         |         |

| your_vs_median      | your_vs_linesag | your_vs_linemassey | your_vs_lineelo | your_vs_linefei | your_vs_linefpi |
| ------------------- | --------------- | ------------------ | --------------- | --------------- | --------------- |
| -6.5687832450000005 | -9.01           | -12.54             | -6.570166489    |                 |                 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-31 — Michigan @ Texas (Citrus Bowl)
- Neutral: `True` | Tier: `X-REVIEW` | Reasons: `BIG_MOVE=-3.00|AGREE=1.00`
- DK (home spread): `-7.50` | Your (home spread): `-2.93` | Edge: `4.57`
- Consensus: mean `-2.74` median `-2.00` std `3.27` z `-0.06`
- Agreement (panel): `1.00`
- Market: open `-4.50` current `-7.50` move `-3.00` CLV `AWAY_FROM_YOU`
- Flags: `BIG_MOVE` | Robust edge: `1.40`

| lineopen | line | lineavg      | linemedian | linesag | linemassey | lineelo      | linefei | linefpi |
| -------- | ---- | ------------ | ---------- | ------- | ---------- | ------------ | ------- | ------- |
| -4.5     | -7.5 | -2.739256218 | -2.0       | -4.98   | -1.58      | -5.184891145 |         |         |

| your_vs_median      | your_vs_linesag    | your_vs_linemassey | your_vs_lineelo    | your_vs_linefei | your_vs_linefpi |
| ------------------- | ------------------ | ------------------ | ------------------ | --------------- | --------------- |
| -0.9300000000000002 | 2.0500000000000003 | -1.35              | 2.2548911449999998 |                 |                 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-31 — Nebraska @ Utah (Las Vegas Bowl)
- Neutral: `True` | Tier: `X-REVIEW` | Reasons: `OUTLIER_Z=2.18|HIGH_STD=5.31|AGREE=0.67`
- DK (home spread): `-16.50` | Your (home spread): `-3.11` | Edge: `13.39`
- Consensus: mean `-14.69` median `-15.24` std `5.31` z `2.18`
- Agreement (panel): `0.67` | Disagree: `lineelo_home_spread`
- Market: open `-14.00` current `-16.50` move `-2.50` CLV `AWAY_FROM_YOU`
- Flags: `OUTLIER|HIGH_STD` | Robust edge: `2.52`

| lineopen | line  | lineavg       | linemedian | linesag | linemassey | lineelo       | linefei | linefpi |
| -------- | ----- | ------------- | ---------- | ------- | ---------- | ------------- | ------- | ------- |
| -14.0    | -16.5 | -14.685939865 | -15.24     | -12.39  | -13.72     | -16.504754049 |         |         |

| your_vs_median | your_vs_linesag   | your_vs_linemassey | your_vs_lineelo | your_vs_linefei | your_vs_linefpi |
| -------------- | ----------------- | ------------------ | --------------- | --------------- | --------------- |
| 12.13          | 9.280000000000001 | 10.610000000000001 | 13.394754049    |                 |                 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-31 — Iowa @ Vanderbilt (ReliaQuest Bowl)
- Neutral: `True` | Tier: `C` | Reasons: `AGREE=1.00`
- DK (home spread): `-5.50` | Your (home spread): `-3.20` | Edge: `2.30`
- Consensus: mean `-2.22` median `-1.75` std `3.22` z `-0.30`
- Agreement (panel): `1.00`
- Market: open `-4.00` current `-5.00` move `-1.00` CLV `AWAY_FROM_YOU`
- Flags: `` | Robust edge: `0.71`

| lineopen | line | lineavg       | linemedian | linesag | linemassey | lineelo      | linefei | linefpi |
| -------- | ---- | ------------- | ---------- | ------- | ---------- | ------------ | ------- | ------- |
| -4.0     | -5.0 | -2.2248999549 | -1.7535    | -2.9    | 1.81       | -4.807557791 |         |         |

| your_vs_median      | your_vs_linesag      | your_vs_linemassey | your_vs_lineelo    | your_vs_linefei | your_vs_linefpi |
| ------------------- | -------------------- | ------------------ | ------------------ | --------------- | --------------- |
| -1.4465000000000001 | -0.30000000000000027 | -5.01              | 1.6075577909999996 |                 |                 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-31 — Arizona State @ Duke (Sun Bowl)
- Neutral: `True` | Tier: `C` | Reasons: ``
- DK (home spread): `-2.50` | Your (home spread): `-2.74` | Edge: `-0.24`
- Consensus: mean `nan` median `nan` std `nan` z `nan`
- Agreement (panel): ``
- Flags: `` | Robust edge: `240000.00`

| lineopen | line | lineavg | linemedian | linesag | linemassey | lineelo | linefei | linefpi |
| -------- | ---- | ------- | ---------- | ------- | ---------- | ------- | ------- | ------- |
|          |      |         |            |         |            |         |         |         |

| your_vs_median | your_vs_linesag | your_vs_linemassey | your_vs_lineelo | your_vs_linefei | your_vs_linefpi |
| -------------- | --------------- | ------------------ | --------------- | --------------- | --------------- |
|                |                 |                    |                 |                 |                 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2026-01-02 — Rice @ Texas State (Armed Forces Bowl)
- Neutral: `True` | Tier: `A` | Reasons: ``
- DK (home spread): `-10.50` | Your (home spread): `-2.57` | Edge: `7.93`
- Consensus: mean `nan` median `nan` std `nan` z `nan`
- Agreement (panel): ``
- Flags: `` | Robust edge: `7930000.00`

| lineopen | line | lineavg | linemedian | linesag | linemassey | lineelo | linefei | linefpi |
| -------- | ---- | ------- | ---------- | ------- | ---------- | ------- | ------- | ------- |
|          |      |         |            |         |            |         |         |         |

| your_vs_median | your_vs_linesag | your_vs_linemassey | your_vs_lineelo | your_vs_linefei | your_vs_linefpi |
| -------------- | --------------- | ------------------ | --------------- | --------------- | --------------- |
|                |                 |                    |                 |                 |                 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2026-01-02 — Wake Forest @ Mississippi State (Duke's Mayo Bowl)
- Neutral: `True` | Tier: `C` | Reasons: ``
- DK (home spread): `-4.00` | Your (home spread): `-2.76` | Edge: `1.24`
- Consensus: mean `nan` median `nan` std `nan` z `nan`
- Agreement (panel): ``
- Flags: `` | Robust edge: `1240000.00`

| lineopen | line | lineavg | linemedian | linesag | linemassey | lineelo | linefei | linefpi |
| -------- | ---- | ------- | ---------- | ------- | ---------- | ------- | ------- | ------- |
|          |      |         |            |         |            |         |         |         |

| your_vs_median | your_vs_linesag | your_vs_linemassey | your_vs_lineelo | your_vs_linefei | your_vs_linefpi |
| -------------- | --------------- | ------------------ | --------------- | --------------- | --------------- |
|                |                 |                    |                 |                 |                 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2026-01-02 — Arizona @ SMU (Holiday Bowl)
- Neutral: `True` | Tier: `A` | Reasons: `HIGH_STD=4.53|AGREE=0.67`
- DK (home spread): `3.00` | Your (home spread): `-3.18` | Edge: `-6.18`
- Consensus: mean `-0.20` median `-0.20` std `4.53` z `-0.66`
- Agreement (panel): `0.67` | Disagree: `lineelo_home_spread`
- Market: open `1.50` current `3.00` move `1.50` CLV `AWAY_FROM_YOU`
- Flags: `HIGH_STD` | Robust edge: `1.36`

| lineopen | line | lineavg       | linemedian | linesag | linemassey | lineelo    | linefei | linefpi |
| -------- | ---- | ------------- | ---------- | ------- | ---------- | ---------- | ------- | ------- |
| 1.5      | 3.0  | -0.1953130564 | -0.195     | -4.15   | -1.26      | 4.69327171 |         |         |

| your_vs_median      | your_vs_linesag    | your_vs_linemassey  | your_vs_lineelo    | your_vs_linefei | your_vs_linefpi |
| ------------------- | ------------------ | ------------------- | ------------------ | --------------- | --------------- |
| -2.9850000000000003 | 0.9700000000000002 | -1.9200000000000002 | -7.873271710000001 |                 |                 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2026-01-02 — Navy @ Cincinnati (Liberty Bowl)
- Neutral: `True` | Tier: `X-REVIEW` | Reasons: `SIGN_CONFLICT|BIG_MOVE=13.50|HIGH_STD=4.96|AGREE=1.00`
- DK (home spread): `6.50` | Your (home spread): `-2.98` | Edge: `-9.48`
- Consensus: mean `-3.18` median `-3.86` std `4.96` z `0.04`
- Agreement (panel): `1.00`
- Market: open `-6.50` current `7.00` move `13.50` CLV `AWAY_FROM_YOU`
- Flags: `BIG_MOVE|HIGH_STD|SIGN_CONFLICT` | Robust edge: `1.91`

| lineopen | line | lineavg       | linemedian | linesag | linemassey | lineelo      | linefei | linefpi |
| -------- | ---- | ------------- | ---------- | ------- | ---------- | ------------ | ------- | ------- |
| -6.5     | 7.0  | -3.1825234917 | -3.86      | -3.17   | -7.95      | -0.664203981 |         |         |

| your_vs_median     | your_vs_linesag     | your_vs_linemassey | your_vs_lineelo | your_vs_linefei | your_vs_linefpi |
| ------------------ | ------------------- | ------------------ | --------------- | --------------- | --------------- |
| 0.8799999999999999 | 0.18999999999999995 | 4.970000000000001  | -2.315796019    |                 |                 |

- Notes: _opt-outs / injuries / motivation / weather_
