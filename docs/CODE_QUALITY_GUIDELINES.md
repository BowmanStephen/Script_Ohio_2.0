# Code Quality Guidelines

**Last Updated**: November 2025  
**Status**: Active code quality standards

## Overview

This document outlines code quality standards for Script Ohio 2.0, including type hints, linting, testing, code organization, and documentation requirements.

## Type Hints

### Requirements

**All public APIs must include type hints**:
- Function parameters
- Return types
- Class attributes (public)
- Module-level constants (when relevant)

### Best Practices

**Function Signatures**:
```python
from typing import Dict, List, Optional, Union

def process_game_data(
    season: int,
    week: int,
    team: Optional[str] = None,
    include_stats: bool = True
) -> Dict[str, Union[int, str, float]]:
    """Process game data for given season and week.
    
    Args:
        season: Season year (1869-2100)
        week: Week number (1-25)
        team: Optional team name filter
        include_stats: Whether to include statistical data
    
    Returns:
        Dictionary with processed game data
    """
    # Implementation
    pass
```

**Class Attributes**:
```python
from dataclasses import dataclass
from typing import List

@dataclass
class Game:
    season: int
    week: int
    home_team: str
    away_team: str
    scores: Optional[List[int]] = None
```

**Type Aliases**:
```python
from typing import TypeAlias, Dict, List

GameData: TypeAlias = Dict[str, Union[int, str, float]]
GameList: TypeAlias = List[GameData]
```

### Type Checking

**Tools**:
- `mypy`: Static type checker for Python
- `pyright`: Fast type checker (VS Code default)
- `pyre`: Facebook's type checker

**Usage**:
```bash
# Install mypy
pip install mypy

# Type check specific directory
mypy agents/ src/

# Type check with strict mode
mypy --strict agents/ src/

# Type check with configuration file
mypy --config-file mypy.ini agents/
```

**Configuration** (`mypy.ini`):
```ini
[mypy]
python_version = 3.13
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
disallow_incomplete_defs = True
check_untyped_defs = True
no_implicit_optional = True
warn_redundant_casts = True
warn_unused_ignores = True
warn_no_return = True
```

### Common Patterns

**Optional Types**:
```python
from typing import Optional

def get_team_rating(team: str, season: int) -> Optional[float]:
    """Returns team rating or None if not available."""
    # Implementation
    pass
```

**Union Types**:
```python
from typing import Union

def process_value(value: Union[int, str, float]) -> str:
    """Process value of different types."""
    if isinstance(value, (int, float)):
        return str(value)
    return value
```

**Generic Types**:
```python
from typing import TypeVar, List

T = TypeVar('T')

def get_first(items: List[T]) -> Optional[T]:
    """Get first item from list."""
    return items[0] if items else None
```

## Linting

### Tools

**Primary Linter**: `black` (code formatter)
**Style Checker**: `flake8` (PEP 8 compliance)
**Import Checker**: `isort` (import organization)

### Configuration

**Black** (`.black` or `pyproject.toml`):
```toml
[tool.black]
line-length = 88
target-version = ['py313']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | venv
  | build
  | dist
)/
'''
```

**Flake8** (`.flake8` or `setup.cfg`):
```ini
[flake8]
max-line-length = 88
extend-ignore = E203, E266, E501, W503
exclude =
    .git,
    __pycache__,
    .venv,
    venv,
    build,
    dist
```

**isort** (`pyproject.toml`):
```toml
[tool.isort]
profile = "black"
line_length = 88
multi_line_output = 3
include_trailing_comma = true
force_grid_wrap = 0
use_parentheses = true
ensure_newline_before_comments = true
```

### Usage

**Format Code**:
```bash
# Format with black
black agents/ src/

# Check formatting (no changes)
black --check agents/ src/
```

**Lint Code**:
```bash
# Run flake8
flake8 agents/ src/

# Run with configuration
flake8 --config=.flake8 agents/
```

