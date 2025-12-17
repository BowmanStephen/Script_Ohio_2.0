# CFBD API Best Practices & Data Sync Guide

## Key Updates (2025)

**API v2 Status**:
- ✅ API v2 is now in General Availability (GA)
- ✅ Both `api.collegefootballdata.com` and `apinext.collegefootballdata.com` 
   point to v2
- ✅ API v1 was sunset prior to 2025 season
- 📖 Migration guide: https://apinext.collegefootballdata.com

**API Keys**:
- ✅ **Required** since April 1, 2025
- ✅ Request via: https://collegefootballdata.com/
- ✅ Your code already handles this correctly

## Rate Limiting Best Practices

### Monthly Limits (API v2)

**Tier Structure**:
- **Free**: 1,000 monthly calls
- **Tier 1 ($1/month)**: 5,000 monthly calls
- **Tier 2 ($5/month)**: 30,000 monthly calls
- **Tier 3 ($10/month)**: 75,000 monthly calls + GraphQL access

**Important Notes**:
- API v2 does NOT implement request throttling (no per-second limits)
- **However**: Cloudflare may block excessive simultaneous requests
- Your current 6 req/sec throttling is still **good practice** to avoid 
  Cloudflare blocks

### Your Current Implementation ✅

Your `UnifiedCFBDClient` already implements:
- ✅ Rate limiting (6 req/sec) - prevents Cloudflare blocks
- ✅ Exponential backoff on 429 errors
- ✅ Retry logic with configurable max retries
- ✅ Metrics tracking (total requests, errors, latency)

**Recommendation**: Keep your rate limiting, but add monthly quota tracking.

## Configuration Options

### Environment Variables

**Required**:
- `CFBD_API_KEY` or `CFBD_API_TOKEN`: Your CFBD API key (required)

**Optional**:
- `CFBD_HOST`: API host selection
  - `production` (default): `https://api.collegefootballdata.com`
  - `next`: `https://apinext.collegefootballdata.com`
- `CFBD_MAX_REQUESTS_PER_SECOND`: Rate limit (default: 5, safe for free tier ~300 req/min)
- `CFBD_MAX_RETRIES`: Max retry attempts (default: 3)
- `CFBD_PREFERRED_TRANSPORT`: Transport preference
  - `auto` (default): Try GraphQL if available, fallback to REST
  - `graphql`: Prefer GraphQL, fallback to REST on 403/401
  - `rest`: Use REST only
- `CFBD_GRAPHQL_FALLBACK_TO_REST`: Enable REST fallback when GraphQL fails (default: true)
- `CFBD_CACHE_ENABLED`: Enable caching (default: true)
- `CFBD_ENABLE_METRICS`: Enable metrics tracking (default: true)
- `CFBD_ENABLE_LOGGING`: Enable logging (default: true)

### Error Handling

The CFBD client now uses a standardized error taxonomy:

- `CFBDAuthenticationError` (401): Invalid or missing API key
- `CFBDForbiddenError` (403): API key lacks required permissions (e.g., GraphQL Tier 3+)
- `CFBDNotFoundError` (404): Resource does not exist
- `CFBDRateLimitError` (429): Rate limit exceeded (includes Retry-After parsing)
- `CFBDServerError` (5xx): CFBD API server issues

All errors include `status_code` and `response_body` for debugging.

### GraphQL Fallback Policy

When `CFBD_PREFERRED_TRANSPORT=graphql` and GraphQL returns 403 (Tier 3+ required):
- If `CFBD_GRAPHQL_FALLBACK_TO_REST=true` (default): Automatically fallback to REST
- If `CFBD_GRAPHQL_FALLBACK_TO_REST=false`: Fail loudly with `CFBDForbiddenError`

This ensures graceful degradation for users without Tier 3+ access.

## Caching Best Practices

### Your Current Implementation ✅

You already have:
- ✅ `CFBDCacheManager` with TTL by data type
- ✅ Cache TTLs: Games (24h), Stats (1h), Teams (7d), Predictions (5m)
- ✅ Cache hit/miss tracking

**Best Practices** (from CFBD recommendations):
1. ✅ **Client-side caching** - You have this
2. ✅ **Appropriate expiration** - Your TTLs are well-configured
3. ⚠️ **Cache invalidation** - Consider adding for data corrections

## Data Sync Best Practices

### 1. Incremental Synchronization ✅

**Your Approach**:
- ✅ Snapshot system (`cfbd_refresh_snapshots.py`)
- ✅ Works with existing CSV structure
- ✅ Can identify missing data

**Recommended Pattern**:
```
Phase A: Build authoritative game index
Phase B: Fetch only missing data per gameId
Phase C: Audit completeness
```

### 2. Batch Processing

**Recommendation**: Process games in batches of 100-1000 to optimize 
efficiency.

### 3. Error Handling ✅

Your `UnifiedCFBDClient` already has:
- ✅ Exponential backoff
- ✅ Retry logic
- ✅ Specific error handling (429, 401, 404, 500+)

**Enhancement**: Add conflict resolution for data corrections.

## Data Audit Best Practices

### Your Current State

**Existing Data** (`starter_pack/data/`):
- ✅ `games.csv` - Master games list (weeks 1-16)
- ✅ `game_stats/2025.csv` - Weeks 1-12
- ✅ `advanced_game_stats/2025.csv` - Weeks 1-12
- ✅ `plays/2025/regular_*_plays.csv` - Weeks 1-12
- ✅ `drives/drives_2025.csv`

