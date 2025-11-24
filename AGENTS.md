# AGENTS.md

A simple, open format for guiding coding agents, used by over 20k open-source projects.

## Setup commands

- **Python version**: Python 3.13+ required
- **Create virtual environment**: `python3.13 -m venv venv`
- **Activate virtual environment**: `source venv/bin/activate` (Linux/macOS) or `venv\Scripts\activate` (Windows)
- **Install dependencies**: `pip install -r requirements.txt`
- **Install dev dependencies**: `pip install -r requirements-dev.txt` (if available)
- **Bootstrap dev environment**: `scripts/bootstrap_dev_env.sh` (installs TypeScript CLI, Kiota, dotnet 9, pnpm/corepack)
- **Set environment variables**: `export CFBD_API_KEY="your-api-key-here"` (required for CFBD API access)

## Code style

- **Python**: Follow PEP 8, use 4-space indentation, maximum line length 88 characters
- **Type hints**: Prefer type hints in new Python modules
- **Docstrings**: Use Google-style docstrings for all functions
- **Pandas**: Use vectorized operations, `.assign` pipelines, avoid chained indexing
- **Agent code**: Use dataclasses for request/response objects, enums for status/permission levels
- **Notebooks**: Include top markdown cell with objectives, inputs, outputs

## Testing instructions

- **Run all tests**: `python3 -m pytest agents/tests -q`
- **Run smoke tests**: `python3 agents/test_agent_system.py`
- **Run agent system demo**: `python3 agents/demo_agent_system.py`
- **Run comprehensive demo**: `python3 agents/COMPREHENSIVE_INTEGRATION_DEMO.py`
- **Run weekly analysis**: `python3 scripts/run_weekly_analysis.py --week 13`
- **Verify agents**: `python3 scripts/verify_weekly_agents.py`
- **Syntax validation**: `find . -name "*.py" -exec python3 -m py_compile {} \;`
- **TOON smoke test**: `python3 scripts/smoke_test_toon.py` (before creating/modifying plans)

## Build commands

- **Verify agent system**: `python -c "from agents.analytics_orchestrator import AnalyticsOrchestrator; print('✅ Agent system OK')"`
- **Verify model engine**: `python -c "from agents.model_execution_engine import ModelExecutionEngine; print('✅ Model engine OK')"`
- **Convert plan to TOON**: `python3 scripts/plan_to_workflow.py .cursor/plans/plan.md --toon --output plan.toon`
- **Validate TOON plan**: `python3 scripts/plan_to_workflow.py plan.toon --validate-only`
- **Execute TOON plan**: Use `WorkflowAutomatorAgent.execute_toon_plan()` capability

## Dev environment tips

- **Agent system**: All agents inherit from `BaseAgent` in `agents/core/agent_framework.py`
- **Permission levels**: READ_ONLY, READ_EXECUTE, READ_EXECUTE_WRITE, ADMIN
- **Adding new agent**: Follow pattern in `.cursorrules` lines 29-50 (inherit BaseAgent, define capabilities, implement _execute_action)
- **CFBD API**: Always use `CFBD_API_KEY` env var, never hardcode keys. Rate limit: 6 req/sec
- **Data files**: Source-of-truth CSVs in `starter_pack/data/` (read-only). Never commit datasets >5MB
- **Model files**: Located in `model_pack/` - `ridge_model_2025.joblib`, `xgb_home_win_model_2025.pkl`, `fastai_home_win_model_2025.pkl`
- **Training data**: `model_pack/updated_training_data.csv` (6.8MB, 86 columns, 4,989 games 2016-2025)
- **Weekly training data**: `data/training/weekly/training_data_2025_week*.csv` (canonical location). Use `get_weekly_training_file()` utility for path resolution
- **Data organization**: See `docs/DATA_ORGANIZATION.md` for complete directory structure and access patterns
- **Legacy code**: `agents/system/` directories are deprecated - see `agents/system/MIGRATION_GUIDE.md`
- **TOON plans**: Create plans in `.cursor/plans/` with uniform arrays for token efficiency (50-70% reduction)

## Project structure

- **Agents**: `agents/` - Production-ready multi-agent architecture
  - `agents/core/`: Framework (agent_framework.py, context_manager.py, tool_loader.py)
  - `agents/system/`: Deprecated system components
