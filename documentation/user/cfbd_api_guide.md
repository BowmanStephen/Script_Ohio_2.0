# CFBD API Guide (Script Ohio 2.0)

This guide explains how to authenticate, respect rate limits, and handle errors
when pulling live data from [CollegeFootballData.com](https://collegefootballdata.com/).
It applies to both starter-pack notebooks and the automated workflows under
`project_management/TOOLS_AND_CONFIG/`.

---

## 1. Obtain & Store Your API Key

1. Request an API key from [collegefootballdata.com](https://collegefootballdata.com/).
2. Export it **before** launching Jupyter or running CLI workflows:

```bash
export CFBD_API_KEY="your-token-here"
# Optional legacy variable name:
export CFBD_API_TOKEN="your-token-here"
```

> On Windows PowerShell use: `setx CFBD_API_KEY "your-token-here"`

---

## 2. Rate Limiting (6 Requests/Second)

- The official limit is **6 requests per second**.
- Script Ohio tools automatically pause `0.17s` between API calls:
  - `starter_pack/utils/cfbd_loader.py`
  - `project_management/TOOLS_AND_CONFIG/update_data.py`
  - `model_pack/scripts/build_training_dataset.py`
- When writing custom loops, add `time.sleep(0.17)` yourself to avoid `429` errors.

---

## 3. Error Handling Patterns

| Error | Meaning | Recommended Action |
| --- | --- | --- |
| `401 Unauthorized` | Missing/invalid token | Re-export `CFBD_API_KEY` and re-run |
| `429 Too Many Requests` | Rate limit exceeded | Sleep for 1–2 seconds and retry |
| `404 Not Found` | Data unavailable (e.g., future week) | Guard with defaults / skip gracefully |
| Timeout/Connection | Network hiccup | Retry with exponential backoff |

The loader raises `CFBDLoaderError` with actionable guidance so notebooks can
fallback to the static CSVs when needed.

---

## 4. Notebook Usage (`fetch_latest` Toggle)

Every starter-pack notebook now supports live pulls:

```python
fetch_latest = True  # False → use bundled CSVs
from starter_pack.utils.cfbd_loader import CFBDLoader
games = CFBDLoader().fetch_games(season=config.current_year)
```

If no API key is present, you’ll see a friendly warning and the notebook will
automatically fall back to the local CSVs.

---

## 5. Automated Workflows

### Refresh Starter-Pack Data

```bash
python project_management/TOOLS_AND_CONFIG/update_data.py \
  --datasets games season_stats advanced_season_stats drives \
  --seasons 2025
```

### Extend Training Data & Retrain Models

```bash
python project_management/data_workflows.py refresh-training \
  --max-week 13 \
  --train-models
```

Both commands:

- Require `CFBD_API_KEY`
- Throttle to 6 req/sec
- Emit clear JSON summaries (snapshot paths, row counts, etc.)

---

## 6. Troubleshooting Checklist

1. **Missing KFBD API key message?** → Set `CFBD_API_KEY` and re-run the first cell (`%run ./_auto_setup.py`).
2. **429 errors?** → Confirm no extra loops exceed 6 req/sec, or add longer sleeps.
3. **Notebook still slow?** → Use the cached CSVs located under `starter_pack/data/live_cache/`.
4. **Need more data fields?** → Extend `starter_pack/utils/cfbd_loader.CFBDLoader` or run the CLI scripts with additional datasets.

---

## 7. Related Files

- `starter_pack/utils/cfbd_loader.py`
- `starter_pack/utils/bootstrap.py` (auto-detects missing API keys)
- `project_management/TOOLS_AND_CONFIG/update_data.py`
- `model_pack/scripts/build_training_dataset.py`
- `documentation/developer/developer_onboarding_program.md` (appendix with API patterns)

Keep this guide handy whenever you refresh data or enable `fetch_latest` in the notebooks.

