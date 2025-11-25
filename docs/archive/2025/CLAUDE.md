# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**Project Type**: College football analytics platform with multi-agent AI system and ML prediction models
**Primary Language**: Python 3.13+ (React/TypeScript frontend in `web_app/`)
**Key Technologies**: CFBD API, scikit-learn, XGBoost, FastAI, pytest, multi-agent architecture
**Architecture**: Production-ready multi-agent system with role-based access control and ensemble ML models

## 🚀 Quick Start & Environment Setup

### First Steps for New Users

```bash
# 1. Verify Python 3.13+ (REQUIRED)
python3.13 --version

# 2. Create and activate virtual environment
python3.13 -m venv venv
source venv/bin/activate  # Linux/macOS

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt        # Core dependencies
pip install -r requirements-dev.txt    # Development dependencies

# 4. Set up environment variables (CRITICAL - never hardcode API keys)
export CFBD_API_KEY="your-api-key-here"
export CFBD_GRAPHQL_DISABLED=true      # Disable GraphQL for CFBD integration
export PYTHONPATH="${PYTHONPATH}:$(pwd)" # Set Python path

# 5. Quick system health checks
python -c "from agents.analytics_orchestrator import AnalyticsOrchestrator; print('✅ Agent system OK')"
python -c "from agents.model_execution_engine import ModelExecutionEngine; print('✅ Model engine OK')"

# 6. Complete system demonstration
python project_management/core_tools/demo_agent_system.py

# 7. Run comprehensive tests
python -m pytest tests/ -v
```

### Primary Development Workflow

**Weekly Analysis Pipeline** (Core Feature):
```bash
# Complete weekly pipeline (main use case)
python3 scripts/run_weekly_analysis.py --week 13

# Step-by-step breakdown:
python3 scripts/cfbd_pull.py --season 2025 --week 13     # 1. Data acquisition
python3 scripts/run_weekly_analysis.py --week 13        # 2. Analysis & predictions
```

**Agent System Development**:
```bash
# Test agent functionality
python3 agents/demo_agent_system.py                      # System demonstration
python3 agents/test_agent_system.py                     # Smoke tests

# Single agent prediction test
python -c "from agents.model_execution_engine import ModelExecutionEngine; print(ModelExecutionEngine('me')._execute_action('predict_game_outcome', {'team1':'Ohio State','team2':'Michigan'}, {}))"
```

### Core Development Commands

**System Validation**:
```bash
python -c "from agents.analytics_orchestrator import AnalyticsOrchestrator; print('✅ Agent system OK')"
python -c "from agents.model_execution_engine import ModelExecutionEngine; print('✅ Model engine OK')"
python project_management/core_tools/test_agents.py                        # Quick validation
```

**Testing**:
```bash
python -m pytest tests/ -v --cov=agents --cov=model_pack                   # Full test suite
python -m pytest agents/tests -q                                          # Agent tests only
python3 agents/test_agent_system.py                                       # Smoke tests
find . -name "*.py" -exec python3 -m py_compile {} \;                     # Syntax validation
```

**Code Quality**:
```bash
black --check agents/ tests/                         # Code formatting
ruff check agents/ tests/                            # Fast linting
mypy agents/                                         # Type checking
pip-audit                                           # Security scan
```

**Model Operations**:
```bash
python model_pack/model_training_agent.py                           # Model validation
python project_management/config/retrain_fixed_models.py            # Retrain models
python project_management/core_tools/data_workflows.py train-fastai --epochs 300
```

**Frontend Development** (React/TypeScript):
```bash
cd web_app && npm install                                            # Install deps
cd web_app && npm run dev                                           # Start dev server
cd web_app && npm run build                                         # Production build
cd web_app && npm run test                                          # Run frontend tests
```

**Educational Content**:
```bash
cd starter_pack && jupyter lab                                      # Data analysis notebooks
cd model_pack && jupyter lab                                        # ML modeling notebooks
```

## 🏗️ Architecture Overview

Script Ohio 2.0 is a **college football analytics platform** with a multi-agent AI system and ML prediction models.

### High-Level Architecture

