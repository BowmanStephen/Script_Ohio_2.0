# Bowl Betting Evaluation Guide

Generated: 2025-12-16T22:34:13

- Slate: `/Users/stephen_bowman/Documents/GitHub/Script_Ohio_2.0/predictions/draftkings_slate_2025/dk_slate_predictions_20251216_214645.csv`
- Systems: `/Users/stephen_bowman/Documents/GitHub/Script_Ohio_2.0/predictions/ncaapredictions.csv`

## Spread Orientation

- Canonical: `home_spread < 0` home favored; `home_spread > 0` home underdog
- Systems lines normalized to canonical home spreads via per-column polarity inference.

## Totals Warning

Totals model appears mis-scaled or mismatched (rf_total median=17.490000000000002, corr=-0.11256909290652314). Totals edges suppressed.

## Quick Board (sorted by date)

| date       | bowl                  | away_team             | home_team         | dk_home_spread | your_home_spread | edge_vs_dk | edge_vs_market | abs_edge_vs_market | current_home_spread | open_home_spread | ratings_sources_home                    | ratings_count | ratings_mean_home | ratings_median_home | ratings_std | ratings_z | agreement_rate | agreement_n | clv_direction | move_from_open | dk_vs_market_conflict | flags                                             | tier     | tier_reasons                                                                | dk_total | rf_total | total_pick | total_edge | adv_stats_coverage |
| ---------- | --------------------- | --------------------- | ----------------- | -------------- | ---------------- | ---------- | -------------- | ------------------ | ------------------- | ---------------- | --------------------------------------- | ------------- | ----------------- | ------------------- | ----------- | --------- | -------------- | ----------- | ------------- | -------------- | --------------------- | ------------------------------------------------- | -------- | --------------------------------------------------------------------------- | -------- | -------- | ---------- | ---------- | ------------------ |
| 2025-12-17 | 68 Ventures Bowl      | Louisiana             | Delaware          | 3.0            | -2.48            | -5.48      | -5.48          | 5.48               | 3.0                 | 3.5              | linesag\|linemassey\|lineelo\|linemoore | 4             | 4.88              | 5.04                | 2.61        | -2.82     | 0.25           | 4           | TOWARD_YOU    | -0.5           | False                 | OUTLIER_MARKET\|OUTLIER_RATINGS                   | A        | EDGE_DK=-5.48\|EDGE_MKT=-5.48\|OUTLIER_MKT\|RATINGS_Z=-2.82                 | 61.5     |          |            |            | 1.0                |
| 2025-12-17 | Cure Bowl             | Old Dominion          | South Florida     | -2.5           | -3.4             | -0.9       | -0.4           | 0.4                | -3.0                | -7.5             | linesag\|linemassey\|lineelo\|linemoore | 4             | -9.25             | -9.2                | 1.27        | 4.59      | 1.0            | 4           | TOWARD_YOU    | 4.5            | False                 | OUTLIER_RATINGS\|BIG_MOVE                         | X-REVIEW | EDGE_DK=-0.90\|EDGE_MKT=-0.40\|BIG_MOVE=4.50\|RATINGS_Z=4.59                | 52.5     |          |            |            | 1.0                |
| 2025-12-18 | Xbox Bowl             | Missouri State        | Arkansas State    | -1.5           | -2.34            | -0.84      |                |                    |                     |                  | linesag\|linemassey\|lineelo\|linemoore | 0             |                   |                     |             |           |                | 0           |               |                | False                 |                                                   | C        | EDGE_DK=-0.84                                                               | 54.5     |          |            |            | 1.0                |
| 2025-12-19 | CFP First Round       | Alabama               | Oklahoma          | 1.5            | -3.14            | -4.64      | -4.14          | 4.14               | 1.0                 | 2.0              | linesag\|linemassey\|lineelo\|linemoore | 4             | -1.48             | -2.06               | 2.55        | -0.65     | 0.75           | 4           | TOWARD_YOU    | -1.0           | False                 | OUTLIER_MARKET                                    | A        | EDGE_DK=-4.64\|EDGE_MKT=-4.14\|OUTLIER_MKT\|RATINGS_Z=-0.65                 | 40.5     |          |            |            | 1.0                |
| 2025-12-19 | Gasparilla Bowl       | Memphis               | NC State          | -4.5           | -2.87            | 1.63       | 1.63           | 1.63               | -4.5                | -5.5             | linesag\|linemassey\|lineelo\|linemoore | 4             | -3.3              | -3.59               | 2.21        | 0.19      | 0.75           | 4           | TOWARD_YOU    | 1.0            | False                 |                                                   | C        | EDGE_DK=1.63\|EDGE_MKT=1.63\|RATINGS_Z=0.19                                 | 58.5     |          |            |            | 1.0                |
| 2025-12-19 | Myrtle Beach Bowl     | Kennesaw State        | Western Michigan  | -3.5           | -2.69            | 0.81       |                |                    |                     |                  | linesag\|linemassey\|lineelo\|linemoore | 0             |                   |                     |             |           |                | 0           |               |                | False                 |                                                   | C        | EDGE_DK=0.81                                                                | 48.5     |          |            |            | 1.0                |
| 2025-12-20 | CFP First Round       | Miami                 | Texas A&M         | -3.5           | -3.22            | 0.28       |                |                    |                     |                  | linesag\|linemassey\|lineelo\|linemoore | 0             |                   |                     |             |           |                | 0           |               |                | False                 |                                                   | C        | EDGE_DK=0.28                                                                | 50.5     |          |            |            | 1.0                |
| 2025-12-20 | CFP First Round       | Tulane                | Ole Miss          | -17.5          | -3.12            | 14.38      |                |                    |                     |                  | linesag\|linemassey\|lineelo\|linemoore | 0             |                   |                     |             |           |                | 0           |               |                | False                 |                                                   | C        | EDGE_DK=14.38                                                               | 56.5     |          |            |            | 1.0                |
| 2025-12-20 | CFP First Round       | James Madison         | Oregon            | -21.0          | -3.63            | 17.37      | 17.87          | 17.87              | -21.5               | -21.0            | linesag\|linemassey\|lineelo\|linemoore | 4             | -17.08            | -17.35              | 5.61        | 2.4       | 0.75           | 4           | AWAY_FROM_YOU | -0.5           | False                 | OUTLIER_MARKET\|OUTLIER_RATINGS\|HIGH_STD_RATINGS | X-REVIEW | EDGE_DK=17.37\|EDGE_MKT=17.87\|OUTLIER_MKT\|RATINGS_Z=2.40                  | 47.5     |          |            |            | 1.0                |
| 2025-12-22 | Potato Bowl           | Washington State      | Utah State        | -2.5           | -2.71            | -0.21      | -0.21          | 0.21               | -2.5                | 1.0              | linesag\|linemassey\|lineelo\|linemoore | 4             | 5.07              | 5.26                | 1.93        | -4.03     | 0.0            | 4           | TOWARD_YOU    | -3.5           | False                 | OUTLIER_RATINGS\|BIG_MOVE                         | C        | EDGE_DK=-0.21\|EDGE_MKT=-0.21\|BIG_MOVE=-3.50\|RATINGS_Z=-4.03              | 50.5     |          |            |            | 1.0                |
| 2025-12-23 | Boca Raton Bowl       | Toledo                | Louisville        | -6.5           | -3.28            | 3.22       | 3.72           | 3.72               | -7.0                | -9.5             | linesag\|linemassey\|lineelo\|linemoore | 4             | -6.04             | -5.37               | 4.79        | 0.57      | 0.5            | 4           | TOWARD_YOU    | 2.5            | False                 | HIGH_STD_RATINGS                                  | B        | EDGE_DK=3.22\|EDGE_MKT=3.72\|RATINGS_Z=0.57                                 | 45.5     |          |            |            | 1.0                |
| 2025-12-23 | Frisco Bowl           | UNLV                  | Ohio              | 5.5            | -2.92            | -8.42      | -7.92          | 7.92               | 5.0                 | 4.0              | linesag\|linemassey\|lineelo\|linemoore | 4             | 4.29              | 4.8                 | 1.04        | -6.95     | 1.0            | 4           | AWAY_FROM_YOU | 1.0            | False                 | OUTLIER_MARKET\|OUTLIER_RATINGS                   | X-REVIEW | EDGE_DK=-8.42\|EDGE_MKT=-7.92\|OUTLIER_MKT\|RATINGS_Z=-6.95                 | 65.5     |          |            |            | 1.0                |
| 2025-12-23 | New Orleans Bowl      | Western Kentucky      | Southern Miss     | 4.5            | -2.85            | -7.35      | -6.85          | 6.85               | 4.0                 | 3.0              | linesag\|linemassey\|lineelo\|linemoore | 4             | 3.33              | 3.72                | 3.93        | -1.57     | 0.5            | 4           | AWAY_FROM_YOU | 1.0            | False                 | OUTLIER_MARKET                                    | X-REVIEW | EDGE_DK=-7.35\|EDGE_MKT=-6.85\|OUTLIER_MKT\|RATINGS_Z=-1.57                 | 57.5     |          |            |            | 1.0                |
| 2025-12-24 | Hawai'i Bowl          | California            | Hawai'i           | 1.5            | -2.59            | -4.09      | -4.09          | 4.09               | 1.5                 | 2.5              | linesag\|linemassey\|lineelo\|linemoore | 4             | 1.22              | 0.98                | 2.98        | -1.28     | 0.5            | 4           | TOWARD_YOU    | -1.0           | False                 | OUTLIER_MARKET                                    | A        | EDGE_DK=-4.09\|EDGE_MKT=-4.09\|OUTLIER_MKT\|RATINGS_Z=-1.28                 | 54.5     |          |            |            | 1.0                |
| 2025-12-26 | First Responder Bowl  | Florida International | UTSA              | -9.5           | -2.77            | 6.73       | 5.73           | 5.73               | -8.5                | -8.5             | linesag\|linemassey\|lineelo\|linemoore | 4             | -8.91             | -7.97               | 3.65        | 1.68      | 0.5            | 4           | NEUTRAL       | 0.0            | False                 | OUTLIER_MARKET                                    | A        | EDGE_DK=6.73\|EDGE_MKT=5.73\|OUTLIER_MKT\|RATINGS_Z=1.68                    | 59.5     |          |            |            | 1.0                |
| 2025-12-26 | GameAbove Sports Bowl | Central Michigan      | Northwestern      | -10.5          | -2.69            | 7.81       |                |                    |                     |                  | linesag\|linemassey\|lineelo\|linemoore | 0             |                   |                     |             |           |                | 0           |               |                | False                 |                                                   | C        | EDGE_DK=7.81                                                                | 43.5     |          |            |            | 1.0                |
| 2025-12-26 | Rate Bowl             | New Mexico            | Minnesota         | -2.5           | -2.65            | -0.15      | -0.15          | 0.15               | -2.5                | -3.0             | linesag\|linemassey\|lineelo\|linemoore | 4             | -5.93             | -5.84               | 4.24        | 0.77      | 0.75           | 4           | TOWARD_YOU    | 0.5            | False                 | HIGH_STD_RATINGS                                  | C        | EDGE_DK=-0.15\|EDGE_MKT=-0.15\|RATINGS_Z=0.77                               | 45.5     |          |            |            | 1.0                |
| 2025-12-27 | Arizona Bowl          | Miami (OH)            | Fresno State      | -4.5           | -2.7             | 1.8        |                |                    |                     |                  | linesag\|linemassey\|lineelo\|linemoore | 0             |                   |                     |             |           |                | 0           |               |                | False                 |                                                   | C        | EDGE_DK=1.80                                                                | 42.5     |          |            |            | 1.0                |
| 2025-12-27 | Fenway Bowl           | UConn                 | Army              | -8.5           | -2.82            | 5.68       |                |                    |                     |                  | linesag\|linemassey\|lineelo\|linemoore | 0             |                   |                     |             |           |                | 0           |               |                | False                 |                                                   | C        | EDGE_DK=5.68                                                                | 44.5     |          |            |            | 1.0                |
| 2025-12-27 | Gator Bowl            | Virginia              | Missouri          | -7.0           | -3.14            | 3.86       | 3.36           | 3.36               | -6.5                | -7.0             | linesag\|linemassey\|lineelo\|linemoore | 4             | -6.98             | -7.17               | 1.92        | 2.0       | 0.5            | 4           | TOWARD_YOU    | 0.5            | False                 |                                                   | B        | EDGE_DK=3.86\|EDGE_MKT=3.36\|RATINGS_Z=2.00                                 | 47.5     |          |            |            | 1.0                |
| 2025-12-27 | Military Bowl         | Pittsburgh            | East Carolina     | 8.5            | -3.06            | -11.56     | -10.06         | 10.06              | 7.0                 | 6.0              | linesag\|linemassey\|lineelo\|linemoore | 4             | 4.85              | 5.09                | 3.03        | -2.61     | 0.75           | 4           | AWAY_FROM_YOU | 1.0            | False                 | OUTLIER_MARKET\|OUTLIER_RATINGS                   | X-REVIEW | EDGE_DK=-11.56\|EDGE_MKT=-10.06\|OUTLIER_MKT\|RATINGS_Z=-2.61               | 57.5     |          |            |            | 1.0                |
| 2025-12-27 | New Mexico Bowl       | North Texas           | San Diego State   | 3.0            | -3.2             | -6.2       |                |                    |                     |                  | linesag\|linemassey\|lineelo\|linemoore | 0             |                   |                     |             |           |                | 0           |               |                | False                 |                                                   | C        | EDGE_DK=-6.20                                                               | 54.5     |          |            |            | 1.0                |
| 2025-12-27 | Pinstripe Bowl        | Penn State            | Clemson           | -3.5           | -2.99            | 0.51       | 0.51           | 0.51               | -3.5                | 1.0              | linesag\|linemassey\|lineelo\|linemoore | 4             | 3.56              | 4.22                | 3.99        | -1.64     | 1.0            | 4           | TOWARD_YOU    | -4.5           | False                 | BIG_MOVE                                          | X-REVIEW | EDGE_DK=0.51\|EDGE_MKT=0.51\|BIG_MOVE=-4.50\|RATINGS_Z=-1.64                | 48.5     |          |            |            | 1.0                |
| 2025-12-27 | Pop-Tarts Bowl        | Georgia Tech          | BYU               | -4.5           | -3.04            | 1.46       | 1.46           | 1.46               | -4.5                | -2.5             | linesag\|linemassey\|lineelo\|linemoore | 4             | -9.96             | -10.1               | 3.8         | 1.82      | 0.0            | 4           | AWAY_FROM_YOU | -2.0           | False                 |                                                   | C        | EDGE_DK=1.46\|EDGE_MKT=1.46\|RATINGS_Z=1.82                                 | 56.5     |          |            |            | 1.0                |
| 2025-12-27 | Texas Bowl            | LSU                   | Houston           | -3.0           | -2.65            | 0.35       | 0.35           | 0.35               | -3.0                | -3.0             | linesag\|linemassey\|lineelo\|linemoore | 4             | 4.2               | 4.63                | 1.21        | -5.64     | 1.0            | 4           | NEUTRAL       | 0.0            | False                 | OUTLIER_RATINGS                                   | C        | EDGE_DK=0.35\|EDGE_MKT=0.35\|RATINGS_Z=-5.64                                | 41.5     |          |            |            | 1.0                |
| 2025-12-29 | Birmingham Bowl       | Georgia Southern      | App State         | 7.0            | -2.38            | -9.38      | -6.88          | 6.88               | 4.5                 | 2.0              | linesag\|linemassey\|lineelo\|linemoore | 4             | 2.68              | 2.9                 | 2.34        | -2.17     | 1.0            | 4           | AWAY_FROM_YOU | 2.5            | False                 | OUTLIER_MARKET\|OUTLIER_RATINGS                   | X-REVIEW | EDGE_DK=-9.38\|EDGE_MKT=-6.88\|OUTLIER_MKT\|RATINGS_Z=-2.17                 | 59.5     |          |            |            | 1.0                |
| 2025-12-30 | Alamo Bowl            | USC                   | TCU               | 4.5            | -3.07            | -7.57      | -7.57          | 7.57               | 4.5                 | 5.5              | linesag\|linemassey\|lineelo\|linemoore | 4             | 5.73              | 6.5                 | 1.76        | -5.01     | 0.25           | 4           | TOWARD_YOU    | -1.0           | False                 | OUTLIER_MARKET\|OUTLIER_RATINGS                   | X-REVIEW | EDGE_DK=-7.57\|EDGE_MKT=-7.57\|OUTLIER_MKT\|RATINGS_Z=-5.01                 | 57.5     |          |            |            | 1.0                |
| 2025-12-30 | Independence Bowl     | Coastal Carolina      | Louisiana Tech    | -8.5           | -2.57            | 5.93       | 6.43           | 6.43               | -9.0                | -7.0             | linesag\|linemassey\|lineelo\|linemoore | 4             | -6.21             | -5.8                | 3.44        | 1.06      | 0.75           | 4           | AWAY_FROM_YOU | -2.0           | False                 | OUTLIER_MARKET                                    | X-REVIEW | EDGE_DK=5.93\|EDGE_MKT=6.43\|OUTLIER_MKT\|RATINGS_Z=1.06                    | 50.5     |          |            |            | 1.0                |
| 2025-12-30 | Music City Bowl       | Tennessee             | Illinois          | 2.5            | -2.95            | -5.45      | -5.45          | 5.45               | 2.5                 | 6.5              | linesag\|linemassey\|lineelo\|linemoore | 4             | 5.95              | 5.29                | 2.28        | -3.91     | 0.0            | 4           | TOWARD_YOU    | -4.0           | False                 | OUTLIER_MARKET\|OUTLIER_RATINGS\|BIG_MOVE         | X-REVIEW | EDGE_DK=-5.45\|EDGE_MKT=-5.45\|OUTLIER_MKT\|BIG_MOVE=-4.00\|RATINGS_Z=-3.91 | 61.5     |          |            |            | 1.0                |
| 2025-12-31 | Citrus Bowl           | Michigan              | Texas             | -7.5           | -2.93            | 4.57       | 4.57           | 4.57               | -7.5                | -4.5             | linesag\|linemassey\|lineelo\|linemoore | 4             | -4.78             | -5.08               | 2.08        | 0.89      | 1.0            | 4           | AWAY_FROM_YOU | -3.0           | False                 | OUTLIER_MARKET\|BIG_MOVE                          | A        | EDGE_DK=4.57\|EDGE_MKT=4.57\|OUTLIER_MKT\|BIG_MOVE=-3.00\|RATINGS_Z=0.89    | 46.5     |          |            |            | 1.0                |
| 2025-12-31 | Las Vegas Bowl        | Nebraska              | Utah              | -16.5          | -3.11            | 13.39      | 13.39          | 13.39              | -16.5               | -14.0            | linesag\|linemassey\|lineelo\|linemoore | 4             | -16.32            | -15.11              | 3.95        | 3.34      | 0.5            | 4           | AWAY_FROM_YOU | -2.5           | False                 | OUTLIER_MARKET\|OUTLIER_RATINGS                   | X-REVIEW | EDGE_DK=13.39\|EDGE_MKT=13.39\|OUTLIER_MKT\|RATINGS_Z=3.34                  | 50.5     |          |            |            | 1.0                |
| 2025-12-31 | ReliaQuest Bowl       | Iowa                  | Vanderbilt        | -5.5           | -3.2             | 2.3        | 1.8            | 1.8                | -5.0                | -4.0             | linesag\|linemassey\|lineelo\|linemoore | 4             | -3.74             | -3.85               | 3.9         | 0.14      | 0.75           | 4           | AWAY_FROM_YOU | -1.0           | False                 |                                                   | C        | EDGE_DK=2.30\|EDGE_MKT=1.80\|RATINGS_Z=0.14                                 | 47.5     |          |            |            | 1.0                |
| 2025-12-31 | Sun Bowl              | Arizona State         | Duke              | -2.5           | -2.74            | -0.24      |                |                    |                     |                  | linesag\|linemassey\|lineelo\|linemoore | 0             |                   |                     |             |           |                | 0           |               |                | False                 |                                                   | C        | EDGE_DK=-0.24                                                               | 49.5     |          |            |            | 1.0                |
| 2026-01-02 | Armed Forces Bowl     | Rice                  | Texas State       | -10.5          | -2.57            | 7.93       |                |                    |                     |                  | linesag\|linemassey\|lineelo\|linemoore | 0             |                   |                     |             |           |                | 0           |               |                | False                 |                                                   | C        | EDGE_DK=7.93                                                                | 59.5     |          |            |            | 1.0                |
| 2026-01-02 | Duke's Mayo Bowl      | Wake Forest           | Mississippi State | -4.0           | -2.76            | 1.24       |                |                    |                     |                  | linesag\|linemassey\|lineelo\|linemoore | 0             |                   |                     |             |           |                | 0           |               |                | False                 |                                                   | C        | EDGE_DK=1.24                                                                | 56.5     |          |            |            | 1.0                |
| 2026-01-02 | Holiday Bowl          | Arizona               | SMU               | 3.0            | -3.18            | -6.18      | -6.18          | 6.18               | 3.0                 | 1.5              | linesag\|linemassey\|lineelo\|linemoore | 4             | 1.53              | 1.72                | 4.42        | -1.07     | 0.5            | 4           | AWAY_FROM_YOU | 1.5            | False                 | OUTLIER_MARKET\|HIGH_STD_RATINGS                  | X-REVIEW | EDGE_DK=-6.18\|EDGE_MKT=-6.18\|OUTLIER_MKT\|RATINGS_Z=-1.07                 | 51.5     |          |            |            | 1.0                |
| 2026-01-02 | Liberty Bowl          | Navy                  | Cincinnati        | 6.5            | -2.98            | -9.48      | -9.98          | 9.98               | 7.0                 | -6.5             | linesag\|linemassey\|lineelo\|linemoore | 4             | -3.91             | -3.51               | 2.62        | 0.36      | 1.0            | 4           |               |                | False                 | OUTLIER_MARKET\|MOVE_DATA_ISSUE                   | X-REVIEW | EDGE_DK=-9.48\|EDGE_MKT=-9.98\|MOVE_DATA_ISSUE\|OUTLIER_MKT\|RATINGS_Z=0.36 | 53.5     |          |            |            | 1.0                |

