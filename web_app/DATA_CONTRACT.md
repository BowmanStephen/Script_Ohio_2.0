# Front-End Data Contract

The React app assumes a simple API surface for game predictions and model
metrics. These contracts mirror the `Game` and `PredictionResult` types in
`src/types.ts` and should be kept stable when wiring a real backend.

## Expected Endpoints

- `GET /api/predictions/week/:week`
  - Returns an array of `Game` objects with optional `prediction` metadata.
- `GET /api/model-metrics`
  - Returns aggregate model accuracy/MAE/RMSE values for display panels.

## Game Payload

```json
{
  "id": 401756964,
  "home_team": "Kansas",
  "away_team": "Utah",
  "spread": 13.0,
  "home_elo": 1499.0,
  "away_elo": 1971.0,
  "home_talent": 705.32,
  "away_talent": 707.86,
  "home_adjusted_epa": 0.2231,
  "away_adjusted_epa": 0.3147,
  "home_adjusted_success": 0.4735,
  "away_adjusted_success": 0.4881,
  "home_adjusted_explosiveness": 1.2249,
  "away_adjusted_explosiveness": 1.2558,
  "home_points_per_opportunity_offense": 4.15,
  "away_points_per_opportunity_offense": 5.03,
  "prediction": {
    "predictedMargin": "+3.7",
    "confidence": "0.68",
    "lineValue": "+6.5 vs spread",
    "valueRating": "A",
    "winner": "Home",
    "suggestedSide": "Kansas +13"
  }
}
```

### Field Reference

- `id` (number): CFBD game ID, unique per matchup.
- `home_team` / `away_team` (string): Team names.
- `spread` (number): Home-team perspective spread; positive means home favored.
- `home_elo` / `away_elo` (number): Elo ratings.
- `home_talent` / `away_talent` (number): 247 composite talent scores.
- `home_adjusted_epa` / `away_adjusted_epa` (number): Possession-level EPA.
- `home_adjusted_success` / `away_adjusted_success` (number): Success rate.
- `home_adjusted_explosiveness` / `away_adjusted_explosiveness` (number):
  Explosiveness multiplier.
- `home_points_per_opportunity_offense` / `away_points_per_opportunity_offense`
  (number): Finishing drives efficiency.
- `prediction` (object, optional): Model/ensemble outputs shown in UI.
- `wcflPoints` (number, optional): Internal WCFL scoring for value view.
- `reasoning` (string, optional): Short justification text if available.

## Model Metrics Payload

```json
{
  "ridge": { "accuracy": 0.63, "mae": 11.2, "weight": 0.3 },
  "xgboost": { "accuracy": 0.65, "mae": 10.5, "weight": 0.5 },
  "fastai": { "accuracy": 0.61, "mae": 12.1, "weight": 0.2 },
  "consensus": { "accuracy": 0.66, "mae": 10.1, "weight": 1.0 }
}
```

Use this shape when backing the `ModelPerformanceView` component.

## Validation

The Vitest suite (`npm test`) enforces:

- Presence of all numeric fields for each game.
- Unique game IDs per payload.
- Optional prediction/reasoning fields do not override base data.

Keep the TypeScript types in `src/types.ts` aligned with any backend changes to
avoid runtime shape drift.

## Current Static Inputs

While the API layer is stubbed, the UI is wired to static assets in
`web_app/public/` for Week 14:

- `week14_model_predictions.json` (fallback: `week14_model_predictions.csv`)
- `week14_ats_data.json` (fallback: `week14_ats_full_table.csv`)

Update `APP_CONSTANTS.CURRENT_WEEK` and replace these files to aim the UI at a
new week until live endpoints are available.
