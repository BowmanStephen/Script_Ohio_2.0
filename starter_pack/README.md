# 🏈 College Football Data Starter Pack

Welcome to the **CollegeFootballData.com Starter Pack** — a curated bundle of structured college football data, custom advanced metrics, and real-world Jupyter notebooks to help you build models, explore trends, and launch your own analytics projects faster.

---

## 📦 What’s Included

- ✅ **Historical Data**  
  - Game results (1869–present)  
  - Play-by-play, drives, season stats (2003–present)  
  - Advanced team-level metrics (EPA, success rate, explosiveness, etc.)

- ✅ **14 Jupyter Notebooks**  
  - Code walkthroughs for ranking, predictions, dashboards, and more  
  - **NEW:** `notebooks/CFBD_Ingestion.ipynb` (REST/Next ingestion + feature engineering)  
  - **NEW:** `notebooks/CFBD_GraphQL_Playground.ipynb` (talent/recruiting exploration + subscription scaffold)

- ✅ **PDF Guides**  
  - Full data dictionary  
  - Overview of included notebooks

- ✅ **Metadata**  
  - Teams, conferences, venues

---

## 🎓 Interactive Learning Path

Navigate through the starter pack notebooks with the interactive **Learning Path Navigator**:

```python
from src.infographics import LearningPathNavigator

navigator = LearningPathNavigator(title="Starter Pack Learning Path")

data = {
    'notebooks': [
        {'name': 'Data Dictionary', 'skill_level': 'beginner'},
        {'name': 'Intro to Data', 'skill_level': 'beginner'},
        {'name': 'Simple Rankings', 'skill_level': 'beginner'},
        {'name': 'Metrics Comparison', 'skill_level': 'intermediate'},
        {'name': 'Team Similarity', 'skill_level': 'intermediate'},
        {'name': 'Matchup Predictor', 'skill_level': 'advanced'}
    ]
}

html_path = navigator.generate_html(data, "starter_pack/infographics/learning_path.html")
```

Or use the CLI tool:
```bash
python scripts/generate_infographics.py --component learning_path --output starter_pack/infographics/
```

---

## 🧠 Who It's For

This pack is designed for:

- Data scientists & analysts  
- CFB modelers and pick’em competitors  
- Academic researchers  
- Hobbyists and fans who love working with real data

---

## 📚 Folder Structure
📂 data
  📂 advanced_game_stats/
  📂 advanced_season_stats/
  📂 drives/
  📂 game_stats/
  📂 plays/
  📂 season_stats/
  📄 conferences.csv
  📄 games.csv
  📄 teams.csv
📄 00_data_dictionary.ipynb
📄 01_intro_to_data.ipynb
📄 02_build_simple_rankings.ipynb
📄 03_metrics_comparison.ipynb
📄 04_team_similarity.ipynb
📄 05_matchup_predictor.ipynb
📄 06_custom_rankings_by_metric.ipynb
📄 07_drive_efficiency.ipynb
📄 08_offense_vs_defense_comparison.ipynb
📄 09_opponent_adjustments.ipynb
📄 10_srs_adjusted_metrics.ipynb
📄 11_metric_distribution_explorer.ipynb
📄 CFBD Starter Pack - Data Files Guide.pdf
📄 CFBD Starter Pack - Notebooks Guide.pdf
📄 headers.md
📄 12_efficiency_dashboards.ipynb
📄 LICENSE.txt
📄 README.md

---

## ⚙️ Requirements & Auto-Setup

Every starter-pack notebook (and each model-pack notebook in `../model_pack/`)
now ships with an **auto-setup cell** (tagged `auto-setup`) as the very first cell.
When you open a notebook it will prompt you to run:

```python
%run ./_auto_setup.py
```

That script calls `starter_pack.utils.bootstrap.ensure_notebook_environment()` which:

- Detects the project root so `agents.*` imports work automatically (even from the model pack).
- Checks for core dependencies (`pandas`, `numpy`, `matplotlib`, `seaborn`, `scikit-learn`,
  `xgboost`, `cfbd`) and, if missing, runs `pip install -r ../requirements.txt` **once** per kernel.
- Warns you if a `CFBD_API_KEY` is not configured so live CFBD pulls don’t fail silently.

To opt out of automatic pip installs (for example in a managed environment), start your
kernel with:

```bash
export CFB_AUTO_INSTALL=0
```

or override the requirements file with:

```bash
export CFB_NOTEBOOK_REQUIREMENTS=requirements-dev.txt
```

You’ll still benefit from:
- Familiarity with Python and pandas
- Basic football domain knowledge (drives, downs, efficiency, etc.)

> 🔐 **Live CFBD Data:** Set `CFBD_API_KEY` (or `CFBD_API_TOKEN`) in your shell before launching
> Jupyter. Respect the 6 req/sec rate limit by inserting `time.sleep(0.17)` inside loops.
> Full walkthrough: `documentation/user/cfbd_api_guide.md`.

---

## 🔄 Automated Data Refresh

Keep the CSV snapshots under `starter_pack/data/` current with the dedicated CLI:

```bash
python project_management/TOOLS_AND_CONFIG/update_data.py \
  --datasets games season_stats advanced_season_stats drives \
  --seasons 2025
```

Key details:

- Requires `cfbd` (`pip install cfbd` or `pip install -r requirements-optional.txt`)
- Reads the API key from `CFBD_API_KEY`/`CFBD_API_TOKEN` (or pass `--api-key`)
- Throttles each request (0.17s) to respect the 6 req/sec limit
- Supports multiple seasons at once (`--seasons 2025 2024`) plus a `--dry-run` mode

---

## ⚡ CFBD Live Pipelines (REST + GraphQL)

### REST / Next API (Default Integration)

The **default integration** for pulling CFBD data (scores, stats, etc.) uses the REST API. This is the recommended approach for most use cases and does not require any special subscription tier.

- **CLI:** `scripts/cfbd_pull.py --season 2025 --week 12 --source rest`  
  - Fetches REST/Next game payloads  
  - Aligns data with the 86-feature schema via `CFBDFeatureEngineer`  
  - Runs the ridge 2025 model to produce margin predictions  
  - Persists JSON/CSV outputs under `outputs/cfbd_ingest/<timestamp>/`

- **Notebooks:**  
  - `notebooks/CFBD_Ingestion.ipynb` — single-run walkthrough that mirrors the CLI and writes to `outputs/notebooks/`

Supply `--source next` or `--use_next=True` to compare experimental `apinext` payloads.

### GraphQL API (Patreon Tier 3+)

GraphQL is available to **CFBD Patreon Tier 3+ supporters** and provides enhanced data access capabilities compared to REST:

**Key Benefits:**
- ✅ **Real-time updates** via WebSocket subscriptions for live scoreboard feeds
- ✅ **Efficient queries** — request only the fields you need, reducing payload size and bandwidth
- ✅ **Reduced over-fetching** — avoid downloading unnecessary data compared to REST endpoints
- ✅ **Flexible composition** — easily combine scoreboard, recruiting, and advanced stats in a single query
- ✅ **Typed schema** — clear, typed schema that maps directly to model features

- **CLI:** `scripts/cfbd_pull.py --season 2025 --week 12 --source graphql`  
  - Fetches game payloads via GraphQL API
  - Automatic field mapping (camelCase → snake_case) for ML compatibility
  - Same feature engineering pipeline as REST
  - Persists JSON/CSV outputs under `outputs/cfbd_ingest/<timestamp>/`

- **Notebooks:**  
  - `notebooks/CFBD_Ingestion.ipynb` — works with GraphQL source for flexible queries
  - `notebooks/CFBD_GraphQL_Playground.ipynb` — browse talent/recruiting queries and wire up WebSocket subscriptions

**⚠️ Requires CFBD Patreon Tier 3+ subscription for GraphQL access.** For complete setup instructions, query examples, REST–GraphQL field mappings, and subscription patterns, see [`docs/CFBD_GRAPHQL_GUIDE.md`](docs/CFBD_GRAPHQL_GUIDE.md).

Both REST and GraphQL paths respect the official 6 req/sec rate limit and require `CFBD_API_KEY` in your shell.

---

## 🔗 Connection to Model Pack

The starter pack teaches you the **analytics concepts** that become **86 ML features** in model pack:

### Learning Journey

| You Learn (Starter Pack) | You Build (Model Pack) | Improvement |
|-------------------------|----------------------|-------------|
| Basic prediction (Notebook 05) | Linear regression with 86 features | 55% → 65-70% accuracy |
| Opponent adjustments (Notebook 09) | All 86 opponent-adjusted features | 4 features → 86 features |
| Rating systems (Notebook 10) | Elo + talent ratings | Basic ratings → ML-optimized |

