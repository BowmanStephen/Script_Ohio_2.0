# Documentation Standards for Model Pack

This document establishes consistent terminology and conventions for documenting the model pack's data structure, features, and schemas.

## Feature Count Terminology

### Standard Format

When referring to the training data structure, use this format:

**"81 predictive features + 7 metadata columns = 88 total columns"**

### Breakdown

- **81 Predictive Features**: Columns used as inputs to machine learning models
  - These include opponent-adjusted metrics, team strength indicators, and game statistics
  - See `feature_validation_summary.json` for complete breakdown by category

- **7 Metadata Columns**: Non-predictive columns used for identification and filtering
  - `id`: Unique game identifier
  - `start_date`: Game start date/time
  - `season_type`: Regular season or postseason
  - `game_key`: Composite key for deduplication
  - `conference_game`: Boolean flag for conference matchups
  - `home_conference`: Home team conference
  - `away_conference`: Away team conference

- **88 Total Columns**: Complete column count in training data files

### When to Use Each Term

| Context | Use This Term | Example |
|---------|--------------|---------|
| Model inputs | "81 features" or "81 predictive features" | "The model uses 81 features for prediction" |
| File structure | "88 columns" or "88 total columns" | "The training data file has 88 columns" |
| Schema validation | "81-feature schema (88 total columns)" | "Verify data matches 81-feature schema (88 total columns)" |
| Complete description | "81 predictive features + 7 metadata columns" | "The dataset contains 81 predictive features + 7 metadata columns = 88 total columns" |

## Margin Convention

### Standard Definition

**`margin = home_points - away_points`**

- **Positive margin**: Home team won
- **Negative margin**: Away team won
- **Zero margin**: Tie game

### Documentation Pattern

When documenting the `margin` column, always use:

```
### `margin`
Description: Final score margin (home - away)
```

### Implementation Reference

The margin calculation is consistently implemented as:
```python
margin = home_points - away_points
```

This convention is used throughout:
- Data migration scripts (`migrate_starter_pack_data.py`)
- Feature engineering notebooks
- Model training pipelines

## Code Documentation Examples

### Correct Documentation Patterns

#### Python Docstrings
```python
"""
Migrates starter pack data to match the model pack's 81-feature format (88 total columns).

The output preserves all 7 metadata columns while ensuring 81 predictive features
match the training data schema.
"""
```

#### Markdown Documentation
```markdown
## Training Data Schema

The training data uses an 81-feature schema with 88 total columns:
- 81 predictive features used by ML models
- 7 metadata columns for identification and filtering

See `feature_validation_summary.json` for detailed feature breakdown.
```

#### JSON Metadata
```json
{
  "total_features": 88,
  "expected_features": 88,
  "predictive_features": 81,
  "metadata_columns": 7
}
```

### Incorrect Patterns to Avoid

❌ **Don't say**: "86 features" (outdated count)
✅ **Do say**: "81 features" or "81 predictive features"

❌ **Don't say**: "margin = away - home"
✅ **Do say**: "margin = home - away"

❌ **Don't mix terms**: "The model uses 86 columns"
✅ **Do use**: "The model uses 81 features" or "The file has 88 columns"

## Schema Validation

When validating data schemas:

1. **Check total column count**: Should be 88 columns
2. **Check predictive features**: Should be 81 features
3. **Check metadata columns**: Should be 7 columns
4. **Verify margin calculation**: `margin = home_points - away_points`

### Validation Script Patterns

```python
# Correct pattern
expected_features = 81  # Predictive features only
expected_columns = 88   # Total columns including metadata

# Validation checks
assert len(feature_columns) == expected_features, \
    f"Expected {expected_features} features, got {len(feature_columns)}"

assert len(df.columns) == expected_columns, \
    f"Expected {expected_columns} columns, got {len(df.columns)}"
```

## Reference Files

- **Feature Breakdown**: `model_pack/feature_validation_summary.json`
- **Column Descriptions**: `model_pack/headers.md`
- **Schema Validation**: `scripts/verify_schema_consistency.py`
- **Data Migration**: `model_pack/migrate_starter_pack_data.py`

## Updates to This Document

When the feature count or schema changes:

1. Update this document with the new counts
2. Update `feature_validation_summary.json`
3. Update all references in code and documentation
4. Run `scripts/verify_schema_consistency.py` to validate

## Questions or Clarifications

If you encounter documentation that doesn't match these standards:

1. Check this document first
2. Verify against `feature_validation_summary.json`
3. Check actual data files for current structure
4. Update documentation to match these standards

---

**Last Updated**: 2025-11-19
**Schema Version**: 88 columns (81 features + 7 metadata)

