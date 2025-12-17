# Bowl Betting Evaluation Guide

Generated: 2025-12-16T22:18:23

- Slate: `/Users/stephen_bowman/Documents/GitHub/Script_Ohio_2.0/predictions/draftkings_slate_2025/dk_slate_predictions_20251216_214645.csv`
- Systems: `/Users/stephen_bowman/Documents/GitHub/Script_Ohio_2.0/predictions/ncaapredictions.csv`

## Spread Orientation

- Canonical: `home_spread < 0` home favored; `home_spread > 0` home underdog
- Systems lines normalized to canonical home spreads via per-column polarity inference.

## Totals Warning

Totals model appears mis-scaled or mismatched (rf_total median=17.490000000000002, corr=-0.11256909290652314). Totals edges suppressed.

## Quick Board (sorted by date)

| date       | bowl                  | away_team             | home_team         | dk_home_spread | your_home_spread | edge_vs_dk | agreement_rate | clv_direction | robust_edge | flags                            | tier     | tier_reasons                                               | dk_total | rf_total | total_pick | total_edge | adv_stats_coverage | consensus_sources_home                | panel_count | open_home_spread | current_home_spread | consensus_mean_home | consensus_median_home | consensus_std | move_from_open | z_vs_consensus | agreement_n |
| ---------- | --------------------- | --------------------- | ----------------- | -------------- | ---------------- | ---------- | -------------- | ------------- | ----------- | -------------------------------- | -------- | ---------------------------------------------------------- | -------- | -------- | ---------- | ---------- | ------------------ | ------------------------------------- | ----------- | ---------------- | ------------------- | ------------------- | --------------------- | ------------- | -------------- | -------------- | ----------- |
| 2025-12-17 | 68 Ventures Bowl      | Louisiana             | Delaware          | 3.0            | -2.48            | -5.48      | 0.25           | TOWARD_YOU    | 2.31        | OUTLIER                          | X-REVIEW | OUTLIER_Z=-3.18\|AGREE=0.25                                | 61.5     |          |            |            | 1.0                | linesag\|linemassey\|lineelo\|linehow | 4           | 3.5              | 3.0                 | 5.06                | 5.04                  | 2.37          | -0.5           | -3.18          | 4           |
| 2025-12-17 | Cure Bowl             | Old Dominion          | South Florida     | -2.5           | -3.4             | -0.9       | 1.0            | TOWARD_YOU    | 0.39        | BIG_MOVE                         | X-REVIEW | BIG_MOVE=4.50\|AGREE=1.00                                  | 52.5     |          |            |            | 1.0                | linesag\|linemassey\|lineelo\|linehow | 4           | -7.5             | -3.0                | -7.35               | -8.35                 | 2.33          | 4.5            | 1.7            | 4           |
| 2025-12-18 | Xbox Bowl             | Missouri State        | Arkansas State    | -1.5           | -2.34            | -0.84      |                |               |             |                                  | C        |                                                            | 54.5     |          |            |            | 1.0                | linesag\|linemassey\|lineelo\|linehow | 0           |                  |                     |                     |                       |               |                |                | 0           |
| 2025-12-19 | CFP First Round       | Alabama               | Oklahoma          | 1.5            | -3.14            | -4.64      | 0.75           | TOWARD_YOU    | 1.63        |                                  | A        | AGREE=0.75                                                 | 40.5     |          |            |            | 1.0                | linesag\|linemassey\|lineelo\|linehow | 4           | 2.0              | 1.0                 | -1.86               | -2.71                 | 2.84          | -1.0           | -0.45          | 4           |
| 2025-12-19 | Gasparilla Bowl       | Memphis               | NC State          | -4.5           | -2.87            | 1.63       | 0.75           | TOWARD_YOU    | 0.53        |                                  | C        | AGREE=0.75                                                 | 58.5     |          |            |            | 1.0                | linesag\|linemassey\|lineelo\|linehow | 4           | -5.5             | -4.5                | -2.19               | -2.13                 | 3.06          | 1.0            | -0.22          | 4           |
| 2025-12-19 | Myrtle Beach Bowl     | Kennesaw State        | Western Michigan  | -3.5           | -2.69            | 0.81       |                |               |             |                                  | C        |                                                            | 48.5     |          |            |            | 1.0                | linesag\|linemassey\|lineelo\|linehow | 0           |                  |                     |                     |                       |               |                |                | 0           |
| 2025-12-20 | CFP First Round       | Miami                 | Texas A&M         | -3.5           | -3.22            | 0.28       |                |               |             |                                  | C        |                                                            | 50.5     |          |            |            | 1.0                | linesag\|linemassey\|lineelo\|linehow | 0           |                  |                     |                     |                       |               |                |                | 0           |
| 2025-12-20 | CFP First Round       | Tulane                | Ole Miss          | -17.5          | -3.12            | 14.38      |                |               |             |                                  | A        |                                                            | 56.5     |          |            |            | 1.0                | linesag\|linemassey\|lineelo\|linehow | 0           |                  |                     |                     |                       |               |                |                | 0           |
| 2025-12-20 | CFP First Round       | James Madison         | Oregon            | -21.0          | -3.63            | 17.37      | 0.75           | AWAY_FROM_YOU | 3.43        | OUTLIER\|HIGH_STD                | X-REVIEW | OUTLIER_Z=2.73\|HIGH_STD=5.06\|AGREE=0.75                  | 47.5     |          |            |            | 1.0                | linesag\|linemassey\|lineelo\|linehow | 4           | -21.0            | -21.5               | -17.46              | -17.35                | 5.06          | -0.5           | 2.73           | 4           |
| 2025-12-22 | Potato Bowl           | Washington State      | Utah State        | -2.5           | -2.71            | -0.21      | 0.0            | TOWARD_YOU    | 0.11        | OUTLIER\|BIG_MOVE\|SIGN_CONFLICT | X-REVIEW | SIGN_CONFLICT\|OUTLIER_Z=-4.29\|BIG_MOVE=-3.50\|AGREE=0.00 | 50.5     |          |            |            | 1.0                | linesag\|linemassey\|lineelo\|linehow | 4           | 1.0              | -2.5                | 5.14                | 5.26                  | 1.83          | -3.5           | -4.29          | 4           |
| 2025-12-23 | Boca Raton Bowl       | Toledo                | Louisville        | -6.5           | -3.28            | 3.22       | 0.5            | TOWARD_YOU    | 0.77        | HIGH_STD                         | B        | HIGH_STD=4.16\|AGREE=0.50                                  | 45.5     |          |            |            | 1.0                | linesag\|linemassey\|lineelo\|linehow | 4           | -9.5             | -7.0                | -6.65               | -5.51                 | 4.16          | 2.5            | 0.81           | 4           |
| 2025-12-23 | Frisco Bowl           | UNLV                  | Ohio              | 5.5            | -2.92            | -8.42      | 0.75           | AWAY_FROM_YOU | 11.63       | OUTLIER                          | X-REVIEW | OUTLIER_Z=-11.34\|AGREE=0.75                               | 65.5     |          |            |            | 1.0                | linesag\|linemassey\|lineelo\|linehow | 4           | 4.0              | 5.0                 | 5.28                | 5.02                  | 0.72          | 1.0            | -11.34         | 4           |
| 2025-12-23 | New Orleans Bowl      | Western Kentucky      | Southern Miss     | 4.5            | -2.85            | -7.35      | 0.5            | AWAY_FROM_YOU | 3.43        | OUTLIER                          | X-REVIEW | OUTLIER_Z=-3.64\|AGREE=0.50                                | 57.5     |          |            |            | 1.0                | linesag\|linemassey\|lineelo\|linehow | 4           | 3.0              | 4.0                 | 4.94                | 4.49                  | 2.14          | 1.0            | -3.64          | 4           |
| 2025-12-24 | Hawai'i Bowl          | California            | Hawai'i           | 1.5            | -2.59            | -4.09      | 0.75           | TOWARD_YOU    | 1.01        | HIGH_STD                         | A        | HIGH_STD=4.06\|AGREE=0.75                                  | 54.5     |          |            |            | 1.0                | linesag\|linemassey\|lineelo\|linehow | 4           | 2.5              | 1.5                 | -0.65               | -1.32                 | 4.06          | -1.0           | -0.48          | 4           |
| 2025-12-26 | First Responder Bowl  | Florida International | UTSA              | -9.5           | -2.77            | 6.73       | 0.5            | NEUTRAL       | 1.56        | HIGH_STD                         | A        | HIGH_STD=4.33\|AGREE=0.50                                  | 59.5     |          |            |            | 1.0                | linesag\|linemassey\|lineelo\|linehow | 4           | -8.5             | -8.5                | -8.29               | -7.97                 | 4.33          | 0.0            | 1.28           | 4           |
| 2025-12-26 | GameAbove Sports Bowl | Central Michigan      | Northwestern      | -10.5          | -2.69            | 7.81       |                |               |             |                                  | A        |                                                            | 43.5     |          |            |            | 1.0                | linesag\|linemassey\|lineelo\|linehow | 0           |                  |                     |                     |                       |               |                |                | 0           |
| 2025-12-26 | Rate Bowl             | New Mexico            | Minnesota         | -2.5           | -2.65            | -0.15      | 0.5            | TOWARD_YOU    | 0.02        | HIGH_STD                         | C        | HIGH_STD=6.29\|AGREE=0.50                                  | 45.5     |          |            |            | 1.0                | linesag\|linemassey\|lineelo\|linehow | 4           | -3.0             | -2.5                | -3.99               | -4.52                 | 6.29          | 0.5            | 0.21           | 4           |
| 2025-12-27 | Arizona Bowl          | Miami (OH)            | Fresno State      | -4.5           | -2.7             | 1.8        |                |               |             |                                  | C        |                                                            | 42.5     |          |            |            | 1.0                | linesag\|linemassey\|lineelo\|linehow | 0           |                  |                     |                     |                       |               |                |                | 0           |
| 2025-12-27 | Fenway Bowl           | UConn                 | Army              | -8.5           | -2.82            | 5.68       |                |               |             |                                  | A        |                                                            | 44.5     |          |            |            | 1.0                | linesag\|linemassey\|lineelo\|linehow | 0           |                  |                     |                     |                       |               |                |                | 0           |
| 2025-12-27 | Gator Bowl            | Virginia              | Missouri          | -7.0           | -3.14            | 3.86       | 0.5            | TOWARD_YOU    | 0.8         | HIGH_STD                         | B        | HIGH_STD=4.85\|AGREE=0.50                                  | 47.5     |          |            |            | 1.0                | linesag\|linemassey\|lineelo\|linehow | 4           | -7.0             | -6.5                | -5.13               | -7.17                 | 4.85          | 0.5            | 0.41           | 4           |
| 2025-12-27 | Military Bowl         | Pittsburgh            | East Carolina     | 8.5            | -3.06            | -11.56     | 0.75           | AWAY_FROM_YOU | 3.84        | OUTLIER                          | X-REVIEW | OUTLIER_Z=-2.63\|AGREE=0.75                                | 57.5     |          |            |            | 1.0                | linesag\|linemassey\|lineelo\|linehow | 4           | 6.0              | 7.0                 | 4.86                | 5.09                  | 3.01          | 1.0            | -2.63          | 4           |
| 2025-12-27 | New Mexico Bowl       | North Texas           | San Diego State   | 3.0            | -3.2             | -6.2       |                |               |             |                                  | A        |                                                            | 54.5     |          |            |            | 1.0                | linesag\|linemassey\|lineelo\|linehow | 0           |                  |                     |                     |                       |               |                |                | 0           |
| 2025-12-27 | Pinstripe Bowl        | Penn State            | Clemson           | -3.5           | -2.99            | 0.51       | 1.0            | TOWARD_YOU    | 0.24        | OUTLIER\|BIG_MOVE\|SIGN_CONFLICT | X-REVIEW | SIGN_CONFLICT\|OUTLIER_Z=-3.82\|BIG_MOVE=-4.50\|AGREE=1.00 | 48.5     |          |            |            | 1.0                | linesag\|linemassey\|lineelo\|linehow | 4           | 1.0              | -3.5                | 4.98                | 4.22                  | 2.09          | -4.5           | -3.82          | 4           |
| 2025-12-27 | Pop-Tarts Bowl        | Georgia Tech          | BYU               | -4.5           | -3.04            | 1.46       | 0.0            | AWAY_FROM_YOU | 0.38        |                                  | X-REVIEW | AGREE=0.00                                                 | 56.5     |          |            |            | 1.0                | linesag\|linemassey\|lineelo\|linehow | 4           | -2.5             | -4.5                | -10.13              | -10.44                | 3.88          | -2.0           | 1.83           | 4           |
| 2025-12-27 | Texas Bowl            | LSU                   | Houston           | -3.0           | -2.65            | 0.35       | 1.0            | NEUTRAL       | 0.1         | SIGN_CONFLICT                    | X-REVIEW | SIGN_CONFLICT\|AGREE=1.00                                  | 41.5     |          |            |            | 1.0                | linesag\|linemassey\|lineelo\|linehow | 4           | -3.0             | -3.0                | 2.39                | 3.61                  | 3.34          | 0.0            | -1.51          | 3           |
| 2025-12-29 | Birmingham Bowl       | Georgia Southern      | App State         | 7.0            | -2.38            | -9.38      | 1.0            | AWAY_FROM_YOU | 4.15        | OUTLIER                          | X-REVIEW | OUTLIER_Z=-2.21\|AGREE=1.00                                | 59.5     |          |            |            | 1.0                | linesag\|linemassey\|lineelo\|linehow | 4           | 2.0              | 4.5                 | 2.62                | 2.9                   | 2.26          | 2.5            | -2.21          | 4           |
| 2025-12-30 | Alamo Bowl            | USC                   | TCU               | 4.5            | -3.07            | -7.57      | 0.0            | TOWARD_YOU    | 7.19        | OUTLIER                          | X-REVIEW | OUTLIER_Z=-9.84\|AGREE=0.00                                | 57.5     |          |            |            | 1.0                | linesag\|linemassey\|lineelo\|linehow | 4           | 5.5              | 4.5                 | 7.29                | 7.02                  | 1.05          | -1.0           | -9.84          | 4           |
| 2025-12-30 | Independence Bowl     | Coastal Carolina      | Louisiana Tech    | -8.5           | -2.57            | 5.93       | 1.0            | AWAY_FROM_YOU | 3.18        |                                  | A        | AGREE=1.00                                                 | 50.5     |          |            |            | 1.0                | linesag\|linemassey\|lineelo\|linehow | 4           | -7.0             | -9.0                | -4.66               | -4.66                 | 1.87          | -2.0           | 1.12           | 4           |
| 2025-12-30 | Music City Bowl       | Tennessee             | Illinois          | 2.5            | -2.95            | -5.45      | 0.25           | TOWARD_YOU    | 1.48        | OUTLIER\|BIG_MOVE                | X-REVIEW | OUTLIER_Z=-2.08\|BIG_MOVE=-4.00\|AGREE=0.25                | 61.5     |          |            |            | 1.0                | linesag\|linemassey\|lineelo\|linehow | 4           | 6.5              | 2.5                 | 4.69                | 4.84                  | 3.67          | -4.0           | -2.08          | 4           |
| 2025-12-31 | Citrus Bowl           | Michigan              | Texas             | -7.5           | -2.93            | 4.57       | 1.0            | AWAY_FROM_YOU | 2.39        | BIG_MOVE                         | X-REVIEW | BIG_MOVE=-3.00\|AGREE=1.00                                 | 46.5     |          |            |            | 1.0                | linesag\|linemassey\|lineelo\|linehow | 4           | -4.5             | -7.5                | -3.19               | -3.28                 | 1.91          | -3.0           | 0.13           | 4           |
| 2025-12-31 | Las Vegas Bowl        | Nebraska              | Utah              | -16.5          | -3.11            | 13.39      | 0.75           | AWAY_FROM_YOU | 8.44        | OUTLIER                          | X-REVIEW | OUTLIER_Z=7.19\|AGREE=0.75                                 | 50.5     |          |            |            | 1.0                | linesag\|linemassey\|lineelo\|linehow | 4           | -14.0            | -16.5               | -14.53              | -14.61                | 1.59          | -2.5           | 7.19           | 4           |
| 2025-12-31 | ReliaQuest Bowl       | Iowa                  | Vanderbilt        | -5.5           | -3.2             | 2.3        | 1.0            | AWAY_FROM_YOU | 0.9         |                                  | C        | AGREE=1.00                                                 | 47.5     |          |            |            | 1.0                | linesag\|linemassey\|lineelo\|linehow | 4           | -4.0             | -5.0                | -2.47               | -3.45                 | 2.56          | -1.0           | -0.28          | 4           |
| 2025-12-31 | Sun Bowl              | Arizona State         | Duke              | -2.5           | -2.74            | -0.24      |                |               |             |                                  | C        |                                                            | 49.5     |          |            |            | 1.0                | linesag\|linemassey\|lineelo\|linehow | 0           |                  |                     |                     |                       |               |                |                | 0           |
| 2026-01-02 | Armed Forces Bowl     | Rice                  | Texas State       | -10.5          | -2.57            | 7.93       |                |               |             |                                  | A        |                                                            | 59.5     |          |            |            | 1.0                | linesag\|linemassey\|lineelo\|linehow | 0           |                  |                     |                     |                       |               |                |                | 0           |
| 2026-01-02 | Duke's Mayo Bowl      | Wake Forest           | Mississippi State | -4.0           | -2.76            | 1.24       |                |               |             |                                  | C        |                                                            | 56.5     |          |            |            | 1.0                | linesag\|linemassey\|lineelo\|linehow | 0           |                  |                     |                     |                       |               |                |                | 0           |
| 2026-01-02 | Holiday Bowl          | Arizona               | SMU               | 3.0            | -3.18            | -6.18      | 0.5            | AWAY_FROM_YOU | 1.73        |                                  | A        | AGREE=0.50                                                 | 51.5     |          |            |            | 1.0                | linesag\|linemassey\|lineelo\|linehow | 4           | 1.5              | 3.0                 | 0.7                 | 1.12                  | 3.58          | 1.5            | -1.08          | 4           |
| 2026-01-02 | Liberty Bowl          | Navy                  | Cincinnati        | 6.5            | -2.98            | -9.48      | 0.75           |               | 1.75        | MOVE_DATA_ISSUE\|HIGH_STD        | X-REVIEW | MOVE_DATA_ISSUE\|HIGH_STD=5.41\|AGREE=0.75                 | 53.5     |          |            |            | 1.0                | linesag\|linemassey\|lineelo\|linehow | 4           | -6.5             | 7.0                 | -1.2                | -1.92                 | 5.41          |                | -0.33          | 4           |

