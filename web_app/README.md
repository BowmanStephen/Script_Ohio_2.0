# Script Ohio 2.0 Web App

Next.js web application for viewing college football predictions, model comparisons, and analytics.

## Quick Start

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

The app will be available at `http://localhost:3000`.

## Features

- **Weekly Predictions** (`/week/[week]`) - View predictions for any week
- **Bowl Season** (`/bowls`) - Bowl and postseason predictions
- **Model Comparison** (`/models`) - Compare Ridge, XGBoost, FastAI, Ensemble models
- **Advanced Analytics** (`/analytics`) - External model analysis and insights

## Data Sources

The app reads directly from repository artifacts:

- **Weekly predictions**: `predictions/week{N}/week{N}_model_predictions.json`
- **Bowl predictions**: `data/outputs/predictions/2025/bowl_season/*.json`
- **Analytics**: `data/outputs/analysis/external_model_analysis_*.json`

### Validating Data Sources

Before running the app, validate that prediction files exist:

```bash
# Validate all data sources
python scripts/sync_web_app_data.py --week 14

# Validate specific sources
python scripts/sync_web_app_data.py --bowls-only
python scripts/sync_web_app_data.py --analytics-only
```

See [docs/WEB_APP_DATA_FLOW.md](../docs/WEB_APP_DATA_FLOW.md) for detailed data flow documentation.

## Hybrid Data Mode (Optional)

The app can optionally use live API data instead of static files:

1. Set environment variable:
   ```bash
   export PY_API_BASE_URL=http://localhost:5001
   ```

2. The app will attempt API calls first, falling back to artifacts if unavailable.

## Development

```bash
# Type checking
npm run typecheck

# Linting
npm run lint

# Run tests
npm test

# Run tests in watch mode
npm run test:watch
```

## Deployment

### Vercel (Recommended)

The app is configured for Vercel deployment:

1. Connect repository to Vercel
2. Set root directory to `web_app`
3. Framework preset: Next.js
4. Deploy automatically on push to main branch

Configuration:
- Build command: `npm run build`
- Output directory: `.next`
- Install command: `npm install`

### Manual Deployment

```bash
npm run build
npm start
```

The built app will be in the `.next` directory.

## Architecture

- **Next.js 15** with App Router
- **TypeScript** for type safety
- **Zod** for runtime schema validation
- **Tailwind CSS** for styling
- **Recharts** for data visualization

## Troubleshooting

**"Predictions not found" error**:
- Run validation script: `python scripts/sync_web_app_data.py --week 14`
- Ensure prediction files are generated first
- Check file paths match expected structure

**Build errors**:
- Run `npm run typecheck` to identify TypeScript errors
- Check that all dependencies are installed: `npm install`
- Verify Node.js version is 18+ (`node --version`)

## Related Documentation

- [Data Flow Guide](../docs/WEB_APP_DATA_FLOW.md) - How data flows from artifacts to UI
- [Legacy App Inventory](../archive/web_app_legacy/LEGACY_INVENTORY.md) - What was replaced
