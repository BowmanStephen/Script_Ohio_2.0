# Prediction Comparison Report

Generated: 2025-12-16T21:41:52

- Predictions: `/Users/stephen_bowman/Documents/GitHub/Script_Ohio_2.0/predictions/draftkings_slate_2025/dk_slate_predictions_20251216_214139.csv`
- Systems: `/Users/stephen_bowman/Documents/GitHub/Script_Ohio_2.0/predictions/ncaapredictions.csv`
- Market column: `lineopen`

Matched rows: 24 / 37

## Your Model vs Market
- Mean edge (home margin): -0.145
- Mean abs edge: 5.347

## System Agreement (vs your model)
| system_column | n  | mae_vs_your_model  | bias_vs_your_model   | corr_vs_your_model  | mae_vs_market      |
| ------------- | -- | ------------------ | -------------------- | ------------------- | ------------------ |
| linestd       | 24 | 1.0092107889541666 | 0.9381320287791667   | 0.14926954548042162 | 5.0521649193875    |
| linelaz       | 24 | 2.6899583333333332 | -2.6899583333333332  | 0.4690939933510809  | 5.801541666666666  |
| linelog       | 24 | 2.907281106525     | -2.0949825069916668  | 0.5598954460312716  | 4.523513511841667  |
| lineloud      | 2  | 3.04               | -0.43999999999999995 |                     | 2.0                |
| linerwp       | 15 | 4.226              | -0.8753333333333333  | 0.49650955978520245 | 3.7760000000000002 |
| linepfz       | 24 | 4.833749999999999  | -0.27791666666666676 | 0.21798702749284699 | 4.939583333333333  |
| linedonchess  | 24 | 4.895833333333333  | 0.07416666666666671  | 0.3890679883620511  | 1.8208333333333335 |
| linemoore     | 24 | 5.095833333333334  | 0.1625000000000003   | 0.3499694542325541  | 4.659166666666668  |
| linehow       | 24 | 5.110833333333333  | -2.1883333333333335  | 0.34670067409131816 | 4.958333333333333  |
| lineca        | 24 | 5.304166666666666  | -0.12583333333333316 | 0.34895259751692453 | 2.0625             |
| line          | 24 | 5.305000000000001  | -0.06333333333333331 | 0.3314673664833129  | 2.3333333333333335 |
| linemidweek   | 24 | 5.305000000000001  | -0.06333333333333331 | 0.3314673664833129  | 2.3333333333333335 |
| lineavg       | 24 | 5.3323816095375    | -0.48054709170416676 | 0.40880380845041153 | 2.2242355918708334 |
| linecons      | 24 | 5.4221875          | -1.2454791666666667  | 0.3602190738654283  | 3.400770833333334  |
| linewayward   | 24 | 5.423750000000001  | -1.3712500000000005  | 0.3716426606489157  | 3.287083333333333  |
| linemedian    | 24 | 5.518463570166666  | -0.5033385701666666  | 0.4201025528380779  | 2.2061634420833336 |
| lineclean     | 24 | 5.614999999999999  | -2.938333333333334   | 0.48872044236919454 | 7.208333333333333  |
| lineelo       | 24 | 5.660362469083334  | -0.5692547990000001  | 0.47123624643167755 | 3.2761085124166662 |
| linebihl      | 24 | 5.805833333333333  | -0.5491666666666666  | 0.2947203765709336  | 3.34               |
| linefidler    | 24 | 5.837083333333333  | 0.07541666666666669  | 0.330194308098986   | 2.5845833333333332 |

## Biggest Disagreements (vs market)
| date       | bowl                  | away_team        | home_team      | model_home_margin | market_home_margin | edge_vs_market     |
| ---------- | --------------------- | ---------------- | -------------- | ----------------- | ------------------ | ------------------ |
| 2025-12-20 | CFP First Round       | James Madison    | Oregon         | 3.63              | 21.0               | -17.37             |
| 2025-12-31 | Las Vegas Bowl        | Nebraska         | Utah           | 3.11              | 14.0               | -10.89             |
| 2025-12-26 | GameAbove Sports Bowl | Central Michigan | Northwestern   | 2.69              | 12.5               | -9.81              |
| 2025-12-30 | Music City Bowl       | Tennessee        | Illinois       | 2.95              | -6.5               | 9.45               |
| 2025-12-27 | Military Bowl         | Pittsburgh       | East Carolina  | 3.06              | -6.0               | 9.06               |
| 2025-12-30 | Alamo Bowl            | USC              | TCU            | 3.07              | -5.5               | 8.57               |
| 2025-12-23 | Frisco Bowl           | UNLV             | Ohio           | 2.92              | -4.0               | 6.92               |
| 2025-12-23 | Boca Raton Bowl       | Toledo           | Louisville     | 3.28              | 9.5                | -6.220000000000001 |
| 2025-12-17 | 68 Ventures Bowl      | Louisiana        | Delaware       | 2.48              | -3.5               | 5.98               |
| 2025-12-19 | CFP First Round       | Alabama          | Oklahoma       | 3.14              | -2.0               | 5.140000000000001  |
| 2026-01-02 | Holiday Bowl          | Arizona          | SMU            | 3.18              | -1.5               | 4.68               |
| 2025-12-30 | Independence Bowl     | Coastal Carolina | Louisiana Tech | 2.57              | 7.0                | -4.43              |
| 2025-12-29 | Birmingham Bowl       | Georgia Southern | App State      | 2.38              | -2.0               | 4.38               |
| 2025-12-17 | Cure Bowl             | Old Dominion     | South Florida  | 3.4               | 7.5                | -4.1               |
| 2025-12-27 | Pinstripe Bowl        | Penn State       | Clemson        | 2.99              | -1.0               | 3.99               |