## Audit / Review Queue

| date       | bowl             | away_team        | home_team     | dk_home_spread | your_home_spread | edge_vs_dk           | current_home_spread | move_from_open | z_vs_consensus       | agreement_rate | flags                            | tier     | tier_reasons                                               |
| ---------- | ---------------- | ---------------- | ------------- | -------------- | ---------------- | -------------------- | ------------------- | -------------- | -------------------- | -------------- | -------------------------------- | -------- | ---------------------------------------------------------- |
| 2025-12-23 | Frisco Bowl      | UNLV             | Ohio          | 5.5            | -2.92            | -8.42                | 5.0                 | 1.0            | -11.336792136376072  | 0.75           | OUTLIER                          | X-REVIEW | OUTLIER_Z=-11.34\|AGREE=0.75                               |
| 2025-12-30 | Alamo Bowl       | USC              | TCU           | 4.5            | -3.07            | -7.57                | 4.5                 | -1.0           | -9.843458304280201   | 0.0            | OUTLIER                          | X-REVIEW | OUTLIER_Z=-9.84\|AGREE=0.00                                |
| 2025-12-31 | Las Vegas Bowl   | Nebraska         | Utah          | -16.5          | -3.11            | 13.39                | -16.5               | -2.5           | 7.194437205917528    | 0.75           | OUTLIER                          | X-REVIEW | OUTLIER_Z=7.19\|AGREE=0.75                                 |
| 2025-12-22 | Potato Bowl      | Washington State | Utah State    | -2.5           | -2.71            | -0.20999999999999996 | -2.5                | -3.5           | -4.293996323043608   | 0.0            | OUTLIER\|BIG_MOVE\|SIGN_CONFLICT | X-REVIEW | SIGN_CONFLICT\|OUTLIER_Z=-4.29\|BIG_MOVE=-3.50\|AGREE=0.00 |
| 2025-12-27 | Pinstripe Bowl   | Penn State       | Clemson       | -3.5           | -2.99            | 0.5099999999999998   | -3.5                | -4.5           | -3.8205413357603932  | 1.0            | OUTLIER\|BIG_MOVE\|SIGN_CONFLICT | X-REVIEW | SIGN_CONFLICT\|OUTLIER_Z=-3.82\|BIG_MOVE=-4.50\|AGREE=1.00 |
| 2025-12-23 | New Orleans Bowl | Western Kentucky | Southern Miss | 4.5            | -2.85            | -7.35                | 4.0                 | 1.0            | -3.6376979471364628  | 0.5            | OUTLIER                          | X-REVIEW | OUTLIER_Z=-3.64\|AGREE=0.50                                |
| 2025-12-17 | 68 Ventures Bowl | Louisiana        | Delaware      | 3.0            | -2.48            | -5.48                | 3.0                 | -0.5           | -3.178084579493614   | 0.25           | OUTLIER                          | X-REVIEW | OUTLIER_Z=-3.18\|AGREE=0.25                                |
| 2025-12-20 | CFP First Round  | James Madison    | Oregon        | -21.0          | -3.63            | 17.37                | -21.5               | -0.5           | 2.7331522941638564   | 0.75           | OUTLIER\|HIGH_STD                | X-REVIEW | OUTLIER_Z=2.73\|HIGH_STD=5.06\|AGREE=0.75                  |
| 2025-12-27 | Military Bowl    | Pittsburgh       | East Carolina | 8.5            | -3.06            | -11.56               | 7.0                 | 1.0            | -2.6276438089833114  | 0.75           | OUTLIER                          | X-REVIEW | OUTLIER_Z=-2.63\|AGREE=0.75                                |
| 2025-12-29 | Birmingham Bowl  | Georgia Southern | App State     | 7.0            | -2.38            | -9.379999999999999   | 4.5                 | 2.5            | -2.213140073472609   | 1.0            | OUTLIER                          | X-REVIEW | OUTLIER_Z=-2.21\|AGREE=1.00                                |
| 2025-12-30 | Music City Bowl  | Tennessee        | Illinois      | 2.5            | -2.95            | -5.45                | 2.5                 | -4.0           | -2.08066224251327    | 0.25           | OUTLIER\|BIG_MOVE                | X-REVIEW | OUTLIER_Z=-2.08\|BIG_MOVE=-4.00\|AGREE=0.25                |
| 2025-12-17 | Cure Bowl        | Old Dominion     | South Florida | -2.5           | -3.4             | -0.8999999999999999  | -3.0                | 4.5            | 1.696194948311976    | 1.0            | BIG_MOVE                         | X-REVIEW | BIG_MOVE=4.50\|AGREE=1.00                                  |
| 2025-12-27 | Texas Bowl       | LSU              | Houston       | -3.0           | -2.65            | 0.3500000000000001   | -3.0                | 0.0            | -1.5088026752729706  | 1.0            | SIGN_CONFLICT                    | X-REVIEW | SIGN_CONFLICT\|AGREE=1.00                                  |
| 2026-01-02 | Liberty Bowl     | Navy             | Cincinnati    | 6.5            | -2.98            | -9.48                | 7.0                 |                | -0.32989399934106284 | 0.75           | MOVE_DATA_ISSUE\|HIGH_STD        | X-REVIEW | MOVE_DATA_ISSUE\|HIGH_STD=5.41\|AGREE=0.75                 |
| 2025-12-31 | Citrus Bowl      | Michigan         | Texas         | -7.5           | -2.93            | 4.57                 | -7.5                | -3.0           | 0.1342426891649304   | 1.0            | BIG_MOVE                         | X-REVIEW | BIG_MOVE=-3.00\|AGREE=1.00                                 |

