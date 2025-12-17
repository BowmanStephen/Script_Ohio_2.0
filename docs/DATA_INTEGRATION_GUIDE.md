# Data Integration Guide

This guide covers integrating new weekly/postseason training CSVs into the
master dataset (`model_pack/updated_training_data.csv`) with comprehensive
validation, observability, testing, and rollback support following A+ project
standards.

## Overview

The integration system provides production-ready data integration with:

- **Multi-layer validation**: Pre/during/post integration validation
- **Structured logging**: ObservabilityHub integration with event tracking
- **Error taxonomy**: Proper error categorization and severity levels
- **Automatic rollback**: Restore from backup on validation failure
- **Atomic writes**: Temp file + move pattern for data integrity
- **Comprehensive metrics**: Track games processed, duplicates removed, duration

## Canonical Locations

- **Weekly files**: `data/training/weekly/training_data_{season}_week{NN}.csv`
- **Postseason file**: `data/training/weekly/training_data_{season}_postseason.csv`
- **Master file**: `model_pack/updated_training_data.csv`
- **Backups**: `model_pack/updated_training_data_backup_YYYYMMDD_HHMMSS.csv` (same directory as master)

## Integration Workflow

### Step 1: Prepare Files

Ensure files are in canonical locations:

```bash
# Verify week 15 file exists
ls -la data/training/weekly/training_data_2025_week15.csv

# Verify postseason file exists
ls -la data/training/weekly/training_data_2025_postseason.csv
```

### Step 2: Run Integration

**Basic integration**:
```bash
python3 scripts/integrate_week15_postseason.py
```

**Dry-run mode** (validate without writing):
```bash
python3 scripts/integrate_week15_postseason.py --dry-run
```

**Skip validation** (not recommended):
```bash
python3 scripts/integrate_week15_postseason.py --skip-validation
```

### Step 3: Verify Integration

**Check game counts**:
```bash
python3 -c "
import pandas as pd
df = pd.read_csv('model_pack/updated_training_data.csv', low_memory=False)
print(f'Total games: {len(df)}')
print(f'2025 games: {len(df[df.season == 2025])}')
print(f'Week 15: {len(df[(df.season == 2025) & (df.week == 15)])}')
print(f'Postseason: {len(df[(df.season == 2025) & (df.season_type == \"postseason\")])}')
"
```

**Validate schema consistency**:
```bash
python3 scripts/verify_schema_consistency.py
```

**Run integration tests**:
```bash
pytest tests/test_integrate_week15_postseason.py -v
```

## Validation Requirements

### Pre-Integration Validation

The integration script performs these checks before combining data:

- **Schema Validation**: All files must have consistent column sets
- **Required Columns**: Must include `id`, `season`, `week`, `season_type`, `home_team`, `away_team`
- **Data Type Validation**: Numeric columns must be numeric, dates must be valid
- **Range Validation**: Seasons (2016-2030), weeks (1-20) in valid ranges
- **File Integrity**: Files must be readable and not corrupted

### Integration Validation

During integration:

- **Column Alignment**: All dataframes must have identical column sets
- **Row Counts**: Track games before/after integration
- **Duplicate Detection**: Identify and remove duplicate game IDs

### Post-Integration Validation

After combining:

- **Game Count Verification**: Verify expected games added
- **Schema Consistency**: All files maintain 86-feature structure
- **Duplicate Verification**: Zero duplicate game IDs remaining
- **Season Coverage**: Verify week 15 and postseason games present
- **Data Quality**: No null values in critical columns

## Rollback Procedures

### Automatic Rollback

If validation fails after backup creation, the integration script automatically
restores from backup. Check logs for rollback confirmation.

### Manual Rollback

**Restore from most recent backup**:
```bash
# Find latest backup
ls -lt model_pack/updated_training_data_backup_*.csv | head -1

# Restore manually
cp model_pack/updated_training_data_backup_YYYYMMDD_HHMMSS.csv \
   model_pack/updated_training_data.csv
```

**Verify backup integrity**:
```bash
# Check backup file exists and is readable
python3 -c "
import pandas as pd
df = pd.read_csv('model_pack/updated_training_data_backup_YYYYMMDD_HHMMSS.csv', low_memory=False)
print(f'Backup contains {len(df)} games')
"
```

