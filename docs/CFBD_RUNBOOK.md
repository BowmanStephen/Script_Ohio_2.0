# CFBD Integration Run-book

## Quick Start
- Get API key: https://collegefootballdata.com/key
- Set env: `export CFBD_API_KEY=your_key_here`
- Rate limit: 6 requests/sec (0.17s throttle auto-enforced)
- Hosts:
  - `production` (default) – stable
  - `next` – beta features
- Toggle host: `export CFBD_HOST=next`

```python
from cfbd_client import CFBDClient
from cfbd_client.datasets import fetch_games

client = CFBDClient()
games = fetch_games(client, year=2025, week=11)
```

## Client Options

| Use case | Python stack (`src/cfbd_client/data_provider.py`) | TypeScript stack (`npm install cfbd`) |
| --- | --- | --- |
| Primary consumers | Agents + analytics notebooks that already live in Python/pandas | Dashboards, web services, or build tooling that prefer Node/TypeScript |
| Coverage | REST helper wrappers + GraphQL queries used by `CFBDDataProvider` (recent games, ratings, lines) | Entire REST surface (auto-generated from CFBD OpenAPI 5.5.1, package 5.13.2) with typed request/response objects |
| Extras | Built-in pandas frames, GraphQL client, memoized caches, telemetry hook | ESM/CJS bundles, `client.setConfig` for headers/base URLs, tree-shakable imports, typed fetch responses |
| Rate limiting | Implemented inside `CFBDClient` (`time.sleep(0.17)` per call) | Implement in Node wrapper (use the same 0.17s throttle or a request queue) |
| Host switching | `CFBD_HOST` env var toggles production vs `next` | Set `client.setConfig({ baseUrl: "https://apinext.collegefootballdata.com" })` |

**Choose Python** when the downstream consumer needs pandas-ready DataFrames, GraphQL access, or the cached snapshot helpers inside `CFBDDataProvider`.  
**Choose TypeScript** when you need typed fetches inside build scripts, Cloudflare Workers, Vercel/Next.js middleware, or to pre-hydrate web assets (see Week 12 dashboards).

Both clients share the same security contract:
- Always source the Bearer token from `CFBD_API_KEY`.
- Respect the 6 req/sec limit (Python enforces automatically; replicate the delay in Node, or reuse the `rateLimiter` helper from `src/cfbd_client/utils.py` once exported).
- For Next API experimentation, swap hosts but keep telemetry pointed at the same log sink for parity.

## Data Flow Visualization

The data processing pipeline can be visualized using the interactive **Data Flow Explorer** component:

```python
from src.infographics import DataFlowExplorer

explorer = DataFlowExplorer(title="CFBD Data Processing Pipeline")

data = {
    'pipeline': [
        {'name': 'CFBD API Ingestion', 'type': 'input'},
        {'name': 'Feature Engineering', 'type': 'transform'},
        {'name': 'Model Prediction', 'type': 'process'},
        {'name': 'Report Generation', 'type': 'output'}
    ]
}

html_path = explorer.generate_html(data, "docs/infographics/data_flow.html")
```

Or use the CLI tool:
```bash
python scripts/generate_infographics.py --component data_flow --output docs/infographics/
```

Embed in documentation:
```markdown
## Data Processing Pipeline

<iframe src="infographics/data_flow.html" width="100%" height="400px" frameborder="0"></iframe>
```

## Node/TypeScript Setup

```bash
npm install cfbd           # or yarn add / pnpm add
export CFBD_API_KEY=...
```

```ts
import { client, getGames } from "cfbd";
import { RateLimiter } from "@script-ohio/cfbd-rate-limit";

client.setConfig({
  baseUrl: process.env.CFBD_HOST === "next"
    ? "https://apinext.collegefootballdata.com"
    : "https://api.collegefootballdata.com",
  headers: {
    Authorization: `Bearer ${process.env.CFBD_API_KEY}`,
  },
});

const limiter = new RateLimiter(1, 170);
await limiter.acquire();
const games = await getGames({ query: { year: 2025, classification: "fbs" } });
limiter.close();
```