## Tier Summary

| X-REVIEW | A  | C | B |
| -------- | -- | - | - |
| 16       | 10 | 9 | 2 |

## Game-By-Game Notes

### 2025-12-17 — Louisiana @ Delaware (68 Ventures Bowl)
- Neutral: `True` | Tier: `X-REVIEW` | Reasons: `OUTLIER_Z=-3.18|AGREE=0.25`
- DK (home spread): `3.00` | Your (home spread): `-2.48` | Edge: `-5.48`
- Consensus: mean `5.06` median `5.04` std `2.37` z `-3.18`
- Agreement (panel): `0.25` | Disagree: `linesag, linemassey, lineelo`
- Market: open `3.50` current `3.00` move `-0.50` CLV `TOWARD_YOU`
- Flags: `OUTLIER` | Robust edge: `2.31`

| lineopen | line | lineavg     | linemedian | linesag | linemassey | lineelo     | linehow |
| -------- | ---- | ----------- | ---------- | ------- | ---------- | ----------- | ------- |
| 3.5      | 3.0  | 4.006348999 | 3.4        | 6.37    | 8.16       | 3.709334409 | 2.0     |

| your_vs_median     | your_vs_linesag | your_vs_linemassey | your_vs_lineelo    | your_vs_linehow |
| ------------------ | --------------- | ------------------ | ------------------ | --------------- |
| -7.519667204500001 | -8.85           | -10.64             | -6.189334409000001 | -4.48           |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-17 — Old Dominion @ South Florida (Cure Bowl)
- Neutral: `True` | Tier: `X-REVIEW` | Reasons: `BIG_MOVE=4.50|AGREE=1.00`
- DK (home spread): `-2.50` | Your (home spread): `-3.40` | Edge: `-0.90`
- Consensus: mean `-7.35` median `-8.35` std `2.33` z `1.70`
- Agreement (panel): `1.00`
- Market: open `-7.50` current `-3.00` move `4.50` CLV `TOWARD_YOU`
- Flags: `BIG_MOVE` | Robust edge: `0.39`

