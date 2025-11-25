# Script Ohio Web App

Interactive UI for exploring Script Ohio predictions, ensemble metrics, and
value opportunities.

## Quick Start

```bash
cd web_app
npm ci
npm run dev   # local dev server
```

## Data Sources

- The simulator now auto-loads weekly predictions from `public/week14_model_predictions.json` (falls back to `week14_model_predictions.csv`).
- ATS tables are pulled from `public/week14_ats_data.json` with CSV fallback already in place.
- To point at a new week, drop the refreshed files into `public/` and update `APP_CONSTANTS.CURRENT_WEEK` plus the file naming pattern in `src/config/constants.ts`.

## Quality Checks

- `npm run lint` – ESLint bundle-mode rules
- `npm run typecheck` – TypeScript type checking
- `npm run test` – Run all tests with coverage
- `npm run test:watch` – Run tests in watch mode
- `npm run test:ui` – Run tests with Vitest UI

See [TESTING.md](./TESTING.md) for detailed testing documentation.

## Data Contract

The UI expects `Game` records plus optional `prediction` metadata; see
`web_app/DATA_CONTRACT.md` for the API surface and sample payloads. TypeScript
types live in `src/types.ts`.
