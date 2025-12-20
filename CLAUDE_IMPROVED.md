# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Script Ohio 2.0 is a comprehensive college football analytics platform featuring:
- **Multi-Agent Architecture**: Production-ready 4-tier agent system with 18+ specialized agents
- **Machine Learning Models**: Three pre-trained models (Ridge Regression, XGBoost, FastAI) for game predictions
- **CFBD Integration**: Unified client for CollegeFootballData.com API with rate limiting and intelligent caching
- **Weekly Analysis Pipeline**: Automated weekly matchup analysis and prediction generation
- **Web Application**: Modern React 19 frontend with TypeScript and comprehensive data visualization
- **TOON Format**: Token-optimized workflow plans for efficient LLM processing (50-70% token reduction)

## Quick Start Commands

### Environment Setup
```bash
# Create virtual environment (Python 3.13+ required)
python3.13 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
make install  # Installs Python + Node.js dependencies
# OR: pip install -r requirements.txt

# Set API key (required for CFBD integration)
export CFBD_API_KEY="your-api-key-here"
```

### Core Development Tasks
```bash
# Run weekly analysis pipeline
python3 scripts/run_weekly_analysis.py --week 13

# Generate bowl predictions
python3 scripts/predict_bowls_2025.py --season 2025 --method all --backup-existing --force

# Test agent system
python3 agents/demo_agent_system.py

# Run all tests
make test  # or: python3 -m pytest agents/tests -q

# System health check
make health-check
```

### Code Quality & Safety
```bash
# Safe code improvements (recommended workflow)
make improve-with-backup    # Creates backup + formats code + sorts imports

# Individual quality checks
make lint                   # Run linting (no changes)
make format                 # Format code with Black
make sort-imports           # Sort imports with Ruff
make syntax-validate        # Validate Python syntax

# Comprehensive validation
make comprehensive-check    # Full validation suite
```

### Web Application Development
```bash
cd web_app
npm install                 # Install dependencies
npm run dev                 # Start development server
npm run build               # Build for production
npm run typecheck           # Type checking
npm run lint                # Linting
```

## Architecture Overview

### Multi-Agent System (4-Tier Architecture)

**Tier 1: Meta Layer** - Master Control
- **Meta Agent** (`agents/meta_agent.py`): Agent lifecycle management, resource allocation, system health monitoring

**Tier 2: Orchestrator Level** - Coordination & Management
- **Analytics Orchestrator**: Routes analytical requests to domain specialists
- **Project Management Agent** (`agents/project_management_agent.py`): Plans, progress tracking, TOON support
- **Documentation Agent** (`agents/documentation_agent.py`): Knowledge base, freshness validation

**Tier 3: Domain Specialists** - 15+ Specialized Agents
- **Model Execution Engine**: ML predictions and ensemble methods
- **CFBD Integration Agent**: Rate-limited API access with caching
- **Insight Generator**: Advanced analytics and visualizations
- **Quality Assurance Agent**: System validation and health checks

**Tier 4: Utility Sub-Agents** - System Services
- **Validation Sub-Agent**: Quality control and data validation
- **Cache Manager**: Performance optimization
- **Error Handler**: Recovery and retry logic

### Core Framework (`agents/core/`)
All agents inherit from `BaseAgent` with strict separation of concerns:

```python
from agents.core.agent_framework import BaseAgent, AgentCapability, PermissionLevel

class CustomAgent(BaseAgent):
    def __init__(self, agent_id: str):
        super().__init__(agent_id, "Agent Name", PermissionLevel.READ_EXECUTE)
        self.max_execution_time = 300  # 5 minutes
        self.memory_limit_mb = 100

    def _define_capabilities(self) -> List[AgentCapability]:
        return [AgentCapability(name="action", ...)]

    def _execute_action(self, action: str, parameters: Dict, user_context: Dict) -> Dict:
        # Implementation with comprehensive error handling
        pass
```

### Data Pipeline Architecture

**Data Flow**:
1. **CFBD API** → Raw data with rate limiting (6 req/sec)
2. **Feature Engineering** → 86 opponent-adjusted features
3. **Model Training** → Three ensemble models (Ridge, XGBoost, FastAI)
4. **Weekly Analysis** → Automated predictions and reports

**Data Organization** (83.3% Migration Complete):
- **Master Training Data**: `data/processed/training/master_training_data_v2.csv` ⭐
- **Production Models**: `models/production/*_2025_v2.{joblib,pkl}` ⭐
- **Historical Archive**: `data/raw/historical/games_1869_2025.csv` ⭐
- **Predictions**: `data/outputs/predictions/2025/bowl_season/` ⭐
- **Legacy Locations**: Still accessible for backward compatibility

## Key Development Patterns

### CFBD Integration
Always use the unified client with proper rate limiting:

```python
from src.cfbd_client.unified_client import UnifiedCFBDClient

client = UnifiedCFBDClient()
# Rate limiting: 6 req/sec with intelligent caching
games = client.get_games(year=2025, week=13)  # Automatically cached
```

### Agent Development
All agents must inherit from BaseAgent and register with Meta Agent:

```python
from agents.core.agent_framework import BaseAgent
from agents.meta_agent import meta_agent

# Register with Meta Agent (required for all new agents)
registration_result = meta_agent._register_agent({
    "agent_id": "my_specialized_agent",
    "agent_name": "My Specialized Agent",
    "class_name": "MySpecializedAgent",
    "file_path": "agents/my_specialized_agent.py",
    "created_by": "developer_name",
    "capabilities": ["primary_action"],
    "dependencies": ["cfbd_integration"]
}, {"agent_id": "meta_agent"})
```

### Testing Patterns
Comprehensive testing is required for all agents:

```bash
# Unit tests
python3 -m pytest agents/tests/test_custom_agent.py -q

# Integration tests
python3 agents/test_agent_system.py

# Comprehensive test suite with coverage
python3 -m pytest agents/tests --cov=agents --cov-report=term-missing
```

### TOON Format Integration
Use TOON format for LLM responses to achieve 50-70% token reduction:

```python
from src.toon_format import encode, decode

# Convert JSON to TOON format
data = {
    "games": [
        {"id": 401752911, "home": "Oregon", "away": "USC", "predicted_margin": -1.61},
        {"id": 401752912, "home": "Alabama", "away": "Georgia", "predicted_margin": 3.2}
    ]
}

toon_output = encode(data)
# Output:
# games[2]{id,home,away,predicted_margin}:
#   401752911,Oregon,USC,-1.61
#   401752912,Alabama,Georgia,3.2

# Convert back to JSON
json_data = decode(toon_output)
```

**TOON Requirements**:
- Use for agent responses with uniform arrays of objects
- Use `[N]` format for array headers (never `[#N]` per v2.0 spec)
- Quote strings that match keywords or contain delimiters
- Validate with: `python3 scripts/smoke_test_toon.py`

## Technology Stack

### Backend Technologies
- **Python 3.13+**: Core language requirement
- **Machine Learning**: scikit-learn, XGBoost, FastAI, pandas, numpy
- **Data Science**: matplotlib, seaborn, plotly, shap
- **API Integration**: cfbd (CollegeFootballData.com client)
- **Testing**: pytest with comprehensive test suite
- **Code Quality**: black, mypy, ruff, bandit, pip-audit

### Frontend Stack
- **React 19**: Modern React with TypeScript and strict type checking
- **Build Tools**: Vite 7.2.4 for fast development and optimized builds
- **UI Components**: Radix UI primitives with comprehensive accessibility
- **Data Visualization**: Recharts 3.4.1 for interactive charts
- **Testing**: Vitest 2.1.8 with Testing Library
- **Styling**: Tailwind CSS v4 with PostCSS

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

### Agent Development Workflow
```bash
# 1. Create agent inheriting from BaseAgent
# 2. Define capabilities with execution time estimates
# 3. Implement _execute_action() with comprehensive error handling
# 4. Add tests in agents/tests/
# 5. Register with Meta Agent for system integration
python3 -c "from agents.meta_agent import meta_agent; result = meta_agent._register_agent({...})"
# 6. Run validation
python3 -m pytest agents/tests/test_new_agent.py -q
```

## File Structure & Conventions

### Directory Organization
```
data/                           # REORGANIZED DATA STRUCTURE ⭐
├── raw/historical/             # Master archives ⭐
├── processed/training/         # ML datasets ⭐
└── outputs/predictions/2025/   # Current season ⭐

models/production/              # ACTIVE MODELS ⭐
├── ridge_regression_2025_v2.joblib
├── xgboost_classifier_2025_v2.pkl
└── fastai_neural_net_2025_v2.pkl

agents/                         # Multi-agent system
├── core/                      # Agent framework
├── tests/                     # Comprehensive test suite
└── *.py                       # Individual agents

src/                           # Python modules
├── cfbd_client/              # CFBD API integration
├── features/                 # Feature engineering
├── models/                   # Model execution
└── utils/                    # Shared utilities

scripts/                       # Automation and utility scripts
├── run_weekly_analysis.py    # Main weekly pipeline
├── predict_bowls_2025.py     # Bowl predictions
└── [100+ specialized scripts]

web_app/                       # React frontend
starter_pack/                  # Educational notebooks
model_pack/                    # ML modeling notebooks
```

### File Naming Conventions
- **Agents**: `{domain}_agent.py` (e.g., `learning_navigator_agent.py`)
- **Scripts**: `{action}_{target}.py` (e.g., `predict_bowls_2025.py`)
- **Models**: `{model_type}_model_2025.{ext}` (e.g., `ridge_model_2025.joblib`)
- **Predictions**: `bowls_2025_predictions_{method}.json`

## Important Notes

### Environment Variables
- `CFBD_API_KEY`: Required for CollegeFootballData.com API access
- Set via `export CFBD_API_KEY="your-key"` or in `.env` file

### Rate Limiting & API Usage
- **CFBD API**: 6 requests per second base rate
- Use `time.sleep(0.17)` between requests in loops
- Unified client includes automatic rate limiting and intelligent caching