| lineopen | line | lineavg       | linemedian | linesag | linemassey | lineelo      | linehow |
| -------- | ---- | ------------- | ---------- | ------- | ---------- | ------------ | ------- |
| -7.5     | -3.0 | -8.4725487191 | -8.675     | -9.2    | -7.5       | -9.202252534 | -3.5    |

| your_vs_median    | your_vs_linesag   | your_vs_linemassey | your_vs_lineelo   | your_vs_linehow     |
| ----------------- | ----------------- | ------------------ | ----------------- | ------------------- |
| 4.949999999999999 | 5.799999999999999 | 4.1                | 5.802252533999999 | 0.10000000000000009 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-18 — Missouri State @ Arkansas State (Xbox Bowl)
- Neutral: `True` | Tier: `C` | Reasons: ``
- DK (home spread): `-1.50` | Your (home spread): `-2.34` | Edge: `-0.84`
- Consensus: mean `nan` median `nan` std `nan` z `nan`
- Agreement (panel): ``
- Flags: `` | Robust edge: `NA`

| lineopen | line | lineavg | linemedian | linesag | linemassey | lineelo | linehow |
| -------- | ---- | ------- | ---------- | ------- | ---------- | ------- | ------- |
|          |      |         |            |         |            |         |         |

| your_vs_median | your_vs_linesag | your_vs_linemassey | your_vs_lineelo | your_vs_linehow |
| -------------- | --------------- | ------------------ | --------------- | --------------- |
|                |                 |                    |                 |                 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-19 — Alabama @ Oklahoma (CFP First Round)
- Neutral: `False` | Tier: `A` | Reasons: `AGREE=0.75`
- DK (home spread): `1.50` | Your (home spread): `-3.14` | Edge: `-4.64`
- Consensus: mean `-1.86` median `-2.71` std `2.84` z `-0.45`
- Agreement (panel): `0.75` | Disagree: `linemassey`
- Market: open `2.00` current `1.00` move `-1.00` CLV `TOWARD_YOU`
- Flags: `` | Robust edge: `1.63`

| lineopen | line | lineavg       | linemedian | linesag | linemassey | lineelo      | linehow |
| -------- | ---- | ------------- | ---------- | ------- | ---------- | ------------ | ------- |
| 2.0      | 1.0  | -1.8997171742 | -1.7       | -1.14   | 2.49       | -4.289692199 | -4.5    |

| your_vs_median       | your_vs_linesag | your_vs_linemassey | your_vs_lineelo | your_vs_linehow    |
| -------------------- | --------------- | ------------------ | --------------- | ------------------ |
| -0.42515390050000024 | -2.0            | -5.630000000000001 | 1.149692199     | 1.3599999999999999 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-19 — Memphis @ NC State (Gasparilla Bowl)
- Neutral: `True` | Tier: `C` | Reasons: `AGREE=0.75`
- DK (home spread): `-4.50` | Your (home spread): `-2.87` | Edge: `1.63`
- Consensus: mean `-2.19` median `-2.13` std `3.06` z `-0.22`
- Agreement (panel): `0.75` | Disagree: `linesag`
- Market: open `-5.50` current `-4.50` move `1.00` CLV `TOWARD_YOU`
- Flags: `` | Robust edge: `0.53`

| lineopen | line | lineavg       | linemedian | linesag | linemassey | lineelo      | linehow |
| -------- | ---- | ------------- | ---------- | ------- | ---------- | ------------ | ------- |
| -5.5     | -4.5 | -2.3896834356 | -2.8       | -6.02   | 0.02       | -4.278950925 | 1.5     |

| your_vs_median      | your_vs_linesag    | your_vs_linemassey | your_vs_lineelo | your_vs_linehow |
| ------------------- | ------------------ | ------------------ | --------------- | --------------- |
| -0.7405245374999998 | 3.1499999999999995 | -2.89              | 1.408950925     | -4.37           |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-19 — Kennesaw State @ Western Michigan (Myrtle Beach Bowl)
- Neutral: `True` | Tier: `C` | Reasons: ``
- DK (home spread): `-3.50` | Your (home spread): `-2.69` | Edge: `0.81`
- Consensus: mean `nan` median `nan` std `nan` z `nan`
- Agreement (panel): ``
- Flags: `` | Robust edge: `NA`

| lineopen | line | lineavg | linemedian | linesag | linemassey | lineelo | linehow |
| -------- | ---- | ------- | ---------- | ------- | ---------- | ------- | ------- |
|          |      |         |            |         |            |         |         |

| your_vs_median | your_vs_linesag | your_vs_linemassey | your_vs_lineelo | your_vs_linehow |
| -------------- | --------------- | ------------------ | --------------- | --------------- |
|                |                 |                    |                 |                 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-20 — Miami @ Texas A&M (CFP First Round)
- Neutral: `False` | Tier: `C` | Reasons: ``
- DK (home spread): `-3.50` | Your (home spread): `-3.22` | Edge: `0.28`
- Consensus: mean `nan` median `nan` std `nan` z `nan`
- Agreement (panel): ``
- Flags: `` | Robust edge: `NA`

| lineopen | line | lineavg | linemedian | linesag | linemassey | lineelo | linehow |
| -------- | ---- | ------- | ---------- | ------- | ---------- | ------- | ------- |
|          |      |         |            |         |            |         |         |

| your_vs_median | your_vs_linesag | your_vs_linemassey | your_vs_lineelo | your_vs_linehow |
| -------------- | --------------- | ------------------ | --------------- | --------------- |
|                |                 |                    |                 |                 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-20 — Tulane @ Ole Miss (CFP First Round)
- Neutral: `False` | Tier: `A` | Reasons: ``
- DK (home spread): `-17.50` | Your (home spread): `-3.12` | Edge: `14.38`
- Consensus: mean `nan` median `nan` std `nan` z `nan`
- Agreement (panel): ``
- Flags: `` | Robust edge: `NA`

| lineopen | line | lineavg | linemedian | linesag | linemassey | lineelo | linehow |
| -------- | ---- | ------- | ---------- | ------- | ---------- | ------- | ------- |
|          |      |         |            |         |            |         |         |

| your_vs_median | your_vs_linesag | your_vs_linemassey | your_vs_lineelo | your_vs_linehow |
| -------------- | --------------- | ------------------ | --------------- | --------------- |
|                |                 |                    |                 |                 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-20 — James Madison @ Oregon (CFP First Round)
- Neutral: `False` | Tier: `X-REVIEW` | Reasons: `OUTLIER_Z=2.73|HIGH_STD=5.06|AGREE=0.75`
- DK (home spread): `-21.00` | Your (home spread): `-3.63` | Edge: `17.37`
- Consensus: mean `-17.46` median `-17.35` std `5.06` z `2.73`
- Agreement (panel): `0.75` | Disagree: `linemassey`
- Market: open `-21.00` current `-21.50` move `-0.50` CLV `AWAY_FROM_YOU`
- Flags: `OUTLIER|HIGH_STD` | Robust edge: `3.43`