## Audit / Review Queue

| date       | bowl                 | away_team             | home_team      | dk_home_spread | your_home_spread | edge_vs_dk           | edge_vs_market       | current_home_spread | move_from_open | ratings_z           | agreement_rate | flags                                             | tier     | tier_reasons                                                                |
| ---------- | -------------------- | --------------------- | -------------- | -------------- | ---------------- | -------------------- | -------------------- | ------------------- | -------------- | ------------------- | -------------- | ------------------------------------------------- | -------- | --------------------------------------------------------------------------- |
| 2026-01-02 | Liberty Bowl         | Navy                  | Cincinnati     | 6.5            | -2.98            | -9.48                | -9.98                | 7.0                 |                | 0.3556915981423873  | 1.0            | OUTLIER_MARKET\|MOVE_DATA_ISSUE                   | X-REVIEW | EDGE_DK=-9.48\|EDGE_MKT=-9.98\|MOVE_DATA_ISSUE\|OUTLIER_MKT\|RATINGS_Z=0.36 |
| 2025-12-20 | CFP First Round      | James Madison         | Oregon         | -21.0          | -3.63            | 17.37                | 17.87                | -21.5               | -0.5           | 2.399073049081942   | 0.75           | OUTLIER_MARKET\|OUTLIER_RATINGS\|HIGH_STD_RATINGS | X-REVIEW | EDGE_DK=17.37\|EDGE_MKT=17.87\|OUTLIER_MKT\|RATINGS_Z=2.40                  |
| 2025-12-31 | Las Vegas Bowl       | Nebraska              | Utah           | -16.5          | -3.11            | 13.39                | 13.39                | -16.5               | -2.5           | 3.3433121996580177  | 0.5            | OUTLIER_MARKET\|OUTLIER_RATINGS                   | X-REVIEW | EDGE_DK=13.39\|EDGE_MKT=13.39\|OUTLIER_MKT\|RATINGS_Z=3.34                  |
| 2025-12-27 | Military Bowl        | Pittsburgh            | East Carolina  | 8.5            | -3.06            | -11.56               | -10.06               | 7.0                 | 1.0            | -2.6117779871580282 | 0.75           | OUTLIER_MARKET\|OUTLIER_RATINGS                   | X-REVIEW | EDGE_DK=-11.56\|EDGE_MKT=-10.06\|OUTLIER_MKT\|RATINGS_Z=-2.61               |
| 2025-12-23 | Frisco Bowl          | UNLV                  | Ohio           | 5.5            | -2.92            | -8.42                | -7.92                | 5.0                 | 1.0            | -6.951352778383489  | 1.0            | OUTLIER_MARKET\|OUTLIER_RATINGS                   | X-REVIEW | EDGE_DK=-8.42\|EDGE_MKT=-7.92\|OUTLIER_MKT\|RATINGS_Z=-6.95                 |
| 2025-12-30 | Alamo Bowl           | USC                   | TCU            | 4.5            | -3.07            | -7.57                | -7.57                | 4.5                 | -1.0           | -5.010244908665388  | 0.25           | OUTLIER_MARKET\|OUTLIER_RATINGS                   | X-REVIEW | EDGE_DK=-7.57\|EDGE_MKT=-7.57\|OUTLIER_MKT\|RATINGS_Z=-5.01                 |
| 2025-12-29 | Birmingham Bowl      | Georgia Southern      | App State      | 7.0            | -2.38            | -9.379999999999999   | -6.88                | 4.5                 | 2.5            | -2.1653137852464974 | 1.0            | OUTLIER_MARKET\|OUTLIER_RATINGS                   | X-REVIEW | EDGE_DK=-9.38\|EDGE_MKT=-6.88\|OUTLIER_MKT\|RATINGS_Z=-2.17                 |
| 2025-12-23 | New Orleans Bowl     | Western Kentucky      | Southern Miss  | 4.5            | -2.85            | -7.35                | -6.85                | 4.0                 | 1.0            | -1.5732586154290416 | 0.5            | OUTLIER_MARKET                                    | X-REVIEW | EDGE_DK=-7.35\|EDGE_MKT=-6.85\|OUTLIER_MKT\|RATINGS_Z=-1.57                 |
| 2025-12-30 | Independence Bowl    | Coastal Carolina      | Louisiana Tech | -8.5           | -2.57            | 5.93                 | 6.43                 | -9.0                | -2.0           | 1.0598155438064714  | 0.75           | OUTLIER_MARKET                                    | X-REVIEW | EDGE_DK=5.93\|EDGE_MKT=6.43\|OUTLIER_MKT\|RATINGS_Z=1.06                    |
| 2026-01-02 | Holiday Bowl         | Arizona               | SMU            | 3.0            | -3.18            | -6.18                | -6.18                | 3.0                 | 1.5            | -1.0650922760568124 | 0.5            | OUTLIER_MARKET\|HIGH_STD_RATINGS                  | X-REVIEW | EDGE_DK=-6.18\|EDGE_MKT=-6.18\|OUTLIER_MKT\|RATINGS_Z=-1.07                 |
| 2025-12-30 | Music City Bowl      | Tennessee             | Illinois       | 2.5            | -2.95            | -5.45                | -5.45                | 2.5                 | -4.0           | -3.907969321307602  | 0.0            | OUTLIER_MARKET\|OUTLIER_RATINGS\|BIG_MOVE         | X-REVIEW | EDGE_DK=-5.45\|EDGE_MKT=-5.45\|OUTLIER_MKT\|BIG_MOVE=-4.00\|RATINGS_Z=-3.91 |
| 2025-12-26 | First Responder Bowl | Florida International | UTSA           | -9.5           | -2.77            | 6.73                 | 5.73                 | -8.5                | 0.0            | 1.6831857377025545  | 0.5            | OUTLIER_MARKET                                    | A        | EDGE_DK=6.73\|EDGE_MKT=5.73\|OUTLIER_MKT\|RATINGS_Z=1.68                    |
| 2025-12-17 | 68 Ventures Bowl     | Louisiana             | Delaware       | 3.0            | -2.48            | -5.48                | -5.48                | 3.0                 | -0.5           | -2.8167313527790716 | 0.25           | OUTLIER_MARKET\|OUTLIER_RATINGS                   | A        | EDGE_DK=-5.48\|EDGE_MKT=-5.48\|OUTLIER_MKT\|RATINGS_Z=-2.82                 |
| 2025-12-31 | Citrus Bowl          | Michigan              | Texas          | -7.5           | -2.93            | 4.57                 | 4.57                 | -7.5                | -3.0           | 0.8924932743176762  | 1.0            | OUTLIER_MARKET\|BIG_MOVE                          | A        | EDGE_DK=4.57\|EDGE_MKT=4.57\|OUTLIER_MKT\|BIG_MOVE=-3.00\|RATINGS_Z=0.89    |
| 2025-12-19 | CFP First Round      | Alabama               | Oklahoma       | 1.5            | -3.14            | -4.640000000000001   | -4.140000000000001   | 1.0                 | -1.0           | -0.6495191183225897 | 0.75           | OUTLIER_MARKET                                    | A        | EDGE_DK=-4.64\|EDGE_MKT=-4.14\|OUTLIER_MKT\|RATINGS_Z=-0.65                 |
| 2025-12-24 | Hawai'i Bowl         | California            | Hawai'i        | 1.5            | -2.59            | -4.09                | -4.09                | 1.5                 | -1.0           | -1.280295775368735  | 0.5            | OUTLIER_MARKET                                    | A        | EDGE_DK=-4.09\|EDGE_MKT=-4.09\|OUTLIER_MKT\|RATINGS_Z=-1.28                 |
| 2025-12-27 | Pinstripe Bowl       | Penn State            | Clemson        | -3.5           | -2.99            | 0.5099999999999998   | 0.5099999999999998   | -3.5                | -4.5           | -1.6406478682202377 | 1.0            | BIG_MOVE                                          | X-REVIEW | EDGE_DK=0.51\|EDGE_MKT=0.51\|BIG_MOVE=-4.50\|RATINGS_Z=-1.64                |
| 2025-12-17 | Cure Bowl            | Old Dominion          | South Florida  | -2.5           | -3.4             | -0.8999999999999999  | -0.3999999999999999  | -3.0                | 4.5            | 4.593172192975621   | 1.0            | OUTLIER_RATINGS\|BIG_MOVE                         | X-REVIEW | EDGE_DK=-0.90\|EDGE_MKT=-0.40\|BIG_MOVE=4.50\|RATINGS_Z=4.59                |
| 2025-12-22 | Potato Bowl          | Washington State      | Utah State     | -2.5           | -2.71            | -0.20999999999999996 | -0.20999999999999996 | -2.5                | -3.5           | -4.03022920735504   | 0.0            | OUTLIER_RATINGS\|BIG_MOVE                         | C        | EDGE_DK=-0.21\|EDGE_MKT=-0.21\|BIG_MOVE=-3.50\|RATINGS_Z=-4.03              |