**Gaps Identified**:
- ⚠️ 30 game IDs in games.csv but not in adv_stats
- ⚠️ Weeks 13+ missing
- ⚠️ Postseason missing

### Audit Checklist

1. **Game Index Completeness**
   - Compare `games.csv` vs all data files by gameId
   - Identify missing games in each dataset

2. **Week Coverage**
   - Verify all weeks present (1-16 regular + postseason)
   - Check for gaps in weekly play files

3. **Data Quality**
   - Validate no critical nulls (gameId, season, week, team)
   - Check for duplicates
   - Verify schema compliance

4. **Cross-Reference Validation**
   - Game IDs consistent across files
   - Team names normalized
   - Coverage > 95% threshold

## Recommended Implementation

### Scripts Created

1. **`scripts/cfbd_audit_completeness.py`**
   - Audit existing CSV files against games.csv
   - Generate manifest: `data/cfbd/2025/manifest.json`
   - Output: `reports/data_audit_2025.md`

2. **`scripts/cfbd_sync_missing_data.py`**
   - Read audit manifest
   - Fetch only missing data
   - Append to existing CSVs (preserves structure)
   - Update manifest

3. **Monthly Quota Tracker** (enhancement)
   - Track API calls per month
   - Warn when approaching limits
   - Add to `CFBDClientMetrics`

### Directory Structure (No Changes)

Works with existing:
- `starter_pack/data/games.csv`
- `starter_pack/data/game_stats/2025.csv`
- `starter_pack/data/advanced_game_stats/2025.csv`
- `starter_pack/data/plays/2025/regular_*_plays.csv`
- `starter_pack/data/drives/drives_2025.csv`

Adds:
- `data/cfbd/2025/manifest.json` (completeness tracking)

## Security Best Practices ✅

Your implementation already follows:
- ✅ API keys via environment variables (never hardcoded)
- ✅ TLS/SSL (via requests library)
- ✅ Error messages don't expose internals

## Monitoring & Metrics ✅

You already track:
- ✅ Total requests
- ✅ Successful requests
- ✅ Cache hits/misses
- ✅ Errors
- ✅ Average latency

**Enhancement**: Add monthly quota tracking to avoid exceeding limits.

### Monitoring 429 Rate Limit Errors

**Watch for 429s in Production**:
- Monitor `CFBDRateLimitError` exceptions in logs
- Track `rate_limit_hits` metric in `UnifiedCFBDClient.metrics`
- If 429s are frequent, consider:
  1. Reducing `CFBD_MAX_REQUESTS_PER_SECOND` (default: 5)
  2. Increasing cache TTLs to reduce API calls
  3. Upgrading CFBD tier for higher monthly quota

**Example Monitoring**:
```python
from src.cfbd_client.unified_client import UnifiedCFBDClient

client = UnifiedCFBDClient()
# ... make requests ...

# Check rate limit hits
if client.metrics.rate_limit_hits > 0:
    logger.warning(
        f"Rate limit hit {client.metrics.rate_limit_hits} times. "
        f"Consider reducing CFBD_MAX_REQUESTS_PER_SECOND"
    )
```

**Adjusting Rate Limits**:
- If 429s occur: Reduce `CFBD_MAX_REQUESTS_PER_SECOND` to 4 or 3
- If no 429s and tier supports it: Can increase to 6-10 req/sec
- Default (5 req/sec) is safe for free tier (~300 req/min)

## Migration to API v2

**Status**: Both endpoints already point to v2, so you're good!

**Action Items**:
1. ✅ Verify API key is set (you have this)
2. ⚠️ Test with `CFBD_HOST=next` to ensure compatibility
3. ✅ Review migration guide: https://apinext.collegefootballdata.com

## Usage

### 1. Audit (offline, based on your local CSVs)
```bash
python3 scripts/cfbd_audit_completeness.py --season 2025
```

### 2. Audit + include postseason estimate from CFBD (recommended)
Make sure you have a token:
- `CFBD_API_TOKEN` or `CFBD_API_KEY`

Then:
```bash
python3 scripts/cfbd_audit_completeness.py \
  --season 2025 \
  --include-online-postseason
```

### 3. Sync missing data (dry-run first)
```bash
python3 scripts/cfbd_sync_missing_data.py --dry-run
```

### 4. Sync for real
```bash
python3 scripts/cfbd_sync_missing_data.py --update-games-csv
```

### 5. Re-audit to confirm everything is filled
```bash
python3 scripts/cfbd_audit_completeness.py --season 2025 --include-online-postseason
```

## Summary

**What You're Doing Right**:
- ✅ Rate limiting (prevents Cloudflare blocks)
- ✅ Caching with appropriate TTLs
- ✅ Error handling with exponential backoff
- ✅ API keys via environment variables
- ✅ Metrics tracking

**Recommended Enhancements**:
1. Add monthly quota tracking
2. Implement completeness audit system (✅ done)
3. Add incremental sync for missing data (✅ done)
4. Consider cache invalidation for corrections

**Next Steps**:
1. Run audit to identify gaps
2. Sync missing data (weeks 13+, postseason)
3. Add monthly quota monitoring
4. Document your sync schedule

## References

- CFBD API v2 Docs: https://apinext.collegefootballdata.com
- API Keys: https://collegefootballdata.com/
- Migration Guide: https://apinext.collegefootballdata.com
- Blog: https://blog.collegefootballdata.com/