## Observability & Monitoring

### Event Types

The integration script emits these observability events:

- `integration.start`: Integration begins
- `integration.file_loaded`: Each file loaded (week15, postseason)
- `integration.validation_passed`: Validation complete (pre/post)
- `integration.backup_created`: Backup successful
- `integration.success`: Integration complete
- `integration.error`: Any errors encountered
- `integration.rollback_successful`: Rollback completed

### Metrics Collected

- Integration duration (seconds)
- Games processed (week15, postseason)
- Duplicates removed
- File sizes processed
- Success/failure rates

### Logging

Structured logging via `src.observability`:
- All operations logged with contextual information
- Error reports include full stack traces
- Performance metrics tracked

## Troubleshooting

### File Not Found Errors

**Problem**: `FileNotFoundError` when running integration

**Solution**:
1. Verify files are in canonical locations:
   ```bash
   ls -la data/training/weekly/training_data_2025_week15.csv
   ls -la data/training/weekly/training_data_2025_postseason.csv
   ```
2. Check path utilities can resolve files:
   ```python
   from model_pack.utils.path_utils import get_weekly_training_file, get_postseason_training_file
   print(get_weekly_training_file(week=15, season=2025))
   print(get_postseason_training_file(season=2025))
   ```

### Schema Mismatch Errors

**Problem**: `ValueError: Schema mismatch` during validation

**Solution**:
1. Check column counts match:
   ```python
   import pandas as pd
   week15 = pd.read_csv('data/training/weekly/training_data_2025_week15.csv')
   postseason = pd.read_csv('data/training/weekly/training_data_2025_postseason.csv')
   print(f"Week15 columns: {len(week15.columns)}")
   print(f"Postseason columns: {len(postseason.columns)}")
   print(f"Missing in postseason: {set(week15.columns) - set(postseason.columns)}")
   ```
2. Ensure all files have same column set
3. Re-run integration after fixing schema

### Duplicate Game IDs

**Problem**: Duplicate game IDs detected

**Solution**:
- Integration automatically deduplicates on `id` column (keeps last occurrence)
- Check logs for number of duplicates removed
- Verify deduplication worked: `df.duplicated(subset=['id']).sum() == 0`

### Validation Failures

**Problem**: Validation fails with specific error

**Solution**:
1. Run with `--dry-run` to see validation errors without modifying files
2. Check error message for specific validation failure
3. Fix data quality issues (null values, invalid ranges, etc.)
4. Re-run integration

## Integration Details

### Deduplication Strategy

- Deduplicates on `id` column (primary key)
- Keeps last occurrence when duplicates found (`keep='last'`)
- Logs number of duplicates removed for transparency

### Backup Strategy

1. Create timestamped backup: `updated_training_data_backup_YYYYMMDD_HHMMSS.csv`
2. Backup stored in same directory as master file (`model_pack/`)
3. Use `shutil.copy2()` to preserve file metadata
4. Backup created before any modifications (fail-safe)

### Atomic Writes

- Write to temporary file: `updated_training_data.tmp`
- Move temp file to final location (atomic operation)
- Ensures data integrity even if process interrupted

## Testing

### Unit Tests

Run comprehensive unit tests:
```bash
pytest tests/test_integrate_week15_postseason.py -v
```

### Test Coverage

Minimum 90% coverage required for integration script:
```bash
pytest tests/test_integrate_week15_postseason.py \
  --cov=scripts/integrate_week15_postseason \
  --cov-report=html \
  --cov-fail-under=90
```

### Integration Tests

End-to-end integration tests verify full workflow:
```bash
pytest tests/test_integrate_week15_postseason.py::test_integration_creates_backup_and_writes_master -v
```

## Notes

- Integration deduplicates on `id` (`keep='last'`).
- Writes are atomic (tmp + replace) and backups are created before writing.
- Observability events are emitted via `src.observability.ObservabilityHub`.
- All validation checks can be skipped with `--skip-validation` (not recommended).
- Dry-run mode validates without modifying files (`--dry-run`).