| lineopen | line  | lineavg       | linemedian | linesag | linemassey | lineelo       | linehow |
| -------- | ----- | ------------- | ---------- | ------- | ---------- | ------------- | ------- |
| -21.0    | -21.5 | -18.620270119 | -20.08     | -18.39  | -24.66     | -16.306133845 | -10.5   |

| your_vs_median     | your_vs_linesag    | your_vs_linemassey | your_vs_lineelo    | your_vs_linehow |
| ------------------ | ------------------ | ------------------ | ------------------ | --------------- |
| 13.718066922500004 | 14.760000000000002 | 21.03              | 12.676133845000003 | 6.87            |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-22 — Washington State @ Utah State (Potato Bowl)
- Neutral: `True` | Tier: `X-REVIEW` | Reasons: `SIGN_CONFLICT|OUTLIER_Z=-4.29|BIG_MOVE=-3.50|AGREE=0.00`
- DK (home spread): `-2.50` | Your (home spread): `-2.71` | Edge: `-0.21`
- Consensus: mean `5.14` median `5.26` std `1.83` z `-4.29`
- Agreement (panel): `0.00` | Disagree: `linesag, linemassey, lineelo, linehow`
- Market: open `1.00` current `-2.50` move `-3.50` CLV `TOWARD_YOU`
- Flags: `OUTLIER|BIG_MOVE|SIGN_CONFLICT` | Robust edge: `0.11`

| lineopen | line | lineavg     | linemedian  | linesag | linemassey | lineelo     | linehow |
| -------- | ---- | ----------- | ----------- | ------- | ---------- | ----------- | ------- |
| 1.0      | -2.5 | 4.262443163 | 4.990707109 | 5.77    | 7.56       | 4.743666999 | 2.5     |

| your_vs_median | your_vs_linesag | your_vs_linemassey | your_vs_lineelo | your_vs_linehow |
| -------------- | --------------- | ------------------ | --------------- | --------------- |
| -7.9668334995  | -8.48           | -10.27             | -7.453666999    | -5.21           |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-23 — Toledo @ Louisville (Boca Raton Bowl)
- Neutral: `True` | Tier: `B` | Reasons: `HIGH_STD=4.16|AGREE=0.50`
- DK (home spread): `-6.50` | Your (home spread): `-3.28` | Edge: `3.22`
- Consensus: mean `-6.65` median `-5.51` std `4.16` z `0.81`
- Agreement (panel): `0.50` | Disagree: `linesag, linemassey`
- Market: open `-9.50` current `-7.00` move `2.50` CLV `TOWARD_YOU`
- Flags: `HIGH_STD` | Robust edge: `0.77`

| lineopen | line | lineavg       | linemedian | linesag | linemassey | lineelo      | linehow |
| -------- | ---- | ------------- | ---------- | ------- | ---------- | ------------ | ------- |
| -9.5     | -7.0 | -5.9781326148 | -5.995     | -8.02   | -12.87     | -2.712957008 | -3.0    |

| your_vs_median | your_vs_linesag | your_vs_linemassey | your_vs_lineelo     | your_vs_linehow     |
| -------------- | --------------- | ------------------ | ------------------- | ------------------- |
| 2.23           | 4.74            | 9.59               | -0.5670429919999997 | -0.2799999999999998 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-23 — UNLV @ Ohio (Frisco Bowl)
- Neutral: `True` | Tier: `X-REVIEW` | Reasons: `OUTLIER_Z=-11.34|AGREE=0.75`
- DK (home spread): `5.50` | Your (home spread): `-2.92` | Edge: `-8.42`
- Consensus: mean `5.28` median `5.02` std `0.72` z `-11.34`
- Agreement (panel): `0.75` | Disagree: `linehow`
- Market: open `4.00` current `5.00` move `1.00` CLV `AWAY_FROM_YOU`
- Flags: `OUTLIER` | Robust edge: `11.63`

| lineopen | line | lineavg     | linemedian | linesag | linemassey | lineelo     | linehow |
| -------- | ---- | ----------- | ---------- | ------- | ---------- | ----------- | ------- |
| 4.0      | 5.0  | 4.917149225 | 5.165      | 5.04    | 4.59       | 5.009477106 | 6.5     |

| your_vs_median      | your_vs_linesag | your_vs_linemassey | your_vs_lineelo | your_vs_linehow |
| ------------------- | --------------- | ------------------ | --------------- | --------------- |
| -7.9447385530000005 | -7.96           | -7.51              | -7.929477106    | -9.42           |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-23 — Western Kentucky @ Southern Miss (New Orleans Bowl)
- Neutral: `True` | Tier: `X-REVIEW` | Reasons: `OUTLIER_Z=-3.64|AGREE=0.50`
- DK (home spread): `4.50` | Your (home spread): `-2.85` | Edge: `-7.35`
- Consensus: mean `4.94` median `4.49` std `2.14` z `-3.64`
- Agreement (panel): `0.50` | Disagree: `linemassey, lineelo`
- Market: open `3.00` current `4.00` move `1.00` CLV `AWAY_FROM_YOU`
- Flags: `OUTLIER` | Robust edge: `3.43`

| lineopen | line | lineavg     | linemedian | linesag | linemassey | lineelo     | linehow |
| -------- | ---- | ----------- | ---------- | ------- | ---------- | ----------- | ------- |
| 3.0      | 4.0  | 3.151152904 | 3.075      | 2.47    | 8.31       | 4.979566329 | 4.0     |

| your_vs_median | your_vs_linesag | your_vs_linemassey | your_vs_lineelo | your_vs_linehow |
| -------------- | --------------- | ------------------ | --------------- | --------------- |
| -7.3397831645  | -5.32           | -11.16             | -7.829566329    | -6.85           |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-24 — California @ Hawai'i (Hawai'i Bowl)
- Neutral: `False` | Tier: `A` | Reasons: `HIGH_STD=4.06|AGREE=0.75`
- DK (home spread): `1.50` | Your (home spread): `-2.59` | Edge: `-4.09`
- Consensus: mean `-0.65` median `-1.32` std `4.06` z `-0.48`
- Agreement (panel): `0.75` | Disagree: `linemassey`
- Market: open `2.50` current `1.50` move `-1.00` CLV `TOWARD_YOU`
- Flags: `HIGH_STD` | Robust edge: `1.01`

| lineopen | line | lineavg     | linemedian | linesag | linemassey | lineelo      | linehow |
| -------- | ---- | ----------- | ---------- | ------- | ---------- | ------------ | ------- |
| 2.5      | 1.5  | 0.396512001 | 0.221      | -0.05   | 5.54       | -2.599491893 | -5.5    |

| your_vs_median      | your_vs_linesag | your_vs_linemassey | your_vs_lineelo      | your_vs_linehow |
| ------------------- | --------------- | ------------------ | -------------------- | --------------- |
| -1.2652540534999999 | -2.54           | -8.129999999999999 | 0.009491893000000307 | 2.91            |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-26 — Florida International @ UTSA (First Responder Bowl)
- Neutral: `True` | Tier: `A` | Reasons: `HIGH_STD=4.33|AGREE=0.50`
- DK (home spread): `-9.50` | Your (home spread): `-2.77` | Edge: `6.73`
- Consensus: mean `-8.29` median `-7.97` std `4.33` z `1.28`
- Agreement (panel): `0.50` | Disagree: `linesag, linemassey`
- Market: open `-8.50` current `-8.50` move `0.00` CLV `NEUTRAL`
- Flags: `HIGH_STD` | Robust edge: `1.56`

| lineopen | line | lineavg       | linemedian | linesag | linemassey | lineelo      | linehow |
| -------- | ---- | ------------- | ---------- | ------- | ---------- | ------------ | ------- |
| -8.5     | -8.5 | -9.9575675047 | -9.85      | -10.37  | -14.22     | -5.571917626 | -3.0    |