- **Notebooks**: `starter_pack/` (13 educational notebooks), `model_pack/` (7 ML modeling notebooks)
- **Source code**: `src/` - Python modules (only when notebook logic reused)
- **Tests**: `tests/` - Test suite for agent system and models
- **Scripts**: `scripts/` - Utility scripts (plan_to_workflow.py, run_weekly_analysis.py, etc.)
- **Plans**: `.cursor/plans/` - TOON-optimized workflow plans
- **Data organization**: 
  - Master training data: `model_pack/updated_training_data.csv`
  - Weekly training files: `data/training/weekly/training_data_2025_week*.csv` (canonical)
  - Weekly enhanced features: `data/weekly/week{XX}/enhanced/`
  - Reports: `reports/` (analysis outputs, performance comparisons)
  - Metadata: `data/metadata/` (data headers, column definitions)
  - See `docs/DATA_ORGANIZATION.md` for complete structure

## Agent system quick reference

## Agent Cheat Sheet
| Agent | When to Use | Key Actions | Permission |
| --- | --- | --- | --- |
| CFBD Integration Agent (`cfbd_integration`) | Provides normalized CFBD datasets and live scoreboard snapshots. | `team_snapshot`, `live_scoreboard` | READ_EXECUTE |
| Conversational AI (`conversational_ai`) | Advanced conversational AI agent for natural language interactions
with context awareness and intelligent dialogue management. | `natural_language_processing`, `intent_recognition`, `conversation_management`, `query_expansion`, `clarification_handling` | READ_EXECUTE_WRITE |
| File Organization Agent (`file_organization`) | Specialized agent for organizing misplaced project files into appropriate
subdirectories according to CLAUDE. | `classify_root_files`, `create_missing_directories`, `organize_into_directories` | READ_EXECUTE_WRITE |
| Insight Generator (`insight_generator`) | Agent responsible for generating advanced analytics insights, statistical analysis,
and sophisticated visualizations for complex college football data. | `generate_analysis`, `statistical_analysis`, `create_visualizations`, `comparative_analysis`, `trend_analysis`, `cfbd_real_time_analysis`, `graphql_trend_scan`, `generate_infographic` | READ_EXECUTE_WRITE |
| Learning Navigator (`learning_navigator`) | Agent for educational guidance and learning path navigation | `guide_learning_path`, `recommend_content` | READ_EXECUTE |
| Model Execution Engine (`model_engine`) | Advanced model execution engine for college football analytics | `predict_game_outcome`, `batch_predictions`, `model_comparison`, `model_performance_analysis`, `kelly_criterion_analysis`, `value_betting_detection`, `betting_opportunity_analysis` | READ_EXECUTE_WRITE |
| Performance Monitor (`performance_monitor`) | Advanced performance monitoring agent with real-time metrics,
intelligent alerting, and automated optimization suggestions. | `monitor_system_performance`, `detect_performance_bottlenecks`, `generate_optimization_recommendations`, `benchmark_performance` | READ_EXECUTE_WRITE |
| Quality Assurance Agent (`quality_assurance`) | Surfaces telemetry summaries, schema diff alerts, and health checks. | `cfbd_health_check`, `cfbd_recent_events` | READ_EXECUTE |
| Report Generator Agent (`report_generator`) | Agent responsible for generating comprehensive analytics reports. | `generate_weekly_report` | READ_EXECUTE_WRITE |
| System Validation Agent (`validation_agent`) | Specialized agent for validating file organization and system integrity. | `validate_file_moves`, `validate_import_integrity`, `update_gitignore`, `generate_validation_report` | READ_EXECUTE |
| Validation Orchestrator (`validation_orchestrator`) | Meta Coordinator for Activation Fix System Validation

