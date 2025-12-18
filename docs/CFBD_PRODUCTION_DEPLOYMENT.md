# CFBD Integration - Production Deployment Guide

## Environment Configuration

### Required Environment Variables

```bash
# CFBD API Key (required)
CFBD_API_KEY=3nSBeJV4ODZlJLxQZ/H0vWG3DRAfTSPU2PporK/5K+BJininva/bPx5G4iNjeOsb

# Flask CORS (production: restrict to frontend origin)
CORS_ORIGINS=https://your-frontend-domain.com

# Optional: CFBD Configuration
CFBD_HOST=production  # or "next"
CFBD_MAX_REQUESTS_PER_SECOND=5  # Default: 5 req/sec (safe for free tier)
CFBD_CACHE_ENABLED=true  # Enable caching to reduce API calls
```

### Production CORS Configuration

**Security**: Never use `CORS_ORIGINS=*` in production.

**Development** (local testing):
```bash
CORS_ORIGINS=*  # Allows all origins (default)
```

**Production**:
```bash
# Single origin
CORS_ORIGINS=https://scriptohio.com

# Multiple origins (comma-separated)
CORS_ORIGINS=https://scriptohio.com,https://www.scriptohio.com
```

**Implementation**: The Flask app in `api/prediction_api.py` reads `CORS_ORIGINS` and splits by comma:
```python
cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")
CORS(app, origins=cors_origins)
```

## CI/CD Configuration

### GitHub Actions

The CI workflow (`.github/workflows/quality-security.yml`) includes:

```yaml
- name: Pytest with coverage
  env:
    # Enable strict auth checking for live CFBD tests in CI
    # This ensures broken API keys fail loudly instead of silently skipping
    CFBD_LIVE_STRICT_AUTH: "1"
  run: |
    pytest tests agents/tests \
      --cov=agents --cov=src --cov-report=xml --cov-report=term-missing
```

**What this does**:
- Sets `CFBD_LIVE_STRICT_AUTH=1` to make 401 errors fail tests (not skip)
- Catches broken API keys in CI before deployment
- Live tests will skip if `CFBD_API_KEY` is not set (expected in PRs)

### Setting CFBD_API_KEY in CI

**For live tests in CI** (optional):
1. Add `CFBD_API_KEY` as GitHub Actions secret
2. Add to workflow:
   ```yaml
   env:
     CFBD_API_KEY: ${{ secrets.CFBD_API_KEY }}
     CFBD_LIVE_STRICT_AUTH: "1"
   ```

**Note**: Live tests are optional - unit tests with mocks should pass without API key.

## Monitoring Production

### Rate Limit Monitoring

**Watch for 429 errors**:
- Monitor `CFBDRateLimitError` exceptions in application logs
- Track `rate_limit_hits` metric in `UnifiedCFBDClient.metrics`
- Alert if rate limit hits exceed threshold (e.g., >10% of requests)

**Adjusting Rate Limits**:
- **If 429s are frequent**: Reduce `CFBD_MAX_REQUESTS_PER_SECOND` to 4 or 3
- **If no 429s and tier supports it**: Can increase to 6-10 req/sec
- **Default (5 req/sec)**: Safe for free tier (~300 req/min)

**Example Monitoring Code**:
```python
from src.cfbd_client.unified_client import UnifiedCFBDClient
import logging

logger = logging.getLogger(__name__)

client = UnifiedCFBDClient()
# ... make requests ...

# Check rate limit hits
if client.metrics.rate_limit_hits > 0:
    hit_rate = client.metrics.rate_limit_hits / max(client.metrics.total_requests, 1)
    if hit_rate > 0.1:  # >10% hit rate
        logger.warning(
            f"High rate limit hit rate: {hit_rate:.1%} "
            f"({client.metrics.rate_limit_hits}/{client.metrics.total_requests}). "
            f"Consider reducing CFBD_MAX_REQUESTS_PER_SECOND"
        )
```

### Cache Performance

**Monitor cache hit rate**:
```python
cache_stats = client.cache_manager.get_cache_stats()
hit_rate = cache_stats['hit_rate_percent']

if hit_rate < 50:  # <50% cache hit rate
    logger.warning(
        f"Low cache hit rate: {hit_rate:.1f}%. "
        f"Consider increasing cache TTLs or checking cache configuration."
    )
```

### Error Monitoring

**Track CFBD errors**:
- `CFBDAuthenticationError` (401): Invalid/expired API key
- `CFBDForbiddenError` (403): Insufficient permissions
- `CFBDNotFoundError` (404): Resource not found (may indicate API changes)
- `CFBDRateLimitError` (429): Rate limit exceeded
- `CFBDServerError` (5xx): CFBD server issues

**Alert on**:
- Authentication errors (401) - API key may be expired
- High error rate (>5% of requests)
- Server errors (5xx) - CFBD may be experiencing issues

## Deployment Checklist

- [ ] Set `CFBD_API_KEY` in production environment
- [ ] Set `CORS_ORIGINS` to specific frontend origin (not `*`)
- [ ] Configure `CFBD_MAX_REQUESTS_PER_SECOND` based on tier (default: 5)
- [ ] Enable caching (`CFBD_CACHE_ENABLED=true`)
- [ ] Set up monitoring for 429 errors
- [ ] Set up alerts for authentication errors (401)
- [ ] Verify cache hit rates are acceptable (>50%)
- [ ] Test live endpoints in staging before production

## Troubleshooting

### High 429 Error Rate

**Symptoms**: Frequent `CFBDRateLimitError` exceptions

**Solutions**:
1. Reduce `CFBD_MAX_REQUESTS_PER_SECOND` to 4 or 3
2. Increase cache TTLs to reduce API calls
3. Check monthly quota usage (may be exhausted)
4. Consider upgrading CFBD tier

### Authentication Errors (401)

**Symptoms**: `CFBDAuthenticationError` exceptions

**Solutions**:
1. Verify `CFBD_API_KEY` is set correctly
2. Check API key hasn't expired
3. Verify API key has correct permissions for endpoints used
4. Check CFBD account status

### Low Cache Hit Rate

**Symptoms**: Cache hit rate <50%

**Solutions**:
1. Increase cache TTLs (games: 24h, stats: 1h, teams: 7d)
2. Verify cache is enabled (`CFBD_CACHE_ENABLED=true`)
3. Check cache directory permissions
4. Review cache key generation (should include all query params)

## References

- CFBD API Docs: https://apinext.collegefootballdata.com
- CFBD Best Practices: `docs/CFBD_BEST_PRACTICES.md`
- CFBD Hardening Summary: `docs/CFBD_HARDENING_FINAL.md`