## Tier Summary

| C  | X-REVIEW | A | B |
| -- | -------- | - | - |
| 17 | 13       | 5 | 2 |

## Game-By-Game Notes

### 2025-12-17 — Louisiana @ Delaware (68 Ventures Bowl)
- Neutral: `True` | Tier: `A` | Reasons: `EDGE_DK=-5.48|EDGE_MKT=-5.48|OUTLIER_MKT|RATINGS_Z=-2.82`
- DK (home spread): `3.00` | Your (home spread): `-2.48`
- DK edge: `-5.48` | Market edge: `-5.48`
- Ratings: mean `4.88` std `2.61` z `-2.82`
- Agreement (panel): `0.25` | Disagree: `linesag, linemassey, lineelo`
- Market: open `3.50` current `3.00` move `-0.50` CLV `TOWARD_YOU`
- Flags: `OUTLIER_MARKET|OUTLIER_RATINGS` | Robust edge: `2.10`

| lineopen | line | lineavg     | linemedian | linesag | linemassey | lineelo     | linemoore |
| -------- | ---- | ----------- | ---------- | ------- | ---------- | ----------- | --------- |
| 3.5      | 3.0  | 4.006348999 | 3.4        | 6.37    | 8.16       | 3.709334409 | 1.28      |

| your_vs_median     | your_vs_linesag | your_vs_linemassey | your_vs_lineelo    | your_vs_linemoore |
| ------------------ | --------------- | ------------------ | ------------------ | ----------------- |
| -7.519667204500001 | -8.85           | -10.64             | -6.189334409000001 | -3.76             |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-17 — Old Dominion @ South Florida (Cure Bowl)
- Neutral: `True` | Tier: `X-REVIEW` | Reasons: `EDGE_DK=-0.90|EDGE_MKT=-0.40|BIG_MOVE=4.50|RATINGS_Z=4.59`
- DK (home spread): `-2.50` | Your (home spread): `-3.40`
- DK edge: `-0.90` | Market edge: `-0.40`
- Ratings: mean `-9.25` std `1.27` z `4.59`
- Agreement (panel): `1.00`
- Market: open `-7.50` current `-3.00` move `4.50` CLV `TOWARD_YOU`
- Flags: `OUTLIER_RATINGS|BIG_MOVE` | Robust edge: `0.71`

