# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Script Ohio 2.0 is a comprehensive college football analytics platform featuring:
- **Multi-Agent Architecture**: Production-ready agent system with 15+ specialized agents
- **Machine Learning Models**: Three pre-trained models (Ridge Regression, XGBoost, FastAI) for game outcome predictions
- **CFBD Integration**: Unified client for CollegeFootballData.com API with rate limiting and caching
- **Weekly Analysis Pipeline**: Automated weekly matchup analysis and prediction generation
- **TOON Format Support**: Token-optimized workflow plans for efficient LLM processing

## Quick Start Commands

### Environment Setup
```bash
# Create virtual environment (Python 3.13+ required)
python3.13 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set API key (required for CFBD integration)
export CFBD_API_KEY="your-api-key-here"
```

### Core Development Tasks
```bash
# Run weekly analysis pipeline
python3 scripts/run_weekly_analysis.py --week 13

# Build training data from CFBD
python3 scripts/build_training_data_from_cfbd.py --season 2025 --week 14

# Generate predictions for bowls 2025
python3 scripts/predict_bowls_2025.py --season 2025 --method all --backup-existing --force

# Test agent system
python3 agents/demo_agent_system.py

# Run all tests
python3 -m pytest agents/tests -q

# Verify agent system
python3 agents/test_agent_system.py
```

### Model Management
```bash
# Retrain models with current data
python3 scripts/retrain_models_current.py

# Integrate new weekly training data
python3 scripts/integrate_weekly_files.py --season 2025 --weeks 15 --include-postseason

# Roll back training data from backup
python3 scripts/rollback_integration.py
```

### Bowl Predictions
```bash
# Generate all bowl prediction methods with backup
python3 scripts/predict_bowls_2025.py --season 2025 --method all --backup-existing --force

# Generate specific method only
python3 scripts/predict_bowls_2025.py --season 2025 --method ml

# Preview without creating files
python3 scripts/predict_bowls_2025.py --season 2025 --dry-run

# Check available prediction files
ls predictions/bowls_2025_predictions_*.json
```

### Code Quality & Security
```bash
# Syntax validation (all Python files)
find . -name "*.py" -exec python3 -m py_compile {} \;

# Type checking
mypy agents/ src/ scripts/

# Linting
black --check agents/ src/ scripts/
ruff check agents/ src/ scripts/

# Security audit
pip-audit
```

## Architecture Overview

### Multi-Agent System
The project uses a sophisticated agent architecture with:

**Core Framework** (`agents/core/`):
- `agent_framework.py`: BaseAgent class with 4-level permission system
- `context_manager.py`: Context compression and role detection
- `tool_loader.py`: Dynamic tool loading and management

**Key Agent Types**:
- **Analytics Orchestrator**: Routes requests to appropriate agents
- **Model Execution Engine**: ML predictions and ensemble methods
- **CFBD Integration Agent**: Rate-limited API access with caching
- **Insight Generator**: Advanced analytics and visualizations
- **Workflow Automator**: Multi-step pipeline execution

All agents inherit from `BaseAgent` and follow the pattern:
```python
from agents.core.agent_framework import BaseAgent, AgentCapability, PermissionLevel

class CustomAgent(BaseAgent):
    def __init__(self, agent_id: str):
        super().__init__(agent_id, "Agent Name", PermissionLevel.READ_EXECUTE)

    def _define_capabilities(self) -> List[AgentCapability]:
        return [AgentCapability(name="action", ...)]

    def _execute_action(self, action: str, parameters: Dict, user_context: Dict) -> Dict:
        # Implementation
        pass
```

### Data Pipeline Architecture

**Data Flow**:
1. **CFBD API** → Raw data with rate limiting (6 req/sec)
2. **Feature Engineering** → 86 opponent-adjusted features
3. **Model Training** → Three ensemble models (Ridge, XGBoost, FastAI)
4. **Weekly Analysis** → Automated predictions and reports

**Data Organization**:
- **Master Training Data**: `model_pack/updated_training_data.csv` (4,989 games, 2016-2025)
- **Weekly Training**: `data/training/weekly/training_data_2025_week*.csv`
- **Enhanced Features**: `data/weekly/week{XX}/enhanced/`
- **Model Files**: `model_pack/{ridge,xgb,fastai}_*_2025.{joblib,pkl}`

