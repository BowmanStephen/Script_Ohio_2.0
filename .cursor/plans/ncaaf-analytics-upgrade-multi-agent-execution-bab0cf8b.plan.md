<!-- bab0cf8b-23bc-4fe8-8858-9783de0401d9 a65a8e82-8fd9-4e93-a5b4-dca88bec035c -->
# NCAAF Analytics Upgrade - Multi-Agent Execution Plan

## Architecture Overview

This plan leverages the existing `AdvancedAgentCoordinator` and `BaseAgent` framework to execute the 4-phase upgrade through specialized sub-agents. Each phase is decomposed into atomic tasks that agents can complete independently with built-in verification.

## Agent Specialization Strategy

### Phase 1: Dependency Management Agents

- **DependencyVerifierAgent**: Verifies package installations
- **RequirementsUpdaterAgent**: Updates requirements.txt
- **EnvironmentValidatorAgent**: Validates environment state

### Phase 2: Feature Engineering Agents  

- **TeamSimilarityAgent**: Implements KNN team similarity
- **DriveEfficiencyAgent**: Calculates PPD and explosive drive metrics
- **OffenseDefenseAgent**: Generates normalized matchup comparisons
- **FeatureValidatorAgent**: Validates new feature implementations

### Phase 3: Model Expansion Agents

- **RandomForestTrainerAgent**: Implements and trains Random Forest model
- **EnsembleIntegratorAgent**: Integrates RF into ensemble pipeline
- **ModelValidatorAgent**: Validates model outputs

### Phase 4: Visualization Agents

- **SHAPVisualizerAgent**: Generates SHAP explanations
- **DashboardBuilderAgent**: Creates Plotly interactive dashboards
- **ReportGeneratorAgent**: Compiles all artifacts into reports

## Coordination Pattern

**Primary Pattern**: Hierarchical with parallel execution

- Master Orchestrator coordinates phase execution
- Phase Coordinators manage sub-agents within each phase
- Sub-agents execute atomic tasks in parallel where possible
- Validation agents verify each step before proceeding

## Phase 1: Dependencies & Environment Hygiene

### Task Decomposition

**Task 1.1: Update Requirements File**

- **Agent**: RequirementsUpdaterAgent
- **Action**: Add plotly>=5.17.0 and ipywidgets>=8.1.0 to requirements.txt
- **Verification**: File exists, contains new packages, syntax valid
- **Dependencies**: None

**Task 1.2: Create Verification Script**

- **Agent**: DependencyVerifierAgent  
- **Action**: Create scripts/verify_dependencies.py with package checking logic
- **Verification**: Script executes without errors, checks all required packages
- **Dependencies**: None (can run parallel with 1.1)

**Task 1.3: Install Dependencies**

- **Agent**: EnvironmentValidatorAgent
- **Action**: Execute `pip install -r requirements.txt`
- **Verification**: Exit code 0, no error messages
- **Dependencies**: [1.1] (requires updated requirements.txt)

**Task 1.4: Verify Installation**

- **Agent**: DependencyVerifierAgent
- **Action**: Execute `python scripts/verify_dependencies.py`
- **Verification**: All packages show ✅, exit code 0
- **Dependencies**: [1.2, 1.3] (requires script and installed packages)

### Coordination Flow

```
RequirementsUpdaterAgent (1.1) ──┐
                                  ├─> EnvironmentValidatorAgent (1.3) ──> DependencyVerifierAgent (1.4)
DependencyVerifierAgent (1.2) ──┘
```

## Phase 2: Feature Engineering Integration

### Task Decomposition

**Task 2.1: Team Similarity Module**

- **Agent**: TeamSimilarityAgent
- **Action**: Create src/features/similarity.py implementing KNN from 04_team_similarity.ipynb
- **Key Functions**: 
  - `find_similar_teams(team_name, top_n=5)` 
  - `calculate_team_similarity_matrix()`
- **Verification**: Module imports successfully, functions return expected types
- **Dependencies**: None

**Task 2.2: Drive Efficiency Features**

- **Agent**: DriveEfficiencyAgent
- **Action**: Update src/features/cfbd_feature_engineering.py to add:
  - `calculate_points_per_drive()`
  - `calculate_explosive_drive_rate()`
- **Verification**: Functions added, calculate PPD correctly on sample data
- **Dependencies**: None (can run parallel with 2.1)

**Task 2.3: Offense vs Defense Comparison**

- **Agent**: OffenseDefenseAgent
- **Action**: Create src/features/offense_defense.py with:
  - `normalize_matchup_metrics(offense_team, defense_team)`
  - `generate_matchup_comparison(team1, team2)`
- **Verification**: Functions normalize correctly, return dict with expected keys
- **Dependencies**: None (can run parallel with 2.1, 2.2)

**Task 2.4: Feature Integration Test**

- **Agent**: FeatureValidatorAgent
- **Action**: Create tests/test_new_features.py with assertions:
  - PPD columns exist in processed data
  - similarity.py returns list of teams
  - offense_defense functions return valid comparisons
- **Verification**: All tests pass (pytest tests/test_new_features.py)
- **Dependencies**: [2.1, 2.2, 2.3] (requires all feature modules)

### Coordination Flow

```
TeamSimilarityAgent (2.1) ──┐
DriveEfficiencyAgent (2.2) ─┼─> FeatureValidatorAgent (2.4)
OffenseDefenseAgent (2.3) ──┘
```

## Phase 3: Model Expansion (Random Forest)

### Task Decomposition

**Task 3.1: Random Forest Implementation**