**Multi-Agent System** (`agents/`):
- **BaseAgent Framework** (`agents/core/agent_framework.py`): All agents inherit from this with 4-level permission system
- **Analytics Orchestrator** (`agents/analytics_orchestrator.py`): Central request routing and coordination
- **Specialized Agents**: Model execution, insight generation, workflow automation, educational guidance

**Data Pipeline**:
- **CFBD API Integration**: Rate-limited (6 req/sec) college football data from CollegeFootballData.com
- **Training Data**: 4,989 games (2016-2025) with 86 opponent-adjusted features in `model_pack/updated_training_data.csv`
- **Weekly Processing**: Automated analysis pipelines in `scripts/run_weekly_analysis.py`

**Machine Learning**:
- **Pre-trained Models**: Ridge regression, XGBoost classifier, FastAI neural network (`model_pack/*_model_2025.*`)
- **Feature Engineering**: 86 opponent-adjusted features preventing data leakage
- **Model Execution**: Batch predictions with confidence intervals

**Frontend** (`web_app/`):
- React/TypeScript application with Vite build system
- Tailwind CSS for styling, Recharts for data visualization
- Deployed on Vercel, consumes Python backend predictions

**Key Patterns**:
- **Agent Development**: All agents must inherit from `BaseAgent` and implement `_define_capabilities()` and `_execute_action()`
- **Data Access**: CFBD API key via environment variable, never hardcoded
- **Testing**: pytest with comprehensive test suite, performance benchmarks
- **Educational Content**: Progressive Jupyter notebooks from basics to advanced modeling

## 🤖 Agent Development

### BaseAgent Inheritance Pattern (CRITICAL REQUIREMENT)

All agents **must** inherit from `BaseAgent` in `agents/core/agent_framework.py`. This is non-negotiable for system integration.

```python
from agents.core.agent_framework import BaseAgent, AgentCapability, PermissionLevel
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class CustomAnalyticsAgent(BaseAgent):
    """Template for creating new analytics agents"""

    def __init__(self, agent_id: str):
        super().__init__(
            agent_id=agent_id,
            name="Custom Analytics Agent",
            permission_level=PermissionLevel.READ_EXECUTE
        )

    def _define_capabilities(self) -> List[AgentCapability]:
        """Define agent capabilities with execution time estimates"""
        return [
            AgentCapability(
                name="custom_analysis",
                description="Perform custom football analytics",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["pandas", "numpy"],
                data_access=["model_pack/updated_training_data.csv"],
                execution_time_estimate=2.0
            )
        ]

    def _execute_action(self, action: str, parameters: Dict[str, Any],
                      user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent-specific logic with comprehensive error handling"""
        try:
            if action == "custom_analysis":
                return {"result": "Analysis completed successfully"}
            else:
                raise ValueError(f"Unknown action: {action}")
        except Exception as e:
            logger.error(f"Error in {self.__class__.__name__}: {str(e)}")
            return {
                "status": "error",
                "error_message": str(e),
                "execution_time": 0
            }
```

### Agent Development Workflow (Production-Ready Pattern)

```bash
# Step 1: Create new agent file
touch agents/your_new_agent.py

# Step 2: Implement using the BaseAgent template (see above)

# Step 3: Test your agent thoroughly
python -m pytest tests/test_your_new_agent.py -v

# Step 4: Register with factory
python -c "
from agents.core.agent_framework import AgentFactory
from agents.your_new_agent import YourNewAgent
factory = AgentFactory()
factory.register_agent_class(YourNewAgent, 'your_agent_name')
print('✅ Agent registered successfully')
"

# Step 5: Verify integration
python -c "
from agents.analytics_orchestrator import AnalyticsOrchestrator
orchestrator = AnalyticsOrchestrator()
print('✅ System integration verified')
"
```

### Permission System (4-Level Security)

**PermissionLevel Enum** (from `agents/core/agent_framework.py`):
- **Level 1 (READ_ONLY)**: Context Manager, Performance Monitor
- **Level 2 (READ_EXECUTE)**: Learning Navigator, Model Engine, Data Access Agents
- **Level 3 (READ_EXECUTE_WRITE)**: Insight Generator, Workflow Automator
- **Level 4 (ADMIN)**: Analytics Orchestrator, System Management

#### Permission Best Practices

