## Front-End Data Contract

The React simulator expects a single uniform contract for every matchup it
renders.  The canonical TypeScript interface lives in `web_app/src/types.ts`
and is reproduced here for convenience:

```ts
export interface Game {
  id: number;
  home_team: string;
  away_team: string;
  spread: number;
  home_elo: number;
  away_elo: number;
  home_talent: number;
  away_talent: number;
  home_adjusted_epa: number;
  away_adjusted_epa: number;
  home_adjusted_success: number;
  away_adjusted_success: number;
  home_adjusted_explosiveness: number;
  away_adjusted_explosiveness: number;
  home_points_per_opportunity_offense: number;
  away_points_per_opportunity_offense: number;
  prediction?: PredictionResult;
  wcflPoints?: number;
  reasoning?: string;
}
```

### Guarantees

- All numeric fields are finite real numbers (no `NaN`, `Infinity`, or
  strings that parse to numbers).
- Team identifiers use NCAA naming conventions and double as unique keys in
  downstream visualizations.
- Optional prediction metadata is appended client-side; the contract
  therefore guarantees those keys will **not** appear in the source data.

### Data sources

- Static JSON snapshots live in `web_app/src/data/week*_data.json`.
- Curated TypeScript exports (`week13Games.ts`, etc.) allow tree-shaking and
  type inference within the app.
- Week selection hooks should only rely on the exported `Game[]`, not the
  raw JSON, to avoid duplicate transformation logic.

### Contract validation

The `web_app/src/__tests__/dataContract.test.ts` suite enforces:

1. Each `Game` contains all required numeric fields.
2. Field ranges stay within sane bounds (e.g., EPA between -1.5 and 1.5).
3. Static JSON payloads and TypeScript exports stay in sync.

Run the checks locally with:

```bash
cd web_app
npm run test
```

### Updating the contract

1. Modify `web_app/src/types.ts`.
2. Update both the JSON sources and TS exports with the new fields.
3. Extend `dataContract.test.ts` to cover the additional constraints.
4. Document the change in this file so downstream consumers can assess
   impact.

CI now blocks merges that break the contract through Vitest coverage and an
npm audit gate.