- **Agent**: RandomForestTrainerAgent
- **Action**: Create src/models/random_forest.py implementing logic from 02_random_forest_team_points.ipynb
- **Key Components**:
  - `RandomForestScorePredictor` class
  - `train_model()` method
  - `predict_scores(home_team, away_team)` method
- **Verification**: Class instantiates, methods exist, type hints correct
- **Dependencies**: None

**Task 3.2: Model Training Dry-Run**

- **Agent**: RandomForestTrainerAgent
- **Action**: Train model on small dataset (100 games), save to .pkl
- **Verification**: 
  - Model file created (random_forest_model.pkl)
  - File size > 0 bytes
  - Model.predict() returns float predictions
- **Dependencies**: [3.1] (requires implementation)

**Task 3.3: Ensemble Integration**

- **Agent**: EnsembleIntegratorAgent
- **Action**: Update main inference pipeline to include Random Forest:
  - Load RF model alongside Ridge/XGBoost/FastAI
  - Add RF predictions to ensemble dictionary
  - Update prediction aggregation logic
- **Verification**: Pipeline loads all 4 models, RF predictions included in output
- **Dependencies**: [3.2] (requires trained model)

**Task 3.4: Model Output Validation**

- **Agent**: ModelValidatorAgent
- **Action**: Validate RF model outputs:
  - Predictions are floats
  - home_points > 0, away_points > 0
  - Predictions within reasonable range (0-100)
- **Verification**: All validation checks pass
- **Dependencies**: [3.3] (requires integrated pipeline)

### Coordination Flow

```
RandomForestTrainerAgent (3.1) ──> RandomForestTrainerAgent (3.2) ──> EnsembleIntegratorAgent (3.3) ──> ModelValidatorAgent (3.4)
```

## Phase 4: Interpretability & Dashboarding

### Task Decomposition

**Task 4.1: SHAP Utilities Module**

- **Agent**: SHAPVisualizerAgent
- **Action**: Create src/visualization/shap_utils.py with:
  - `generate_beeswarm_plot(model, features)`
  - `generate_force_plot(model, instance, features)`
  - `generate_waterfall_plot(model, instance, features)`
- **Verification**: Module imports, functions create valid SHAP plots
- **Dependencies**: None

**Task 4.2: Interactive Dashboard Module**

- **Agent**: DashboardBuilderAgent
- **Action**: Create src/visualization/dashboard.py with:
  - `create_team_efficiency_dashboard(teams_data)` - Scatter plot: Offense PPA vs Defense PPA
  - `create_metric_distribution_explorer(metrics_data)` - Histograms with KDE
- **Verification**: Functions create Plotly figures, HTML export works
- **Dependencies**: None (can run parallel with 4.1)

**Task 4.3: Report Generator Update**

- **Agent**: ReportGeneratorAgent
- **Action**: Update weekly report generator to:
  - Call SHAP utilities for each game prediction
  - Generate interactive dashboards
  - Save plots as HTML files (week{XX}_interactive_dashboard.html)
- **Verification**: Report generation includes new artifacts
- **Dependencies**: [4.1, 4.2] (requires visualization modules)

**Task 4.4: Artifact Validation**

- **Agent**: ReportGeneratorAgent
- **Action**: Run reporting pipeline for current week, verify outputs:
  - HTML files exist in outputs/ folder
  - PNG files generated and non-empty
  - All visualization artifacts present
- **Verification**: 
  - File count matches expected
  - File sizes > 0 bytes
  - HTML files openable in browser
- **Dependencies**: [4.3] (requires updated report generator)

### Coordination Flow

```
SHAPVisualizerAgent (4.1) ──┐
                              ├─> ReportGeneratorAgent (4.3) ──> ReportGeneratorAgent (4.4)
DashboardBuilderAgent (4.2) ──┘
```

## Implementation Details

### Agent Creation Pattern

Each specialized agent inherits from `BaseAgent`:

```python

class TeamSimilarityAgent(BaseAgent):

def **init**(self, agent_id: str):

super().**init**(

agent_id=agent_id,

name="Team Similarity Agent",

permission_level=PermissionLevel.READ_EXEC

### To-dos

- [ ] RequirementsUpdaterAgent: Add plotly>=5.17.0 and ipywidgets>=8.1.0 to requirements.txt
- [ ] DependencyVerifierAgent: Create scripts/verify_dependencies.py with package checking logic
- [ ] EnvironmentValidatorAgent: Execute pip install -r requirements.txt
- [ ] DependencyVerifierAgent: Execute verification script and confirm all packages installed
- [ ] TeamSimilarityAgent: Create src/features/similarity.py with KNN team similarity functions
- [ ] DriveEfficiencyAgent: Add PPD and explosive drive rate functions to feature engineering module
- [ ] OffenseDefenseAgent: Create src/features/offense_defense.py with normalized matchup comparison functions
- [ ] FeatureValidatorAgent: Create tests/test_new_features.py and verify all new features work
- [ ] RandomForestTrainerAgent: Create src/models/random_forest.py implementing score prediction logic
- [ ] RandomForestTrainerAgent: Train Random Forest model on sample data and save to .pkl file
- [ ] EnsembleIntegratorAgent: Update inference pipeline to include Random Forest predictions
- [ ] ModelValidatorAgent: Validate Random Forest model outputs are correct format and range
- [ ] SHAPVisualizerAgent: Create src/visualization/shap_utils.py with beeswarm, force, and waterfall plot functions
- [ ] DashboardBuilderAgent: Create src/visualization/dashboard.py with team efficiency and metric distribution functions
- [ ] ReportGeneratorAgent: Update weekly report generator to include SHAP and dashboard artifacts
- [ ] ReportGeneratorAgent: Run reporting pipeline and verify all HTML/PNG artifacts are generated correctly