| your_vs_median | your_vs_linesag | your_vs_linemassey | your_vs_lineelo    | your_vs_linehow     |
| -------------- | --------------- | ------------------ | ------------------ | ------------------- |
| 5.200958813    | 7.6             | 11.450000000000001 | 2.8019176260000003 | 0.22999999999999998 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-26 — Central Michigan @ Northwestern (GameAbove Sports Bowl)
- Neutral: `True` | Tier: `A` | Reasons: ``
- DK (home spread): `-10.50` | Your (home spread): `-2.69` | Edge: `7.81`
- Consensus: mean `nan` median `nan` std `nan` z `nan`
- Agreement (panel): ``
- Flags: `` | Robust edge: `NA`

| lineopen | line | lineavg | linemedian | linesag | linemassey | lineelo | linehow |
| -------- | ---- | ------- | ---------- | ------- | ---------- | ------- | ------- |
|          |      |         |            |         |            |         |         |

| your_vs_median | your_vs_linesag | your_vs_linemassey | your_vs_lineelo | your_vs_linehow |
| -------------- | --------------- | ------------------ | --------------- | --------------- |
|                |                 |                    |                 |                 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-26 — New Mexico @ Minnesota (Rate Bowl)
- Neutral: `True` | Tier: `C` | Reasons: `HIGH_STD=6.29|AGREE=0.50`
- DK (home spread): `-2.50` | Your (home spread): `-2.65` | Edge: `-0.15`
- Consensus: mean `-3.99` median `-4.52` std `6.29` z `0.21`
- Agreement (panel): `0.50` | Disagree: `lineelo, linehow`
- Market: open `-3.00` current `-2.50` move `0.50` CLV `TOWARD_YOU`
- Flags: `HIGH_STD` | Robust edge: `0.02`

| lineopen | line | lineavg       | linemedian | linesag | linemassey | lineelo      | linehow |
| -------- | ---- | ------------- | ---------- | ------- | ---------- | ------------ | ------- |
| -3.0     | -2.5 | -3.8032413368 | -2.582     | -8.44   | -11.41     | -0.608899505 | 4.5     |

| your_vs_median | your_vs_linesag   | your_vs_linemassey | your_vs_lineelo | your_vs_linehow |
| -------------- | ----------------- | ------------------ | --------------- | --------------- |
| 1.8744497525   | 5.789999999999999 | 8.76               | -2.041100495    | -7.15           |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-27 — Miami (OH) @ Fresno State (Arizona Bowl)
- Neutral: `True` | Tier: `C` | Reasons: ``
- DK (home spread): `-4.50` | Your (home spread): `-2.70` | Edge: `1.80`
- Consensus: mean `nan` median `nan` std `nan` z `nan`
- Agreement (panel): ``
- Flags: `` | Robust edge: `NA`

| lineopen | line | lineavg | linemedian | linesag | linemassey | lineelo | linehow |
| -------- | ---- | ------- | ---------- | ------- | ---------- | ------- | ------- |
|          |      |         |            |         |            |         |         |

| your_vs_median | your_vs_linesag | your_vs_linemassey | your_vs_lineelo | your_vs_linehow |
| -------------- | --------------- | ------------------ | --------------- | --------------- |
|                |                 |                    |                 |                 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-27 — UConn @ Army (Fenway Bowl)
- Neutral: `True` | Tier: `A` | Reasons: ``
- DK (home spread): `-8.50` | Your (home spread): `-2.82` | Edge: `5.68`
- Consensus: mean `nan` median `nan` std `nan` z `nan`
- Agreement (panel): ``
- Flags: `` | Robust edge: `NA`

| lineopen | line | lineavg | linemedian | linesag | linemassey | lineelo | linehow |
| -------- | ---- | ------- | ---------- | ------- | ---------- | ------- | ------- |
|          |      |         |            |         |            |         |         |

| your_vs_median | your_vs_linesag | your_vs_linemassey | your_vs_lineelo | your_vs_linehow |
| -------------- | --------------- | ------------------ | --------------- | --------------- |
|                |                 |                    |                 |                 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-27 — Virginia @ Missouri (Gator Bowl)
- Neutral: `True` | Tier: `B` | Reasons: `HIGH_STD=4.85|AGREE=0.50`
- DK (home spread): `-7.00` | Your (home spread): `-3.14` | Edge: `3.86`
- Consensus: mean `-5.13` median `-7.17` std `4.85` z `0.41`
- Agreement (panel): `0.50` | Disagree: `linemassey, lineelo`
- Market: open `-7.00` current `-6.50` move `0.50` CLV `TOWARD_YOU`
- Flags: `HIGH_STD` | Robust edge: `0.80`

| lineopen | line | lineavg       | linemedian | linesag | linemassey | lineelo      | linehow |
| -------- | ---- | ------------- | ---------- | ------- | ---------- | ------------ | ------- |
| -7.0     | -6.5 | -5.5508217241 | -5.2915    | -5.92   | -9.18      | -8.417849229 | 3.0     |

| your_vs_median    | your_vs_linesag | your_vs_linemassey | your_vs_lineelo   | your_vs_linehow    |
| ----------------- | --------------- | ------------------ | ----------------- | ------------------ |
| 4.028924614499999 | 2.78            | 6.039999999999999  | 5.277849228999999 | -6.140000000000001 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-27 — Pittsburgh @ East Carolina (Military Bowl)
- Neutral: `True` | Tier: `X-REVIEW` | Reasons: `OUTLIER_Z=-2.63|AGREE=0.75`
- DK (home spread): `8.50` | Your (home spread): `-3.06` | Edge: `-11.56`
- Consensus: mean `4.86` median `5.09` std `3.01` z `-2.63`
- Agreement (panel): `0.75` | Disagree: `linesag`
- Market: open `6.00` current `7.00` move `1.00` CLV `AWAY_FROM_YOU`
- Flags: `OUTLIER` | Robust edge: `3.84`

| lineopen | line | lineavg     | linemedian  | linesag | linemassey | lineelo     | linehow |
| -------- | ---- | ----------- | ----------- | ------- | ---------- | ----------- | ------- |
| 6.0      | 7.0  | 4.632879869 | 5.027318292 | 8.76    | 6.09       | 4.086359493 | 0.5     |

| your_vs_median | your_vs_linesag | your_vs_linemassey | your_vs_lineelo | your_vs_linehow |
| -------------- | --------------- | ------------------ | --------------- | --------------- |
| -8.1481797465  | -11.82          | -9.15              | -7.146359493    | -3.56           |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-27 — North Texas @ San Diego State (New Mexico Bowl)
- Neutral: `True` | Tier: `A` | Reasons: ``
- DK (home spread): `3.00` | Your (home spread): `-3.20` | Edge: `-6.20`
- Consensus: mean `nan` median `nan` std `nan` z `nan`
- Agreement (panel): ``
- Flags: `` | Robust edge: `NA`

| lineopen | line | lineavg | linemedian | linesag | linemassey | lineelo | linehow |
| -------- | ---- | ------- | ---------- | ------- | ---------- | ------- | ------- |
|          |      |         |            |         |            |         |         |

| your_vs_median | your_vs_linesag | your_vs_linemassey | your_vs_lineelo | your_vs_linehow |
| -------------- | --------------- | ------------------ | --------------- | --------------- |
|                |                 |                    |                 |                 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-27 — Penn State @ Clemson (Pinstripe Bowl)
- Neutral: `True` | Tier: `X-REVIEW` | Reasons: `SIGN_CONFLICT|OUTLIER_Z=-3.82|BIG_MOVE=-4.50|AGREE=1.00`
- DK (home spread): `-3.50` | Your (home spread): `-2.99` | Edge: `0.51`
- Consensus: mean `4.98` median `4.22` std `2.09` z `-3.82`
- Agreement (panel): `1.00`
- Market: open `1.00` current `-3.50` move `-4.50` CLV `TOWARD_YOU`
- Flags: `OUTLIER|BIG_MOVE|SIGN_CONFLICT` | Robust edge: `0.24`

| lineopen | line | lineavg     | linemedian | linesag | linemassey | lineelo     | linehow |
| -------- | ---- | ----------- | ---------- | ------- | ---------- | ----------- | ------- |
| 1.0      | -3.5 | 4.169582882 | 4.215      | 4.5     | 8.47       | 3.945146338 | 3.0     |