```python
# Choose appropriate permission level based on agent responsibilities
permission_level_map = {
    "data_access_only": PermissionLevel.READ_ONLY,
    "analysis_and_models": PermissionLevel.READ_EXECUTE,
    "create_insights": PermissionLevel.READ_EXECUTE_WRITE,
    "system_management": PermissionLevel.ADMIN
}

# Validate permissions in capability definitions
capability = AgentCapability(
    name="sensitive_operation",
    description="Access to sensitive data",
    permission_required=PermissionLevel.ADMIN,  # Require high permission
    tools_required=["secure_tool"],
    data_access=["restricted_data"],
    execution_time_estimate=5.0
)
```

### Agent Registration and Factory Pattern

```python
from agents.core.agent_framework import AgentFactory

# 1. Create factory instance
factory = AgentFactory()

# 2. Register agent class
factory.register_agent_class(CustomAnalyticsAgent, "custom_analytics")

# 3. Create agent instance
agent = factory.create_agent("custom_analytics", "agent_001")

# 4. Verify agent capabilities
capabilities = agent.capabilities
print(f"Agent has {len(capabilities)} capabilities")
```

#### Agent Naming Conventions (Critical for Integration)
- **Files**: `{domain}_agent.py` (e.g., `learning_navigator_agent.py`)
- **Classes**: `{Domain}Agent` (e.g., `LearningNavigatorAgent`)
- **Types**: `{domain}_agent` (e.g., `"learning_navigator"`)
- **IDs**: `{domain}_{identifier}` (e.g., `"learning_001"`)

### Development Workflow (Micro-Slice Approach)

```bash
# Work in small slices (30-60 minutes)
# 1. Pick one task
# 2. Complete the task
# 3. Immediately run the happy path: python3 scripts/run_weekly_analysis.py --week 13
# 4. If it breaks, fix or revert before adding new work
# 5. Log progress in SESSION_LOG.md
```

## 🌐 CFBD API Integration (Verified Official Standards)

### Authentication and Security Patterns

```python
import os
import cfbd
import time
import logging
from cfbd import Configuration, ApiClient, GamesApi, StatsApi, TeamsApi

logger = logging.getLogger(__name__)

# Secure authentication using environment variables (REQUIRED)
configuration = Configuration()
configuration.api_key['Authorization'] = f"Bearer {os.environ['CFBD_API_KEY']}"
configuration.api_key_prefix['Authorization'] = 'Bearer'
configuration.host = "https://api.collegefootballdata.com"

# Alternative: Use Next API for experimental features
# configuration.host = "https://apinext.collegefootballdata.com"

# Create API clients
with cfbd.ApiClient(configuration) as api_client:
    games_api = GamesApi(api_client)
    stats_api = StatsApi(api_client)
    teams_api = TeamsApi(api_client)
```

### Rate Limiting Implementation (CRITICAL - 6 req/sec maximum)

```python
class CFBDRateLimitedClient:
    """CFBD API client with built-in rate limiting"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.last_request_time = 0
        self.rate_limit_delay = 0.17  # 6 requests/second = 1/6 = 0.17s delay

    def _rate_limit(self):
        """Implement rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def safe_cfbd_call(self, api_function, *args, **kwargs):
        """Safe CFBD API call with comprehensive error handling"""
        try:
            self._rate_limit()  # Apply rate limiting
            result = api_function(*args, **kwargs)

            if not result:
                logger.warning("CFBD API returned empty result")
                return None

            return result

        except Exception as e:
            logger.error(f"CFBD API error: {str(e)}")

            # Handle specific error types
            if "401" in str(e):
                logger.error("Authentication failed - check API key")
            elif "429" in str(e):
                logger.error("Rate limit exceeded - increase delay")
            elif "timeout" in str(e).lower():
                logger.warning("Request timeout - retry with exponential backoff")

            return None
```

### Data Transformation for 86-Feature Model Pipeline

