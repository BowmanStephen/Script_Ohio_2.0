# Prediction Comparison Report

Generated: 2025-12-16T21:42:30

- Predictions: `/Users/stephen_bowman/Documents/GitHub/Script_Ohio_2.0/predictions/draftkings_slate_2025/dk_slate_predictions_20251216_214139.csv`
- Systems: `/Users/stephen_bowman/Documents/GitHub/Script_Ohio_2.0/predictions/ncaapredictions.csv`
- Market column: `line`

Matched rows: 24 / 37

## Your Model vs Market
- Mean edge (home margin): 0.063
- Mean abs edge: 5.305

## System Agreement (vs your model)
| system_column | n  | mae_vs_your_model  | bias_vs_your_model   | corr_vs_your_model  | mae_vs_market      |
| ------------- | -- | ------------------ | -------------------- | ------------------- | ------------------ |
| linelaz       | 24 | 2.6899583333333332 | -2.6899583333333332  | 0.4690939933510809  | 5.988041666666667  |
| linelog       | 24 | 2.907281106525     | -2.0949825069916668  | 0.5598954460312716  | 4.610101226508333  |
| lineloud      | 2  | 3.04               | -0.43999999999999995 |                     | 2.5                |
| linerwp       | 15 | 4.226              | -0.8753333333333333  | 0.49650955978520245 | 3.677333333333334  |
| linepfz       | 24 | 4.833749999999999  | -0.27791666666666676 | 0.21798702749284699 | 5.390416666666667  |
| linedonchess  | 24 | 4.895833333333333  | 0.07416666666666671  | 0.3890679883620511  | 1.7041666666666666 |
| linemoore     | 24 | 5.095833333333334  | 0.1625000000000003   | 0.3499694542325541  | 4.395              |
| linehow       | 24 | 5.110833333333333  | -2.1883333333333335  | 0.34670067409131816 | 4.125              |
| lineca        | 24 | 5.304166666666666  | -0.12583333333333316 | 0.34895259751692453 | 0.4791666666666667 |
| linemidweek   | 24 | 5.305000000000001  | -0.06333333333333331 | 0.3314673664833129  | 0.0                |
| lineavg       | 24 | 5.3323816095375    | -0.48054709170416676 | 0.40880380845041153 | 3.2632756745375    |
| lineopen      | 24 | 5.346666666666667  | 0.14500000000000002  | 0.38161286094914976 | 2.3333333333333335 |
| linecons      | 24 | 5.4221875          | -1.2454791666666667  | 0.3602190738654283  | 3.935729166666667  |
| linewayward   | 24 | 5.423750000000001  | -1.3712500000000005  | 0.3716426606489157  | 4.264583333333333  |
| linemedian    | 24 | 5.518463570166666  | -0.5033385701666666  | 0.4201025528380779  | 3.2253953791666667 |
| lineclean     | 24 | 5.614999999999999  | -2.938333333333334   | 0.48872044236919454 | 6.75               |
| lineelo       | 24 | 5.660362469083334  | -0.5692547990000001  | 0.47123624643167755 | 3.5300287358333335 |
| linebihl      | 24 | 5.805833333333333  | -0.5491666666666666  | 0.2947203765709336  | 3.9625             |
| linefidler    | 24 | 5.837083333333333  | 0.07541666666666669  | 0.330194308098986   | 3.7937499999999993 |
| linedokter    | 5  | 5.8420000000000005 | 3.082                | 0.8665740048211599  | 1.5619999999999998 |

## Biggest Disagreements (vs market)
| date       | bowl                  | away_team        | home_team      | model_home_margin | market_home_margin | edge_vs_market      |
| ---------- | --------------------- | ---------------- | -------------- | ----------------- | ------------------ | ------------------- |
| 2025-12-20 | CFP First Round       | James Madison    | Oregon         | 3.63              | 21.5               | -17.87              |
| 2025-12-31 | Las Vegas Bowl        | Nebraska         | Utah           | 3.11              | 16.5               | -13.39              |
| 2025-12-27 | Military Bowl         | Pittsburgh       | East Carolina  | 3.06              | -7.0               | 10.06               |
| 2026-01-02 | Liberty Bowl          | Navy             | Cincinnati     | 2.98              | -7.0               | 9.98                |
| 2025-12-23 | Frisco Bowl           | UNLV             | Ohio           | 2.92              | -5.0               | 7.92                |
| 2025-12-26 | GameAbove Sports Bowl | Central Michigan | Northwestern   | 2.69              | 10.5               | -7.8100000000000005 |
| 2025-12-30 | Alamo Bowl            | USC              | TCU            | 3.07              | -4.5               | 7.57                |
| 2025-12-29 | Birmingham Bowl       | Georgia Southern | App State      | 2.38              | -4.5               | 6.88                |
| 2025-12-30 | Independence Bowl     | Coastal Carolina | Louisiana Tech | 2.57              | 9.0                | -6.43               |
| 2026-01-02 | Holiday Bowl          | Arizona          | SMU            | 3.18              | -3.0               | 6.18                |
| 2025-12-17 | 68 Ventures Bowl      | Louisiana        | Delaware       | 2.48              | -3.0               | 5.48                |
| 2025-12-30 | Music City Bowl       | Tennessee        | Illinois       | 2.95              | -2.5               | 5.45                |
| 2025-12-31 | Citrus Bowl           | Michigan         | Texas          | 2.93              | 7.5                | -4.57               |
| 2025-12-19 | CFP First Round       | Alabama          | Oklahoma       | 3.14              | -1.0               | 4.140000000000001   |
| 2025-12-23 | Boca Raton Bowl       | Toledo           | Louisville     | 3.28              | 7.0                | -3.72               |
