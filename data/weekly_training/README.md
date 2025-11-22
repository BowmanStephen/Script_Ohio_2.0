# Legacy Weekly Training Directory

This directory previously contained weekly training data files. These files have been migrated to the canonical location: `data/training/weekly/`

## Migration Status

- **Migrated**: All weekly training files moved to `data/training/weekly/`
- **Backup**: Legacy files backed up to `data/backups/weekly_training_legacy/`
- **Status**: This directory is now empty and maintained for backward compatibility

## Current Usage

The path utility (`model_pack/utils/path_utils.py`) searches for weekly training files in this order:

1. `data/training/weekly/` (canonical location) ✅
2. `data/weekly_training/` (legacy location - empty)
3. Root level (temporary, during migration)

## For Developers

- **New files**: Always place weekly training files in `data/training/weekly/`
- **Access**: Use `get_weekly_training_file(week, season)` from `model_pack.utils.path_utils`
- **Do not**: Create new files in this legacy directory

See `docs/DATA_ORGANIZATION.md` for complete data organization guidelines.
