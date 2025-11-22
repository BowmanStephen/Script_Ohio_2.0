# Week N Analysis API Reference

Generated from Week 13 implementation - 2025-11-20

## Overview

This document provides API references for the Week N analysis system, derived from the Week 13 implementation.

## Agent APIs

### Week N Consolidation Agent

```python
from agents.week13_consolidation_agent import Week13ConsolidationAgent

# Initialize agent
agent = Week13ConsolidationAgent("weekN_consolidation_001")

# Perform consolidation
result = agent.execute_request(
    request=AgentRequest(
        request_id="consolidate_weekN",
        agent_type="week13_consolidation",  # Same agent type reused
        action="full_consolidation",
        parameters={"week": N},
        user_context={"user_id": "user_001"},
        timestamp=time.time(),
        priority=2
    ),
    user_permissions=PermissionLevel.ADMIN
)
```

### Legacy Creation Agent

```python
from agents.legacy_creation_agent import LegacyCreationAgent

# Initialize agent
agent = LegacyCreationAgent("legacy_creation_001")

# Create templates for week N
result = agent.execute_request(
    request=AgentRequest(
        request_id="create_weekN_templates",
        agent_type="legacy_creation",
        action="template_extraction",
        parameters={"source_week": 13, "target_week": N},
        user_context={"user_id": "user_001"},
        timestamp=time.time(),
        priority=2
    ),
    user_permissions=PermissionLevel.ADMIN
)
```

## Data APIs

### Feature Loading

```python
import pandas as pd

def load_weekN_features(week: int, season: int = 2025) -> pd.DataFrame:
    """Load 86 opponent-adjusted features for week N"""
    feature_path = f"data/week{week}/enhanced/week{week}_features_86_model_compatible.csv"
    return pd.read_csv(feature_path)
```

### Prediction Loading

```python
def load_weekN_predictions(week: int, season: int = 2025) -> pd.DataFrame:
    """Load predictions for week N"""
    prediction_path = f"predictions/week{week}/week{week}_predictions_enhanced.csv"
    return pd.read_csv(prediction_path)
```

### Analysis Loading

```python
import json

def load_weekN_analysis(week: int, season: int = 2025) -> dict:
    """Load comprehensive analysis for week N"""
    analysis_files = list(Path(f"analysis/week{week}/").glob("week{week}_comprehensive_analysis_*.json"))
    if analysis_files:
        with open(analysis_files[0], 'r') as f:
            return json.load(f)
    return {}
```

## Utility APIs

### Week N Pipeline Orchestration

```python
def run_weekN_pipeline(week: int, season: int = 2025) -> dict:
    """Run complete analysis pipeline for week N"""

    results = {}

    # Step 1: Feature generation
    results['features'] = generate_weekN_features(week, season)

    # Step 2: Predictions
    results['predictions'] = generate_weekN_predictions(week, season)

    # Step 3: Analysis
    results['analysis'] = generate_weekN_analysis(week, season)

    # Step 4: Dashboard
    results['dashboard'] = generate_weekN_dashboard(week, season)

    return results
```

### Quality Validation

```python
def validate_weekN_data(week: int) -> dict:
    """Validate data quality for week N"""

    validation_results = {
        'features_valid': False,
        'predictions_valid': False,
        'analysis_valid': False
    }

    # Validate features (86 columns expected)
    try:
        features = load_weekN_features(week)
        validation_results['features_valid'] = len(features.columns) == 86
    except:
        pass

    # Validate predictions
    try:
        predictions = load_weekN_predictions(week)
        validation_results['predictions_valid'] = len(predictions) > 0
    except:
        pass

    # Validate analysis
    try:
        analysis = load_weekN_analysis(week)
        validation_results['analysis_valid'] = len(analysis) > 0
    except:
        pass

    return validation_results
```

## Configuration APIs

### Model Configuration

```python
MODEL_CONFIG = {
    'ridge': {
        'model_file': 'model_pack/ridge_model_2025.joblib',
        'feature_count': 86,
        'prediction_type': 'margin'
    },
    'xgboost': {
        'model_file': 'model_pack/xgb_home_win_model_2025.pkl',
        'feature_count': 86,
        'prediction_type': 'probability'
    },
    'fastai': {
        'model_file': 'model_pack/fastai_home_win_model_2025.pkl',
        'feature_count': 86,
        'prediction_type': 'probability'
    }
}
```

### CFBD API Configuration

```python
CFBD_CONFIG = {
    'base_url': 'https://api.collegefootballdata.com',
    'rate_limit': 6,  # requests per second
    'timeout': 30,    # seconds
    'required_headers': {
        'Authorization': 'Bearer YOUR_API_KEY'
    }
}
```

## Error Handling

Standard error responses across all APIs:

```python
{
    "status": "error",
    "error_message": "Description of error",
    "execution_time": 0.123,
    "error_code": "SPECIFIC_ERROR_CODE",
    "suggestions": ["Recovery suggestions"]
}
```

Success responses:

```python
{
    "status": "success",
    "data": {...},
    "execution_time": 1.234,
    "metadata": {
        "week": 13,
        "season": 2025,
        "timestamp": "2025-11-20T12:00:00Z"
    }
}
```

## Performance Guidelines

Based on Week 13 execution:

- **API Response Time**: <2 seconds for all operations
- **Data Loading**: <5 seconds for feature sets
- **Prediction Generation**: <30 seconds for full week
- **Analysis Generation**: <2 minutes for comprehensive analysis

---

*API documentation automatically generated from Week 13 implementation patterns.*