```python
import pandas as pd
import numpy as np
from typing import Dict, List

def transform_cfbd_to_model_features(games_data: List[Dict]) -> pd.DataFrame:
    """Transform CFBD data into 86 opponent-adjusted features for model compatibility"""
    df = pd.DataFrame(games_data)
    features = []

    for _, game in df.iterrows():
        game_features = {
            'season': game.get('season', 0),
            'week': game.get('week', 0),
            'home_points': game.get('home_points', 0),
            'away_points': game.get('away_points', 0),
            # ... continue with remaining 82 features to match training data format
        }
        features.append(game_features)

    feature_df = pd.DataFrame(features)

    # Ensure 86 columns for model compatibility
    if len(feature_df.columns) != 86:
        logger.warning(f"Expected 86 features, got {len(feature_df.columns)}")

    return feature_df
```

### CFBD Integration Resources (Verified)
- **Official Website**: https://collegefootballdata.com/
- **API Documentation**: https://apinext.collegefootballdata.com/
- **Python Client**: https://github.com/CFBD/cfbd-python
- **Rate Limiting**: 6 requests/second maximum (use `time.sleep(0.17)`)
- **Data Coverage**: Historical data 1869-present, play-by-play 2003-present

## 📊 Data Workflows & Model Operations

### High-Level Data Orchestration

```bash
# Data pipeline commands
python project_management/core_tools/data_workflows.py starter-data --season 2025 --week 13
python project_management/core_tools/data_workflows.py extend-training --migrated-file model_pack/2025_starter_pack_migrated.csv
python project_management/core_tools/data_workflows.py train-fastai --epochs 300 --learning-rate 0.001
python project_management/core_tools/data_workflows.py refresh-training --max-week 13 --train-models
```

### Model Training and Validation

```bash
# Model operations
python model_pack/model_training_agent.py                           # Model validation
python project_management/config/retrain_fixed_models.py            # Retrain with new data
python model_pack/2025_data_acquisition.py                         # Acquire latest data

# FastAI custom training
python project_management/core_tools/data_workflows.py train-fastai --epochs 300 --learning-rate 0.001
```

### Educational Content Structure

**Educational Notebooks** (`starter_pack/`, 13 notebooks):
- **Beginner**: `00_data_dictionary.ipynb` → `01_intro_to_data.ipynb` → `02_build_simple_rankings.ipynb`
- **Intermediate**: `03_metrics_comparison.ipynb` → `04_team_similarity.ipynb` → `05_matchup_predictor.ipynb`
- **Advanced**: `06_predictive_modeling.ipynb` → `07_advanced_visualizations.ipynb`

**ML Modeling Notebooks** (`model_pack/`, 7+ notebooks):
- `01_linear_regression_margin.ipynb`: Margin prediction
- `03_xgboost_win_probability.ipynb`: Classification modeling
- `04_fastai_win_probability.ipynb`: Neural network approach

## 🧪 Testing & Quality Assurance

### Comprehensive Testing Suite

```bash
# Run all tests with coverage
python -m pytest tests/ -v --cov=agents --cov=model_pack --cov-report=html

# Specific component testing
python -m pytest tests/test_agent_system.py -v                       # Agent system
python -m pytest tests/test_model_pack_comprehensive.py -v           # Model integration
python -m pytest tests/test_model_execution_engine_comprehensive.py -v  # Model engine
python -m pytest tests/test_week12_agents_comprehensive.py -v        # Week 12 agents

# Performance testing
pytest -m performance tests/ -v                                      # Response time validation

# Quick validation
python project_management/core_tools/test_agents.py                  # Agent health check
python project_management/quality_assurance/test_fixed_system.py     # Full system validation
```

### Performance Requirements

- **Agent Response Time**: <2 seconds for all operations
- **Model Training**: FastAI models train in <5 minutes on standard hardware
- **Memory Usage**: <100MB increase for normal operations
- **Cache Hit Rate**: >80% for repeated requests

### Code Quality Standards

```bash
# Syntax validation (all files must pass)
find . -name "*.py" -exec python3 -m py_compile {} \;

# Code quality checks
black --check agents/ tests/          # Code formatting
ruff check agents/ tests/            # Fast linting (replaces flake8)
mypy agents/                         # Type checking

# Coverage requirements (minimum 85% for core components, 90% goal)
pytest --cov=agents --cov-report=term-missing
```

## 📁 Key Directories & Files