Coordinates specialized sub-agents to validate and document the
existing activation fix implementation using hierarchical orchestration. | `coordinate_validation`, `discover_system`, `validate_comprehensive`, `document_system`, `quality_assurance`, `synthesize_results` | ADMIN |
| Week 12 Mock Enhancement Agent (`week12_mock_enhancement`) | Agent responsible for enhancing mock data with Week 12 patterns
and current season trends for more realistic predictions | `enhance_mock_data` | READ_EXECUTE_WRITE |
| Week 13 Analysis Orchestrator (`weekly_analysis_orchestrator`) | Orchestrator that coordinates weekly analysis agents for comprehensive
matchup analysis, model validation, and prediction generation | `run_weekly_analysis`, `validate_models`, `generate_predictions` | ADMIN |
| Week 13 Matchup Analysis Agent (`weekly_matchup_analysis`) | Agent responsible for analyzing weekly matchups and generating strategic insights
using enhanced mock data and historical patterns | `analyze_matchups` | READ_EXECUTE_WRITE |
| Week 13 Model Validation Agent (`weekly_model_validation`) | Agent responsible for validating ML models for weekly predictions
and ensuring they work correctly with enhanced data | `validate_models`, `check_compatibility`, `performance_test` | READ_EXECUTE_WRITE |
| Week 13 Prediction Generation Agent (`weekly_prediction_generation`) | Agent responsible for generating weekly predictions using validated ML models
and enhanced matchup data | `generate_predictions`, `calculate_confidence`, `create_ensemble` | READ_EXECUTE_WRITE |
| Week12MatchupAnalysis Agent (`week12_matchup_analysis`) | Backward compatibility wrapper for Week 12 matchup analysis. | `analyze_matchups` | READ_EXECUTE_WRITE |
| Week12ModelValidation Agent (`week12_model_validation`) | Backward compatibility wrapper for Week 12 model validation. | `validate_models`, `check_compatibility`, `performance_test` | READ_EXECUTE_WRITE |
| Week12PredictionGeneration Agent (`week12_prediction_generation`) | Backward compatibility wrapper for Week 12 prediction generation. | `generate_predictions`, `calculate_confidence`, `create_ensemble` | READ_EXECUTE_WRITE |

### Core Agents

- **AnalyticsOrchestrator** (`agents/analytics_orchestrator.py`): Main orchestrator, routes requests to agents
- **CFBD Integration Agent** (`cfbd_integration`): CFBD data access via REST/GraphQL
- **Model Execution Engine** (`model_engine`): ML model predictions (Ridge, XGBoost, FastAI)
- **Insight Generator** (`insight_generator`): Advanced analytics, visualizations, CFBD real-time analysis
- **Learning Navigator** (`learning_navigator`): Educational guidance and learning paths
- **Workflow Automator** (`workflow_automator`): Multi-step pipelines, TOON plan execution

### Agent Development Pattern

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

## PR instructions

- **Before committing**: Run `python3 -m pytest agents/tests -q` and `python3 agents/test_agent_system.py`
- **Code quality**: Ensure syntax validation passes: `find . -name "*.py" -exec python3 -m py_compile {} \;`
- **TOON plans**: Run `python3 scripts/smoke_test_toon.py` before creating/modifying plans in `.cursor/plans/`
- **Agent changes**: Update smoke tests/pytest suite to cover new agent functionality
- **Documentation**: Update `AGENTS.md` if adding new agents or capabilities
- **Breaking changes**: Never modify existing agent interfaces - use additive patterns only

## Security considerations

- **API keys**: Never hardcode `CFBD_API_KEY` - always use environment variables
- **Data files**: Never commit datasets >5MB or sensitive data
- **Rate limiting**: Respect CFBD API rate limits (6 req/sec) - use `time.sleep(0.17)` in loops
- **Authentication**: Use `cfbd.Configuration(access_token=os.environ["CFBD_API_KEY"])` pattern

## Common workflows

- **Weekly analysis**: `python3 scripts/run_weekly_analysis.py --week 13`
- **CFBD data pull**: `python3 scripts/cfbd_pull.py --season 2025 --week 12`
- **Plan execution**: Use `WorkflowAutomatorAgent.execute_toon_plan()` with TOON plans
- **Model predictions**: Use `ModelExecutionEngine.predict_game_outcome()` capability
- **Agent demo**: `python3 agents/demo_agent_system.py`

## Power Rating Integration Workflow

### Overview

Integrate CFBD GraphQL ratings (SP+, FPI, SRS) and implement academic power rating methodologies (Massey, Coleman metamodel) using TOON-optimized workflows.

### TOON Plan Structure

Create plans in `.cursor/plans/` following this structure for token efficiency:

**Required Components:**

- **Metadata**: title, objective, created_at, author, version
- **Tasks Array**: Uniform structure (id, name, description, steps, dependencies, agent_type, tools_required, estimated_time)
- **Steps Array**: Uniform structure (id, task_id, action, parameters, step_type, timeout, dependencies, retry_count)
- **Shared Inputs**: Data shared across workflow steps
- **Workflow Config**: parallel_execution, error_recovery, max_retries

