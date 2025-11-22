# CFBD Cache Manager Plan

## Goals
- Reduce redundant CFBD API calls (6 req/sec limit) by layering in-memory and Redis caches.
- Provide a shared helper (`cfbd_cache_manager.py`) that agents and CLI tools can use without duplicating TTL logic.
- Support manual invalidation hooks (model retrains, roster refreshes, weekly resets).

## Proposed Architecture
1. **Module:** `agents/core/cfbd_cache_manager.py`
   - `CFBDCacheEntry`: dataclass storing payload, timestamp, TTL, and metadata (endpoint, parameters hash, version).
   - `BaseCacheBackend` interface with `get`, `set`, `invalidate`, `stat` methods.
   - Implementations:
     - `InMemoryCacheBackend` (thread-safe dict + TTL eviction via `cachetools.TTLCache`).
     - `RedisCacheBackend` (optional, uses `redis.asyncio` with JSON serialization).
   - `CFBDCacheManager` orchestrates backends (read-through, write-back). Accepts eviction policy config and TTL map.

2. **TTL Recommendations**
   | Endpoint Group | TTL | Notes |
   | --- | --- | --- |
   | `/games`, `/records`, `/metrics` | 15 minutes | Most frequently queried; short TTL balances freshness. |
   | `/teams`, `/venues`, `/conferences` | 24 hours | Largely static. |
   | `/lines`, live scores | 2 minutes | Highly volatile; optionally bypass cache in live modes. |
   | Model predictions | 5 minutes | Avoid re-running ensembles when analysts refresh dashboard. |

3. **Key Schema**
   ```
   f"cfbd:{endpoint}:{normalized_params}:{version}"
   ```
   - `normalized_params` sorted JSON to avoid duplicates.
   - `version` increments on schema changes to invalidate old cache entries.

4. **Invalidation Hooks**
   - Manual CLI `python scripts/cache_control.py --invalidate games`.
   - Automatic: orchestrator event when models retrain or nightly job runs (call `invalidate_prefix("cfbd:games")`).
   - Detect HTTP 409/412 responses to force refresh.

5. **Integration Points**
   - `src/data_sources/cfbd_client.py`: wrap each API call with `cache_manager.get_or_fetch(...)`.
   - `InsightGeneratorAgent` / `WorkflowAutomatorAgent`: inject cache manager via constructor to share TTL map.
   - CLI utilities (e.g., `cfbd_pull.py`): optionally bypass cache via `--no-cache`.

6. **Incremental Delivery Plan**
   1. Implement `CFBDCacheEntry`, `InMemoryCacheBackend`, and `CFBDCacheManager`.
   2. Wire in-memory caching into `cfbd_client.py` for `get_games` and `get_records`.
   3. Add Redis backend (feature-flagged) and environment variables (`REDIS_URL`, `CACHE_DEFAULT_TTL`).
   4. Expose admin CLI for invalidation and metrics.
   5. Extend agent tests (`agents/tests`) to cover cache hits/misses and fallback logic.

7. **Open Questions**
   - Should Redis be mandatory in production or optional with fallback?
   - Where to log cache stats (Prometheus? built-in logging?) for observability?
   - Need to coordinate with security to store CFBD responses if they contain subscription-only data.