```
agents/                              # Multi-agent system
├── core/agent_framework.py         # BaseAgent class (all agents inherit from this)
├── analytics_orchestrator.py        # Central request routing
├── model_execution_engine.py        # ML model predictions
└── [specialized_agents].py          # Domain-specific agents

web_app/                             # React/TypeScript frontend
├── package.json                     # NPM dependencies (Vite, React 19, TypeScript)
├── src/types.ts                     # TypeScript type definitions
└── src/                             # React components

starter_pack/                        # Educational notebooks (13 total)
├── data/                           # Historical datasets (read-only)
└── *.ipynb                         # Learning progression notebooks

model_pack/                          # ML modeling + pre-trained models
├── updated_training_data.csv        # 4,989 games, 86 features (2016-2025)
├── ridge_model_2025.joblib          # Ridge regression model
├── xgb_home_win_model_2025.pkl      # XGBoost classifier
└── fastai_home_win_model_2025.pkl   # Neural network model

scripts/                             # Utility scripts (62+ tools)
├── run_weekly_analysis.py           # Main weekly pipeline
├── cfbd_pull.py                     # CFBD API data acquisition
└── [specialized_scripts].py         # Domain-specific utilities

tests/                               # pytest test suite
├── conftest.py                      # pytest configuration
├── test_agent_system.py             # Agent system tests
└── [specific_tests].py              # Component-specific tests

data/                                # Data organization
├── weekly/week{XX}/enhanced/        # Weekly enhanced features
└── training/weekly/                 # Weekly training files
```

**Critical Files**:
- `requirements.txt` / `pyproject.toml` - Python dependencies and Black/Ruff configuration
- `agents/core/agent_framework.py` - BaseAgent class (CRITICAL: all agents must inherit from this)
- `model_pack/updated_training_data.csv` - Master training dataset (86 opponent-adjusted features)
- `pytest.ini` - Test configuration with custom markers (integration, performance)
- `web_app/src/types.ts` - Frontend TypeScript definitions for data contracts

## 🔧 Development Workflows & Patterns

### Agent Development Workflow

```bash
# Step 1: Create new agent
touch agents/your_new_agent.py

# Step 2: Implement BaseAgent inheritance (use template from .cursorrules)

# Step 3: Test your agent thoroughly
python -m pytest tests/test_your_new_agent.py -v
find . -name "*.py" -exec python3 -m py_compile {} \;  # Syntax validation

# Step 4: Register with factory
python -c "
from agents.core.agent_framework import AgentFactory
from agents.your_new_agent import YourNewAgent
factory = AgentFactory()
factory.register_agent_class(YourNewAgent, 'your_agent_name')
print('✅ Agent registered successfully')
"

# Step 5: Verify integration
python -c "
from agents.analytics_orchestrator import AnalyticsOrchestrator
orchestrator = AnalyticsOrchestrator()
print('✅ System integration verified')
"
```

### Context Window Management

For long-running sessions, manage context efficiently:

```python
# Clear context between major phases
/clear  # Clear Claude's context window

# Use focused queries (recommended approach)
# Good: "What are the top 5 most efficient offenses in 2025 by EPA/play?"
# Bad: "Analyze everything about the 2025 season"

# Use context manager for optimization
from agents.core.context_manager import ContextManager, UserRole

context_manager = ContextManager()
optimized_context = context_manager.get_optimized_context(
    user_id="your_user_id",
    role=UserRole.DATA_SCIENTIST,  # 75% token budget
    query="specific focused query"
)
```

### Performance Monitoring

```python
# Monitor agent performance
import time
from agents.analytics_orchestrator import AnalyticsOrchestrator

orchestrator = AnalyticsOrchestrator()
start_time = time.time()
response = orchestrator.process_analytics_request(request)
print(f'Response time: {time.time() - start_time:.2f}s (target: <2s)')
```

### Frontend Development Patterns

**TypeScript Integration** (`web_app/src/types.ts`):
```typescript
// Define TypeScript interfaces for data contracts
interface GamePrediction {
  homeTeam: string;
  awayTeam: string;
  homeWinProbability: number;
  predictedMargin: number;
  confidence: number;
}

interface TeamStats {
  team: string;
  season: number;
  offense: {
    pointsPerGame: number;
    yardsPerGame: number;
  };
  defense: {
    pointsAllowedPerGame: number;
    yardsAllowedPerGame: number;
  };
}
```

### Pull Request Requirements

