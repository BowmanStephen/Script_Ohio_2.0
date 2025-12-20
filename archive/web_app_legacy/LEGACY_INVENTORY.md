# Legacy Web App Inventory

**Status**: Archived - Replaced by Next.js rewrite (v2)

**Date Archived**: 2025-12-20

## Overview

This directory contains the legacy Vite SPA that was replaced by a Next.js-based
architecture. It used state-based view switching instead of proper routing.

## Key Components

### Top-Level Views (from `App.tsx`)
1. **Postseason Dashboard** (`UnifiedPostseasonDashboard`) - Main bowl/postseason view
2. **ML Simulator** (`MLSimulator`) - Model training/interactive simulation
3. **Bowl Analytics Dashboard** (`BowlAnalyticsDashboard`) - Bowl-specific analytics
4. **Stakeholder Dashboard** (`StakeholderDashboard`) - Stakeholder-friendly summary
5. **Demo Mode** - Special demo presentation mode

### Data Loaders (`src/utils/`)
- `loadPredictionsData.ts` - Loads weekly predictions from JSON/CSV
- `loadATSData.ts` - Loads ATS (Against The Spread) data
- `apiClient.ts` - Live API client with fallback to static data
- `predictionLogic.ts` - Prediction calculation logic
- `auditApiClient.ts` - Audit dashboard API client

### Component Structure
- `components/analytics/` - Analytics dashboards (bowl, recruiting, roster, etc.)
- `components/simulator/` - ML simulator components (predictions, ATS, training)
- `components/ui/` - Radix UI primitives (button, card, tabs, etc.)
- `components/cfbd/` - CFBD integration views

### Data Sources (`public/`)
- `week14_model_predictions.json` - Weekly predictions (hard-coded to week 14)
- `week14_ats_data.json` - ATS data
- `bowls_2025_predictions.json` - Bowl predictions

### API Endpoints Used
- Flask prediction API: `http://localhost:5001` (via `api/prediction_api.py`)
- Flask bowl API: `http://localhost:5002` (via `api_server/bowl_api.py`)
- Flask analytics API: `http://localhost:5002` (via `api_server/analytics_api.py`)
- Flask audit API: `http://localhost:5001` (via `api_server/audit_api.py`)

## Known Issues (Why It Was Replaced)

1. **No routing** - Single-page app with state-based view switching
2. **Hard-coded week assumptions** - Week 14 hard-coded throughout
3. **Duplicated data logic** - `loadPredictionsData` vs `apiClient.ts` have overlapping transforms
4. **Fragmented backend** - Multiple Flask/FastAPI servers with port conflicts
5. **Complex component hierarchy** - Difficult to navigate and maintain

## What Was Preserved

The new Next.js app preserves these features:
- Weekly predictions view
- Bowl/postseason predictions
- Model comparison/metrics
- Advanced analytics dashboards

The simulator and audit dashboard features were deferred for v2.