### Model System

**Pre-trained Models**:
- `ridge_model_2025.joblib`: Ridge regression model
- `xgb_home_win_model_2025.pkl`: XGBoost classifier
- `fastai_home_win_model_2025.pkl`: FastAI neural network

**Feature Engineering**:
- 86 opponent-adjusted features to prevent data leakage
- Normalized stat lines (yards per play, success rates, etc.)
- Market-based features (betting lines, consensus picks)
- Historical performance metrics

## Key Development Patterns

### CFBD Integration
Always use the unified client with proper rate limiting:

```python
from src.cfbd_client.unified_client import UnifiedCFBDClient
import time

client = UnifiedCFBDClient()
# Rate limiting: 6 req/sec → time.sleep(0.17) between requests
```

**Authentication**:
```python
import os
from cfbd import Configuration, ApiClient, GamesApi

configuration = Configuration()
configuration.api_key['Authorization'] = f"Bearer {os.environ['CFBD_API_KEY']}"
games_api = GamesApi(ApiClient(configuration))
```

### Data Access Patterns
Use the centralized path utilities:

```python
from model_pack.utils.path_utils import get_training_data_file, get_weekly_training_file

# Master training data
training_path = get_training_data_file()
df = pd.read_csv(training_path)

# Weekly data with automatic fallback search
week_file = get_weekly_training_file(week=13, season=2025)
df = pd.read_csv(week_file)
```

### Agent Development
Follow these patterns when creating new agents:

1. **Inherit from BaseAgent** with proper permission level
2. **Define capabilities** with execution time estimates
3. **Implement _execute_action** with comprehensive error handling
4. **Use dataclasses** for request/response objects
5. **Add comprehensive tests** in `agents/tests/`

### Weekly Analysis Pipeline
The weekly pipeline follows this structure:
1. **Model Validation**: Verify model performance on recent data
2. **Matchup Analysis**: Enhanced features for upcoming games
3. **Prediction Generation**: Ensemble model predictions
4. **Report Creation**: Comprehensive analysis reports

Outputs saved to:
- Predictions: `predictions/week{XX}/`
- Enhanced data: `data/weekly/week{XX}/enhanced/`
- Reports: `reports/`

## File Structure & Conventions

### Directory Organization
```
agents/                 # Multi-agent system (15+ specialized agents)
├── core/              # Agent framework and base classes
├── tests/             # Comprehensive test suite
└── *.py               # Individual agent implementations

src/                   # Python modules (reused notebook logic)
├── cfbd_client/       # CFBD API integration layer
├── features/          # Feature engineering utilities
├── models/            # Model execution engine
├── ratings/           # Rating systems (Massey, etc.)
└── utils/             # Shared utilities

scripts/               # Automation and utility scripts
├── run_weekly_analysis.py    # Main weekly pipeline
├── cfbd_pull.py              # CFBD data ingestion
├── predict_bowls_2025.py     # Bowl predictions
└── [many specialized scripts]

model_pack/            # ML models and training data
├── updated_training_data.csv   # Master dataset (6.8MB)
├── *_model_2025.*            # Pre-trained models
└── *.ipynb                   # Modeling notebooks

predictions/           # Generated predictions and analysis
├── bowls_2025_predictions_ml.json      # ML ensemble predictions
├── bowls_2025_predictions_massey.json  # Massey ratings predictions
├── bowls_2025_predictions_simple.json  # Simple predictions
└── bowls_2025_predictions_*_backup_*.json  # Timestamped backups

data/                 # Data organization
├── training/weekly/          # Weekly training files
├── weekly/week{XX}/enhanced/  # Enhanced features
└── metadata/                 # Data definitions

starter_pack/         # Educational notebooks (13 total)
```

### File Naming Conventions
- **Agents**: `{domain}_agent.py` (e.g., `learning_navigator_agent.py`)
- **Scripts**: `{action}_{target}.py` (e.g., `predict_bowls_2025.py`)
- **Models**: `{model_type}_model_2025.{ext}` (e.g., `ridge_model_2025.joblib`)
- **Predictions**: `bowls_2025_predictions_{method}.json` (e.g., `bowls_2025_predictions_ml.json`)
- **Backups**: `bowls_2025_predictions_{method}_backup_{timestamp}.json`
- **Data**: `training_data_2025_week*.csv`, `week{XX}_features_86.csv`

