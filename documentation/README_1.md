# Script Ohio 2.0

![Docs Status](https://img.shields.io/badge/docs-Grade%20A-green)

Script Ohio 2.0 is an agent-driven college football analytics platform that
combines a multi-agent system, educational starter-pack notebooks, and a model
pack with opponent-adjusted features (2016-2025 seasons).

## ✨ Features

- **Agent System (95% production ready)** – Analytics Orchestrator, Context Manager, Model Execution Engine, and specialized agents that coordinate end-to-end requests.
- **Starter Pack** – 12 learning-first notebooks, helper utilities, and curated data snapshots dating back to 1869 for rapid onboarding.
- **Model Pack** – Seven modeling notebooks, updated training data (4,989 games, 86 features), and pre-trained Ridge, XGBoost, and FastAI artifacts refreshed for the 2025 season.

## 🚀 Installation

1. Install Python 3.13+ and clone the repo.
2. Create and activate a virtual environment:
   ```bash
   python3.13 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
4. (Optional) Install extra tooling:
   ```bash
   pip install -r requirements-dev.txt
   pip install -r requirements-optional.txt  # includes cfbd client
   ```

## ▶️ Usage

1. Export your CFBD API key before running data pulls:
   ```bash
   export CFBD_API_KEY="your-key"
   ```
2. Run the end-to-end agent demo to verify the system:
   ```bash
   python project_management/TOOLS_AND_CONFIG/demo_agent_system.py
   ```
3. Kick off a quick workflow loop (data refresh → training):
   ```bash
   python project_management/data_workflows.py refresh-training --max-week 13 --train-models
   ```
4. Open the starter pack notebooks (e.g., `starter_pack/01_intro_to_data.ipynb`) after running `make bootstrap-notebooks` to ensure the auto-setup cell is present.

## 🤝 Contributing

- Review `AGENTS.md` plus the guides in `documentation/developer/` before opening PRs.
- Run the core pytest suite (`python -m pytest -v`) and relevant workflow scripts before submitting changes.
- Follow the BaseAgent inheritance pattern and permission requirements documented in the repo.

## 📄 License

The bundled starter pack content is licensed for personal, non-commercial use per `starter_pack/LICENSE`. Contact admin@collegefootballdata.com for organizational licensing questions. Additional documentation around usage restrictions lives in `documentation/user/cfbd_api_guide.md`.

---

## 🧰 Turnkey Workflows

| Task | Command | Notes |
|------|---------|-------|
| Bootstrap notebook cells | `make bootstrap-notebooks` | Reinserts the standardized `%run ./_auto_setup.py` cell across the starter pack. |
| Refresh starter-pack datasets | `python project_management/TOOLS_AND_CONFIG/update_data.py --datasets games season_stats advanced_season_stats drives --seasons 2025` | Pulls live CFBD data with built-in snapshots + throttling and rewrites the CSVs under `starter_pack/data/`. |
| Extend training dataset | `python project_management/data_workflows.py refresh-training --skip-migration --migrated-file model_pack/2025_starter_pack_migrated.csv` | Appends newly migrated rows into `model_pack/updated_training_data.csv` with auto backups. |
| Train FastAI model | `python project_management/data_workflows.py train-fastai --epochs 50 --learning-rate 5e-4` | Produces a fresh `model_pack/fastai_home_win_model_2025.pkl` that the Model Execution Engine can load. |
| Full refresh loop | `python project_management/data_workflows.py refresh-training --max-week 13 --train-models` | Runs migration → extend-training → FastAI retrain sequentially. |
| Notebook live fetch toggle | `fetch_latest = True` (see `01_intro_to_data.ipynb`) | Switches notebooks to `starter_pack.utils.cfbd_loader.CFBDLoader()` for live CFBD pulls. |
| Tests | `python -m pytest tests/test_data_refresh_workflow.py -v` | Exercises the new data refresh + training builder pipelines (in addition to the main suite). |
| Data validation bundle | `make verify-data` | Runs `DATA_VALIDATION_SCRIPT.py`, `DATA_REMEDIATION_SCRIPT.py`, and `MASTER_ADMIN_SYSTEM_AUDIT.py` sequentially. |

All targets rely on `python3` (3.13+) and the requirements files checked into the
repo. The `project_management/data_workflows.py` orchestrator exposes the same
functionality without make:

```bash
python project_management/data_workflows.py starter-data --season 2025 --week 13
python project_management/data_workflows.py extend-training --migrated-file model_pack/2025_starter_pack_migrated.csv
python project_management/data_workflows.py refresh-training --max-week 13 --train-models
```

---

## 🔑 CFBD API Key & Rate Limiting

1. Obtain a key from https://collegefootballdata.com/ and export it before running
   data refresh or notebooks:
   ```bash
   export CFBD_API_KEY="your-key"
   ```
2. Live pulls respect the documented 6 req/sec limit. For loops, add
  `time.sleep(0.17)` to avoid HTTP 429 responses (all built-in tools already do this).
3. The notebook bootstrapper (`starter_pack/utils/bootstrap.py`) warns if the key
  is missing and points to `documentation/user/cfbd_api_guide.md` for remediation.

---

## 📁 Key Directories

- `starter_pack/` – Educational notebooks, auto-setup helpers, and bundled data.
- `model_pack/` – Training data, notebooks, and serialized ML models.
- `agents/` – Production multi-agent system (Analytics Orchestrator, Context Manager, etc.).
- `project_management/` – Tooling, workflows, quality assurance scripts.
- `tests/` – Pytest suite covering configuration, bootstrap utilities, and data workflows.

---

## 🧪 Testing & Validation

```bash
python -m pytest -v                    # full test suite
python -m pytest tests/test_notebook_bootstrap.py -v
python -m pytest tests/test_data_workflows.py -v
python -m pytest tests/test_notebook_entry_smoke.py -v  # Papermill smoke for 01_intro_to_data
python -m pytest tests/test_model_execution_engine_comprehensive.py -k fastai_model_real_prediction
```

Before shipping code:
1. Run notebook/bootstrap tests to ensure the auto-setup helper still behaves.
2. Execute `project_management/data_workflows.py train-fastai` after extending the
   training dataset so the FastAI model artifact is refreshed.
3. Optionally run `project_management/TOOLS_AND_CONFIG/test_agents.py` to validate
   the multi-agent orchestration.

---

## 🧭 Documentation Links

- `AGENTS.md` – Comprehensive platform and agent guidance (OpenAI agents.md format).
- `starter_pack/README.md` – Notebook contents, auto-setup behavior, and CFBD usage tips.
- `model_pack/model_deployment_guide_2025.md` – Model integration details.

For additional automation instructions see `project_management/data_workflows.py
--help`.