| lineopen | line | lineavg       | linemedian | linesag | linemassey | lineelo      | linemoore |
| -------- | ---- | ------------- | ---------- | ------- | ---------- | ------------ | --------- |
| -7.5     | -3.0 | -8.4725487191 | -8.675     | -9.2    | -7.5       | -9.202252534 | -11.1     |

| your_vs_median    | your_vs_linesag   | your_vs_linemassey | your_vs_lineelo   | your_vs_linemoore |
| ----------------- | ----------------- | ------------------ | ----------------- | ----------------- |
| 5.801126266999999 | 5.799999999999999 | 4.1                | 5.802252533999999 | 7.699999999999999 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-18 — Missouri State @ Arkansas State (Xbox Bowl)
- Neutral: `True` | Tier: `C` | Reasons: `EDGE_DK=-0.84`
- DK (home spread): `-1.50` | Your (home spread): `-2.34`
- DK edge: `-0.84` | Market edge: `nan`
- Agreement (panel): ``
- Flags: `` | Robust edge: `NA`

| lineopen | line | lineavg | linemedian | linesag | linemassey | lineelo | linemoore |
| -------- | ---- | ------- | ---------- | ------- | ---------- | ------- | --------- |
|          |      |         |            |         |            |         |           |

| your_vs_median | your_vs_linesag | your_vs_linemassey | your_vs_lineelo | your_vs_linemoore |
| -------------- | --------------- | ------------------ | --------------- | ----------------- |
|                |                 |                    |                 |                   |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-19 — Alabama @ Oklahoma (CFP First Round)
- Neutral: `False` | Tier: `A` | Reasons: `EDGE_DK=-4.64|EDGE_MKT=-4.14|OUTLIER_MKT|RATINGS_Z=-0.65`
- DK (home spread): `1.50` | Your (home spread): `-3.14`
- DK edge: `-4.64` | Market edge: `-4.14`
- Ratings: mean `-1.48` std `2.55` z `-0.65`
- Agreement (panel): `0.75` | Disagree: `linemassey`
- Market: open `2.00` current `1.00` move `-1.00` CLV `TOWARD_YOU`
- Flags: `OUTLIER_MARKET` | Robust edge: `1.82`

| lineopen | line | lineavg       | linemedian | linesag | linemassey | lineelo      | linemoore |
| -------- | ---- | ------------- | ---------- | ------- | ---------- | ------------ | --------- |
| 2.0      | 1.0  | -1.8997171742 | -1.7       | -1.14   | 2.49       | -4.289692199 | -2.99     |

| your_vs_median      | your_vs_linesag | your_vs_linemassey | your_vs_lineelo | your_vs_linemoore   |
| ------------------- | --------------- | ------------------ | --------------- | ------------------- |
| -1.0750000000000002 | -2.0            | -5.630000000000001 | 1.149692199     | -0.1499999999999999 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-19 — Memphis @ NC State (Gasparilla Bowl)
- Neutral: `True` | Tier: `C` | Reasons: `EDGE_DK=1.63|EDGE_MKT=1.63|RATINGS_Z=0.19`
- DK (home spread): `-4.50` | Your (home spread): `-2.87`
- DK edge: `1.63` | Market edge: `1.63`
- Ratings: mean `-3.30` std `2.21` z `0.19`
- Agreement (panel): `0.75` | Disagree: `linesag`
- Market: open `-5.50` current `-4.50` move `1.00` CLV `TOWARD_YOU`
- Flags: `` | Robust edge: `0.74`

| lineopen | line | lineavg       | linemedian | linesag | linemassey | lineelo      | linemoore |
| -------- | ---- | ------------- | ---------- | ------- | ---------- | ------------ | --------- |
| -5.5     | -4.5 | -2.3896834356 | -2.8       | -6.02   | 0.02       | -4.278950925 | -2.91     |

| your_vs_median     | your_vs_linesag    | your_vs_linemassey | your_vs_lineelo | your_vs_linemoore    |
| ------------------ | ------------------ | ------------------ | --------------- | -------------------- |
| 0.7244754625000001 | 3.1499999999999995 | -2.89              | 1.408950925     | 0.040000000000000036 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-19 — Kennesaw State @ Western Michigan (Myrtle Beach Bowl)
- Neutral: `True` | Tier: `C` | Reasons: `EDGE_DK=0.81`
- DK (home spread): `-3.50` | Your (home spread): `-2.69`
- DK edge: `0.81` | Market edge: `nan`
- Agreement (panel): ``
- Flags: `` | Robust edge: `NA`