| your_vs_median     | your_vs_linesag | your_vs_linemassey | your_vs_lineelo | your_vs_linehow |
| ------------------ | --------------- | ------------------ | --------------- | --------------- |
| -7.212573169000001 | -7.49           | -11.46             | -6.935146338    | -5.99           |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-27 — Georgia Tech @ BYU (Pop-Tarts Bowl)
- Neutral: `True` | Tier: `X-REVIEW` | Reasons: `AGREE=0.00`
- DK (home spread): `-4.50` | Your (home spread): `-3.04` | Edge: `1.46`
- Consensus: mean `-10.13` median `-10.45` std `3.88` z `1.83`
- Agreement (panel): `0.00` | Disagree: `linesag, linemassey, lineelo, linehow`
- Market: open `-2.50` current `-4.50` move `-2.00` CLV `AWAY_FROM_YOU`
- Flags: `` | Robust edge: `0.38`

| lineopen | line | lineavg       | linemedian | linesag | linemassey | lineelo       | linehow |
| -------- | ---- | ------------- | ---------- | ------- | ---------- | ------------- | ------- |
| -2.5     | -4.5 | -8.4003641538 | -8.46      | -4.57   | -8.89      | -15.041773596 | -12.0   |

| your_vs_median | your_vs_linesag    | your_vs_linemassey | your_vs_lineelo | your_vs_linehow |
| -------------- | ------------------ | ------------------ | --------------- | --------------- |
| 7.405          | 1.5300000000000002 | 5.8500000000000005 | 12.001773596    | 8.96            |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-27 — LSU @ Houston (Texas Bowl)
- Neutral: `True` | Tier: `X-REVIEW` | Reasons: `SIGN_CONFLICT|AGREE=1.00`
- DK (home spread): `-3.00` | Your (home spread): `-2.65` | Edge: `0.35`
- Consensus: mean `2.39` median `3.61` std `3.34` z `-1.51`
- Agreement (panel): `1.00`
- Market: open `-3.00` current `-3.00` move `0.00` CLV `NEUTRAL`
- Flags: `SIGN_CONFLICT` | Robust edge: `0.10`

| lineopen | line | lineavg    | linemedian  | linesag | linemassey | lineelo     | linehow |
| -------- | ---- | ---------- | ----------- | ------- | ---------- | ----------- | ------- |
| -3.0     | -3.0 | 3.53078727 | 3.800317038 | 5.32    | 5.02       | 2.209484019 | -3.0    |

| your_vs_median     | your_vs_linesag    | your_vs_linemassey | your_vs_lineelo | your_vs_linehow    |
| ------------------ | ------------------ | ------------------ | --------------- | ------------------ |
| -6.264742009499999 | -7.970000000000001 | -7.67              | -4.859484019    | 0.3500000000000001 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-29 — Georgia Southern @ App State (Birmingham Bowl)
- Neutral: `True` | Tier: `X-REVIEW` | Reasons: `OUTLIER_Z=-2.21|AGREE=1.00`
- DK (home spread): `7.00` | Your (home spread): `-2.38` | Edge: `-9.38`
- Consensus: mean `2.62` median `2.90` std `2.26` z `-2.21`
- Agreement (panel): `1.00`
- Market: open `2.00` current `4.50` move `2.50` CLV `AWAY_FROM_YOU`
- Flags: `OUTLIER` | Robust edge: `4.15`

| lineopen | line | lineavg     | linemedian | linesag | linemassey | lineelo     | linehow |
| -------- | ---- | ----------- | ---------- | ------- | ---------- | ----------- | ------- |
| 2.0      | 4.5  | 1.617014225 | 1.95       | 3.06    | -0.83      | 2.744878853 | 5.5     |

| your_vs_median | your_vs_linesag     | your_vs_linemassey  | your_vs_lineelo | your_vs_linehow |
| -------------- | ------------------- | ------------------- | --------------- | --------------- |
| -5.2824394265  | -5.4399999999999995 | -1.5499999999999998 | -5.124878853    | -7.88           |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-30 — USC @ TCU (Alamo Bowl)
- Neutral: `True` | Tier: `X-REVIEW` | Reasons: `OUTLIER_Z=-9.84|AGREE=0.00`
- DK (home spread): `4.50` | Your (home spread): `-3.07` | Edge: `-7.57`
- Consensus: mean `7.29` median `7.01` std `1.05` z `-9.84`
- Agreement (panel): `0.00` | Disagree: `linesag, linemassey, lineelo, linehow`
- Market: open `5.50` current `4.50` move `-1.00` CLV `TOWARD_YOU`
- Flags: `OUTLIER` | Robust edge: `7.19`

| lineopen | line | lineavg     | linemedian | linesag | linemassey | lineelo     | linehow |
| -------- | ---- | ----------- | ---------- | ------- | ---------- | ----------- | ------- |
| 5.5      | 4.5  | 7.862746603 | 7.945      | 7.18    | 6.85       | 6.147686169 | 9.0     |

| your_vs_median      | your_vs_linesag | your_vs_linemassey | your_vs_lineelo | your_vs_linehow |
| ------------------- | --------------- | ------------------ | --------------- | --------------- |
| -10.084999999999999 | -10.25          | -9.92              | -9.217686169    | -12.07          |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-30 — Coastal Carolina @ Louisiana Tech (Independence Bowl)
- Neutral: `True` | Tier: `A` | Reasons: `AGREE=1.00`
- DK (home spread): `-8.50` | Your (home spread): `-2.57` | Edge: `5.93`
- Consensus: mean `-4.66` median `-4.66` std `1.87` z `1.12`
- Agreement (panel): `1.00`
- Market: open `-7.00` current `-9.00` move `-2.00` CLV `AWAY_FROM_YOU`
- Flags: `` | Robust edge: `3.18`

| lineopen | line | lineavg       | linemedian | linesag | linemassey | lineelo      | linehow |
| -------- | ---- | ------------- | ---------- | ------- | ---------- | ------------ | ------- |
| -7.0     | -9.0 | -7.6520938087 | -7.49      | -7.27   | -4.32      | -2.038003874 | -5.0    |

| your_vs_median     | your_vs_linesag   | your_vs_linemassey | your_vs_lineelo     | your_vs_linehow |
| ------------------ | ----------------- | ------------------ | ------------------- | --------------- |
| 2.0900000000000003 | 4.699999999999999 | 1.7500000000000004 | -0.5319961259999997 | 2.43            |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-30 — Tennessee @ Illinois (Music City Bowl)
- Neutral: `True` | Tier: `X-REVIEW` | Reasons: `OUTLIER_Z=-2.08|BIG_MOVE=-4.00|AGREE=0.25`
- DK (home spread): `2.50` | Your (home spread): `-2.95` | Edge: `-5.45`
- Consensus: mean `4.69` median `4.84` std `3.67` z `-2.08`
- Agreement (panel): `0.25` | Disagree: `linesag, linemassey, lineelo`
- Market: open `6.50` current `2.50` move `-4.00` CLV `TOWARD_YOU`
- Flags: `OUTLIER|BIG_MOVE` | Robust edge: `1.48`

| lineopen | line | lineavg     | linemedian  | linesag | linemassey | lineelo     | linehow |
| -------- | ---- | ----------- | ----------- | ------- | ---------- | ----------- | ------- |
| 6.5      | 2.5  | 3.675062018 | 3.618783245 | 6.06    | 9.59       | 3.620166489 | -0.5    |

| your_vs_median | your_vs_linesag | your_vs_linemassey | your_vs_lineelo | your_vs_linehow |
| -------------- | --------------- | ------------------ | --------------- | --------------- |
| -7.7900832445  | -9.01           | -12.54             | -6.570166489    | -2.45           |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-31 — Michigan @ Texas (Citrus Bowl)
- Neutral: `True` | Tier: `X-REVIEW` | Reasons: `BIG_MOVE=-3.00|AGREE=1.00`
- DK (home spread): `-7.50` | Your (home spread): `-2.93` | Edge: `4.57`
- Consensus: mean `-3.19` median `-3.28` std `1.91` z `0.13`
- Agreement (panel): `1.00`
- Market: open `-4.50` current `-7.50` move `-3.00` CLV `AWAY_FROM_YOU`
- Flags: `BIG_MOVE` | Robust edge: `2.39`

