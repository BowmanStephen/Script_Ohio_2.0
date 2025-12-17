# CFBD Integration Enhancement Changelog

## Summary

Enhanced CFBD integration with REST endpoint expansion, GraphQL improvements, near-real-time polling, secure BFF endpoints, and optimized rate limiting.

## Changes

### REST Endpoint Expansion

**Added 5 new REST endpoints to `UnifiedCFBDClient`:**

- `get_plays()` - Play-by-play data with caching
- `get_recruiting()` - Team recruiting rankings
- `get_venues()` - Venue information
- `get_coaches()` - Coach information
- `get_rankings()` - Poll rankings

**Total endpoints**: 15 (up from ~10)

**Files modified:**
- `src/cfbd_client/unified_client.py` - Added 5 new methods
- `tests/test_unified_cfbd_client.py` - Added tests for all new endpoints

### GraphQL Enhancement

**Added 2 new GraphQL methods:**

- `get_plays()` - Play-by-play via GraphQL
- `get_betting_lines()` - Betting lines via GraphQL (with shape normalization)

**Agent capabilities added:**
- `graphql_plays` - Play-by-play via GraphQL
- `graphql_betting_lines` - Betting lines via GraphQL

**Features:**
- Explicit REST fallback on 401/403 errors (configurable via `CFBD_GRAPHQL_FALLBACK_TO_REST`)
- Shape normalization for GraphQL betting lines to match REST API format
- Transport preference: `CFBD_PREFERRED_TRANSPORT=graphql|rest|auto` (default: auto)

**Files modified:**
- `src/data_sources/cfbd_graphql.py` - Added 2 methods + normalization function
- `agents/cfbd_integration_agent.py` - Added capabilities + handlers with fallback logic

### Near-Real-Time Polling Service

**New service:** `src/services/live_scoreboard_poller.py`

**Features:**
- Configurable polling interval (default: 30 seconds)
- Thread-safe operation with global lock (one poller per season/week)
- Bounded event queue (max_queue_size: 100)
- Exponential backoff on repeated failures (max_failures: 5)
- Clean shutdown hook with thread stop event
- Cache integration with CFBDCacheManager

**Operational guardrails:**
- Prevents duplicate poller instances (raises RuntimeError if duplicate)
- Bounded memory (deque with maxlen)
- Automatic backoff (1x → 8x multiplier on failures)
- Graceful shutdown (5s timeout)

### BFF Endpoints (Backend for Frontend)

**Enhanced existing endpoints with secure pattern:**

- `GET /api/cfbd/games` - Proxy to UnifiedCFBDClient.get_games()
- `GET /api/cfbd/scoreboard` - Proxy to live scoreboard (cached)
- `GET /api/cfbd/ratings` - Proxy to UnifiedCFBDClient.get_ratings() (NEW)
- `GET /api/cfbd/advanced-stats` - Proxy to advanced stats

**Security improvements:**
- CORS restricted: No "*" in production (raises ValueError)
- Development default: localhost origins only
- Production requires explicit `CORS_ORIGINS` env var
- Error handling: No internal details exposed
- No API keys in responses (verified by contract tests)

**Files modified:**
- `api/prediction_api.py` - Enhanced endpoints + CORS restrictions

### Rate Limit Optimization

**Already optimized to 5 req/sec (300 req/min)**

- Default: 5 req/sec (was 6 req/sec)
- Configuration: `CFBD_MAX_REQUESTS_PER_SECOND=5` (env var)
- Verified working correctly

### Contract Tests

**New test suite:** `tests/test_cfbd_contract_tests.py`

**Tests:**
1. `test_no_api_key_in_response` - Ensures no API keys in JSON responses
2. `test_no_api_key_in_error_messages` - Ensures no API keys in error messages
3. `test_graphql_fallback_on_403_when_enabled` - Verifies REST fallback when enabled
4. `test_graphql_no_fallback_on_403_when_disabled` - Verifies no fallback when disabled
5. `test_graphql_fallback_respects_env_var` - Verifies env var control

## Configuration

### Environment Variables

- `CFBD_API_KEY` - Required for API access (backend only)
- `CFBD_PREFERRED_TRANSPORT` - `graphql|rest|auto` (default: auto)
- `CFBD_GRAPHQL_FALLBACK_TO_REST` - `true|false` (default: true)
- `CFBD_MAX_REQUESTS_PER_SECOND` - Rate limit (default: 5)
- `CORS_ORIGINS` - Comma-separated origins (required in production, no "*")
- `FLASK_ENV` - `production|development` (affects CORS defaults)

### Feature Flags

- GraphQL fallback: Controlled by `CFBD_GRAPHQL_FALLBACK_TO_REST`
- Transport preference: Controlled by `CFBD_PREFERRED_TRANSPORT`
- GraphQL disabled: Set `CFBD_GRAPHQL_DISABLED=true` to disable entirely

## Breaking Changes

**None** - All changes are additive and backward compatible.

## Migration Guide

**No migration required** - Existing code continues to work.

**Optional enhancements:**
- Use new REST endpoints: `client.get_plays()`, `client.get_recruiting()`, etc.
- Enable GraphQL: Set `CFBD_API_KEY` and install `gql[all]`
- Use polling service: `LiveScoreboardPoller` for near-real-time updates
- Access via BFF: Frontend calls `/api/cfbd/*` endpoints (no direct CFBD access)

## Testing

**Test coverage:**
- REST endpoints: 27 tests in `tests/test_unified_cfbd_client.py` (all passing)
- Contract tests: 5 tests in `tests/test_cfbd_contract_tests.py` (all passing)
- GraphQL integration: Existing tests in `tests/test_cfbd_graphql_integration.py`

**Run tests:**
```bash
# CFBD-specific tests
python3 -m pytest -q tests/test_unified_cfbd_client.py
python3 -m pytest -q tests/test_cfbd_contract_tests.py

# Full suite (includes pre-existing failures in week12/week13 agents)
python3 -m pytest -q
```

## Security Notes

- ✅ No CFBD API keys in frontend code
- ✅ No CFBD API keys in API responses (verified by contract tests)
- ✅ CORS restricted in production (no "*" allowed)
- ✅ Error messages don't expose internal details
- ✅ All CFBD access via backend BFF pattern

## Performance

- Rate limiting: 5 req/sec (300 req/min) - optimized
- Caching: TTL-based caching for all endpoints
- Polling: Configurable interval (default: 30s) with backoff
- GraphQL: Reduces multiple REST calls to single queries

## Dependencies

**Required:**
- `cfbd` Python package (existing)
- `flask-cors` (existing)

**Optional:**
- `gql[all]` - For GraphQL support (Patreon Tier 3+ required)
- `gql[websockets]` - For WebSocket subscriptions (not implemented in this change)

## Future Enhancements

- WebSocket subscriptions for true real-time updates
- Additional GraphQL endpoints (venues, conferences, etc.)
- Rate limit metrics dashboard
- Poller service integration with agent system
