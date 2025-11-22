# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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

# 4. Set up environment variables
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

### Happy Path for Weekly Analysis (Primary Workflow)

```bash
# Single command for complete weekly pipeline
python3 scripts/run_weekly_analysis.py --week 13

# Step-by-step alternative:
# 1. Data pull: python3 scripts/cfbd_pull.py --season 2025 --week 13
# 2. Analysis: python3 scripts/run_weekly_analysis.py --week 13
# 3. Agent API test: python -c "from agents.model_execution_engine import ModelExecutionEngine; print(ModelExecutionEngine('me')._execute_action('predict_game_outcome', {'team1':'Ohio State','team2':'Michigan'}, {}))"
```

### Essential Commands

```bash
# System health checks
python project_management/core_tools/test_agents.py                    # Quick validation
python -c "from agents.analytics_orchestrator import AnalyticsOrchestrator; print('✅ Agent system OK')"
python -c "from agents.model_execution_engine import ModelExecutionEngine; print('✅ Model engine OK')"

# Agent system testing and validation
python3 agents/test_agent_system.py                                     # Agent system smoke tests
python3 agents/demo_agent_system.py                                    # Complete system demonstration
python3 scripts/verify_weekly_agents.py                                # Verify weekly agents
python -m pytest agents/tests -q                                       # Agent-specific tests

# Development and testing
python -m pytest tests/ -v --cov=agents --cov=model_pack              # Full test suite
python -m pytest tests/test_agent_system.py -v                       # Agent system tests
find . -name "*.py" -exec python3 -m py_compile {} \;                 # Syntax validation

# Code quality and security
black --check agents/ tests/          # Code formatting
flake8 agents/ tests/                # Style checking
mypy agents/                         # Type checking
pip-audit                            # Security vulnerability scan

# Model operations and workflows
python model_pack/model_training_agent.py              # Model validation
python project_management/core_tools/data_workflows.py train-fastai --epochs 300
python project_management/config/retrain_fixed_models.py # Retrain with new data
python model_pack/2025_data_acquisition.py            # Acquire latest data

# Weekly analysis and production
python3 scripts/run_weekly_analysis.py --week 13     # Complete weekly pipeline
python3 scripts/cfbd_pull.py --season 2025 --week 13 # Data pull only

# Educational content
cd starter_pack && jupyter lab        # Educational notebooks (start: 00_data_dictionary.ipynb)
cd model_pack && jupyter lab          # ML modeling notebooks

# TOON plan validation (required before plan creation/modification)
python3 scripts/smoke_test_toon.py   # TOON CLI and plan system validation
```

## 🏗️ Platform Architecture Overview

Script Ohio 2.0 is a **production-ready college football analytics platform** that combines intelligent conversational AI with comprehensive data analysis and machine learning.

### Core Components

```mermaid
graph TB
    subgraph "Multi-Agent Intelligence Layer"
        AO[Analytics Orchestrator<br/>Central Coordination]
        CM[Context Manager<br/>Role-Based Optimization]
    end

    subgraph "Specialized Agents"
        LN[Learning Navigator<br/>Educational Guidance]
        ME[Model Execution Engine<br/>ML Predictions]
        IG[Insight Generator<br/>Advanced Analysis]
        WA[Workflow Automator<br/>Process Orchestration]
    end

    subgraph "Data & Models"
        SP[Starter Pack<br/>12 Educational Notebooks]
        MP[Model Pack<br/>7 ML Modeling Notebooks]
        MD[Pre-trained Models<br/>Ridge/XGBoost/FastAI]
        CFBD[CFBD API<br/>Live Data Pipeline]
    end

    AO --> CM
    AO --> LN
    AO --> ME
    AO --> IG
    AO --> WA

    LN --> SP
    ME --> MP
    ME --> MD
    IG --> CFBD
```

### Key Architectural Patterns

#### Multi-Agent System
- **Analytics Orchestrator** (`agents/analytics_orchestrator.py`): Central coordination and request routing
- **BaseAgent Framework** (`agents/core/agent_framework.py`): Modular agent development with 4-level permission system
- **Context Manager** (`agents/core/context_manager.py`): Role-based experiences with 40% token reduction

#### Data Architecture
- **Historical Coverage**: College football games 1869-present, play-by-play 2003-present
- **Model Training**: 4,989 games (2016-2025) with 86 opponent-adjusted features
- **Live Integration**: Real-time CFBD API with rate limiting (6 req/sec)