| lineopen | line | lineavg | linemedian | linesag | linemassey | lineelo | linemoore |
| -------- | ---- | ------- | ---------- | ------- | ---------- | ------- | --------- |
|          |      |         |            |         |            |         |           |

| your_vs_median | your_vs_linesag | your_vs_linemassey | your_vs_lineelo | your_vs_linemoore |
| -------------- | --------------- | ------------------ | --------------- | ----------------- |
|                |                 |                    |                 |                   |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-20 — Miami @ Texas A&M (CFP First Round)
- Neutral: `False` | Tier: `C` | Reasons: `EDGE_DK=0.28`
- DK (home spread): `-3.50` | Your (home spread): `-3.22`
- DK edge: `0.28` | Market edge: `nan`
- Agreement (panel): ``
- Flags: `` | Robust edge: `NA`

| lineopen | line | lineavg | linemedian | linesag | linemassey | lineelo | linemoore |
| -------- | ---- | ------- | ---------- | ------- | ---------- | ------- | --------- |
|          |      |         |            |         |            |         |           |

| your_vs_median | your_vs_linesag | your_vs_linemassey | your_vs_lineelo | your_vs_linemoore |
| -------------- | --------------- | ------------------ | --------------- | ----------------- |
|                |                 |                    |                 |                   |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-20 — Tulane @ Ole Miss (CFP First Round)
- Neutral: `False` | Tier: `C` | Reasons: `EDGE_DK=14.38`
- DK (home spread): `-17.50` | Your (home spread): `-3.12`
- DK edge: `14.38` | Market edge: `nan`
- Agreement (panel): ``
- Flags: `` | Robust edge: `NA`

| lineopen | line | lineavg | linemedian | linesag | linemassey | lineelo | linemoore |
| -------- | ---- | ------- | ---------- | ------- | ---------- | ------- | --------- |
|          |      |         |            |         |            |         |           |

| your_vs_median | your_vs_linesag | your_vs_linemassey | your_vs_lineelo | your_vs_linemoore |
| -------------- | --------------- | ------------------ | --------------- | ----------------- |
|                |                 |                    |                 |                   |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-20 — James Madison @ Oregon (CFP First Round)
- Neutral: `False` | Tier: `X-REVIEW` | Reasons: `EDGE_DK=17.37|EDGE_MKT=17.87|OUTLIER_MKT|RATINGS_Z=2.40`
- DK (home spread): `-21.00` | Your (home spread): `-3.63`
- DK edge: `17.37` | Market edge: `17.87`
- Ratings: mean `-17.08` std `5.61` z `2.40`
- Agreement (panel): `0.75` | Disagree: `linemassey`
- Market: open `-21.00` current `-21.50` move `-0.50` CLV `AWAY_FROM_YOU`
- Flags: `OUTLIER_MARKET|OUTLIER_RATINGS|HIGH_STD_RATINGS` | Robust edge: `3.10`

| lineopen | line  | lineavg       | linemedian | linesag | linemassey | lineelo       | linemoore |
| -------- | ----- | ------------- | ---------- | ------- | ---------- | ------------- | --------- |
| -21.0    | -21.5 | -18.620270119 | -20.08     | -18.39  | -24.66     | -16.306133845 | -8.96     |

| your_vs_median     | your_vs_linesag    | your_vs_linemassey | your_vs_lineelo    | your_vs_linemoore |
| ------------------ | ------------------ | ------------------ | ------------------ | ----------------- |
| 13.718066922500004 | 14.760000000000002 | 21.03              | 12.676133845000003 | 5.330000000000001 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-22 — Washington State @ Utah State (Potato Bowl)
- Neutral: `True` | Tier: `C` | Reasons: `EDGE_DK=-0.21|EDGE_MKT=-0.21|BIG_MOVE=-3.50|RATINGS_Z=-4.03`
- DK (home spread): `-2.50` | Your (home spread): `-2.71`
- DK edge: `-0.21` | Market edge: `-0.21`
- Ratings: mean `5.07` std `1.93` z `-4.03`
- Agreement (panel): `0.00` | Disagree: `linesag, linemassey, lineelo, linemoore`
- Market: open `1.00` current `-2.50` move `-3.50` CLV `TOWARD_YOU`
- Flags: `OUTLIER_RATINGS|BIG_MOVE` | Robust edge: `0.11`

| lineopen | line | lineavg     | linemedian  | linesag | linemassey | lineelo     | linemoore |
| -------- | ---- | ----------- | ----------- | ------- | ---------- | ----------- | --------- |
| 1.0      | -2.5 | 4.262443163 | 4.990707109 | 5.77    | 7.56       | 4.743666999 | 2.22      |

| your_vs_median | your_vs_linesag | your_vs_linemassey | your_vs_lineelo | your_vs_linemoore |
| -------------- | --------------- | ------------------ | --------------- | ----------------- |
| -7.9668334995  | -8.48           | -10.27             | -7.453666999    | -4.93             |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-23 — Toledo @ Louisville (Boca Raton Bowl)
- Neutral: `True` | Tier: `B` | Reasons: `EDGE_DK=3.22|EDGE_MKT=3.72|RATINGS_Z=0.57`
- DK (home spread): `-6.50` | Your (home spread): `-3.28`
- DK edge: `3.22` | Market edge: `3.72`
- Ratings: mean `-6.04` std `4.79` z `0.57`
- Agreement (panel): `0.50` | Disagree: `linesag, linemassey`
- Market: open `-9.50` current `-7.00` move `2.50` CLV `TOWARD_YOU`
- Flags: `HIGH_STD_RATINGS` | Robust edge: `0.67`

| lineopen | line | lineavg       | linemedian | linesag | linemassey | lineelo      | linemoore |
| -------- | ---- | ------------- | ---------- | ------- | ---------- | ------------ | --------- |
| -9.5     | -7.0 | -5.9781326148 | -5.995     | -8.02   | -12.87     | -2.712957008 | -0.54     |

| your_vs_median | your_vs_linesag | your_vs_linemassey | your_vs_lineelo     | your_vs_linemoore   |
| -------------- | --------------- | ------------------ | ------------------- | ------------------- |
| 2.086478504    | 4.74            | 9.59               | -0.5670429919999997 | -2.7399999999999998 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-23 — UNLV @ Ohio (Frisco Bowl)
- Neutral: `True` | Tier: `X-REVIEW` | Reasons: `EDGE_DK=-8.42|EDGE_MKT=-7.92|OUTLIER_MKT|RATINGS_Z=-6.95`
- DK (home spread): `5.50` | Your (home spread): `-2.92`
- DK edge: `-8.42` | Market edge: `-7.92`
- Ratings: mean `4.29` std `1.04` z `-6.95`
- Agreement (panel): `1.00`
- Market: open `4.00` current `5.00` move `1.00` CLV `AWAY_FROM_YOU`
- Flags: `OUTLIER_MARKET|OUTLIER_RATINGS` | Robust edge: `8.12`

| lineopen | line | lineavg     | linemedian | linesag | linemassey | lineelo     | linemoore |
| -------- | ---- | ----------- | ---------- | ------- | ---------- | ----------- | --------- |
| 4.0      | 5.0  | 4.917149225 | 5.165      | 5.04    | 4.59       | 5.009477106 | 2.52      |

| your_vs_median | your_vs_linesag | your_vs_linemassey | your_vs_lineelo | your_vs_linemoore   |
| -------------- | --------------- | ------------------ | --------------- | ------------------- |
| -7.719738553   | -7.96           | -7.51              | -7.929477106    | -5.4399999999999995 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-23 — Western Kentucky @ Southern Miss (New Orleans Bowl)
- Neutral: `True` | Tier: `X-REVIEW` | Reasons: `EDGE_DK=-7.35|EDGE_MKT=-6.85|OUTLIER_MKT|RATINGS_Z=-1.57`
- DK (home spread): `4.50` | Your (home spread): `-2.85`
- DK edge: `-7.35` | Market edge: `-6.85`
- Ratings: mean `3.33` std `3.93` z `-1.57`
- Agreement (panel): `0.50` | Disagree: `linemassey, lineelo`
- Market: open `3.00` current `4.00` move `1.00` CLV `AWAY_FROM_YOU`
- Flags: `OUTLIER_MARKET` | Robust edge: `1.87`

| lineopen | line | lineavg     | linemedian | linesag | linemassey | lineelo     | linemoore |
| -------- | ---- | ----------- | ---------- | ------- | ---------- | ----------- | --------- |
| 3.0      | 4.0  | 3.151152904 | 3.075      | 2.47    | 8.31       | 4.979566329 | -2.45     |

| your_vs_median     | your_vs_linesag | your_vs_linemassey | your_vs_lineelo | your_vs_linemoore   |
| ------------------ | --------------- | ------------------ | --------------- | ------------------- |
| -6.574783164499999 | -5.32           | -11.16             | -7.829566329    | -0.3999999999999999 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-24 — California @ Hawai'i (Hawai'i Bowl)
- Neutral: `False` | Tier: `A` | Reasons: `EDGE_DK=-4.09|EDGE_MKT=-4.09|OUTLIER_MKT|RATINGS_Z=-1.28`
- DK (home spread): `1.50` | Your (home spread): `-2.59`
- DK edge: `-4.09` | Market edge: `-4.09`
- Ratings: mean `1.22` std `2.98` z `-1.28`
- Agreement (panel): `0.50` | Disagree: `linemassey, linemoore`
- Market: open `2.50` current `1.50` move `-1.00` CLV `TOWARD_YOU`
- Flags: `OUTLIER_MARKET` | Robust edge: `1.37`

