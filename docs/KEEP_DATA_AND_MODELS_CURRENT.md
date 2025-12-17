# Keeping Data + Models Current

This repo’s “source of truth” inputs are the CFBD API plus the canonical weekly
CSV drops in `data/training/weekly/`. The production models train from the
master dataset at `model_pack/updated_training_data.csv`.

## Prereqs

- Set API key in your shell or `.env`:
  - `CFBD_API_KEY=...` (or `CFBD_API_TOKEN=...`)
- Optional host selection:
  - `CFBD_HOST=production` (default) uses `https://api.collegefootballdata.com`
  - `CFBD_HOST=next` uses `https://apinext.collegefootballdata.com`

## Typical Weekly Update (Regular Season)

1. Build the latest week’s training CSV:
   - `python3 scripts/build_training_data_from_cfbd.py --season 2025 --week 14`
2. Integrate it into the master dataset:
   - `python3 scripts/integrate_weekly_files.py --season 2025 --weeks 14`
3. Retrain models from the updated master dataset:
   - `python3 scripts/retrain_models_current.py --skip-fastai`

## Postseason Update

1. Build postseason training CSV:
   - `python3 scripts/build_training_data_from_cfbd.py --season 2025 --season-type postseason`
2. Integrate postseason (and optionally the latest week as well):
   - `python3 scripts/integrate_weekly_files.py --season 2025 --weeks 15 --include-postseason`
3. Retrain models:
   - `python3 scripts/retrain_models_current.py --skip-fastai`
4. **Generate Bowl Predictions** (NEW):
   - `python3 scripts/predict_bowls_2025.py --season 2025 --method all --backup-existing --force`

**Step D Details - Bowl Predictions:**
- **--method**: Choose from `ml` (machine learning), `massey` (ratings-based), `simple` (basic), or `all` (generates all three)
- **--backup-existing**: Creates timestamped backup of existing predictions
- **--force**: Overwrites existing files without confirmation
- **--dry-run**: Preview what would be generated without creating files
- **Output Files**:
  - `predictions/bowls_2025_predictions_ml.json` (ML ensemble predictions)
  - `predictions/bowls_2025_predictions_massey.json` (Massey ratings-based)
  - `predictions/bowls_2025_predictions_simple.json` (Simple rating difference)
- **Safety Features**: Automatic backups, git SHA tracking, input validation

## One-Command Audit + Sync

- `python3 scripts/sync_all_data_sources.py --season 2025 --week auto --retrain`

This runs a system audit, checks whether weekly/postseason input IDs exist in
`model_pack/updated_training_data.csv`, integrates missing inputs, and can
retrain models when requested.

## Notes

- If you want the FastAI model to be “real” (and fix the known pickle issue),
  install FastAI and retrain without `--skip-fastai`.
- Avoid committing generated datasets/models; treat them as local artifacts.