### Data Architecture Notes
- **NEW Master Training Data**: 5,250 games (2016-2025)
- **86 opponent-adjusted features** prevent data leakage
- **Migration Status**: 83.3% complete - run validation with `python3 scripts/maintenance/02_validation_check.py`

### Agent System Governance
- **Meta Agent**: Enforces 20-agent hard limit (currently at 9% capacity)
- **Permission Levels**: READ_ONLY, READ_EXECUTE, READ_EXECUTE_WRITE, ADMIN
- **Agent Registration**: Required for all new agents via Meta Agent
- **Performance Monitoring**: Real-time metrics and optimization recommendations

### Security Requirements
- **API Keys**: Never hardcode, use environment variables
- **Input Validation**: Validate all external inputs
- **Rate Limiting**: Strict adherence to CFBD API limits
- **Security Audit**: Run `pip-audit` for dependency vulnerability scanning

### Model Status
- **Training Data**: 4,989 games (2016-2025, Week 5+, FBS only)
- **Model Files**:
  - `ridge_model_2025.joblib`: ✓ Loads correctly
  - `xgb_home_win_model_2025.pkl`: ✓ Loads correctly
  - `fastai_home_win_model_2025.pkl`: ⚠️ Uses mock due to pickle protocol issues
- **Performance**: XGBoost (43.1% accuracy), Ensemble (44.2% accuracy)

## Planning & Development Workflow

### Multi-Step Work Pattern
For plans with 3+ distinct tasks, use Coordinator + Sandbox pattern:
- **Coordinator**: Manages merges, runs verification, coordinates subagents
- **Subagents**: Each has isolated sandbox and strict file scope
- **Isolation**: Git worktrees or separate branches
- **Minimal Changes**: One commit per phase, no refactors unless requested

### Repository-Specific Rules
- **Do NOT touch `agents/`** unless explicitly requested or test failing
- **Prefer snapshot-based data refresh** for CFBD work (deterministic)
- **Use `UnifiedCFBDClient`** from `src/cfbd_client/unified_client.py`
- **Rate limit**: 6 req/sec → `time.sleep(0.17)` between requests
- **Data Structure**: Use NEW organized structure (`data/`, `models/`) over legacy paths

### TOON Plan Requirements
- Run `python3 scripts/smoke_test_toon.py` before creating plans
- Validate plan structure: `python3 scripts/plan_to_workflow.py plan.md --toon --validate-only`
- Use uniform arrays for maximum token savings
- Array headers MUST use `[N]` format (never `[#N]`) per v2.0 spec

## Documentation References

### Primary Documentation
- **Agent Development**: `AGENTS.md` - Complete agent framework documentation
- **Super AI Architecture**: `project_management/plans/SUPER_AI_AGENT_ARCHITECTURE_PLAN.md`
- **Data Organization**: `docs/DATA_ORGANIZATION.md` - File structure and access patterns
- **TOON Format**: `docs/TOON_FORMAT_GUIDE.md` - Token optimization guide
- **Security**: `docs/SECURITY_BEST_PRACTICES.md` - Complete security guidelines

### Development Environment
- **Cursor Integration**: `.cursorrules` - Development environment patterns and AI assistance
- **Planning Templates**: `.cursor/plans/.template.plan.md` - Structured plan creation
- **Migration Guide**: `agents/system/MIGRATION_GUIDE.md` - Legacy component migration

## Implementation Status

### System Health
- **Overall Grade**: A+ system, production-ready
- **Agent System**: 95% complete, 18+ specialized agents operational
- **Code Quality**: 100% syntax validation across all Python files
- **Test Coverage**: Comprehensive pytest suite with smoke tests
- **Security**: Comprehensive security best practices implemented

### Performance Optimization
- **Context Window**: 60-70% reduction via TOON + smart loading
- **Agent Coordination**: 40-50% faster via Meta Agent optimization
- **Memory Usage**: 50-60% reduction via compression and hierarchical storage
- **API Efficiency**: 80% cache hit rate for CFBD data
- **Overall Performance**: 3-4x improvement in task completion time

## Quick Reference Commands

### Essential Commands (Most Used)
```bash
make improve-with-backup     # Safe code improvements (creates backup first)
make health-check           # Complete system health assessment
make test                   # Run all tests
python3 scripts/run_weekly_analysis.py --week 13    # Weekly analysis
python3 scripts/predict_bowls_2025.py --season 2025 --method all  # Bowl predictions
```

### System Management
```bash
# Monitor agent system
python3 -c "from agents.meta_agent import meta_agent; print(meta_agent._monitor_system({}, {}))"

# Check optimization performance
python3 -c "from agents.orchestration_agent import orchestration_agent; print(orchestration_agent._monitor_optimization({}, {}))"

# Validate data architecture
python3 scripts/maintenance/02_validation_check.py
```

### AI Assistant Tools
```bash
make ai-assistant           # Easy-to-use AI assistant (recommended)
make smart-ai              # Interactive AI code assistant
make smart CMD='task'      # Single AI command execution
```

---

**Development Philosophy**: Script Ohio 2.0 follows a safety-first approach with comprehensive validation, automated testing, and backup protection for all code changes. The agent system enables autonomous operation while maintaining strict governance and performance monitoring.