| lineopen | line | lineavg     | linemedian | linesag | linemassey | lineelo      | linemoore |
| -------- | ---- | ----------- | ---------- | ------- | ---------- | ------------ | --------- |
| 2.5      | 1.5  | 0.396512001 | 0.221      | -0.05   | 5.54       | -2.599491893 | 2.0       |

| your_vs_median | your_vs_linesag | your_vs_linemassey | your_vs_lineelo      | your_vs_linemoore |
| -------------- | --------------- | ------------------ | -------------------- | ----------------- |
| -3.565         | -2.54           | -8.129999999999999 | 0.009491893000000307 | -4.59             |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-26 — Florida International @ UTSA (First Responder Bowl)
- Neutral: `True` | Tier: `A` | Reasons: `EDGE_DK=6.73|EDGE_MKT=5.73|OUTLIER_MKT|RATINGS_Z=1.68`
- DK (home spread): `-9.50` | Your (home spread): `-2.77`
- DK edge: `6.73` | Market edge: `5.73`
- Ratings: mean `-8.91` std `3.65` z `1.68`
- Agreement (panel): `0.50` | Disagree: `linesag, linemassey`
- Market: open `-8.50` current `-8.50` move `0.00` CLV `NEUTRAL`
- Flags: `OUTLIER_MARKET` | Robust edge: `1.84`

| lineopen | line | lineavg       | linemedian | linesag | linemassey | lineelo      | linemoore |
| -------- | ---- | ------------- | ---------- | ------- | ---------- | ------------ | --------- |
| -8.5     | -8.5 | -9.9575675047 | -9.85      | -10.37  | -14.22     | -5.571917626 | -5.48     |

| your_vs_median | your_vs_linesag | your_vs_linemassey | your_vs_lineelo    | your_vs_linemoore  |
| -------------- | --------------- | ------------------ | ------------------ | ------------------ |
| 5.200958813    | 7.6             | 11.450000000000001 | 2.8019176260000003 | 2.7100000000000004 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-26 — Central Michigan @ Northwestern (GameAbove Sports Bowl)
- Neutral: `True` | Tier: `C` | Reasons: `EDGE_DK=7.81`
- DK (home spread): `-10.50` | Your (home spread): `-2.69`
- DK edge: `7.81` | Market edge: `nan`
- Agreement (panel): ``
- Flags: `` | Robust edge: `NA`

| lineopen | line | lineavg | linemedian | linesag | linemassey | lineelo | linemoore |
| -------- | ---- | ------- | ---------- | ------- | ---------- | ------- | --------- |
|          |      |         |            |         |            |         |           |

| your_vs_median | your_vs_linesag | your_vs_linemassey | your_vs_lineelo | your_vs_linemoore |
| -------------- | --------------- | ------------------ | --------------- | ----------------- |
|                |                 |                    |                 |                   |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-26 — New Mexico @ Minnesota (Rate Bowl)
- Neutral: `True` | Tier: `C` | Reasons: `EDGE_DK=-0.15|EDGE_MKT=-0.15|RATINGS_Z=0.77`
- DK (home spread): `-2.50` | Your (home spread): `-2.65`
- DK edge: `-0.15` | Market edge: `-0.15`
- Ratings: mean `-5.93` std `4.24` z `0.77`
- Agreement (panel): `0.75` | Disagree: `lineelo`
- Market: open `-3.00` current `-2.50` move `0.50` CLV `TOWARD_YOU`
- Flags: `HIGH_STD_RATINGS` | Robust edge: `0.04`

| lineopen | line | lineavg       | linemedian | linesag | linemassey | lineelo      | linemoore |
| -------- | ---- | ------------- | ---------- | ------- | ---------- | ------------ | --------- |
| -3.0     | -2.5 | -3.8032413368 | -2.582     | -8.44   | -11.41     | -0.608899505 | -3.25     |

| your_vs_median | your_vs_linesag   | your_vs_linemassey | your_vs_lineelo | your_vs_linemoore  |
| -------------- | ----------------- | ------------------ | --------------- | ------------------ |
| 3.195          | 5.789999999999999 | 8.76               | -2.041100495    | 0.6000000000000001 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-27 — Miami (OH) @ Fresno State (Arizona Bowl)
- Neutral: `True` | Tier: `C` | Reasons: `EDGE_DK=1.80`
- DK (home spread): `-4.50` | Your (home spread): `-2.70`
- DK edge: `1.80` | Market edge: `nan`
- Agreement (panel): ``
- Flags: `` | Robust edge: `NA`

| lineopen | line | lineavg | linemedian | linesag | linemassey | lineelo | linemoore |
| -------- | ---- | ------- | ---------- | ------- | ---------- | ------- | --------- |
|          |      |         |            |         |            |         |           |

| your_vs_median | your_vs_linesag | your_vs_linemassey | your_vs_lineelo | your_vs_linemoore |
| -------------- | --------------- | ------------------ | --------------- | ----------------- |
|                |                 |                    |                 |                   |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-27 — UConn @ Army (Fenway Bowl)
- Neutral: `True` | Tier: `C` | Reasons: `EDGE_DK=5.68`
- DK (home spread): `-8.50` | Your (home spread): `-2.82`
- DK edge: `5.68` | Market edge: `nan`
- Agreement (panel): ``
- Flags: `` | Robust edge: `NA`

| lineopen | line | lineavg | linemedian | linesag | linemassey | lineelo | linemoore |
| -------- | ---- | ------- | ---------- | ------- | ---------- | ------- | --------- |
|          |      |         |            |         |            |         |           |

| your_vs_median | your_vs_linesag | your_vs_linemassey | your_vs_lineelo | your_vs_linemoore |
| -------------- | --------------- | ------------------ | --------------- | ----------------- |
|                |                 |                    |                 |                   |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-27 — Virginia @ Missouri (Gator Bowl)
- Neutral: `True` | Tier: `B` | Reasons: `EDGE_DK=3.86|EDGE_MKT=3.36|RATINGS_Z=2.00`
- DK (home spread): `-7.00` | Your (home spread): `-3.14`
- DK edge: `3.86` | Market edge: `3.36`
- Ratings: mean `-6.98` std `1.92` z `2.00`
- Agreement (panel): `0.50` | Disagree: `linemassey, lineelo`
- Market: open `-7.00` current `-6.50` move `0.50` CLV `TOWARD_YOU`
- Flags: `` | Robust edge: `2.01`

| lineopen | line | lineavg       | linemedian | linesag | linemassey | lineelo      | linemoore |
| -------- | ---- | ------------- | ---------- | ------- | ---------- | ------------ | --------- |
| -7.0     | -6.5 | -5.5508217241 | -5.2915    | -5.92   | -9.18      | -8.417849229 | -4.39     |

| your_vs_median    | your_vs_linesag | your_vs_linemassey | your_vs_lineelo   | your_vs_linemoore  |
| ----------------- | --------------- | ------------------ | ----------------- | ------------------ |
| 4.028924614499999 | 2.78            | 6.039999999999999  | 5.277849228999999 | 1.2499999999999996 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-27 — Pittsburgh @ East Carolina (Military Bowl)
- Neutral: `True` | Tier: `X-REVIEW` | Reasons: `EDGE_DK=-11.56|EDGE_MKT=-10.06|OUTLIER_MKT|RATINGS_Z=-2.61`
- DK (home spread): `8.50` | Your (home spread): `-3.06`
- DK edge: `-11.56` | Market edge: `-10.06`
- Ratings: mean `4.85` std `3.03` z `-2.61`
- Agreement (panel): `0.75` | Disagree: `linesag`
- Market: open `6.00` current `7.00` move `1.00` CLV `AWAY_FROM_YOU`
- Flags: `OUTLIER_MARKET|OUTLIER_RATINGS` | Robust edge: `3.82`

| lineopen | line | lineavg     | linemedian  | linesag | linemassey | lineelo     | linemoore |
| -------- | ---- | ----------- | ----------- | ------- | ---------- | ----------- | --------- |
| 6.0      | 7.0  | 4.632879869 | 5.027318292 | 8.76    | 6.09       | 4.086359493 | 0.46      |

| your_vs_median | your_vs_linesag | your_vs_linemassey | your_vs_lineelo | your_vs_linemoore |
| -------------- | --------------- | ------------------ | --------------- | ----------------- |
| -8.1481797465  | -11.82          | -9.15              | -7.146359493    | -3.52             |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-27 — North Texas @ San Diego State (New Mexico Bowl)
- Neutral: `True` | Tier: `C` | Reasons: `EDGE_DK=-6.20`
- DK (home spread): `3.00` | Your (home spread): `-3.20`
- DK edge: `-6.20` | Market edge: `nan`
- Agreement (panel): ``
- Flags: `` | Robust edge: `NA`

| lineopen | line | lineavg | linemedian | linesag | linemassey | lineelo | linemoore |
| -------- | ---- | ------- | ---------- | ------- | ---------- | ------- | --------- |
|          |      |         |            |         |            |         |           |

