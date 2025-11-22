# Weekly Analysis - Quick Reference Guide

## 🚀 Quick Start

### Prepare for Week 13
```bash
python scripts/prepare_week13_analysis.py
```

### Run Week 13 Analysis
```bash
python scripts/run_weekly_analysis.py --week 13
```

### Verify Everything Works
```bash
python scripts/verify_weekly_agents.py
```

## 📋 Common Commands

### Preparation
```bash
# Prepare any week
python scripts/prepare_weekly_analysis.py --week 14

# Skip API fetch (use existing data)
python scripts/prepare_weekly_analysis.py --week 13 --skip-fetch

# Skip validation check
python scripts/prepare_weekly_analysis.py --week 13 --skip-validation
```

### Running Analysis
```bash
# Complete pipeline
python scripts/run_weekly_analysis.py --week 13

# Individual steps
python scripts/run_weekly_analysis.py --week 13 --step validation
python scripts/run_weekly_analysis.py --week 13 --step matchup
python scripts/run_weekly_analysis.py --week 13 --step predictions

# Verbose output
python scripts/run_weekly_analysis.py --week 13 --verbose
```

### Python API
```python
# Complete pipeline
from agents.weekly_analysis_orchestrator import WeeklyAnalysisOrchestrator
orchestrator = WeeklyAnalysisOrchestrator(week=13, season=2025)
result = orchestrator.run_complete_analysis()

# Individual agents
from agents.weekly_matchup_analysis_agent import WeeklyMatchupAnalysisAgent
agent = WeeklyMatchupAnalysisAgent(week=13, season=2025)
result = agent.execute_task({})
```

## 📁 Output Locations

After running analysis, results are saved to:

- **Analysis**: `analysis/week{XX}/`
- **Predictions**: `predictions/week{XX}/`
- **Validation**: `validation/week{XX}/`
- **Data**: `data/week{XX}/enhanced/`

## 🔄 Migration from Week 12

### Old Way (Still Works!)
```python
from agents.week12_matchup_analysis_agent import Week12MatchupAnalysisAgent
agent = Week12MatchupAnalysisAgent()
result = agent.execute_task({})
```

### New Way (Recommended)
```python
from agents.weekly_matchup_analysis_agent import WeeklyMatchupAnalysisAgent
agent = WeeklyMatchupAnalysisAgent(week=12, season=2025)
result = agent.execute_task({})
```

Both work identically - Week 12 agents are thin wrappers around weekly agents.

## 🛠️ Troubleshooting

### "Week XX features not found"
```bash
# Generate features using enhancement agent or CFBD pipeline
# Check: data/week{XX}/enhanced/week{XX}_features_86.csv
```

### "Models not loading"
```bash
# Check model files exist:
ls -lh model_pack/*_2025.*
# If missing, retrain:
python config/retrain_fixed_models.py
```

### "No games found for week XX"
```bash
# Fetch from CFBD API (requires CFBD_API_KEY):
export CFBD_API_KEY=your_key
python scripts/prepare_weekly_analysis.py --week XX
```

## 📚 More Information

- **Full Documentation**: `project_management/WEEKLY_MAINTENANCE.md`
- **Usage Examples**: `scripts/example_weekly_usage.py`
- **Implementation Details**: `project_management/WEEK13_IMPLEMENTATION_SUMMARY.md`
- **Agent Documentation**: `AGENTS.md`

