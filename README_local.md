# Script Ohio 2.0 — Local Working Rhythm

This project is for local use: pull CFBD data, build features, run the three models, and emit weekly predictions. Keep the happy path green and work in tiny slices.

## Happy Path Commands
1) Activate env: `python3.13 -m venv venv && source venv/bin/activate`
2) Install deps: `pip install -r requirements.txt`
3) Set key: `export CFBD_API_KEY=...`
4) Data pull: `python3 scripts/cfbd_pull.py --season 2025 --week 13`
5) Weekly run: `python3 scripts/run_weekly_analysis.py --week 13`
6) (Optional) Agent API sanity:  
   `python -c "from agents.model_execution_engine import ModelExecutionEngine; print(ModelExecutionEngine('me')._execute_action('predict_game_outcome', {'team1':'Ohio State','team2':'Michigan'}, {}))"`

## Workstyle (micro-slices)
- Pick one task that fits in 30–60 minutes, not a big bang.
- Do the task, then immediately run the happy path (steps 4–5). If it breaks, fix or revert the change before adding new work.
- Log 2–3 lines in `SESSION_LOG.md` per session (date, task, result, next step).
- Keep changes small and self-contained; avoid parallel edits.

## Canonical Paths
- **Data (enhanced)**: `data/weekly/week{XX}/enhanced/`
- **Training data**: `data/training/weekly/`
- **Predictions**: `predictions/week{XX}/predictions.csv` and `predictions/week{XX}/summary.md`
- **Logs**: `logs/cfbd_pull.log` and `logs/weekly_analysis.log`

## Single Happy-Path Command
```bash
python3 scripts/run_weekly_analysis.py --week {XX}
```

This single command runs the complete pipeline:
1. Validates models
2. Analyzes matchups
3. Generates predictions
4. Creates report

Outputs are saved to standardized locations (see Canonical Paths above).

## Status (Updated)
✅ **P0 Complete**: UnifiedCFBDClient only, feature validation added, canonical paths established
✅ **P1 Complete**: Centralized logging to `logs/`, standardized predictions output
✅ **P2 Complete**: Smoke tests created, unused agents disabled

For details on completed work, see `Combined Outstanding issues.md`.

## Cleanup Safety
- Before deleting backups/copies, confirm no imports rely on them. Temporarily park deletions in `archive/old/` if unsure.
- Remove one legacy client at a time: mark deprecated → search imports → swap → rerun happy path.

## Session Template (for `SESSION_LOG.md`)
- Date:
- Task:
- Result (pass/fail and quick note):
- Next step:

Keep this file as the anchor. Any session (or agent) can read this to resume work without prior chat context.***