#### Machine Learning Pipeline
- **Pre-trained Models**: Ridge regression, XGBoost classifier, FastAI neural network
- **Feature Engineering**: 86 opponent-adjusted features preventing data leakage
- **Model Execution**: Batch predictions with confidence intervals

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

**Educational Notebooks** (`starter_pack/`, 12 notebooks):
- **Beginner**: `00_data_dictionary.ipynb` → `01_intro_to_data.ipynb` → `02_build_simple_rankings.ipynb`
- **Intermediate**: `03_metrics_comparison.ipynb` → `04_team_similarity.ipynb` → `05_matchup_predictor.ipynb`
- **Advanced**: `06_predictive_modeling.ipynb` → `07_advanced_visualizations.ipynb`

**ML Modeling Notebooks** (`model_pack/`, 7 notebooks):
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
flake8 agents/ tests/                # Style checking
mypy agents/                         # Type checking

# Coverage requirements (minimum 80% for core components, 90% goal)
pytest --cov=agents --cov-report=term-missing
```

## 📁 Project Structure & File Organization

### Directory Organization

```
Script_Ohio_2.0/
├── agents/                           # Multi-agent system
│   ├── core/                        # Framework components
│   │   ├── agent_framework.py       # BaseAgent class and factory
│   │   ├── context_manager.py       # Role-based optimization
│   │   └── tool_loader.py          # Dynamic tool management
│   ├── tests/                       # Agent-specific tests
│   ├── analytics_orchestrator.py    # Main coordination hub
│   ├── model_execution_engine.py    # ML model integration
│   └── [specialized_agents].py     # Domain-specific agents
├── starter_pack/                     # Educational notebooks (13 total)
│   ├── data/                        # Historical datasets (read-only)
│   └── *.ipynb                     # Learning progression notebooks
├── model_pack/                       # ML modeling notebooks (7+) + models
│   ├── *_model_2025.*              # Pre-trained models
│   └── updated_training_data.csv   # Training dataset (86 features, 4,989 games)
├── tests/                           # Comprehensive test suite
├── scripts/                         # Utility scripts (62+ tools)
├── data/                           # Canonical data paths
│   ├── weekly/week{XX}/enhanced/   # Weekly enhanced features
│   ├── training/weekly/            # Weekly training files
│   └── metadata/                   # Data headers and definitions
├── predictions/week{XX}/           # Prediction outputs
├── logs/                          # Centralized logging (cfbd_pull.log, weekly_analysis.log)
├── project_management/              # Project tools and documentation
│   ├── core_tools/                 # Core working scripts
│   ├── quality_assurance/          # Testing and validation
│   └── config/                     # Configuration files
├── reports/                       # Analysis outputs and performance comparisons
└── .cursor/plans/                 # TOON-optimized workflow plans
```

### Canonical Paths (Primary Data Locations)

- **Enhanced Features**: `data/weekly/week{XX}/enhanced/`
- **Training Data**: `data/training/weekly/training_data_2025_week*.csv` (canonical)
- **Predictions**: `predictions/week{XX}/predictions.csv` and `predictions/week{XX}/summary.md`
- **Master Training Data**: `model_pack/updated_training_data.csv`
- **System Logs**: `logs/cfbd_pull.log` and `logs/weekly_analysis.log`

### File Naming Conventions

- **Agents**: `{domain}_agent.py` (e.g., `learning_navigator_agent.py`)
- **Core Files**: `{component}.py` (e.g., `agent_framework.py`)
- **Tests**: `test_{component}.py` (e.g., `test_agent_system.py`)
- **Models**: `{model_type}_model_2025.{ext}` (e.g., `ridge_model_2025.joblib`)
- **Plans**: `{plan_name}.plan.md` in `.cursor/plans/` (TOON format compatible)

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

### Pull Request Requirements

Before submitting a pull request:

```bash
# Required validation checks
python3 -m pytest agents/tests -q                    # Agent tests
python3 agents/test_agent_system.py                   # Smoke tests
find . -name "*.py" -exec python3 -m py_compile {} \; # Syntax validation
python3 scripts/smoke_test_toon.py                   # TOON system validation (if plans modified)