- Node 18+ (or any runtime with native `fetch`) is required.
- The SDK is generated from commit `CFBD/cfbd-typescript@04db468` and signed via GitHub Actions. Check the provenance link on npm before upgrading major versions.
- Mirror the Python telemetry expectations: log the `requestId`, endpoint, latency, and retries so agent health dashboards stay consistent across languages.
- Reuse the `@script-ohio/cfbd-rate-limit` helper (or the shim at `starter_pack/utils/rate_limit.js`) to avoid duplicating throttle logic. For exponential backoff, follow *Troubleshooting → Rate limit (429)*.

## Troubleshooting

### "Missing API key"
- **Symptom**: `ValueError` when instantiating `CFBDClient`
- **Fix**: `export CFBD_API_KEY=...` or populate `.env`

### Rate limit (429)
- **Symptom**: Logs show `rate limit hit`
- **Client behavior**: waits 60 seconds then retries automatically
- **Action**: Reduce concurrent agents if persistent

### Schema validation failure
- **Symptom**: `Missing required columns` from dataset helpers
- **Fix**: Review CFBD changelog (https://github.com/CFBD/cfbd-python) and update `datasets.py`
- **Verification**: `pytest tests/test_cfbd_client.py::test_*_schema`

### Auth errors (401/403)
- **Symptom**: Logs show `authentication failure`
- **Fix**: Regenerate key at https://collegefootballdata.com/key and update env var

## Escalation Flow
1. Inspect logs: `grep "cfbd_client" logs/*.log`
2. Validate API key via curl: `curl -H "Authorization: Bearer $CFBD_API_KEY" https://api.collegefootballdata.com/games?year=2025&week=1`
3. Check CFBD status: https://collegefootballdata.com/status
4. Contact data platform on-call (add contact info)

## Operational Notes
- Client logs structured lines: `[timestamp] LEVEL: METHOD /endpoint (status, latency_ms, attempt=n)`
- Telemetry snapshots: `client.get_metrics()` returns totals; pass `telemetry_hook` or `metrics_log_path` to `CFBDClient` for JSON events.
- Schema monitoring: run `python project_management/cfbd_schema_diff.py` weekly to snapshot schemas and compare against `project_management/cfbd_schema_baseline.json`.
- Commands before release:
  - `mypy src/cfbd_client/`
  - `pytest tests/ -v`
  - `black src/cfbd_client/ tests/`
  - Smoke test (see README snippet)
- Never hardcode API keys or bypass throttling logic.

## Live Scoreboard Feed
- The orchestrator boots `CFBDSubscriptionManager` automatically when GraphQL credentials are available.
- Live events are cached in-memory and surfaced through `AnalyticsOrchestrator.get_live_scoreboard_events()`.
- Agents (Workflow Automator, Insight Generator, CFBD Integration) can opt-in via `include_live_scoreboard=true` or `live_scoreboard` capability.
- Subscription failures emit telemetry events (`outcome=subscription_error`) so you can alert on them.

## Telemetry Exporter
- Run `python monitoring/cfbd_telemetry_exporter.py --log-file logs/cfbd_events.jsonl --port 9107`.
- Metrics exposed:
  - `cfbd_client_requests_total{client,outcome}`
  - `cfbd_client_latency_ms`
  - `cfbd_client_retries_total{client}`
  - `cfbd_subscription_last_heartbeat`
- Recommended Prometheus scrape interval: 30 seconds.
- Restart the exporter whenever you rotate telemetry log files to ensure it reopens the file handle.

## Validation Checklist
1. `python scripts/validate_cfbd_pipeline.py` – runs a smoke request through the orchestrator and prints summary JSON.
2. `pytest tests/test_cfbd_client.py tests/test_cfbd_subscription_manager.py tests/test_consolidated_agents.py -q`
3. `python project_management/cfbd_schema_diff.py --validate` (optional) to ensure dataset schemas remain stable.