**Organize Imports**:
```bash
# Organize imports
isort agents/ src/

# Check imports (no changes)
isort --check-only agents/ src/
```

### CI/CD Integration

**Pre-commit Hook**:
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3.13

  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8

  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort
```

## Test Coverage

### Targets

**Minimum Coverage**:
- Core components: 80%+
- Critical paths: 90%+
- Utilities: 70%+
- Overall project: 75%+

### Tools

**Coverage Tool**: `pytest-cov`

**Usage**:
```bash
# Install pytest-cov
pip install pytest-cov

# Run tests with coverage
pytest --cov=agents --cov-report=html --cov-report=term-missing

# Coverage threshold
pytest --cov=agents --cov-fail-under=80
```

**Configuration** (`pytest.ini` or `pyproject.toml`):
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

[tool:pytest]
addopts = 
    --cov=agents
    --cov=src
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=75
```

### Test Types

**Unit Tests**:
- Test individual functions/methods
- Mock external dependencies
- Fast execution
- High coverage

**Integration Tests**:
- Test multiple components together
- Use test fixtures
- Verify interactions

**End-to-End Tests**:
- Test complete workflows
- Use real dependencies when possible
- Verify end-user scenarios

**Performance Tests**:
- Benchmark critical paths
- Load testing for high-traffic scenarios
- Identify performance regressions

### Test Organization

**Directory Structure**:
```
tests/
├── unit/
│   ├── test_agent_framework.py
│   ├── test_cfbd_client.py
│   └── test_model_engine.py
├── integration/
│   ├── test_agent_workflow.py
│   └── test_cfbd_integration.py
├── e2e/
│   └── test_weekly_analysis.py
├── fixtures/
│   ├── game_data.json
│   └── team_data.json
└── conftest.py
```

**Fixtures**:
```python
# tests/conftest.py
import pytest
from agents.analytics_orchestrator import AnalyticsOrchestrator

@pytest.fixture
def orchestrator():
    return AnalyticsOrchestrator()

@pytest.fixture
def sample_game_data():
    return {
        "season": 2025,
        "week": 13,
        "home_team": "Ohio State",
        "away_team": "Michigan"
    }
```

### Writing Tests

**Test Structure**:
```python
import pytest
from agents.model_execution_engine import ModelExecutionEngine

def test_predict_game_outcome(orchestrator, sample_game_data):
    """Test game outcome prediction.
    
    GIVEN: A game between two teams
    WHEN: Predicting the outcome
    THEN: Should return prediction with confidence
    """
    engine = ModelExecutionEngine(agent_id="test_engine")
    
    result = engine._execute_action(
        "predict_game_outcome",
        sample_game_data,
        {"user_id": "test_user"}
    )
    
    assert result["status"] == "success"
    assert "prediction" in result
    assert "confidence" in result
    assert 0 <= result["confidence"] <= 1
```

**Test Best Practices**:
- Use descriptive test names
- Follow AAA pattern (Arrange, Act, Assert)
- One assertion per test when possible
- Use fixtures for reusable test data
- Mock external dependencies
- Test edge cases and error conditions

## Code Organization

### File Structure

**Module Organization**:
- Single responsibility per module
- Clear module boundaries
- Logical grouping of related functionality

**File Size Guidelines**:
- Core logic files: <500 lines
- Utility files: <300 lines
- Test files: <400 lines

### Code Style

**PEP 8 Compliance**:
- Maximum line length: 88 characters (Black default)
- Use 4 spaces for indentation
- Use blank lines to separate logical sections
- Import organization: stdlib, third-party, local

**Naming Conventions**:
- Classes: `PascalCase`
- Functions/Methods: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Private attributes: `_leading_underscore`
- Private methods: `_leading_underscore`