**Example Plan**: `.cursor/plans/power_rating_integration.plan.md`

### Implementation Steps

1. **Add GraphQL Ratings Capability**
   - File: `agents/cfbd_integration_agent.py`
   - Add `graphql_ratings` capability using `CFBDGraphQLClient.get_ratings()`
   - Test: `python3 -m pytest tests/test_cfbd_graphql_ratings.py`

2. **Fetch CFBD Ratings** (Parallel execution)
   - Use `CFBDIntegrationAgent` to fetch SP+, FPI, SRS, Elo ratings
   - Graceful degradation: REST Elo if GraphQL unavailable
   - Rate limiting: 6 req/sec via `UnifiedCFBDClient`

3. **Implement Massey Ratings**
   - File: `src/ratings/massey_ratings.py`
   - Method: Linear least squares on point differentials
   - Validation: Ratings sum to 0, home-field advantage positive

4. **Build Rating Library**
   - File: `src/ratings/rating_library.py`
   - Aggregate: CFBD ratings (SP+, FPI, Elo, SRS), Massey, model predictions (Ridge, XGBoost, FastAI)
   - Output: DataFrame with game_id, system_name, predicted_margin

5. **Implement Coleman Metamodel**
   - File: `src/ratings/coleman_metamodel.py`
   - Method: Ridge regression on predicted margins from all systems
   - Meta-features: disagreement, home/road_split, early_season
   - Evaluation: MAE, bias, ATS performance

6. **Benchmark & Validate**
   - Calculate: MAE, bias, winner-correct %, ATS performance
   - Compare: All systems vs metamodel
   - Report: `reports/rating_system_benchmark_2025.md`

### TOON Plan Execution

```bash
# Convert markdown plan to TOON
python3 scripts/plan_to_workflow.py \
  .cursor/plans/power_rating_integration.plan.md \
  --toon \
  --output .cursor/plans/power_rating_integration.toon

# Validate TOON plan
python3 scripts/plan_to_workflow.py \
  .cursor/plans/power_rating_integration.toon \
  --validate-only

# Execute via WorkflowAutomatorAgent
python3 -c "
from agents.workflow_automator_agent import WorkflowAutomatorAgent
import os

agent = WorkflowAutomatorAgent(agent_id='power_rating_workflow')
result = agent._execute_action(
    'execute_toon_plan',
    {
        'plan_path': '.cursor/plans/power_rating_integration.toon',
        'shared_inputs': {
            'season': 2025,
            'cfbd_api_key': os.getenv('CFBD_API_KEY')
        }
    },
    {'user_id': 'system'}
)
print(f\"Status: {result['status']}\")
"
```

### Key Integration Points

- **CFBD GraphQL**: Provides SP+, FPI, SRS ratings (Patreon Tier 3+ required)
- **CFBD REST**: Provides Elo ratings (always available)
- **Existing Models**: Ridge, XGBoost, FastAI predictions
- **New Systems**: Massey ratings, Coleman metamodel
- **Non-Breaking**: All changes are additive, existing models unchanged

### Success Criteria

- ✅ GraphQL ratings capability added and tested
- ✅ SP+, FPI, SRS, Elo ratings fetched successfully
- ✅ Massey ratings calculated and validated (sum to 0)
- ✅ Rating library contains 10+ systems
- ✅ Coleman metamodel trained (MAE < 15 points)
- ✅ Benchmark report generated with all metrics
- ✅ No existing functionality broken
- ✅ TOON plan executes successfully

### Files Created/Modified

**New Files:**

- `src/ratings/massey_ratings.py`
- `src/ratings/rating_library.py`
- `src/ratings/coleman_metamodel.py`
- `tests/test_cfbd_graphql_ratings.py`
- `.cursor/plans/power_rating_integration.toon`

**Modified Files:**

- `agents/cfbd_integration_agent.py` (add graphql_ratings capability)

**Generated Files:**

- `src/ratings/rating_library_2025.csv`
- `src/ratings/coleman_metamodel_2025.joblib`
- `reports/rating_system_benchmark_2025.md`

## Troubleshooting