Before submitting a pull request:

```bash
# Required validation checks
python3 -m pytest agents/tests -q                    # Agent tests
python3 agents/test_agent_system.py                   # Smoke tests
find . -name "*.py" -exec python3 -m py_compile {} \; # Syntax validation

# Security and quality checks
pip-audit                                            # Security scan
black --check agents/ tests/                         # Code formatting
mypy agents/                                         # Type checking

# Frontend validation (if modified)
cd web_app && npm run typecheck && npm run test      # TypeScript check + tests
```

**Security Checklist**:
- [ ] No hardcoded secrets or API keys (CRITICAL)
- [ ] All environment variables documented
- [ ] Dependencies scanned for vulnerabilities
- [ ] Input validation implemented for new features
- [ ] Error messages don't expose system internals

**Code Quality Checklist**:
- [ ] Type hints added to public APIs
- [ ] Code passes linting and formatting checks
- [ ] Test coverage maintained or improved (85%+ minimum)
- [ ] Documentation updated for new features
- [ ] Frontend TypeScript types defined for API contracts

## 🚨 Important Notes & Security

### Security Requirements (CRITICAL)
- **Never hardcode API keys**: Use environment variables (`export CFBD_API_KEY="your-key"`)
- **⚠️ IMMEDIATE ACTION REQUIRED**: Remove any hardcoded secrets found in `debug_cfbd_auth.py` or `.env` files
- **Rate limiting**: 6 requests/second maximum - use `time.sleep(0.17)` between CFBD API calls
- **No secrets in commits**: Never commit `.env` files or hardcoded credentials
- **Input validation**: Validate all user inputs using Pydantic models
- **Error handling**: Don't expose system internals in error messages

### Data Handling
- **Source CSVs**: `starter_pack/data/` files are read-only historical artifacts
- **Large files**: Never commit derived datasets larger than 5 MB
- **Model features**: All training data includes opponent-adjusted features to prevent data leakage