| your_vs_median | your_vs_linesag | your_vs_linemassey | your_vs_lineelo | your_vs_linemoore |
| -------------- | --------------- | ------------------ | --------------- | ----------------- |
|                |                 |                    |                 |                   |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-27 — Penn State @ Clemson (Pinstripe Bowl)
- Neutral: `True` | Tier: `X-REVIEW` | Reasons: `EDGE_DK=0.51|EDGE_MKT=0.51|BIG_MOVE=-4.50|RATINGS_Z=-1.64`
- DK (home spread): `-3.50` | Your (home spread): `-2.99`
- DK edge: `0.51` | Market edge: `0.51`
- Ratings: mean `3.56` std `3.99` z `-1.64`
- Agreement (panel): `1.00`
- Market: open `1.00` current `-3.50` move `-4.50` CLV `TOWARD_YOU`
- Flags: `BIG_MOVE` | Robust edge: `0.13`

| lineopen | line | lineavg     | linemedian | linesag | linemassey | lineelo     | linemoore |
| -------- | ---- | ----------- | ---------- | ------- | ---------- | ----------- | --------- |
| 1.0      | -3.5 | 4.169582882 | 4.215      | 4.5     | 8.47       | 3.945146338 | -2.66     |

| your_vs_median     | your_vs_linesag | your_vs_linemassey | your_vs_lineelo | your_vs_linemoore    |
| ------------------ | --------------- | ------------------ | --------------- | -------------------- |
| -7.212573169000001 | -7.49           | -11.46             | -6.935146338    | -0.33000000000000007 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-27 — Georgia Tech @ BYU (Pop-Tarts Bowl)
- Neutral: `True` | Tier: `C` | Reasons: `EDGE_DK=1.46|EDGE_MKT=1.46|RATINGS_Z=1.82`
- DK (home spread): `-4.50` | Your (home spread): `-3.04`
- DK edge: `1.46` | Market edge: `1.46`
- Ratings: mean `-9.96` std `3.80` z `1.82`
- Agreement (panel): `0.00` | Disagree: `linesag, linemassey, lineelo, linemoore`
- Market: open `-2.50` current `-4.50` move `-2.00` CLV `AWAY_FROM_YOU`
- Flags: `` | Robust edge: `0.38`

| lineopen | line | lineavg       | linemedian | linesag | linemassey | lineelo       | linemoore |
| -------- | ---- | ------------- | ---------- | ------- | ---------- | ------------- | --------- |
| -2.5     | -4.5 | -8.4003641538 | -8.46      | -4.57   | -8.89      | -15.041773596 | -11.32    |

| your_vs_median | your_vs_linesag    | your_vs_linemassey | your_vs_lineelo | your_vs_linemoore |
| -------------- | ------------------ | ------------------ | --------------- | ----------------- |
| 7.065          | 1.5300000000000002 | 5.8500000000000005 | 12.001773596    | 8.280000000000001 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-27 — LSU @ Houston (Texas Bowl)
- Neutral: `True` | Tier: `C` | Reasons: `EDGE_DK=0.35|EDGE_MKT=0.35|RATINGS_Z=-5.64`
- DK (home spread): `-3.00` | Your (home spread): `-2.65`
- DK edge: `0.35` | Market edge: `0.35`
- Ratings: mean `4.20` std `1.21` z `-5.64`
- Agreement (panel): `1.00`
- Market: open `-3.00` current `-3.00` move `0.00` CLV `NEUTRAL`
- Flags: `OUTLIER_RATINGS` | Robust edge: `0.29`

| lineopen | line | lineavg    | linemedian  | linesag | linemassey | lineelo     | linemoore |
| -------- | ---- | ---------- | ----------- | ------- | ---------- | ----------- | --------- |
| -3.0     | -3.0 | 3.53078727 | 3.800317038 | 5.32    | 5.02       | 2.209484019 | 4.24      |

| your_vs_median     | your_vs_linesag    | your_vs_linemassey | your_vs_lineelo | your_vs_linemoore  |
| ------------------ | ------------------ | ------------------ | --------------- | ------------------ |
| -7.279999999999999 | -7.970000000000001 | -7.67              | -4.859484019    | -6.890000000000001 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-29 — Georgia Southern @ App State (Birmingham Bowl)
- Neutral: `True` | Tier: `X-REVIEW` | Reasons: `EDGE_DK=-9.38|EDGE_MKT=-6.88|OUTLIER_MKT|RATINGS_Z=-2.17`
- DK (home spread): `7.00` | Your (home spread): `-2.38`
- DK edge: `-9.38` | Market edge: `-6.88`
- Ratings: mean `2.68` std `2.34` z `-2.17`
- Agreement (panel): `1.00`
- Market: open `2.00` current `4.50` move `2.50` CLV `AWAY_FROM_YOU`
- Flags: `OUTLIER_MARKET|OUTLIER_RATINGS` | Robust edge: `4.01`

| lineopen | line | lineavg     | linemedian | linesag | linemassey | lineelo     | linemoore |
| -------- | ---- | ----------- | ---------- | ------- | ---------- | ----------- | --------- |
| 2.0      | 4.5  | 1.617014225 | 1.95       | 3.06    | -0.83      | 2.744878853 | 5.74      |

| your_vs_median | your_vs_linesag     | your_vs_linemassey  | your_vs_lineelo | your_vs_linemoore  |
| -------------- | ------------------- | ------------------- | --------------- | ------------------ |
| -5.2824394265  | -5.4399999999999995 | -1.5499999999999998 | -5.124878853    | -8.120000000000001 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-30 — USC @ TCU (Alamo Bowl)
- Neutral: `True` | Tier: `X-REVIEW` | Reasons: `EDGE_DK=-7.57|EDGE_MKT=-7.57|OUTLIER_MKT|RATINGS_Z=-5.01`
- DK (home spread): `4.50` | Your (home spread): `-3.07`
- DK edge: `-7.57` | Market edge: `-7.57`
- Ratings: mean `5.73` std `1.76` z `-5.01`
- Agreement (panel): `0.25` | Disagree: `linesag, linemassey, lineelo`
- Market: open `5.50` current `4.50` move `-1.00` CLV `TOWARD_YOU`
- Flags: `OUTLIER_MARKET|OUTLIER_RATINGS` | Robust edge: `4.31`

| lineopen | line | lineavg     | linemedian | linesag | linemassey | lineelo     | linemoore |
| -------- | ---- | ----------- | ---------- | ------- | ---------- | ----------- | --------- |
| 5.5      | 4.5  | 7.862746603 | 7.945      | 7.18    | 6.85       | 6.147686169 | 2.76      |

| your_vs_median | your_vs_linesag | your_vs_linemassey | your_vs_lineelo | your_vs_linemoore |
| -------------- | --------------- | ------------------ | --------------- | ----------------- |
| -9.5688430845  | -10.25          | -9.92              | -9.217686169    | -5.83             |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-30 — Coastal Carolina @ Louisiana Tech (Independence Bowl)
- Neutral: `True` | Tier: `X-REVIEW` | Reasons: `EDGE_DK=5.93|EDGE_MKT=6.43|OUTLIER_MKT|RATINGS_Z=1.06`
- DK (home spread): `-8.50` | Your (home spread): `-2.57`
- DK edge: `5.93` | Market edge: `6.43`
- Ratings: mean `-6.21` std `3.44` z `1.06`
- Agreement (panel): `0.75` | Disagree: `linemoore`
- Market: open `-7.00` current `-9.00` move `-2.00` CLV `AWAY_FROM_YOU`
- Flags: `OUTLIER_MARKET` | Robust edge: `1.72`

| lineopen | line | lineavg       | linemedian | linesag | linemassey | lineelo      | linemoore |
| -------- | ---- | ------------- | ---------- | ------- | ---------- | ------------ | --------- |
| -7.0     | -9.0 | -7.6520938087 | -7.49      | -7.27   | -4.32      | -2.038003874 | -11.23    |

| your_vs_median | your_vs_linesag   | your_vs_linemassey | your_vs_lineelo     | your_vs_linemoore |
| -------------- | ----------------- | ------------------ | ------------------- | ----------------- |
| 3.225          | 4.699999999999999 | 1.7500000000000004 | -0.5319961259999997 | 8.66              |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-30 — Tennessee @ Illinois (Music City Bowl)
- Neutral: `True` | Tier: `X-REVIEW` | Reasons: `EDGE_DK=-5.45|EDGE_MKT=-5.45|OUTLIER_MKT|BIG_MOVE=-4.00|RATINGS_Z=-3.91`
- DK (home spread): `2.50` | Your (home spread): `-2.95`
- DK edge: `-5.45` | Market edge: `-5.45`
- Ratings: mean `5.95` std `2.28` z `-3.91`
- Agreement (panel): `0.00` | Disagree: `linesag, linemassey, lineelo, linemoore`
- Market: open `6.50` current `2.50` move `-4.00` CLV `TOWARD_YOU`
- Flags: `OUTLIER_MARKET|OUTLIER_RATINGS|BIG_MOVE` | Robust edge: `2.39`

| lineopen | line | lineavg     | linemedian  | linesag | linemassey | lineelo     | linemoore |
| -------- | ---- | ----------- | ----------- | ------- | ---------- | ----------- | --------- |
| 6.5      | 2.5  | 3.675062018 | 3.618783245 | 6.06    | 9.59       | 3.620166489 | 4.52      |

| your_vs_median     | your_vs_linesag | your_vs_linemassey | your_vs_lineelo | your_vs_linemoore |
| ------------------ | --------------- | ------------------ | --------------- | ----------------- |
| -8.239999999999998 | -9.01           | -12.54             | -6.570166489    | -7.47             |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-31 — Michigan @ Texas (Citrus Bowl)
- Neutral: `True` | Tier: `A` | Reasons: `EDGE_DK=4.57|EDGE_MKT=4.57|OUTLIER_MKT|BIG_MOVE=-3.00|RATINGS_Z=0.89`
- DK (home spread): `-7.50` | Your (home spread): `-2.93`
- DK edge: `4.57` | Market edge: `4.57`
- Ratings: mean `-4.78` std `2.08` z `0.89`
- Agreement (panel): `1.00`
- Market: open `-4.50` current `-7.50` move `-3.00` CLV `AWAY_FROM_YOU`
- Flags: `OUTLIER_MARKET|BIG_MOVE` | Robust edge: `2.20`