| lineopen | line | lineavg      | linemedian | linesag | linemassey | lineelo      | linehow |
| -------- | ---- | ------------ | ---------- | ------- | ---------- | ------------ | ------- |
| -4.5     | -7.5 | -2.739256218 | -2.0       | -4.98   | -1.58      | -5.184891145 | -1.0    |

| your_vs_median     | your_vs_linesag    | your_vs_linemassey | your_vs_lineelo    | your_vs_linehow     |
| ------------------ | ------------------ | ------------------ | ------------------ | ------------------- |
| 0.3500000000000001 | 2.0500000000000003 | -1.35              | 2.2548911449999998 | -1.9300000000000002 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-31 — Nebraska @ Utah (Las Vegas Bowl)
- Neutral: `True` | Tier: `X-REVIEW` | Reasons: `OUTLIER_Z=7.19|AGREE=0.75`
- DK (home spread): `-16.50` | Your (home spread): `-3.11` | Edge: `13.39`
- Consensus: mean `-14.53` median `-14.61` std `1.59` z `7.19`
- Agreement (panel): `0.75` | Disagree: `lineelo`
- Market: open `-14.00` current `-16.50` move `-2.50` CLV `AWAY_FROM_YOU`
- Flags: `OUTLIER` | Robust edge: `8.44`

| lineopen | line  | lineavg       | linemedian | linesag | linemassey | lineelo       | linehow |
| -------- | ----- | ------------- | ---------- | ------- | ---------- | ------------- | ------- |
| -14.0    | -16.5 | -14.685939865 | -15.24     | -12.39  | -13.72     | -16.504754049 | -15.5   |

| your_vs_median | your_vs_linesag   | your_vs_linemassey | your_vs_lineelo | your_vs_linehow |
| -------------- | ----------------- | ------------------ | --------------- | --------------- |
| 11.5           | 9.280000000000001 | 10.610000000000001 | 13.394754049    | 12.39           |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-31 — Iowa @ Vanderbilt (ReliaQuest Bowl)
- Neutral: `True` | Tier: `C` | Reasons: `AGREE=1.00`
- DK (home spread): `-5.50` | Your (home spread): `-3.20` | Edge: `2.30`
- Consensus: mean `-2.47` median `-3.45` std `2.56` z `-0.28`
- Agreement (panel): `1.00`
- Market: open `-4.00` current `-5.00` move `-1.00` CLV `AWAY_FROM_YOU`
- Flags: `` | Robust edge: `0.90`

| lineopen | line | lineavg       | linemedian | linesag | linemassey | lineelo      | linehow |
| -------- | ---- | ------------- | ---------- | ------- | ---------- | ------------ | ------- |
| -4.0     | -5.0 | -2.2248999549 | -1.7535    | -2.9    | 1.81       | -4.807557791 | -4.0    |

| your_vs_median | your_vs_linesag      | your_vs_linemassey | your_vs_lineelo    | your_vs_linehow    |
| -------------- | -------------------- | ------------------ | ------------------ | ------------------ |
| 0.25           | -0.30000000000000027 | -5.01              | 1.6075577909999996 | 0.7999999999999998 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-31 — Arizona State @ Duke (Sun Bowl)
- Neutral: `True` | Tier: `C` | Reasons: ``
- DK (home spread): `-2.50` | Your (home spread): `-2.74` | Edge: `-0.24`
- Consensus: mean `nan` median `nan` std `nan` z `nan`
- Agreement (panel): ``
- Flags: `` | Robust edge: `NA`

| lineopen | line | lineavg | linemedian | linesag | linemassey | lineelo | linehow |
| -------- | ---- | ------- | ---------- | ------- | ---------- | ------- | ------- |
|          |      |         |            |         |            |         |         |

| your_vs_median | your_vs_linesag | your_vs_linemassey | your_vs_lineelo | your_vs_linehow |
| -------------- | --------------- | ------------------ | --------------- | --------------- |
|                |                 |                    |                 |                 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2026-01-02 — Rice @ Texas State (Armed Forces Bowl)
- Neutral: `True` | Tier: `A` | Reasons: ``
- DK (home spread): `-10.50` | Your (home spread): `-2.57` | Edge: `7.93`
- Consensus: mean `nan` median `nan` std `nan` z `nan`
- Agreement (panel): ``
- Flags: `` | Robust edge: `NA`

| lineopen | line | lineavg | linemedian | linesag | linemassey | lineelo | linehow |
| -------- | ---- | ------- | ---------- | ------- | ---------- | ------- | ------- |
|          |      |         |            |         |            |         |         |

| your_vs_median | your_vs_linesag | your_vs_linemassey | your_vs_lineelo | your_vs_linehow |
| -------------- | --------------- | ------------------ | --------------- | --------------- |
|                |                 |                    |                 |                 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2026-01-02 — Wake Forest @ Mississippi State (Duke's Mayo Bowl)
- Neutral: `True` | Tier: `C` | Reasons: ``
- DK (home spread): `-4.00` | Your (home spread): `-2.76` | Edge: `1.24`
- Consensus: mean `nan` median `nan` std `nan` z `nan`
- Agreement (panel): ``
- Flags: `` | Robust edge: `NA`

| lineopen | line | lineavg | linemedian | linesag | linemassey | lineelo | linehow |
| -------- | ---- | ------- | ---------- | ------- | ---------- | ------- | ------- |
|          |      |         |            |         |            |         |         |

| your_vs_median | your_vs_linesag | your_vs_linemassey | your_vs_lineelo | your_vs_linehow |
| -------------- | --------------- | ------------------ | --------------- | --------------- |
|                |                 |                    |                 |                 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2026-01-02 — Arizona @ SMU (Holiday Bowl)
- Neutral: `True` | Tier: `A` | Reasons: `AGREE=0.50`
- DK (home spread): `3.00` | Your (home spread): `-3.18` | Edge: `-6.18`
- Consensus: mean `0.70` median `1.12` std `3.58` z `-1.08`
- Agreement (panel): `0.50` | Disagree: `lineelo, linehow`
- Market: open `1.50` current `3.00` move `1.50` CLV `AWAY_FROM_YOU`
- Flags: `` | Robust edge: `1.73`

| lineopen | line | lineavg       | linemedian | linesag | linemassey | lineelo    | linehow |
| -------- | ---- | ------------- | ---------- | ------- | ---------- | ---------- | ------- |
| 1.5      | 3.0  | -0.1953130564 | -0.195     | -4.15   | -1.26      | 4.69327171 | 3.5     |

| your_vs_median     | your_vs_linesag    | your_vs_linemassey  | your_vs_lineelo    | your_vs_linehow |
| ------------------ | ------------------ | ------------------- | ------------------ | --------------- |
| -4.300000000000001 | 0.9700000000000002 | -1.9200000000000002 | -7.873271710000001 | -6.68           |

- Notes: _opt-outs / injuries / motivation / weather_

### 2026-01-02 — Navy @ Cincinnati (Liberty Bowl)
- Neutral: `True` | Tier: `X-REVIEW` | Reasons: `MOVE_DATA_ISSUE|HIGH_STD=5.41|AGREE=0.75`
- DK (home spread): `6.50` | Your (home spread): `-2.98` | Edge: `-9.48`
- Consensus: mean `-1.20` median `-1.92` std `5.41` z `-0.33`
- Agreement (panel): `0.75` | Disagree: `linehow`
- Market: open `-6.50` current `7.00` move `nan` CLV `<NA>`
- Flags: `MOVE_DATA_ISSUE|HIGH_STD` | Robust edge: `1.75`

| lineopen | line | lineavg       | linemedian | linesag | linemassey | lineelo      | linehow |
| -------- | ---- | ------------- | ---------- | ------- | ---------- | ------------ | ------- |
| -6.5     | 7.0  | -3.1825234917 | -3.86      | -3.17   | -7.95      | -0.664203981 | 7.0     |

| your_vs_median | your_vs_linesag     | your_vs_linemassey | your_vs_lineelo | your_vs_linehow |
| -------------- | ------------------- | ------------------ | --------------- | --------------- |
| -1.0628980095  | 0.18999999999999995 | 4.970000000000001  | -2.315796019    | -9.98           |

- Notes: _opt-outs / injuries / motivation / weather_
