<!-- 9c81c153-dad0-4a7b-9c45-6ac0164e3a2c 7b29d9d0-6de6-4b6f-9286-5b6f2d9adbe0 -->
# Massey Ratings Solver Implementation

## Objective
Deliver a production-ready Massey ratings solver that ingests CFBD game data,
solves the linear system with home-field adjustments, and exposes the results
through the shared rating library, tests, and documentation updates.

## Metadata
- **Created At**: 2025-11-24T00:00:00Z
- **Author**: system
- **Version**: 1.0

## Tasks

### Task 1: Requirements & Data Contracts
- **ID**: task_requirements
- **Description**: Collect academic references, confirm CFBD data parity, and
  capture the exact linear system plus normalization rules.
- **Agent**: insight_generator
- **Steps**: [step_requirements_review, step_equation_spec]
- **Dependencies**: []
- **Estimated Time**: 12.0s

### Task 2: Solver Module Construction
- **ID**: task_build_solver
- **Description**: Scaffold `src/ratings/massey_ratings.py`, implement the
  linear solver, and add validation helpers.
- **Agent**: model_engine
- **Steps**: [step_module_scaffold, step_linear_system, step_validation_suite]
- **Dependencies**: [task_requirements]
- **Estimated Time**: 42.0s

### Task 3: Rating Library Integration
- **ID**: task_integrate_library
- **Description**: Wire the new solver into `rating_library.py`, expose CLI /
  agent hooks, and ensure cached artifacts stay consistent.
- **Agent**: workflow_automator
- **Steps**: [step_library_integration, step_cli_hook]
- **Dependencies**: [task_build_solver]
- **Estimated Time**: 28.0s

### Task 4: Validation, Benchmarking, Documentation
- **ID**: task_validation_docs
- **Description**: Run pytest plus targeted scripts, benchmark against existing
  ratings, and update documentation plus TOON plan assets.
- **Agent**: quality_assurance
- **Steps**: [step_benchmark_tests, step_doc_publish, step_plan_validation]
- **Dependencies**: [task_integrate_library]
- **Estimated Time**: 33.0s

## Steps

### Step 1: Requirements Deep Dive
- **ID**: step_requirements_review
- **Task**: task_requirements
- **Action**: gather_requirements
- **Type**: ANALYSIS
- **Parameters**: {"sources": ["docs/ACADEMIC_METHODOLOGY_GUIDE.md",
  "AGENTS.md#Agent System Quick Reference", "docs/DATA_ORGANIZATION.md"],
  "outputs": ["docs/massey_requirements_notes.md"]}
- **Timeout**: 180s
- **Dependencies**: []
- **Retry Count**: 2

### Step 2: Equation Specification
- **ID**: step_equation_spec
- **Task**: task_requirements
- **Action**: draft_equations
- **Type**: DATA_PROCESSING
- **Parameters**: {"deliverable": "docs/massey_linear_system_spec.md",
  "include_home_field": true, "normalization_target": 0}
- **Timeout**: 240s
- **Dependencies**: [step_requirements_review]
- **Retry Count**: 2

### Step 3: Module Scaffold
- **ID**: step_module_scaffold
- **Task**: task_build_solver
- **Action**: scaffold_module
- **Type**: DATA_PROCESSING
- **Parameters**: {"path": "src/ratings/massey_ratings.py",
  "templates": ["src/ratings/rating_library.py"]}
- **Timeout**: 300s
- **Dependencies**: [step_equation_spec]
- **Retry Count**: 3

### Step 4: Implement Linear Solver
- **ID**: step_linear_system
- **Task**: task_build_solver
- **Action**: implement_linear_solver
- **Type**: DATA_PROCESSING
- **Parameters**: {"method": "least_squares", "matrix_strategy": "sparse",
  "stabilizers": {"lambda": 0.001}, "home_field_term": "hfa"}
- **Timeout**: 480s
- **Dependencies**: [step_module_scaffold]
- **Retry Count**: 3

### Step 5: Validation Suite
- **ID**: step_validation_suite
- **Task**: task_build_solver
- **Action**: write_unit_tests
- **Type**: ANALYSIS
- **Parameters**: {"tests": ["tests/test_massey_ratings.py"],
  "fixtures": ["tests/fixtures/massey_sample_games.csv"],
  "assertions": ["ratings_sum_zero", "home_field_positive"]}
- **Timeout**: 360s
- **Dependencies**: [step_linear_system]
- **Retry Count**: 3

### Step 6: Library Integration
- **ID**: step_library_integration
- **Task**: task_integrate_library
- **Action**: wire_rating_library
- **Type**: DATA_PROCESSING
- **Parameters**: {"path": "src/ratings/rating_library.py",
  "functions": ["load_massey_ratings", "merge_cfbd_inputs"],
  "cache_targets": ["src/ratings/rating_library_2025.csv"]}
- **Timeout**: 360s
- **Dependencies**: [step_validation_suite]
- **Retry Count**: 2

### Step 7: CLI & Agent Hooks
- **ID**: step_cli_hook
- **Task**: task_integrate_library
- **Action**: expose_cli_entrypoints
- **Type**: AGENT_EXECUTION
- **Parameters**: {"agents": ["cfbd_integration", "model_engine"],
  "scripts": ["scripts/run_weekly_analysis.py"],
  "flags": ["--massey-only"]}
- **Timeout**: 240s
- **Dependencies**: [step_library_integration]
- **Retry Count**: 2

### Step 8: Benchmarks & Tests
- **ID**: step_benchmark_tests
- **Task**: task_validation_docs
- **Action**: run_pytest_suite
- **Type**: ANALYSIS
- **Parameters**: {"commands": [
  "python3 -m pytest tests/test_massey_ratings.py -q",
  "python3 agents/test_agent_system.py"],
  "metrics": ["mae", "bias", "ats_pct"]}
- **Timeout**: 600s
- **Dependencies**: [step_cli_hook]
- **Retry Count**: 2

### Step 9: Documentation & Reports
- **ID**: step_doc_publish
- **Task**: task_validation_docs
- **Action**: update_docs
- **Type**: DATA_PROCESSING
- **Parameters**: {"files": ["AGENTS.md", "docs/ACADEMIC_METHODOLOGY_GUIDE.md",
  "reports/rating_system_benchmark_2025.md"],
  "sections": ["Massey Ratings", "Benchmark Summary"]}
- **Timeout**: 420s
- **Dependencies**: [step_benchmark_tests]
- **Retry Count**: 2

### Step 10: Plan & TOON Validation
- **ID**: step_plan_validation
- **Task**: task_validation_docs
- **Action**: validate_plan_conversion
- **Type**: CONDITION_CHECK
- **Parameters**: {"commands": [
  "python3 scripts/plan_to_workflow.py .cursor/plans/massey-ratings-solver-implementation.plan.md --toon --validate-only",
  "python3 scripts/plan_to_workflow.py .cursor/plans/massey-ratings-solver-implementation.plan.md --toon --output /tmp/massey_workflow.json"
  ]}
- **Timeout**: 180s
- **Dependencies**: [step_doc_publish]
- **Retry Count**: 1

## Shared Inputs
{"season": 2025, "cfbd_api_key_env": "CFBD_API_KEY",
"massey_regularization": 0.001, "home_field_advantage": 2.3,
"games_source": "model_pack/updated_training_data.csv"}

## Workflow Config
- Parallel Execution: false
- Error Recovery: true
- Max Retries: 3