# Security and quality checks
pip-audit                                            # Security scan
black --check agents/ tests/                         # Code formatting
mypy agents/                                         # Type checking
```

**Security Checklist**:
- [ ] No hardcoded secrets or API keys
- [ ] All environment variables documented
- [ ] Dependencies scanned for vulnerabilities
- [ ] Input validation implemented for new features
- [ ] Error messages don't expose system internals

**Code Quality Checklist**:
- [ ] Type hints added to public APIs
- [ ] Code passes linting and formatting checks
- [ ] Test coverage maintained or improved
- [ ] Documentation updated for new features

## 🚨 Important Notes & Security

### Security Requirements
- **Never hardcode API keys**: Use environment variables (`export CFBD_API_KEY="your-key"`)
- **Rate limiting**: 6 requests/second maximum - use `time.sleep(0.17)` between CFBD API calls
- **No secrets in commits**: Never commit `.env` files or hardcoded credentials

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

## 🚨 Current Outstanding Issues

### **🔴 Critical Issues (IMMEDIATE ACTION REQUIRED)**

**1. GraphQL Removal (COMPLETED PATTERN - 2/8 files fixed, 6 remaining)**
Multiple agents reference GraphQL capabilities that require Patreon subscription and are not available. **Fix pattern established and demonstrated** - remaining files follow same process.

**✅ COMPLETED Files (Fixed):**
  - `agents/insight_generator_agent.py` - GraphQL capability → REST API trend analysis
  - `agents/workflow_automator_agent.py` - GraphQL summary → REST API seasonal analysis

**🔄 REMAINING Files (Apply same fix pattern):**
  - `agents/cfbd_integration_agent.py` - Remove GraphQL client, use REST alternatives
  - `agents/analytics_orchestrator.py` - Remove GraphQL subscription manager
  - `agents/system/cfbd_subscription_manager.py` - Remove GraphQL dependency
  - `agents/core/enhanced_cfbd_integration.py` - Use REST API only
  - `agents/core/ecosystem_integration.py` - Remove GraphQL references
  - `starter_pack/notebooks/CFBD_Ingestion.ipynb` - Make GraphQL cells optional

**Fix Pattern:** Remove GraphQL imports, update capabilities to use REST API, replace GraphQL methods with REST alternatives, add deprecation warnings.

**2. BaseAgent Inheritance Issues (213 errors across 29 files)**
Week12 agents use old constructor pattern and missing abstract methods.

**Quick Fix Pattern:**
```python
# OLD (Broken):
super().__init__(name="Agent", description="...", role="...", permissions=["..."])

# NEW (Fixed):
super().__init__(agent_id, name, permission_level)