- **FastAI model warnings**: Expected - bundled neural net uses placeholder pickle. Ridge/XGB models load correctly.
- **GraphQL unavailable**: System gracefully degrades to REST API. Check `CFBD_API_KEY` and Patreon Tier 3+ subscription.
- **Import errors**: Ensure virtual environment is activated and dependencies installed: `pip install -r requirements.txt`
- **Agent not found**: Verify agent is registered via `AgentFactory.register_agent_class()` in orchestrator initialization
- **TOON plan errors**: Run `python3 scripts/smoke_test_toon.py` to verify TOON CLI availability and plan structure
- **Rating system validation fails**: Check Massey ratings sum to 0, verify CFBD API responses include required fields

## Additional Resources

- **Agent Framework**: `agents/core/agent_framework.py`
- **CFBD Integration**: `agents/cfbd_integration_agent.py`, `src/cfbd_client/unified_client.py`
- **TOON Format**: `docs/TOON_FORMAT_GUIDE.md`, `docs/TOON_PLAN_SYSTEM.md`
- **Plan Structure**: `docs/PLAN_STRUCTURE.md`
- **Academic Methodology**: `docs/ACADEMIC_METHODOLOGY_GUIDE.md` (to be created)
- **CFBD GraphQL**: `docs/CFBD_GRAPHQL_GUIDE.md`

## Architecture Improvements & Technical Debt

### Priority Improvements Identified

**CRITICAL (Security & Operations)**

1. **Security Hardening**
   - Implement dependency vulnerability scanning (`pip-audit` or `safety`)
   - Add API key rotation mechanism
   - Encrypt sensitive data (cache files, model files)
   - Implement audit logging for all API key usage
   - Add input sanitization for all external inputs
   - Require HTTPS in production deployments

2. **Dependency Management**
   - Set up automated dependency scanning in CI/CD
   - Document security update process
   - Review and minimize dependency tree (30+ packages)

3. **Data Security**
   - Encrypt SQLite cache files
   - Encrypt model pickle files
   - Implement data encryption at rest
   - Review pickle file security (potential deserialization risks)

**HIGH PRIORITY (Scalability & Performance)**

4. **Scalability Preparation**
   - Migrate from SQLite to Redis for distributed caching
   - Implement message queue system for async tasks
   - Design for horizontal scaling (multi-instance deployment)
   - Consider PostgreSQL migration for production data

5. **Performance Monitoring**
   - Integrate APM tools (e.g., New Relic, Datadog)
   - Add performance profiling for critical paths
   - Implement async/await for I/O operations
   - Add connection pooling for database/cache

6. **Code Consolidation**
   - Complete migration to UnifiedCFBDClient (remove duplicates)
   - Split large files (orchestrator >1000 lines)
   - Move archive/backup directories to separate branch or external storage

**MEDIUM PRIORITY (Code Quality & Testing)**

7. **Code Quality**
   - Add type hints to all public APIs
   - Integrate automated linting and type checking in CI
   - Set up code coverage reporting (pytest-cov)
   - Auto-generate API docs from code

8. **Testing Enhancements**
   - Add end-to-end workflow tests
   - Add load testing for critical paths
   - Centralize test data fixtures
   - Set up test coverage metrics

9. **Logging & Observability**
   - Implement structured logging (JSON format)
   - Standardize log level usage across codebase
   - Set up log rotation for production
   - Configure centralized log collection
   - Set up monitoring dashboard (Grafana)
   - Configure alerting for critical metrics
   - Add distributed tracing for request flows

> **New:** `src/observability/` now exposes `configure_logging`, `ObservabilityHub`,
> and the canonical error taxonomy. Refer to `docs/OBSERVABILITY_GUIDE.md`
> before wiring new agents or scripts.

**LOW PRIORITY (Documentation & Process)**

10. **Documentation Gaps**
    - Complete API reference documentation integration
    - Add more examples in agent capability docs
    - Create troubleshooting guides for common issues
    - Add performance tuning guides
    - Expand security best practices documentation

11. **CI/CD & Deployment**
    - Set up automated CI/CD pipeline
    - Separate dev/staging/prod configurations
    - Document rollback procedures
    - Implement comprehensive health check endpoints

### Code Organization Improvements

**Duplicate Code Elimination**

- ⚠️ Multiple CFBD client implementations exist
- ✅ Target: Complete migration to `UnifiedCFBDClient`
- Action: Deprecate `src/cfbd_client/client.py`, `src/data_sources/cfbd_client.py`, 
  `starter_pack/utils/cfbd_loader.py`, `agents/core/enhanced_cfbd_integration.py`

**File Size Management**

