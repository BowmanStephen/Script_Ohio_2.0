# Data Organization Guide

This document explains the data organization structure for Script Ohio 2.0 and how to access data files using the centralized path utilities.

## Directory Structure

```
Script_Ohio_2.0/
├── model_pack/
│   ├── updated_training_data.csv      # Master training dataset (canonical)
│   ├── training_data.csv              # Legacy fallback
│   └── *.ipynb                        # Modeling notebooks
│
├── data/
│   ├── training/
│   │   ├── master/                    # (Future: symlink to model_pack)
│   │   └── weekly/                    # Weekly training files (2025)
│   │       └── training_data_2025_week*.csv
│   │
│   ├── weekly/                        # Weekly enhanced features (agents)
│   │   └── week{XX}/enhanced/
│   │       ├── week{XX}_features_86.csv
│   │       └── week{XX}_enhanced_games.csv
│   │
│   ├── weekly_training/               # Legacy location (backward compatibility)
│   │   └── training_data_2025_week*.csv
│   │
│   ├── raw/                           # Raw acquired data
│   │   └── 2025_raw_games.csv
│   │
│   ├── metadata/                      # Data metadata files
│   │   ├── headers_2025.csv
│   │   └── headers_model.csv
│   │
│   └── backups/                       # Data backups
│       └── training_data_2025_20251119/
│
├── reports/                           # Analysis outputs, CSV reports
│   ├── usage-stats-*.csv
│   ├── model_performance_comparison_*.csv
│   └── *.md
│
└── [clean root - only project files]
```

## Core Principles

1. **Single Source of Truth**: Each data file has ONE canonical location
2. **Hierarchical Organization**: Clear directory structure following domain boundaries
3. **Configuration-Driven Paths**: All code uses config/utilities, no hardcoded paths
4. **Root Cleanliness**: Root directory only contains project metadata, not data files
5. **Backward Compatibility**: Path utilities search multiple locations during migration

## Accessing Data Files

### Master Training Data

The master training dataset is located in `model_pack/updated_training_data.csv` (canonical) with fallback to `model_pack/training_data.csv`.

**Recommended Pattern**:
```python
from model_pack.config.data_config import get_data_config

config = get_data_config()
training_data_path = config.get_training_data_path()
df = pd.read_csv(training_data_path)
```

**Alternative** (if config system not available):
```python
from model_pack.utils.path_utils import get_training_data_file

training_data_path = get_training_data_file()
df = pd.read_csv(training_data_path)
```

### Weekly Training Files

Weekly training files are in `data/training/weekly/` (canonical) with fallbacks to `data/weekly_training/` (legacy) and root level (during migration).

**Recommended Pattern**:
```python
from model_pack.utils.path_utils import get_weekly_training_file

# Get file for week 12, season 2025
week_file = get_weekly_training_file(week=12, season=2025)
df = pd.read_csv(week_file)
```

**Search Order**:
1. `data/training/weekly/` (canonical location)
2. `data/weekly_training/` (legacy location)
3. Root level (temporary, during migration)

The utility function automatically searches these locations in order and logs warnings when using non-canonical locations.

### Weekly Enhanced Data Files

Weekly enhanced data files (features, games, metadata) are in `data/weekly/week{XX}/enhanced/` (canonical) with fallback to `data/week{XX}/enhanced/` (legacy).

**Recommended Pattern**:
```python
from model_pack.utils.path_utils import get_weekly_enhanced_file

# Get features file for week 13, season 2025
features_path = get_weekly_enhanced_file(week=13, file_type='features', season=2025)
features_df = pd.read_csv(features_path)

# Get games file
games_path = get_weekly_enhanced_file(week=13, file_type='games', season=2025)
games_df = pd.read_csv(games_path)

# Get metadata file
metadata_path = get_weekly_enhanced_file(week=13, file_type='metadata', season=2025)
with open(metadata_path) as f:
    metadata = json.load(f)
```

**File Types**:
- `'features'`: `week{XX}_features_86.csv`
- `'games'`: `week{XX}_enhanced_games.csv`
- `'metadata'`: `enhancement_metadata.json`

**Search Order**:
1. `data/weekly/week{XX:02d}/enhanced/` (canonical location)
2. `data/week{XX}/enhanced/` (legacy location)

The utility function automatically searches these locations in order and logs warnings when using legacy paths.

## Migration History

The data organization structure was migrated in November 2025:

- **Before**: Weekly training files scattered across root level and `data/weekly_training/`
- **After**: All weekly training files consolidated in `data/training/weekly/`
- **Root cleanup**: All data CSV files moved to appropriate subdirectories

## File Locations

### Training Data Files

| File Type | Canonical Location | Legacy Locations | Access Method |
|-----------|-------------------|------------------|---------------|
| Master training data | `model_pack/updated_training_data.csv` | `model_pack/training_data.csv` | `config.get_training_data_path()` |
| Weekly training files | `data/training/weekly/training_data_2025_week*.csv` | `data/weekly_training/`, root | `get_weekly_training_file()` |
| Weekly enhanced features | `data/weekly/week{XX}/enhanced/week{XX}_features_86.csv` | `data/week{XX}/enhanced/` | `get_weekly_enhanced_file(week, 'features')` |
| Weekly enhanced games | `data/weekly/week{XX}/enhanced/week{XX}_enhanced_games.csv` | `data/week{XX}/enhanced/` | `get_weekly_enhanced_file(week, 'games')` |
| Weekly enhancement metadata | `data/weekly/week{XX}/enhanced/enhancement_metadata.json` | `data/week{XX}/enhanced/` | `get_weekly_enhanced_file(week, 'metadata')` |

### Analysis Outputs

| File Type | Location | Notes |
|-----------|----------|-------|
| Usage statistics | `reports/usage-stats-*.csv` | Analysis reports |
| Model performance | `reports/model_performance_comparison_*.csv` | Performance comparisons |
| Migration reports | `reports/migration_report.txt` | Migration verification |

### Metadata Files

| File Type | Location | Notes |
|-----------|----------|-------|
| Data headers | `data/metadata/headers_*.csv` | Column definitions |
| Model headers | `data/metadata/headers_model.csv` | Model feature headers |

## Path Utilities

The `model_pack/utils/path_utils.py` module provides centralized path resolution:

- `find_project_root()`: Find project root directory
- `get_training_data_file()` / `get_master_training_data_path()`: Get master training data file path
- `get_weekly_training_file(week, season)`: Get weekly training file path with fallback search
- `get_weekly_enhanced_dir(week, season)`: Get canonical directory path for weekly enhanced data
- `get_weekly_enhanced_file(week, file_type, season)`: Get weekly enhanced file path (features, games, metadata)
- `get_model_file_path(model_name)`: Get model file path in `model_pack/`
- `resolve_path(relative_path)`: Resolve relative paths safely
- `find_data_file(filename)`: Search for data files in common locations
- `ensure_directory_exists(path)`: Ensure directory exists, creating if necessary

## Configuration System

The `model_pack/config/data_config.py` module provides centralized configuration:

- `get_data_config()`: Get global configuration instance
- `config.get_training_data_path()`: Get master training data path
- `config.get_season()`: Get current season
- `config.get_week()`: Get current week

## Best Practices

1. **Always use path utilities**: Never hardcode file paths in code
2. **Use config system**: Prefer `config.get_training_data_path()` over direct file paths
3. **Check canonical locations first**: When adding new files, use canonical locations
4. **Update scripts gradually**: Migrate scripts to use path utilities one at a time
5. **Test after changes**: Verify path resolution works after file moves

## Verification

To verify data organization:

```bash
# Check for root-level data files (should be 0)
ls *.csv 2>/dev/null | wc -l

# Verify weekly files are in canonical location
ls data/training/weekly/*.csv | wc -l

# Run verification script
python3 scripts/verify_weekly_file_equivalence.py
```

## Troubleshooting

### File Not Found Errors

If you get `FileNotFoundError` when accessing files:

1. Check if file exists in canonical location: `ls data/training/weekly/`
2. Verify path utility search order matches file location
3. Check logs for warnings about non-canonical locations

### Path Resolution Issues

If path utilities don't find files:

1. Verify project root detection: `python3 -c "from model_pack.utils.path_utils import find_project_root; print(find_project_root())"`
2. Check file permissions
3. Verify file exists: `test -f data/training/weekly/training_data_2025_week12.csv`

### Migration Issues

If files are in wrong locations:

1. Run migration script: `python3 scripts/migrate_training_data.py --dry-run`
2. Check migration report: `cat reports/migration_report.txt`
3. Verify file equivalence: `python3 scripts/verify_weekly_file_equivalence.py`

## Future Improvements

- Symlink `data/training/master/` to `model_pack/updated_training_data.csv`
- Add data versioning system
- Implement automated validation scripts
- Add CI/CD checks for file locations