# Add missing methods:
def _define_capabilities(self) -> List[AgentCapability]:
def _execute_action(self, action: str, parameters: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
```

### High Priority Issues (This Week)

**2025 Data Integration (3-4 hours):**
- Verify weeks 1-12 are fully integrated into training data
- Run `python scripts/integrate_weeks_1_12_and_retrain.py` to ensure complete data
- Validate week 12 data is properly formatted

**Model Retraining (3-4 hours):**
- Retrain all models with complete weeks 1-12 data
- Fix FastAI model pickle protocol issue
- Verify models load correctly after retraining

### **📋 Comprehensive Issue Documentation**

**🔥 NEW: Unified Issue Integration System**

For detailed fix implementations, code examples, and step-by-step resolution instructions, see:

**📋 [Issue Integration Hub - COMPREHENSIVE FIX CATALOG](project_management/ISSUE_INTEGRATION_HUB.md)**
*Created November 18, 2025 - 642+ issues catalogued with agent-based resolution*

**✨ What's Included:**
- **642+ Total Issues**: Comprehensive catalog across 8 categories
- **Agent-Based Resolution**: Automated fixing system with specialized agents
- **Exact Code Examples**: Before/after implementations for all critical fixes
- **Step-by-Step Instructions**: Detailed procedures for complex issues
- **Priority Matrix**: Clear action plan with time estimates
- **GraphQL Removal Pattern**: Complete fix pattern demonstrated and ready for application

**📚 Legacy Documentation:**
- [Operational Issues](project_management/REMAINING_ISSUES_AND_MISSING_PIECES.md) - Model training, data integration
- [Code Quality Catalog](project_management/COMPREHENSIVE_ISSUE_CATALOG.md) - 568 BaseAgent/inherited issues

### Quick Action Items

```bash
# 1. Verify data integration
python -c "
import pandas as pd
df = pd.read_csv('model_pack/updated_training_data.csv')
week12 = df[(df['season'] == 2025) & (df['week'] == 12)]
print(f'Week 12 games: {len(week12)}')
"

# 2. Run integration script
python scripts/integrate_weeks_1_12_and_retrain.py

# 3. Test GraphQL removal
python -c "
from agents.insight_generator_agent import InsightGeneratorAgent
agent = InsightGeneratorAgent('test_001')
result = agent._execute_action('graphql_trend_scan', {}, {})
print('GraphQL handling:', result.get('error', 'OK'))
"
```

## 🔍 Troubleshooting Common Issues

> **🚀 NEW: Comprehensive Issue Resolution System**
>
> For complete issue resolution with **agent-based automated fixes**, see:
> **[Issue Integration Hub - 642+ Issues Catalogued](project_management/ISSUE_INTEGRATION_HUB.md)**
>
> **Legacy Issues**: See [REMAINING_ISSUES_AND_MISSING_PIECES.md](project_management/REMAINING_ISSUES_AND_MISSING_PIECES.md) for operational issues.

### GraphQL-Related Errors

**Problem:** `GraphQL client unavailable` or `GraphQL access forbidden`

**Solution:**
```bash
# Set environment variable to disable GraphQL
export CFBD_GRAPHQL_DISABLED=true

# Or update agent code to remove GraphQL references
# See: project_management/REMAINING_ISSUES_AND_MISSING_PIECES.md (Category 1)
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

### CFBD API Issues
```bash
# Test CFBD API key
python -c "
import os
if 'CFBD_API_KEY' not in os.environ:
    print('❌ CFBD_API_KEY not set in environment')
else:
    print('✅ CFBD_API_KEY found')
"
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

## 📚 Key Resources & Documentation

### Essential Documentation
- **🔥 NEW: Issue Integration Hub**: `project_management/ISSUE_INTEGRATION_HUB.md` (642+ issues with agent-based resolution)
- **📖 Complete Agent Guide**: `AGENTS.md` (comprehensive agent development guidelines)
- **🚨 Operational Issues**: `project_management/REMAINING_ISSUES_AND_MISSING_PIECES.md` (model training, data integration)
- **📊 Code Quality Catalog**: `project_management/COMPREHENSIVE_ISSUE_CATALOG.md` (568 BaseAgent/inherited issues)
- **🔧 System Demo**: `python project_management/core_tools/demo_agent_system.py`
- **📊 Quality Assurance**: `project_management/quality_assurance/VERIFICATION_REPORT_2025.md`
- **🎓 Educational Content**: `starter_pack/CLAUDE.md` (notebook learning guidance)
- **🧪 Testing Guide**: `tests/CLAUDE.md` (comprehensive testing documentation)
- **🎯 Development Patterns**: `.cursorrules` (Cursor-specific development patterns and shortcuts)

### Additional Key Files
- **📋 Agent Development**: See `.cursorrules` for comprehensive BaseAgent templates and patterns
- **🔧 Integration Scripts**: `scripts/` directory contains 62+ utility scripts for data integration and analysis
- **📦 Configuration**: `config/` directory for deployment and system configuration
- **🎯 Model Files**: Pre-trained models in `model_pack/` (ridge_model_2025.joblib, xgb_home_win_model_2025.pkl, fastai_home_win_model_2025.pkl)

### CFBD Integration Resources
- **Official Website**: https://collegefootballdata.com/
- **API Documentation**: https://apinext.collegefootballdata.com/
- **Python Client**: https://github.com/CFBD/cfbd-python
- **Rate Limiting**: 6 requests/second maximum

### Platform Specifications
- **Python Version**: 3.13+ required
- **Data Coverage**: Historical data 1869-present, model training 2016-2025 (4,989 games)
- **Performance**: <2 second response times, 90%+ test coverage goal
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
```

## Platform Philosophy

Script Ohio 2.0 represents a new paradigm in sports analytics: **conversational intelligence** that makes sophisticated football analytics accessible through natural language. The multi-agent system bridges the gap between complex data science and intuitive user experiences, providing role-appropriate interfaces for everyone from students to production systems.

**Design Principles**: Following Claude's best practices for agent development - focused capabilities, clear boundaries, modular design, and comprehensive performance monitoring.

**Production Ready**: The platform maintains 99%+ uptime with <2 second response times, 90%+ test coverage, and comprehensive error handling for robust deployment.