- ⚠️ Large files (>1000 lines) need refactoring
- Files: `agents/analytics_orchestrator.py`
- Action: Split into focused modules (orchestration, routing, synthesis)

**Archive Management**

- ⚠️ Archive/backup directories in main repo
- Action: Move to separate branch or external storage
- Consider: Git LFS for large backup files

### Error Handling Improvements

**Current State**: ✅ Comprehensive error handling system exists

**Improvements Needed**:
- Translate technical errors to user-friendly messages
- Implement centralized structured logging service
- Enhance automatic recovery mechanisms
- Add error categorization and intelligent routing

### Logging Strategy

**Current State**: ✅ Basic logging, ⚠️ Inconsistent levels

**Required Improvements**:

1. **Structured Logging**: Use JSON format for log aggregation
   ```python
   import structlog
   logger = structlog.get_logger()
   logger.info("event", agent_id="model_engine", action="predict", duration_ms=150)
   ```

2. **Log Levels**: Standardize usage
   - DEBUG: Detailed diagnostic information
   - INFO: General informational messages
   - WARNING: Warning messages (non-critical)
   - ERROR: Error messages (recoverable)
   - CRITICAL: Critical errors (system failure)

3. **Log Rotation**: Implement for production
   ```python
   from logging.handlers import RotatingFileHandler
   handler = RotatingFileHandler('app.log', maxBytes=10*1024*1024, backupCount=5)
   ```

4. **Centralized Collection**: Set up log aggregation service

### Security Best Practices

**When Working with Secrets**:
- ✅ NEVER hardcode API keys or credentials
- ✅ Always use environment variables
- ✅ Validate `.gitignore` excludes `.env` files
- ✅ Use `python-dotenv` for local development
- ✅ Rotate API keys regularly
- ✅ Log API key usage (without exposing keys)

**Input Validation**:
- ✅ Validate all external inputs
- ✅ Sanitize user-provided data
- ✅ Use type hints for parameter validation
- ✅ Implement rate limiting on internal endpoints

**Dependency Security**:
- ⚠️ Run `pip-audit` or `safety check` regularly
- ⚠️ Keep dependencies up to date
- ⚠️ Review security advisories
- Action: Add to CI/CD pipeline

### Performance Optimization Guidelines

**Caching Strategy**:
- ✅ Current: SQLite-based caching with TTL
- ⚠️ Production: Migrate to Redis for distributed systems
- Action: Implement Redis adapter for cache manager

**Async Operations**:
- ⚠️ Consider async/await for I/O operations
- Action: Refactor CFBD client to use `aiohttp` for async requests

**Connection Pooling**:
- ⚠️ Implement for database/cache connections
- Action: Use connection pool for Redis/PostgreSQL

**Profiling**:
- ⚠️ Add performance profiling for critical paths
- Tools: `cProfile`, `py-spy`, `line_profiler`
- Action: Integrate profiling in development workflow

### Testing Best Practices

**Test Coverage**:
- ⚠️ Add pytest-cov for coverage reporting
- Target: 80%+ coverage for core components
- Action: `pytest --cov=agents --cov-report=html`

**Test Types**:
- ✅ Unit tests: Individual component testing
- ✅ Integration tests: Multi-agent workflows
- ⚠️ E2E tests: Complete workflow testing
- ⚠️ Performance tests: Load testing for critical paths

**Test Data**:
- ⚠️ Centralize test data fixtures
- Action: Create `tests/fixtures/` directory

### Deployment & Operations

**CI/CD Pipeline**:
- ⚠️ Set up automated testing and deployment
- Tools: GitHub Actions, GitLab CI, or Jenkins
- Steps: Test → Lint → Type Check → Deploy

**Environment Management**:
- ⚠️ Separate dev/staging/prod configurations
- Action: Use environment-specific config files

**Health Checks**:
- ⚠️ Implement comprehensive health check endpoints
- Checks: API connectivity, cache status, model loading

**Monitoring**:
- ⚠️ Set up monitoring dashboard (Grafana)
- ⚠️ Configure alerting for critical metrics
- ⚠️ Add distributed tracing (OpenTelemetry)

For detailed implementation guides, see:
- **Architecture Improvements**: `docs/ARCHITECTURE_IMPROVEMENTS.md`
- **Security Best Practices**: `docs/SECURITY_BEST_PRACTICES.md`
- **Code Quality Guidelines**: `docs/CODE_QUALITY_GUIDELINES.md`