## Code Quality Standards

### Python Standards
- **Style**: PEP 8, 4-space indentation, 88-character line length
- **Type Hints**: Preferred in new modules (using `typing` module)
- **Docstrings**: Google-style for all functions and classes
- **Error Handling**: Comprehensive with specific exception types

### Testing Requirements
- **Unit Tests**: All agents must have tests in `agents/tests/`
- **Integration Tests**: End-to-end workflow validation
- **Performance Tests**: Model execution and API rate limiting
- **Syntax Validation**: 100% pass rate required

```bash
# Run complete test suite
python3 -m pytest agents/tests -q
python3 agents/test_agent_system.py
```

### Security Requirements
- **API Keys**: Never hardcode, use environment variables
- **Input Validation**: Validate all external inputs
- **Rate Limiting**: Strict adherence to CFBD API limits
- **Data Encryption**: Sensitive data encrypted at rest

## TOON Format Integration

**TOON v2.0** (Token-Oriented Object Notation) provides 50-70% token reduction:

**When to Use TOON**:
- Agent responses with uniform arrays of objects
- Analysis outputs consumed by LLMs
- Tabular data exports (games, predictions, stats)
- Cached data sent to LLMs

**Key Syntax Rules**:
- Use `[N]` format for array headers (never `[#N]`)
- Uniform arrays for maximum savings
- Quote strings that match keywords or contain delimiters

```python
from src.toon_format import encode, decode

# Encode JSON to TOON
toon_output = encode(data)

# Convert plans to TOON
python3 scripts/plan_to_workflow.py plan.md --toon
```

## Common Workflows

### Adding New Weekly Analysis
```bash
# 1. Pull latest data
python3 scripts/cfbd_pull.py --season 2025 --week 15

# 2. Generate features
python3 scripts/build_training_data_from_cfbd.py --season 2025 --week 15

# 3. Run analysis pipeline
python3 scripts/run_weekly_analysis.py --week 15

# 4. Verify outputs
ls predictions/week15/
ls data/weekly/week15/enhanced/
```

### Model Retraining
```bash
# 1. Integrate new data
python3 scripts/integrate_weekly_files.py --season 2025 --weeks 15

# 2. Retrain models
python3 scripts/retrain_models_current.py

# 3. Validate performance
python3 scripts/validate_model_performance.py
```

### Bowl Predictions
```bash
# 1. Generate all bowl predictions (ML, Massey, Simple)
python3 scripts/predict_bowls_2025.py --season 2025 --method all --backup-existing --force

# 2. Preview predictions without creating files
python3 scripts/predict_bowls_2025.py --season 2025 --dry-run

# 3. Generate specific method only
python3 scripts/predict_bowls_2025.py --season 2025 --method ml

# 4. Verify prediction files
ls predictions/bowls_2025_predictions_*.json

# 5. Start web app to serve predictions
python3 web_app/app.py
```

### Agent Development
```bash
# 1. Create agent inheriting from BaseAgent
# 2. Add capabilities in _define_capabilities()
# 3. Implement _execute_action() with error handling
# 4. Add tests in agents/tests/
# 5. Run validation
python3 -m pytest agents/tests/test_new_agent.py -q
```

## Important Notes

### Environment Variables
- `CFBD_API_KEY`: Required for CollegeFootballData.com API access
- Set via `export CFBD_API_KEY="your-key"` or in `.env` file

### Rate Limiting
- CFBD API: 6 requests per second
- Use `time.sleep(0.17)` between requests in loops
- Unified client includes automatic rate limiting

### Model Dependencies
- Pydantic v1 required for CFBD compatibility (not v2)
- FastAI model uses mock on load due to pickle protocol issues
- Ridge and XGBoost models load correctly

### Data Integrity
- Master training data: 4,989 games (2016-2025, Week 5+, FBS only)
- 86 opponent-adjusted features prevent data leakage
- All files use snake_case naming with descriptive prefixes

### Documentation References
- **Agent Development**: `AGENTS.md` - Complete framework documentation
- **Data Organization**: `docs/DATA_ORGANIZATION.md` - File structure and access patterns
- **TOON Format**: `docs/TOON_FORMAT_GUIDE.md` - Token optimization guide
- **Security**: `docs/SECURITY_BEST_PRACTICES.md` - Complete security guidelines