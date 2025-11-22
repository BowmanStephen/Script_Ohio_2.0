# CFBD API Integration Guide

## Overview

This guide explains how to use the unified CFBD API client in Script Ohio 2.0.

## Quick Start

```python
from src.cfbd_client import UnifiedCFBDClient

# Initialize client (uses environment variables)
client = UnifiedCFBDClient()

# Get games data (returns List[Dict])
games = client.get_games(year=2025, week=12)

# Get ratings
ratings = client.get_ratings(year=2025)

# Get metrics
metrics = client.get_metrics()
```

## Configuration

The client can be configured via environment variables:

- `CFBD_API_KEY`: Your CFBD API key (required)
- `CFBD_HOST`: API host (production or next)
- `CFBD_MAX_REQUESTS_PER_SECOND`: Rate limit (default: 6)
- `CFBD_CACHE_ENABLED`: Enable caching (default: true)
- `CFBD_CACHE_TTL_GAMES`: Cache TTL for games (default: 86400)

## Rate Limiting

The client automatically handles rate limiting at 6 requests per second.
This is enforced through precise timing and burst protection.

## Caching

The client includes intelligent caching with different TTLs by data type:
- Games: 24 hours
- Stats: 1 hour
- Teams: 7 days
- Predictions: 5 minutes

## Error Handling

The client includes comprehensive error handling with:
- Automatic retries with exponential backoff
- Specific handling for 401, 429, 404, and 5xx errors
- Graceful degradation when possible

## Migration

### Migrating from `CFBDClient` (Legacy)

**Old:**
```python
from src.cfbd_client.client import CFBDClient
client = CFBDClient()
games = client.get_games(year=2025) # Returns JSON (List[Dict])
```

**New:**
```python
from src.cfbd_client import UnifiedCFBDClient
client = UnifiedCFBDClient()
games = client.get_games(year=2025) # Returns List[Dict]
```

The new client uses the official `cfbd` SDK internally but converts responses to Dicts for compatibility.

### Removing GraphQL

GraphQL subscriptions are removed. Use polling via `CFBDRestAlternatives` or `CFBDSubscriptionManager` (which now polls).

```python
from agents.system.cfbd_subscription_manager import CFBDSubscriptionManager
manager = CFBDSubscriptionManager()
manager.start_scoreboard_feed() # Polls REST API
```

