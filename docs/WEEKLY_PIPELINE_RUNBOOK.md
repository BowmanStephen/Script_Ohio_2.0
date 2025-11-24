## Weekly Pipeline Runbook

**Objective:** refresh data, retrain ensembles, and publish reports for a
given CFBD week.

### 0. Preconditions

- `CFBD_API_KEY` exported in the shell that will run the commands.
- Virtual environment activated (`python3.13 -m venv venv && source venv/bin/activate`).
- Dependencies installed (`pip install -r requirements.txt -r requirements-dev.txt`).

### 1. Smoke test tooling

```bash
python3 scripts/smoke_test_toon.py
python3 -m pytest tests/agents -m "not performance" --maxfail=1
```

### 2. Ingest latest data

```bash
python3 scripts/cfbd_pull.py --season 2025 --week ${WEEK}
python3 scripts/sync_all_data_sources.py --week ${WEEK}
```

Artifacts land under `data/weekly/week${WEEK}/`.

### 3. Feature engineering & validation

```bash
python3 scripts/run_weekly_analysis.py --week ${WEEK} --validate
python3 scripts/verify_weekly_agents.py --week ${WEEK}
```

- `run_weekly_analysis` populates `analysis/week${WEEK}/` with enriched
  features, power ratings, and matchup notes.
- `verify_weekly_agents` ensures all orchestrated agent capabilities still
  pass lint + type gates before predictions begin.

### 4. Model refresh

```bash
python3 scripts/retrain_models_full_features.py --week ${WEEK}
python3 scripts/optimize_meta_ensemble_weights.py --week ${WEEK}
```

Upload resulting models to the secure artifact bucket (see
`docs/DATA_ASSET_SECURITY.md`) if they differ from the last baseline.

### 5. Publish predictions & reports

```bash
python3 scripts/generate_week13_master_report.py --week ${WEEK}
python3 scripts/enhance_predictions_with_ratings.py --week ${WEEK}
python3 agents/demo_agent_system.py --mode weekly --week ${WEEK}
```

- CSV/JSON predictions drop in `predictions/week${WEEK}/`.
- Narrative Markdown reports are stored in `reports/week${WEEK}_*.md`.
- Commit lightweight assets only; encrypt/cache large files via
  `scripts/secure_artifacts.py`.

### 6. Post-run checklist

- [ ] CI Quality & Security workflow green.
- [ ] Observability dashboard shows no CRITICAL errors.
- [ ] `outputs/secure/` updated with encrypted cache/model snapshot.
- [ ] `reports/weekly_summary_${WEEK}.md` reviewed and shared.

