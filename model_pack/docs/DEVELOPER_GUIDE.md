# Model Pack Developer Guide

## Overview

This guide provides comprehensive information for developers working on the Model Pack system. It covers architecture, data flow, testing strategies, and contribution guidelines.

## Table of Contents

1. [Architecture](#architecture)
2. [Data Flow](#data-flow)
3. [Testing Strategy](#testing-strategy)
4. [Development Workflow](#development-workflow)
5. [Troubleshooting](#troubleshooting)
6. [Contribution Guidelines](#contribution-guidelines)

## Architecture

### System Components

The Model Pack system consists of several key components:

1. **Data Acquisition Agent** (`data_acquisition_agent.py`)
   - Fetches data from CFBD API (GraphQL primary, REST fallback)
   - Handles rate limiting and error recovery
   - Validates data quality

2. **Metrics Calculation Agent** (`metrics_calculation_agent.py`)
   - Calculates opponent-adjusted advanced metrics
   - Ensures methodological consistency
   - Validates feature distributions

3. **Model Training Agent** (`model_training_agent.py`)
   - Trains Ridge Regression, XGBoost, and FastAI models
   - Implements temporal validation
   - Generates performance reports

4. **Hyperparameter Tuner** (`utils/hyperparameter_tuner.py`)
   - Automated hyperparameter optimization
   - Supports GridSearchCV and Optuna
   - Saves/loads best parameters

5. **Automated Retraining Pipeline** (`scripts/automated_retraining.py`)
   - Orchestrates complete retraining workflow
   - Archives old models
   - Validates performance

### Shared Utilities

The system uses shared utilities to reduce code duplication:

- **Data Acquisition Utils** (`utils/data_acquisition_utils.py`)
  - GraphQL/REST client initialization
  - Rate limiting
  - Data validation
  - Column normalization

- **Configuration System** (`config/data_config.py`)
  - Centralized configuration management
  - Dynamic season/week detection
  - Path resolution

## Data Flow

### Complete Pipeline

```
1. Data Acquisition
   └─> Fetch games from CFBD API (GraphQL/REST)
   └─> Filter FBS games
   └─> Save raw data

2. Feature Calculation
   └─> Calculate opponent-adjusted metrics
   └─> Validate feature distributions
   └─> Merge with historical data

3. Model Training
   └─> Temporal validation split
   └─> Hyperparameter tuning
   └─> Train models (Ridge, XGBoost, FastAI)
   └─> Evaluate performance

4. Model Deployment
   └─> Archive old models
   └─> Save new models
   └─> Update model registry
   └─> Generate reports
```

### Temporal Validation

The system uses temporal validation to prevent data leakage:

- **Training Set**: All seasons before current season
- **Test Set**: Current season only
- **Validation**: Ensures no future data leaks into training features

## Testing Strategy

### Test Structure

Tests are organized into three categories:

1. **Unit Tests** (`tests/test_model_pack_agents.py`)
   - Test individual agent methods
   - Mock external dependencies
   - Test edge cases

2. **Integration Tests** (`tests/test_model_pack_integration.py`)
   - Test complete pipeline workflows
   - Verify data consistency
   - Test model loading/prediction

3. **Data Quality Tests** (`tests/test_data_quality.py`)
   - Test opponent adjustment calculations
   - Verify no data leakage
   - Validate feature distributions

### Running Tests

```bash
# Run all tests
pytest tests/test_model_pack*.py -v

# Run with coverage
pytest tests/test_model_pack*.py --cov=model_pack --cov-report=html

# Run specific test file
pytest tests/test_model_pack_agents.py -v

# Run specific test
pytest tests/test_model_pack_agents.py::TestDataAcquisitionAgent::test_rate_limit -v
```

### Test Coverage Goals

- **Target**: 80%+ code coverage
- **Critical Paths**: 100% coverage (data acquisition, model training)
- **Utilities**: 90%+ coverage

## Development Workflow

### Setting Up Development Environment

1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd Script_Ohio_2.0
   ```

2. **Create Virtual Environment**
   ```bash
   python3.13 -m venv venv
   source venv/bin/activate  # Linux/macOS
   # or
   venv\Scripts\activate  # Windows
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. **Set Environment Variables**
   ```bash
   export CFBD_API_KEY="your-api-key-here"
   ```

### Code Style

- **Python**: Follow PEP 8
- **Line Length**: 88 characters (Black default)
- **Type Hints**: Use type hints for all public APIs
- **Docstrings**: Google-style docstrings

### Adding New Features

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Write Tests First** (TDD approach)
   - Write failing tests
   - Implement feature
   - Make tests pass

3. **Update Documentation**
   - Add docstrings
   - Update this guide if needed
   - Update API documentation

4. **Run Tests and Linters**
   ```bash
   pytest tests/ -v
   black --check model_pack/
   flake8 model_pack/
   mypy model_pack/
   ```

5. **Submit Pull Request**
   - Include test coverage
   - Document changes
   - Link to related issues

## Troubleshooting

### Common Issues

#### 1. Import Errors

**Problem**: `ModuleNotFoundError` when importing model_pack modules

**Solution**:
```python
# Add project root to sys.path
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
```

#### 2. API Key Not Found

**Problem**: `ValueError: CFBD_API_KEY environment variable required`

**Solution**:
```bash
export CFBD_API_KEY="your-api-key"
# Or add to .env file
echo "CFBD_API_KEY=your-api-key" >> .env
```

#### 3. FastAI Model Loading Issues

**Problem**: Pickle protocol errors when loading FastAI models

**Solution**: FastAI models use their own export/load methods. Use `load_learner()` instead of `pickle.load()`.

#### 4. Data Leakage Warnings

**Problem**: Tests detect potential data leakage

**Solution**: Ensure temporal validation split is correct:
- Training: `df[df['season'] < current_season]`
- Test: `df[df['season'] == current_season]`

#### 5. Hyperparameter Tuning Takes Too Long

**Problem**: GridSearchCV takes hours to complete

**Solution**: 
- Use smaller parameter grids
- Use Optuna for faster optimization
- Cache best parameters to avoid re-tuning

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contribution Guidelines

### Before Submitting

- [ ] All tests pass
- [ ] Code coverage maintained or improved
- [ ] Documentation updated
- [ ] Type hints added
- [ ] No linting errors
- [ ] Performance tested (if applicable)

### Code Review Checklist

- [ ] Code follows style guidelines
- [ ] Tests are comprehensive
- [ ] Error handling is appropriate
- [ ] Documentation is clear
- [ ] No hardcoded values
- [ ] Configuration system used

### Commit Messages

Use conventional commit format:

```
feat: Add hyperparameter tuning for Ridge regression
fix: Resolve FastAI variable scope error
docs: Update developer guide with troubleshooting
test: Add integration tests for complete pipeline
refactor: Consolidate data acquisition scripts
```

## Additional Resources

- **API Documentation**: See `model_pack/docs/api/` (to be generated)
- **Configuration Guide**: See `model_pack/config/data_config.py`
- **Testing Examples**: See `tests/test_model_pack_*.py`
- **Agent Patterns**: See `AGENTS.md` in project root

## Getting Help

- **Issues**: Create GitHub issue with detailed description
- **Discussions**: Use GitHub Discussions for questions
- **Documentation**: Check `model_pack/CLAUDE.md` for usage examples

