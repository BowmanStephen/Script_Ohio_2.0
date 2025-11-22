# Backup Directory

This directory contains backups of data files created during various maintenance and update operations.

## Contents
- `training_data_2025_20251119/`: Contains a snapshot of weekly training data files as of Nov 19, 2025.
  - **Note**: The live versions of these files are now located in `data/weekly_training/`.
  - `training_data_2025_week12_updated.csv` in this backup was an intermediate file; the canonical version is `data/weekly_training/training_data_2025_week12.csv`.

## Retention Policy
Backups should be reviewed periodically. Files older than 30 days may be archived to `archive/backups/` or deleted if no longer needed.