| lineopen | line | lineavg      | linemedian | linesag | linemassey | lineelo      | linemoore |
| -------- | ---- | ------------ | ---------- | ------- | ---------- | ------------ | --------- |
| -4.5     | -7.5 | -2.739256218 | -2.0       | -4.98   | -1.58      | -5.184891145 | -7.39     |

| your_vs_median | your_vs_linesag    | your_vs_linemassey | your_vs_lineelo    | your_vs_linemoore |
| -------------- | ------------------ | ------------------ | ------------------ | ----------------- |
| 2.1524455725   | 2.0500000000000003 | -1.35              | 2.2548911449999998 | 4.459999999999999 |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-31 — Nebraska @ Utah (Las Vegas Bowl)
- Neutral: `True` | Tier: `X-REVIEW` | Reasons: `EDGE_DK=13.39|EDGE_MKT=13.39|OUTLIER_MKT|RATINGS_Z=3.34`
- DK (home spread): `-16.50` | Your (home spread): `-3.11`
- DK edge: `13.39` | Market edge: `13.39`
- Ratings: mean `-16.32` std `3.95` z `3.34`
- Agreement (panel): `0.50` | Disagree: `lineelo, linemoore`
- Market: open `-14.00` current `-16.50` move `-2.50` CLV `AWAY_FROM_YOU`
- Flags: `OUTLIER_MARKET|OUTLIER_RATINGS` | Robust edge: `3.39`

| lineopen | line  | lineavg       | linemedian | linesag | linemassey | lineelo       | linemoore |
| -------- | ----- | ------------- | ---------- | ------- | ---------- | ------------- | --------- |
| -14.0    | -16.5 | -14.685939865 | -15.24     | -12.39  | -13.72     | -16.504754049 | -22.66    |

| your_vs_median | your_vs_linesag   | your_vs_linemassey | your_vs_lineelo | your_vs_linemoore |
| -------------- | ----------------- | ------------------ | --------------- | ----------------- |
| 12.0023770245  | 9.280000000000001 | 10.610000000000001 | 13.394754049    | 19.55             |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-31 — Iowa @ Vanderbilt (ReliaQuest Bowl)
- Neutral: `True` | Tier: `C` | Reasons: `EDGE_DK=2.30|EDGE_MKT=1.80|RATINGS_Z=0.14`
- DK (home spread): `-5.50` | Your (home spread): `-3.20`
- DK edge: `2.30` | Market edge: `1.80`
- Ratings: mean `-3.74` std `3.90` z `0.14`
- Agreement (panel): `0.75` | Disagree: `linemoore`
- Market: open `-4.00` current `-5.00` move `-1.00` CLV `AWAY_FROM_YOU`
- Flags: `` | Robust edge: `0.59`

| lineopen | line | lineavg       | linemedian | linesag | linemassey | lineelo      | linemoore |
| -------- | ---- | ------------- | ---------- | ------- | ---------- | ------------ | --------- |
| -4.0     | -5.0 | -2.2248999549 | -1.7535    | -2.9    | 1.81       | -4.807557791 | -9.06     |

| your_vs_median     | your_vs_linesag      | your_vs_linemassey | your_vs_lineelo    | your_vs_linemoore |
| ------------------ | -------------------- | ------------------ | ------------------ | ----------------- |
| 0.6537788954999995 | -0.30000000000000027 | -5.01              | 1.6075577909999996 | 5.86              |

- Notes: _opt-outs / injuries / motivation / weather_

### 2025-12-31 — Arizona State @ Duke (Sun Bowl)
- Neutral: `True` | Tier: `C` | Reasons: `EDGE_DK=-0.24`
- DK (home spread): `-2.50` | Your (home spread): `-2.74`
- DK edge: `-0.24` | Market edge: `nan`
- Agreement (panel): ``
- Flags: `` | Robust edge: `NA`

| lineopen | line | lineavg | linemedian | linesag | linemassey | lineelo | linemoore |
| -------- | ---- | ------- | ---------- | ------- | ---------- | ------- | --------- |
|          |      |         |            |         |            |         |           |

| your_vs_median | your_vs_linesag | your_vs_linemassey | your_vs_lineelo | your_vs_linemoore |
| -------------- | --------------- | ------------------ | --------------- | ----------------- |
|                |                 |                    |                 |                   |

- Notes: _opt-outs / injuries / motivation / weather_

### 2026-01-02 — Rice @ Texas State (Armed Forces Bowl)
- Neutral: `True` | Tier: `C` | Reasons: `EDGE_DK=7.93`
- DK (home spread): `-10.50` | Your (home spread): `-2.57`
- DK edge: `7.93` | Market edge: `nan`
- Agreement (panel): ``
- Flags: `` | Robust edge: `NA`

| lineopen | line | lineavg | linemedian | linesag | linemassey | lineelo | linemoore |
| -------- | ---- | ------- | ---------- | ------- | ---------- | ------- | --------- |
|          |      |         |            |         |            |         |           |

| your_vs_median | your_vs_linesag | your_vs_linemassey | your_vs_lineelo | your_vs_linemoore |
| -------------- | --------------- | ------------------ | --------------- | ----------------- |
|                |                 |                    |                 |                   |

- Notes: _opt-outs / injuries / motivation / weather_

### 2026-01-02 — Wake Forest @ Mississippi State (Duke's Mayo Bowl)
- Neutral: `True` | Tier: `C` | Reasons: `EDGE_DK=1.24`
- DK (home spread): `-4.00` | Your (home spread): `-2.76`
- DK edge: `1.24` | Market edge: `nan`
- Agreement (panel): ``
- Flags: `` | Robust edge: `NA`

| lineopen | line | lineavg | linemedian | linesag | linemassey | lineelo | linemoore |
| -------- | ---- | ------- | ---------- | ------- | ---------- | ------- | --------- |
|          |      |         |            |         |            |         |           |

| your_vs_median | your_vs_linesag | your_vs_linemassey | your_vs_lineelo | your_vs_linemoore |
| -------------- | --------------- | ------------------ | --------------- | ----------------- |
|                |                 |                    |                 |                   |

- Notes: _opt-outs / injuries / motivation / weather_

### 2026-01-02 — Arizona @ SMU (Holiday Bowl)
- Neutral: `True` | Tier: `X-REVIEW` | Reasons: `EDGE_DK=-6.18|EDGE_MKT=-6.18|OUTLIER_MKT|RATINGS_Z=-1.07`
- DK (home spread): `3.00` | Your (home spread): `-3.18`
- DK edge: `-6.18` | Market edge: `-6.18`
- Ratings: mean `1.53` std `4.42` z `-1.07`
- Agreement (panel): `0.50` | Disagree: `lineelo, linemoore`
- Market: open `1.50` current `3.00` move `1.50` CLV `AWAY_FROM_YOU`
- Flags: `OUTLIER_MARKET|HIGH_STD_RATINGS` | Robust edge: `1.40`

| lineopen | line | lineavg       | linemedian | linesag | linemassey | lineelo    | linemoore |
| -------- | ---- | ------------- | ---------- | ------- | ---------- | ---------- | --------- |
| 1.5      | 3.0  | -0.1953130564 | -0.195     | -4.15   | -1.26      | 4.69327171 | 6.84      |

| your_vs_median | your_vs_linesag    | your_vs_linemassey  | your_vs_lineelo    | your_vs_linemoore |
| -------------- | ------------------ | ------------------- | ------------------ | ----------------- |
| -4.896635855   | 0.9700000000000002 | -1.9200000000000002 | -7.873271710000001 | -10.02            |

- Notes: _opt-outs / injuries / motivation / weather_

### 2026-01-02 — Navy @ Cincinnati (Liberty Bowl)
- Neutral: `True` | Tier: `X-REVIEW` | Reasons: `EDGE_DK=-9.48|EDGE_MKT=-9.98|MOVE_DATA_ISSUE|OUTLIER_MKT|RATINGS_Z=0.36`
- DK (home spread): `6.50` | Your (home spread): `-2.98`
- DK edge: `-9.48` | Market edge: `-9.98`
- Ratings: mean `-3.91` std `2.62` z `0.36`
- Agreement (panel): `1.00`
- Market: open `-6.50` current `7.00` move `nan` CLV `<NA>`
- Flags: `OUTLIER_MARKET|MOVE_DATA_ISSUE` | Robust edge: `3.62`

| lineopen | line | lineavg       | linemedian | linesag | linemassey | lineelo      | linemoore |
| -------- | ---- | ------------- | ---------- | ------- | ---------- | ------------ | --------- |
| -6.5     | 7.0  | -3.1825234917 | -3.86      | -3.17   | -7.95      | -0.664203981 | -3.86     |

| your_vs_median     | your_vs_linesag     | your_vs_linemassey | your_vs_lineelo | your_vs_linemoore  |
| ------------------ | ------------------- | ------------------ | --------------- | ------------------ |
| 0.5349999999999997 | 0.18999999999999995 | 4.970000000000001  | -2.315796019    | 0.8799999999999999 |

- Notes: _opt-outs / injuries / motivation / weather_
