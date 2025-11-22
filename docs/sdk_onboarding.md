# Script Ohio 2.0 SDK Onboarding & Caching Guide

## 1. Overview
This note consolidates everything needed to integrate CollegeFootballData (CFBD) SDKs with Script Ohio 2.0 across Python, TypeScript/Node, and .NET surfaces. It also provides caching and key-management guidance so downstream services stay performant and compliant.

## 2. Prerequisites
| Component | Required Version | Notes |
| --- | --- | --- |
| Python | 3.13.x | Matches repo toolchain for agents and pytest |
| Node.js | ≥ 18.x | Verified locally with 24.5.0 |
| TypeScript CLI | ≥ 5.9.x | Install via `npm install -g typescript` ([TypeScript compiler](https://www.typescriptlang.org/download)) |
| pnpm (optional) | ≥ 8.x | Needed when working with `cfb-api-v2` |
| .NET SDK | ≥ 9.0 | Installed automatically with Homebrew `kiota` formula |
| Kiota CLI | ≥ 1.29 | Install via `brew install kiota` or `dotnet tool install --global Microsoft.OpenApi.Kiota` ([Kiota Getting Started](https://learn.microsoft.com/azure/kiota/getting-started)) |

Set `CFBD_API_KEY` (and `CFBD_NEXT_API_KEY` if applicable) via `.env`, local shell profile, or your secrets manager so tooling can authenticate.

## 3. Installation Summary
```bash
# TypeScript compiler
npm install -g typescript

# Kiota CLI (Homebrew – installs dotnet dependency automatically)
brew install kiota
# or via dotnet tool once the SDK is available
dotnet tool install --global Microsoft.OpenApi.Kiota

# Optional: pnpm for API v2 development
corepack enable
corepack prepare pnpm@latest --activate
```

After installation, verify with `tsc --version`, `kiota --version`, and `dotnet --version`. Capture versions in release notes or CI logs for traceability.

## 4. SDK Quickstart Examples
### 4.1 TypeScript (cfbd-typescript, Hey API client)
```ts
import { client, getGames } from 'cfbd';

client.setConfig({
  headers: { Authorization: `Bearer ${process.env.CFBD_API_KEY}` }
});

const response = await getGames({
  query: { year: 2025, classification: 'fbs', week: 8 }
});

console.log(response.data?.map(game =>
  `${game.awayTeam} @ ${game.homeTeam} – ${game.excitementIndex}`
));
```

### 4.2 Kiota-based generation (cfbd-net style)
```bash
kiota generate \
  --openapi https://api.collegefootballdata.com/openapi.json \
  --language csharp \
  --output cfbd.Client \
  --client-class-name CfbdClient \
  --namespace-name ScriptOhio.Cfbd
```
Wire the resulting client into .NET services with an `HttpClientFactory` and inject the `Authorization: Bearer` header through Kiota’s request adapter.

## 5. Caching Strategy Recommendations
1. **Layered caching**  
   - *In-memory (LRU/TTL)*: cache hot `/games`, `/records`, `/metrics` responses for 5–15 minutes inside the service using `functools.lru_cache`, `cachetools`, or Node `lru-cache`.
   - *Distributed (Redis/Memcached)*: store serialized CFBD responses keyed by endpoint + normalized query params. Set TTL based on volatility (`games` 15m, `records` 6h, `teams` 24h). Include a version suffix to bust cache on schema changes.
2. **HTTP-aware caching**  
   - Respect `Cache-Control`, `ETag`, and `Last-Modified` headers when CFBD exposes them. Implement conditional requests with `If-None-Match` or `If-Modified-Since` to reduce rate-limit pressure ([MDN HTTP caching](https://developer.mozilla.org/en-US/docs/Web/HTTP/Caching)).
3. **Prediction cache**  
   - Store orchestrator outputs (model ensemble probabilities, recommended bets) separately with short TTL (≤5 minutes) to avoid serving stale edges.
4. **Invalidation hooks**  
   - Tie cache busting to explicit events: model retrain, roster update, or manual “refresh” command inside the Workflow Automator agent. Document each hook in `agents/core/cache` to keep behavior predictable.

## 6. API Key Management & Rate Limits
- Load keys only from environment variables or secret stores; never commit them to notebooks or config.
- Enforce the documented 6 req/sec CFBD rate limit by default (`time.sleep(0.17)` throttle in Python cfbd client, per-agent queueing in orchestrator).
- For multi-tenant usage, issue per-user keys (if their Patreon tier allows) or proxy requests through a centralized CFBD gateway that enforces quotas, caching, and observability.

## 7. Troubleshooting Checklist
| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| `tsc` not found | Global npm bin not on PATH | Re-run install, confirm `npm config get prefix`, add to shell profile |
| `kiota` fails due to dotnet runtime | Missing .NET SDK | Install via `brew install kiota` or `brew install --cask dotnet-sdk` (requires sudo) |
| `pytest` warnings about FastAI pickle | Expected when loading placeholder FastAI model; verify the `.pkl` is trusted |
| HTTP 401 from CFBD | Missing/invalid API key | Confirm env var and Patreon tier; regenerate key if necessary |
| HTTP 429 from CFBD | Rate limit exceeded | Increase delay, enable caching, or stagger agent requests |

## 8. References
- [TypeScript compiler](https://www.typescriptlang.org/download)
- [Kiota Getting Started](https://learn.microsoft.com/azure/kiota/getting-started)
- [Node.js downloads](https://nodejs.org/)
- [Pytest documentation](https://docs.pytest.org/)
- [MDN HTTP caching](https://developer.mozilla.org/en-US/docs/Web/HTTP/Caching)

