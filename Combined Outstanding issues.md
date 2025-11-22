# Script Ohio 2.0 — Simplified Outstanding Issues (Local-Only)

Goal: keep a small, reliable pipeline that pulls CFBD data, builds features, runs the existing models, and spits out weekly predictions on my laptop. Everything below is scoped to that.

## What to Keep (core path)
- Unified CFBD client and cache under `src/cfbd_client/`; continue to use env var `CFBD_API_KEY`.
- Feature and model code in `src/features/`, `src/models/`, `model_config.py`, `model_features.py`.
- Pretrained models in `ridge_model_2025.joblib`, `xgb_home_win_model_2025.pkl`, `fastai_home_win_model_2025.pkl` (assume these remain the canonical assets).
- Simple drivers: `scripts/run_weekly_analysis.py`, `scripts/cfbd_pull.py`, and any small notebook like `starter_pack/notebooks/CFBD_Ingestion_v2.ipynb` for ad hoc checks.
- Minimal agent entry if helpful: `agents/model_execution_engine.py` for a programmatic API; otherwise, keep orchestration out of the happy path.

## What to Ignore/Drop for a personal project
- Kubernetes/deployment/monitoring under `deployment/` and `monitoring/`.
- Heavy security/audit/CI pipelines, dependency scans, and TOON workflow ceremonies unless they directly stop you from running locally.
- Duplicated backups and alternate clients (`archive/`, `backup/`, duplicated `model_pack` or `starter_pack`, `debug_*` backups) once you’ve confirmed nothing critical lives there.
- Excess agent wrappers (weekly orchestration variants, legacy system agents) unless you actively use them.

## Quick start (fresh machine)
1) `python3.13 -m venv venv && source venv/bin/activate`
2) `pip install -r requirements.txt` (only add `-r requirements-dev.txt` if you need tests right now)
3) `export CFBD_API_KEY=...`
4) Run a sanity pull: `python3 scripts/cfbd_pull.py --season 2025 --week 13`
5) Run the simple weekly pipeline: `python3 scripts/run_weekly_analysis.py --week 13`
6) Spot-check model load: `python -c "from agents.model_execution_engine import ModelExecutionEngine; print(ModelExecutionEngine('me')._execute_action('predict_game_outcome', {'team1':'Ohio State','team2':'Michigan'}, {}))"`

## Outstanding Issues (prioritized for “make it run simply”)
- P0 Data pull reliability: verify `src/cfbd_client/unified_client.py` is the only client used; remove or clearly mark any older clients from imports. Confirm rate limiting works and GraphQL fallbacks are graceful (REST fallback accepted).
- P0 Model inputs: ensure the weekly analysis script aligns with `model_features.py` expectations (column names/dtypes). Add a small check that warns if features are missing or shifted.
- ✅ P0 Paths and assets: **RESOLVED** — Canonical paths established (`data/weekly/weekXX/enhanced/` for enhanced, `data/training/weekly/` for training). Path utilities added for centralized access. Copy directory references removed from active code.
- P1 Predictions output: standardize one output location (e.g., `predictions/week13/`) with CSV + brief markdown summary. Delete/ignore older scattered outputs after confirming you don’t need them.
- P1 Logging: add a lightweight structured logger (or keep stdlib) but ensure data pulls and model run steps emit start/end/errors to a single log file under `logs/`.
- P1 Notebook drift: if a notebook contains logic not in `src/`, lift that code into `src/` and leave the notebook as a thin demo so production and notebooks are consistent.
- P2 Tests (lightweight): keep only a smoke suite that (a) pulls a tiny sample via the unified client, (b) loads each model file, and (c) runs one end-to-end predict call with stubbed data. Skip broader CI ambitions.
- P2 Cleanup of agents: demote/disable unused agents in `agents/analytics_orchestrator.py` to reduce surface area; keep only CFBD, model execution, and optionally insight/report if you use them.
- P3 Documentation trim: create a short `README_local.md` that explains the quick start above, the data paths, and the single happy-path command. Link to deeper docs only if needed.

## Concrete Deletes/Archival (after verifying no unique data)
- Extra copies: `model_pack copy/`, `starter_pack copy/`.
- Backup/debug files: anything ending in `.backup` under root, `debug_*` scripts you don’t run, old logs in `logs/` older than your last two weeks.
- Legacy clients: `src/cfbd_client/client.py`, `src/data_sources/cfbd_client.py`, `starter_pack/utils/cfbd_loader.py` once you confirm no imports rely on them.
- Excess orchestration artifacts: unused TOON plans in `.cursor/plans/` and `workflows/`—keep one “golden” plan if you actually use the Workflow Automator.

## “If starting over today” plan
- Minimal stack: keep Python + CFBD client + three models + one weekly script. No TOON, no K8s, no CI beyond a local smoke test.
- Data habit: one canonical weekly data folder, one predictions folder, one log file. Delete or archive everything else.
- Reuse: move any good utilities from notebooks into `src/` modules and delete notebook copies once migrated.
- Guardrails: a 5-minute smoke test (`pytest tests/smoke_local.py` or similar) that (1) fetches one endpoint with the unified client, (2) loads each model, (3) runs one predict.
- Output: single CSV + short markdown summary per week; optional Plotly chart if desired.

## Open Questions to resolve before cleaning
- Are any legacy datasets in `backup/` or `archive/` the only source for certain weeks? If not, archive externally and drop.
- Do you still need GraphQL-specific flows, or is REST good enough for your usage? Decide and trim code accordingly.
- Which agents do you actually call? List them and disable the rest.

When these are addressed, the repo becomes a lean local tool: pull data → build features → run three models → emit one set of predictions, with minimal maintenance overhead.***