### Environment Variables (Required)
```bash
# Required for CFBD API integration
export CFBD_API_KEY="your-api-key-here"
export CFBD_GRAPHQL_DISABLED=true  # Disable GraphQL for CFBD integration

# Python path for imports (run from project root)
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

## 🔍 Troubleshooting Common Issues

### Security-Related Errors (Critical)

**Problem**: Hardcoded API keys or secrets in code
**Solution**:
```bash
# Remove immediately
git rm debug_cfbd_auth.py .env
echo ".env" >> .gitignore
echo "debug_*" >> .gitignore
# Regenerate API keys and use environment variables
```

**Problem**: `CFBD_API_KEY not found in environment`
**Solution**:
```bash
export CFBD_API_KEY="your-api-key-here"
# Add to shell profile (.bashrc, .zshrc) for persistence
```

### Import Errors
```bash
# Set Python path from project root
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python -c "from agents.core.agent_framework import BaseAgent"
```

### Model Loading Issues
```bash
# Verify model files exist
ls -la model_pack/*_2025.*
python -c "from pathlib import Path; print(Path('model_pack/ridge_model_2025.joblib').exists())"
```

### Agent System Issues
```bash
# Test agent factory registration
python -c "
from agents.core.agent_framework import AgentFactory
factory = AgentFactory()
print('Registered agents:', list(factory.registered_agents.keys()))
"

# Test analytics orchestrator directly
python -c "
from agents.analytics_orchestrator import AnalyticsOrchestrator, AnalyticsRequest
orchestrator = AnalyticsOrchestrator()
request = AnalyticsRequest('test_user', 'test query', 'analysis', {}, {})
response = orchestrator.process_analytics_request(request)
print(f'Status: {response.status}, Time: {response.execution_time:.2f}s')
"
```

### Frontend Development Issues
```bash
# TypeScript errors
cd web_app && npm run typecheck

# Missing dependencies
cd web_app && npm install

# Build issues
cd web_app && npm run build
```

## 📚 Key Resources & Documentation

### Essential Documentation
- **📖 Complete Agent Guide**: `AGENTS.md` (comprehensive agent development guidelines)
- **🔧 System Demo**: `python project_management/core_tools/demo_agent_system.py`
- **📊 Quality Assurance**: `project_management/quality_assurance/VERIFICATION_REPORT_2025.md`
- **🎓 Educational Content**: `starter_pack/CLAUDE.md` (notebook learning guidance)
- **🧪 Testing Guide**: `tests/CLAUDE.md` (comprehensive testing documentation)
- **🎯 Development Patterns**: `.cursorrules` (Cursor-specific development patterns and shortcuts)
- **🌐 Frontend Contract**: `web_app/DATA_CONTRACT.md` (API surface definition)

### Additional Key Files
- **📋 Agent Development**: See `.cursorrules` for comprehensive BaseAgent templates and patterns
- **🔧 Integration Scripts**: `scripts/` directory contains 62+ utility scripts for data integration and analysis
- **📦 Configuration**: `config/` directory for deployment and system configuration
- **🎯 Model Files**: Pre-trained models in `model_pack/` (ridge_model_2025.joblib, xgb_home_win_model_2025.pkl, fastai_home_win_model_2025.pkl)
- **🌐 Frontend Types**: `web_app/src/types.ts` for TypeScript interface definitions

### CFBD Integration Resources
- **Official Website**: https://collegefootballdata.com/
- **API Documentation**: https://apinext.collegefootballdata.com/
- **Python Client**: https://github.com/CFBD/cfbd-python
- **Rate Limiting**: 6 requests/second maximum

### Platform Specifications
- **Python Version**: 3.13+ required
- **Data Coverage**: Historical data 1869-present, model training 2016-2025 (4,989 games)
- **Performance**: <2 second response times, 85%+ test coverage goal
- **Architecture**: Multi-agent system with role-based context optimization

### Quick Validation Commands
```bash
# System health
python -c "from agents.analytics_orchestrator import AnalyticsOrchestrator; print('✅ Agent system OK')"
python -c "from agents.model_execution_engine import ModelExecutionEngine; print('✅ Model engine OK')"

# Comprehensive testing
python -m pytest tests/ -v --cov=agents --cov=model_pack

# Educational environment
cd starter_pack && jupyter lab  # Start with: 00_data_dictionary.ipynb

# Complete system validation
python project_management/core_tools/test_agents.py && python project_management/quality_assurance/test_fixed_system.py

# Frontend validation
cd web_app && npm run typecheck && npm run test
```

## ⚡ Quick Reference

**Environment Setup**:
```bash
export CFBD_API_KEY="your-api-key-here"
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

**Most Common Commands**:
```bash
python3 scripts/run_weekly_analysis.py --week 13     # Run weekly analysis
python -m pytest tests/ -v                          # Run all tests
python3 agents/demo_agent_system.py                  # Test agent system
cd web_app && npm run dev                            # Start frontend dev server
```

**Critical Files**:
- `agents/core/agent_framework.py` - BaseAgent class (all agents inherit from this)
- `model_pack/updated_training_data.csv` - Training data (4,989 games, 86 features)
- `requirements.txt` / `pyproject.toml` - Dependencies and code quality configuration
- `pytest.ini` - Test configuration
- `web_app/src/types.ts` - Frontend TypeScript type definitions

**Key Patterns**:
- All agents inherit from `BaseAgent` with 4-level permission system
- CFBD API rate limiting: 6 req/sec (use `time.sleep(0.17)`)
- Never hardcode API keys - use environment variables
- Feature engineering uses opponent-adjusted features to prevent data leakage
- Frontend uses TypeScript interfaces for type safety
- Test coverage requirement: 85% minimum for core components

## Platform Philosophy

Script Ohio 2.0 represents a new paradigm in sports analytics: **conversational intelligence** that makes sophisticated football analytics accessible through natural language. The multi-agent system bridges the gap between complex data science and intuitive user experiences, providing role-appropriate interfaces for everyone from students to production systems.

**Design Principles**: Following Claude's best practices for agent development - focused capabilities, clear boundaries, modular design, and comprehensive performance monitoring.

**Production Ready**: The platform maintains 99%+ uptime with <2 second response times, 85%+ test coverage, and comprehensive error handling for robust deployment. The architecture demonstrates enterprise-grade patterns while maintaining educational accessibility.

**Security First**: While the platform demonstrates strong architectural patterns, immediate attention is required for secret management and input validation to ensure production security standards are met.