### Quick Bridge

**Explore weekly training data** to see how your concepts become ML features:

```python
from starter_pack.utils.weekly_data_explorer import explore_weekly_features

# See Week 1 features (86 total)
features = explore_weekly_features(week=1)
print(f"Week 1: {features['total_games']} games, {features['total_features']} features")

# See feature categories
print(features['feature_categories'])
```

**Get agent guidance**:

```python
from agents.analytics_orchestrator import AnalyticsOrchestrator, AnalyticsRequest

orchestrator = AnalyticsOrchestrator()
request = AnalyticsRequest(
    user_id='your_id',
    query='Bridge me from starter pack to model pack',
    query_type='learning',
    parameters={'current_notebook': '05_matchup_predictor.ipynb'},
    context_hints={'role': 'data_scientist'}
)
response = orchestrator.process_analytics_request(request)
print(response.insights)
```

### Recommended Path

1. **Complete Starter Pack** (Notebooks 00-12) - Learn analytics fundamentals
2. **Explore Weekly Training Data** - See how concepts become 86 features
3. **Try Model Pack** - Build ML models with 65-70% accuracy
4. **Understand Interpretability** - See which features matter most (SHAP)

📖 **Full Bridge Guide**: `documentation/user/starter_pack_to_model_pack_guide.md`

---

## 🌐 Live CFBD Loader Inside Notebooks

Need the very latest games without waiting for CSVs to regenerate? Toggle the new
`fetch_latest` flag near the top of `01_intro_to_data.ipynb` (and reuse the pattern
elsewhere):

```
fetch_latest = True
from starter_pack.utils.cfbd_loader import CFBDLoader
games = CFBDLoader().fetch_games(season=config.current_year)
```

The loader caches responses under `starter_pack/data/live_cache/` and automatically
applies the same 0.17s rate limit guidance from the CFBD docs.

### Using the cfbd npm client for dashboards

Some deliverables (e.g., `week12_digestible_analysis/visualizations/week12_interactive_dashboard.html`)
now hydrate directly from the CollegeFootballData API using the [`cfbd`](https://www.npmjs.com/package/cfbd)
TypeScript SDK. To replicate that workflow:

1. Install the SDK in a Node 18+ environment: `npm install cfbd`
2. Configure the shared Bearer token exactly like the Python client and import the Node helper:
   ```ts
   import { client, getGames } from "cfbd";
   import { RateLimiter } from "@script-ohio/cfbd-rate-limit";

   client.setConfig({
     headers: { Authorization: `Bearer ${process.env.CFBD_API_KEY}` },
   });

   const limiter = new RateLimiter(1, 170);
   await limiter.acquire();
   const games = await getGames({ query: { year: 2025, week: 12, classification: "fbs" } });
   ```
3. Write the payload to a local JSON file (e.g., `visualizations/data/week12_payload.json`) and
   `fetch()` it inside your dashboard JavaScript.

> 📖 See `docs/CFBD_RUNBOOK.md` for canonical guidance on API keys, host overrides (production vs `next`),
> telemetry expectations, and rate limiting. All starter-pack notebooks, model-pack workflows, and agents
> link back to that document so these instructions stay synchronized.

---

## 🚀 Getting Started
1. Extract the ZIP package
2. Open the folder in Jupyter Lab, Jupyter Notebook, or VS Code
3. Start with `01_intro_to_data.ipynb`
4. Explore and modify notebooks for your own analysis.

---

## 📜 License & Terms of Use
This Starter Pack is provided for personal, non-commercial use only by the original purchaser or Patreon subscriber.

By downloading or using this product, you agree to the following:
* ✅ You may use the data, code, and examples for personal projects, academic research, or internal use.
* 🚫 You may not redistribute, resell, republish, or repackage this content — in whole or in part — without written permission.
* 🚫 You may not share access to the ZIP file, notebooks, or datasets publicly or with teams.
* 🧠 Attribution is appreciated but not required.

If you're interested in licensing this pack for organizational use, educational programs, or media coverage, [please contact me](mailto:admin@collegefootballdata.com).

---

## 📬 Contact
For questions, feedback, or support:
🏠 CollegeFootballData.com
💌 Email: admin@collegefootballdata.com
🧵 Twitter / X: @CFB_Data
🌐 Bluesky: @collegefootballdata.com

---

Thanks for supporting independent sports data!