**Docstrings**:
```python
def calculate_epa(
    yards: float,
    down: int,
    distance: int,
    field_position: int
) -> float:
    """Calculate Expected Points Added (EPA).
    
    Args:
        yards: Yards gained on play
        down: Current down (1-4)
        distance: Yards to first down
        field_position: Current field position (0-100)
    
    Returns:
        Expected Points Added value
    
    Raises:
        ValueError: If down or distance is invalid
    
    Example:
        >>> calculate_epa(yards=5, down=1, distance=10, field_position=50)
        0.35
    """
    # Implementation
    pass
```

### Code Duplication

**DRY Principle**:
- Don't Repeat Yourself
- Extract common functionality
- Use functions/classes for reuse
- Avoid copy-paste code

**Refactoring Checklist**:
- [ ] Identify duplicate code patterns
- [ ] Extract to shared function/class
- [ ] Update all usages
- [ ] Add tests for extracted code
- [ ] Remove duplicate code

## Documentation Requirements

### Code Documentation

**Required Documentation**:
- Module docstrings (top of file)
- Class docstrings
- Public function/method docstrings
- Complex algorithm explanations

**Docstring Format**: Google-style

```python
"""Module for game data processing.

This module provides functionality for processing college football
game data, including data validation, transformation, and analysis.

Example:
    >>> from src.game_processor import process_game
    >>> game_data = {"season": 2025, "week": 13}
    >>> result = process_game(game_data)
"""

class GameProcessor:
    """Processor for college football game data.
    
    Attributes:
        season: Current season year
        week: Current week number
    """
    pass
```

### API Documentation

**Requirements**:
- Document all public APIs
- Include parameter descriptions
- Document return values
- Include examples where helpful

**Auto-generation**:
- Use Sphinx for API documentation
- Generate from docstrings
- Include type information
- Link to examples

### README Files

**Required Sections**:
- Project description
- Installation instructions
- Usage examples
- Configuration options
- Contributing guidelines

## Quality Metrics

### Targets

**Code Quality**:
- Type hint coverage: 100% (public APIs)
- Test coverage: 75%+ (overall)
- Linting: Zero warnings
- Documentation: All public APIs documented

**Maintainability**:
- Cyclomatic complexity: <10 per function
- File size: <500 lines (core logic)
- Function length: <50 lines
- Class cohesion: High

**Performance**:
- Test execution: <5 minutes (full suite)
- Import time: <2 seconds (main modules)
- Memory usage: Within acceptable limits

### Monitoring

**Regular Checks**:
- Run linting before commits
- Check type hints in CI/CD
- Monitor test coverage trends
- Review code complexity metrics

## CI/CD Integration

### Quality Gates

**Pre-commit Checks**:
- Linting (black, flake8)
- Type checking (mypy)
- Import organization (isort)
- Syntax validation

**CI Pipeline**:
1. Install dependencies
2. Run linting checks
3. Run type checking
4. Run tests with coverage
5. Check coverage threshold
6. Generate coverage report

**Example Workflow**:
```yaml
# .github/workflows/quality.yml
name: Code Quality

on: [push, pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.13'
      - name: Install dependencies
        run: pip install -r requirements-dev.txt
      - name: Lint
        run: |
          black --check agents/ src/
          flake8 agents/ src/
          isort --check-only agents/ src/
      - name: Type check
        run: mypy agents/ src/
      - name: Test
        run: pytest --cov=agents --cov-report=xml
      - name: Coverage
        run: pytest --cov=agents --cov-fail-under=75
```

## References

- **Main Documentation**: `AGENTS.md`
- **Architecture Guide**: `docs/ARCHITECTURE_IMPROVEMENTS.md`
- **Security Guide**: `docs/SECURITY_BEST_PRACTICES.md`
- **PEP 8**: https://pep8.org/
- **Type Hints**: https://docs.python.org/3/library/typing.html
- **Black**: https://black.readthedocs.io/
- **MyPy**: https://mypy.readthedocs.io/
- **pytest**: https://docs.pytest.org/

