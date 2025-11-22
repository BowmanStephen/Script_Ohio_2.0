# Weekly Maintenance Workflow

## When to Run: Every Tuesday after weekend games finalize

### Step 1: Prepare for New Week Analysis
```bash
# Run the preparation script for the new week (e.g., Week 13)
python scripts/prepare_week13_analysis.py

# Or for any week:
python scripts/prepare_weekly_analysis.py --week 14

# Or with custom season:
python scripts/prepare_weekly_analysis.py --week 14 --season 2025
```

This script will:
- Check CFBD API key availability
- Fetch the new week's schedule (if API key available)
- Validate previous week's results are in training data
- Check model file status
- Create necessary directory structure
- Provide recommendations for next steps

### Step 2: Fetch New Week Data
```bash
export CFBD_API_KEY=your_key_here
cd project_management/TOOLS_AND_CONFIG

# Replace XX with current week number
python fetch_future_week.py --week XX
```

### Step 3: Rebuild Plays File
```bash
cd project_management/core_tools
python rebuild_model_pack_plays.py
```

### Step 4: Verify Data Integrity
```bash
# Check for mock data
rg -i "mock" model_pack/2025_plays.csv

# Count games by week
python - <<'EOF'
import pandas as pd
games = pd.read_csv('starter_pack/data/2025_games.csv')
print(games.groupby('week')['id'].count().sort_index())
EOF
```

### Step 5: Update Training Data (Every 2-4 Weeks)
```bash
python project_management/core_tools/create_migration_file.py --max-week XX
python project_management/core_tools/data_workflows.py extend-training     --migrated-file model_pack/2025_weeks1-XX_migrated.csv
```

### Step 6: Retrain Models
```bash
python config/retrain_fixed_models.py
python project_management/core_tools/data_workflows.py train-fastai     --epochs 50 --learning-rate 5e-4
```

### Step 7: Run Weekly Analysis (Week 13+)

#### Option A: Using the Command-Line Script (Easiest)
```bash
# Run complete Week 13 analysis
python scripts/run_weekly_analysis.py --week 13

# Run specific step only
python scripts/run_weekly_analysis.py --week 13 --step validation
python scripts/run_weekly_analysis.py --week 13 --step matchup
python scripts/run_weekly_analysis.py --week 13 --step predictions

# Verbose output
python scripts/run_weekly_analysis.py --week 13 --verbose
```

#### Option B: Using the Weekly Orchestrator (Python)
```python
from agents.weekly_analysis_orchestrator import WeeklyAnalysisOrchestrator

# Initialize orchestrator for the week
orchestrator = WeeklyAnalysisOrchestrator(week=13, season=2025)

# Run complete analysis pipeline
result = orchestrator.run_complete_analysis()
print(f"Analysis Status: {result['final_status']}")
print(f"Steps Completed: {result['steps_completed']}")
```

#### Option C: Using Individual Weekly Agents
```python
from agents.weekly_matchup_analysis_agent import WeeklyMatchupAnalysisAgent
from agents.weekly_model_validation_agent import WeeklyModelValidationAgent
from agents.weekly_prediction_generation_agent import WeeklyPredictionGenerationAgent

# Step 1: Validate models
validation_agent = WeeklyModelValidationAgent(week=13, season=2025)
validation_result = validation_agent.execute_task({})

# Step 2: Analyze matchups
matchup_agent = WeeklyMatchupAnalysisAgent(week=13, season=2025)
matchup_result = matchup_agent.execute_task({})

# Step 3: Generate predictions
prediction_agent = WeeklyPredictionGenerationAgent(week=13, season=2025)
prediction_result = prediction_agent.execute_task({})
```

#### Option D: Using Week 12 Agents (Backward Compatible)
```python
# Week 12 agents are now thin wrappers around weekly agents
from agents.week12_matchup_analysis_agent import Week12MatchupAnalysisAgent
from agents.week12_model_validation_agent import Week12ModelValidationAgent
from agents.week12_prediction_generation_agent import Week12PredictionGenerationAgent

# These work exactly as before, but now delegate to generic weekly agents
agent = Week12MatchupAnalysisAgent()
result = agent.execute_task({})
```

### Weekly Agent System Architecture

The system now uses a reusable weekly agent architecture:

- **Generic Weekly Agents** (Week-agnostic):
  - `WeeklyMatchupAnalysisAgent(week, season)` - Analyzes matchups for any week
  - `WeeklyModelValidationAgent(week, season)` - Validates models for any week
  - `WeeklyPredictionGenerationAgent(week, season)` - Generates predictions for any week
  - `WeeklyAnalysisOrchestrator(week, season)` - Coordinates all weekly agents

- **Week 12 Agents** (Backward Compatible):
  - `Week12MatchupAnalysisAgent` - Thin wrapper around `WeeklyMatchupAnalysisAgent(week=12)`
  - `Week12ModelValidationAgent` - Thin wrapper around `WeeklyModelValidationAgent(week=12)`
  - `Week12PredictionGenerationAgent` - Thin wrapper around `WeeklyPredictionGenerationAgent(week=12)`

### Directory Structure

Each week requires the following directory structure:
```
data/week{XX}/enhanced/
  - week{XX}_features_86.csv
  - week{XX}_enhanced_games.csv
  - enhancement_metadata.json

analysis/week{XX}/
  - week{XX}_comprehensive_analysis.json
  - week{XX}_strategic_recommendations.csv
  - week{XX}_power_rankings.csv
  - week{XX}_upset_alerts.csv

predictions/week{XX}/
  - week{XX}_comprehensive_predictions.csv
  - week{XX}_predictions.json
  - week{XX}_recommendations.csv
  - prediction_insights.json
  - week{XX}_prediction_summary.json

validation/week{XX}/
  - week{XX}_model_validation_report.json
  - validation_summary.csv
```

### Troubleshooting
- **"No games found for week XX"** – CFBD may not be updated; wait 24-48 hours.
- **Duplicate game_id errors** – rebuild `2025_games.csv` by deduplicating `id`.
- **Model predictions seem off** – confirm training data includes latest weeks and retrain models.
- **"Week XX features not found"** – Run mock enhancement agent or CFBD pipeline to generate features.
- **"Week XX directory not found"** – Run `scripts/prepare_week13_analysis.py` to create directory structure.
