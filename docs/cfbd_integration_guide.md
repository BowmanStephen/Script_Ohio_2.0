# CFBD Integration Guide

This comprehensive guide covers integration with CollegeFootballData.com (CFBD) API services across all available endpoints, client libraries, and best practices for Script Ohio 2.0.

## CFBD Ecosystem Overview

### Official Resources
- **Main API**: https://collegefootballdata.com
- **Next Gen API**: https://apinext.collegefootballdata.com
- **GraphQL API**: https://graphqldocs.collegefootballdata.com
- **Python Client**: https://github.com/CFBD/cfbd-python
- **.NET Client**: https://github.com/CFBD/cfbd-net
- **NPM Package**: https://www.npmjs.com/package/cfbd

### Available APIs

#### REST API (Legacy)
- **Base URL**: `https://api.collegefootballdata.com`
- **Rate Limit**: ~300 requests/minute (free tier)
- **Authentication**: API key required for some endpoints
- **Best for**: Simple data requests, legacy compatibility

#### Next Generation API
- **Base URL**: `https://apinext.collegefootballdata.com`
- **Features**: Enhanced performance, real-time updates
- **Rate Limit**: More generous than legacy API
- **Documentation**: https://apinext.collegefootballdata.com/docs

#### GraphQL API
- **Endpoint**: https://graphqldocs.collegefootballdata.com
- **Benefits**: Flexible queries, exactly the data you need
- **Schema**: Complete schema reference available
- **Real-time**: Live scoring and play-by-play support

## Quick Start for Script Ohio 2.0

```python
from src.cfbd_client.unified_client import UnifiedCFBDClient

# Initialize client (uses environment variables)
client = UnifiedCFBDClient()

# Get games data (returns List[Dict])
games = client.get_games(year=2025, week=15)

# Get team ratings
ratings = client.get_ratings(year=2025)

# Get betting lines
lines = client.get_betting_lines(year=2025, week=15)

# Get performance metrics
metrics = client.get_metrics()
print(f"Total requests: {metrics.total_requests}")
print(f"Cache hit rate: {metrics.cache_hit_rate:.2%}")
```

## Authentication Setup

### Environment Variables
```bash
# Required for API access
export CFBD_API_KEY="3nSBeJV4ODZlJLxQZ/H0vWG3DRAfTSPU2PporK/5K+BJininva/bPx5G4iNjeOsb"

# Optional configurations
export CFBD_HOST="https://api.collegefootballdata.com"  # or apinext host
export CFBD_MAX_REQUESTS_PER_SECOND=6
export CFBD_CACHE_ENABLED=true
```

### Direct Authentication Pattern
```python
from cfbd import Configuration, ApiClient, GamesApi
import os

configuration = Configuration()
configuration.api_key['Authorization'] = f"Bearer {os.environ['CFBD_API_KEY"]}'

games_api = GamesApi(ApiClient(configuration))
```

## Configuration Options

The Script Ohio 2.0 unified client supports extensive configuration:

### Environment Variables
- `CFBD_API_KEY`: Your CFBD API key (required)
- `CFBD_HOST`: API host (`https://api.collegefootballdata.com` or `https://apinext.collegefootballdata.com`)
- `CFBD_MAX_REQUESTS_PER_SECOND`: Rate limit (default: 6)
- `CFBD_CACHE_ENABLED`: Enable caching (default: true)
- `CFBD_CACHE_DIR`: Cache directory (default: "cfbd_cache")
- `CFBD_CACHE_TTL_GAMES`: Cache TTL for games (default: 86400 seconds)
- `CFBD_CACHE_TTL_STATS`: Cache TTL for stats (default: 3600 seconds)
- `CFBD_CACHE_TTL_TEAMS`: Cache TTL for teams (default: 604800 seconds)
- `CFBD_CACHE_TTL_PREDICTIONS`: Cache TTL for predictions (default: 300 seconds)

### Programmatic Configuration
```python
from src.cfbd_client.unified_client import UnifiedCFBDClient, CFBDCacheConfig

cache_config = CFBDCacheConfig(
    enable_cache=True,
    cache_ttl_games=86400,      # 24 hours - game results stable
    cache_ttl_stats=3600,       # 1 hour - stats update periodically
    cache_ttl_teams=604800,     # 7 days - team info stable
    cache_ttl_predictions=300   # 5 minutes - prediction data volatile
)

client = UnifiedCFBDClient(cache_config=cache_config)
```

## Key API Endpoints & Usage

### Games & Scores
```python
# Get games by week
games = client.get_games(year=2025, week=15, season_type='regular')

# Get games by teams
games = client.get_games(year=2025, team='Ohio State', opponent='Michigan')

# Game metrics and EPA
metrics = client.get_game_metrics(game_id=401512589)

# Calendar information
calendar = client.get_calendar(year=2025)
```

### Team Information
```python
# FBS teams
teams = client.get_fbs_teams()

# Team talent rankings
talent = client.get_talent(year=2025)

# Team matchups (historical)
matchups = client.get_team_matchup(team1='Ohio State', team2='Michigan', min_week=1)

# Team statistics
stats = client.get_team_stats(year=2025, team='Ohio State')
```

### Player Statistics
```python
# Player season stats
stats = client.get_player_stats(year=2025, team='Ohio State', position='QB')

# Search players
players = client.search_players('C.J. Stroud')

# Individual game stats
game_stats = client.get_player_game_stats(player_id=123456, year=2025)

# Player usage stats
usage = client.get_player_usage(year=2025, team='Ohio State')
```

### Betting & Odds
```python
# Betting lines
lines = client.get_betting_lines(year=2025, week=15)

# Moneyline odds
moneyline = client.get_moneyline(year=2025, week=15)

# Player props (if available)
props = client.get_player_props(year=2025, week=15)
```

### Advanced Analytics
```python
# Predicted Points Added (PPA)
ppa = client.get_ppa(year=2025, team='Ohio State')

# Advanced game statistics
advanced = client.get_advanced_game_stats(year=2025, week=15)

# Season advanced statistics
season_advanced = client.get_advanced_season_stats(year=2025, team='Ohio State')

# EPA (Expected Points Added) data
epa = client.get_epa(year=2025, team='Ohio State')
```

### Rankings & Polls
```python
# AP/Coaches polls
polls = client.get_polls(year=2025, week=15)

# Playoff rankings
playoff_rankings = client.get_playoff_rankings(year=2025)

# Historical rankings
historical = client.get_historical_rankings(year=2025, poll_type='AP')
```

## Rate Limiting Best Practices

### Current Limits
- **Legacy API**: ~300 requests/minute (free tier)
- **Next Gen API**: More generous limits
- **Script Ohio 2.0 Default**: 6 requests/second for safety

### Automatic Rate Limiting
The unified client handles rate limiting automatically:
```python
from src.cfbd_client.unified_client import UnifiedCFBDClient

client = UnifiedCFBDClient(max_requests_per_second=6)

# All calls are automatically rate-limited
for week in range(1, 16):
    games = client.get_games(year=2025, week=week)  # Automatic 0.17s delays
```

### Manual Rate Limiting
If you need custom rate limiting:
```python
import time
from concurrent.futures import ThreadPoolExecutor
import threading

class CustomRateLimiter:
    def __init__(self, max_requests_per_second=6):
        self.max_requests = max_requests_per_second
        self.requests = []
        self.lock = threading.Lock()

    def wait(self):
        with self.lock:
            now = time.time()
            # Remove requests older than 1 second
            self.requests = [req_time for req_time in self.requests if now - req_time < 1.0]

            if len(self.requests) >= self.max_requests:
                sleep_time = 1.0 - (now - self.requests[0])
                if sleep_time > 0:
                    time.sleep(sleep_time)

            self.requests.append(now)

# Usage
rate_limiter = CustomRateLimiter(max_requests_per_second=6)
```

## Caching Strategies

### Intelligent Caching
The unified client includes intelligent caching with different TTLs:

#### Cache Configuration by Data Type
- **Games**: 24 hours (game results don't change)
- **Team Information**: 7 days (roster changes infrequent)
- **Statistics**: 1 hour (stats update periodically)
- **Predictions**: 5 minutes (prediction data volatile)
- **Live Data**: 1-5 minutes (frequent updates)

#### Cache Implementation
```python
from src.cfbd_client.enhanced_client import CFBDCacheManager

cache_manager = CFBDCacheManager()

# Manual cache operations
cache_key = cache_manager._get_cache_key("games", {"year": 2025, "week": 15})
cached_data = cache_manager.get_cached_data(cache_key)

if cached_data:
    print("Using cached data")
else:
    print("Fetching fresh data")
    fresh_data = client.get_games(year=2025, week=15)
    cache_manager.cache_data(cache_key, fresh_data, ttl=86400)
```

### Cache Monitoring
```python
metrics = client.get_metrics()
print(f"Cache hits: {metrics.cache_hits}")
print(f"Cache misses: {metrics.cache_misses}")
print(f"Cache hit rate: {metrics.cache_hit_rate:.2%}")
```

## Error Handling & Best Practices

### Robust Error Handling
The unified client includes comprehensive error handling:

```python
from cfbd.rest import ApiException
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True
)
def safe_api_call(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except ApiException as e:
        logger.error(f"CFBD API error: {e.status} - {e.reason}")
        if e.status == 429:
            logger.warning("Rate limit exceeded, backing off...")
            raise
        elif e.status >= 500:
            logger.warning("Server error, retrying...")
            raise
        else:
            logger.error(f"Client error: {e}")
            return None
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return None

# Usage
games = safe_api_call(client.get_games, year=2025, week=15)
```

### Error Response Patterns
- **401 Unauthorized**: Check API key configuration
- **403 Forbidden**: Insufficient permissions for endpoint
- **404 Not Found**: Invalid endpoint or parameters
- **429 Too Many Requests**: Rate limit exceeded (automatic retry)
- **5xx Server Errors**: CFBD server issues (automatic retry)

## Performance Optimization

### Batch Processing
```python
import concurrent.futures

def fetch_week_data(week):
    """Fetch all data for a specific week"""
    games = client.get_games(year=2025, week=week)
    lines = client.get_betting_lines(year=2025, week=week)
    advanced = client.get_advanced_game_stats(year=2025, week=week)

    return {
        'week': week,
        'games': games,
        'lines': lines,
        'advanced': advanced
    }

# Process multiple weeks in parallel (with rate limiting)
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
    week_data = list(executor.map(fetch_week_data, range(1, 16)))
```

### Connection Optimization
```python
# Configure client for optimal performance
client = UnifiedCFBDClient(
    max_requests_per_second=6,
    cache_config=CFBDCacheConfig(
        enable_cache=True,
        cache_ttl_games=86400
    )
)

# Use connection pooling for better performance
client.configure_connection_pooling(
    pool_connections=10,
    pool_maxsize=20,
    max_retries=3
)
```

## GraphQL Integration

### GraphQL Query Examples
```graphql
query GetGamesWithLines($year: Int!, $week: Int!) {
  games(year: $year, week: $week) {
    id
    homeTeam
    awayTeam
    homePoints
    awayPoints
    lines {
      provider
      spread
      overUnder
    }
    metrics {
      predictedPoints
      winProbability
    }
  }
}

query GetTeamStats($year: Int!, $team: String!) {
  teamStats(year: $year, team: $team) {
    offense {
      totalYards
      passingYards
      rushingYards
      pointsPerGame
    }
    defense {
      totalYardsAllowed
      passingYardsAllowed
      rushingYardsAllowed
      pointsAllowedPerGame
    }
  }
}
```

### JavaScript GraphQL Client
```javascript
import { gql, request } from 'graphql-request';

const query = gql`
  query GetGames($year: Int!, $week: Int!) {
    games(year: $year, week: $week) {
      id
      homeTeam
      awayTeam
      homePoints
      awayPoints
    }
  }
`;

const variables = { year: 2025, week: 15 };
const data = await request('https://apinext.collegefootballdata.com/graphql', query, variables);
```

## Data Validation & Quality

### Data Validation Patterns
```python
from typing import Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class GameData:
    id: int
    home_team: str
    away_team: str
    home_points: Optional[int] = None
    away_points: Optional[int] = None
    season: int = 2025

    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> 'GameData':
        """Validate and create GameData from API response"""
        required_fields = ['id', 'home_team', 'away_team']
        for field in required_fields:
            if field not in data or data[field] is None:
                raise ValueError(f"Missing required field: {field}")

        return cls(
            id=data['id'],
            home_team=data['home_team'],
            away_team=data['away_team'],
            home_points=data.get('home_points'),
            away_points=data.get('away_points'),
            season=data.get('season', 2025)
        )

# Usage
try:
    games_raw = client.get_games(year=2025, week=15)
    games_validated = [GameData.from_api_response(game) for game in games_raw]
except ValueError as e:
    logger.error(f"Invalid game data: {e}")
```

## Integration with Agent System

### CFBD Agent Integration
```python
from agents.core.agent_framework import BaseAgent, AgentCapability, PermissionLevel
from src.cfbd_client.unified_client import UnifiedCFBDClient

class CFBDAgent(BaseAgent):
    def __init__(self, agent_id: str):
        super().__init__(agent_id, "CFBD Integration Agent", PermissionLevel.READ_EXECUTE)
        self.client = UnifiedCFBDClient()

    def _define_capabilities(self):
        return [
            AgentCapability(
                name="fetch_games",
                description="Fetch game data from CFBD API",
                estimated_time=2.0
            ),
            AgentCapability(
                name="fetch_team_stats",
                description="Fetch team statistics",
                estimated_time=1.5
            ),
            AgentCapability(
                name="fetch_betting_lines",
                description="Fetch betting lines and odds",
                estimated_time=1.0
            )
        ]

    def _execute_action(self, action: str, parameters: Dict, user_context: Dict):
        if action == "fetch_games":
            return self.client.get_games(**parameters)
        elif action == "fetch_team_stats":
            return self.client.get_team_stats(**parameters)
        elif action == "fetch_betting_lines":
            return self.client.get_betting_lines(**parameters)
        else:
            raise ValueError(f"Unknown action: {action}")
```

## Monitoring & Metrics

### Client Performance Metrics
```python
from src.cfbd_client.unified_client import UnifiedCFBDClient

client = UnifiedCFBDClient()

# Make some API calls...
games = client.get_games(year=2025, week=15)
stats = client.get_team_stats(year=2025, team='Ohio State')

# Get comprehensive metrics
metrics = client.get_metrics()
print(f"Total requests: {metrics.total_requests}")
print(f"Successful requests: {metrics.successful_requests}")
print(f"Cache hit rate: {metrics.cache_hit_rate:.2%}")
print(f"Average latency: {metrics.average_latency_ms:.2f}ms")
print(f"Error rate: {metrics.error_rate:.2%}")
print(f"Rate limit hits: {metrics.rate_limit_hits}")
```

### Custom Monitoring
```python
import logging

# Enable debug logging for CFBD operations
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('cfbd_client')

# Monitor API calls in real-time
client = UnifiedCFBDClient(debug=True)

# Custom metrics tracking
def track_api_call(endpoint, params, success, latency):
    logger.info(f"API Call: {endpoint} - Success: {success} - Latency: {latency}ms")
    # Send to monitoring system (Prometheus, DataDog, etc.)
```

## Migration Guide

### From Basic CFBD Client to Unified Client

#### Old Pattern (Multiple Clients)
```python
# Old approach with multiple clients
from cfbd import Configuration, ApiClient, GamesApi, TeamsApi
import os

config = Configuration()
config.api_key['Authorization'] = f"Bearer {os.environ['CFBD_API_KEY']}"
games_api = GamesApi(ApiClient(config))
teams_api = TeamsApi(ApiClient(config))

# Manual rate limiting required
import time
for week in range(1, 16):
    games = games_api.get_games(year=2025, week=week)
    time.sleep(0.17)  # Manual rate limiting
```

#### New Pattern (Unified Client)
```python
# New unified approach
from src.cfbd_client.unified_client import UnifiedCFBDClient

client = UnifiedCFBDClient()  # Auto-configures auth, rate limiting, caching

for week in range(1, 16):
    games = client.get_games(year=2025, week=week)  # Automatic rate limiting and caching
```

### From REST API to GraphQL

#### REST API Pattern
```python
# Multiple API calls for different data types
games = client.get_games(year=2025, week=15)
lines = client.get_betting_lines(year=2025, week=15)
advanced = client.get_advanced_game_stats(year=2025, week=15)
```

#### GraphQL Pattern
```python
# Single GraphQL query for all data
graphql_query = """
query GetWeekData($year: Int!, $week: Int!) {
  games(year: $year, week: $week) {
    id
    homeTeam
    awayTeam
    homePoints
    awayPoints
    lines {
      spread
      overUnder
    }
    advancedStats {
      epa
    }
  }
}
"""
```

## Troubleshooting

### Common Issues & Solutions

#### 1. Authentication Errors
```python
# Symptom: 401/403 status codes
# Solution: Verify API key setup
import os
if 'CFBD_API_KEY' not in os.environ:
    raise ValueError("CFBD_API_KEY environment variable not set")

# Test authentication
try:
    client = UnifiedCFBDClient()
    teams = client.get_fbs_teams()
    print("Authentication successful")
except Exception as e:
    print(f"Authentication failed: {e}")
```

#### 2. Rate Limiting Issues
```python
# Symptom: 429 status codes
# Solution: Check rate limiting configuration
metrics = client.get_metrics()
if metrics.rate_limit_hits > 0:
    print("Rate limit exceeded - consider reducing request frequency")

# Adjust rate limiting if needed
client = UnifiedCFBDClient(max_requests_per_second=4)  # More conservative
```

#### 3. Data Quality Issues
```python
# Symptom: Missing fields or invalid data
# Solution: Add robust validation
def validate_game_data(data):
    required_fields = ['id', 'home_team', 'away_team']
    missing = [f for f in required_fields if f not in data or data[f] is None]
    if missing:
        raise ValueError(f"Missing required fields: {missing}")

    # Validate data types
    if not isinstance(data['id'], int):
        raise ValueError("Game ID must be an integer")

    return True

# Usage with validation
try:
    games = client.get_games(year=2025, week=15)
    validated_games = [game for game in games if validate_game_data(game)]
except ValueError as e:
    logger.error(f"Data validation error: {e}")
```

### Debug Mode
```python
import logging

# Enable comprehensive debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Monitor all CFBD operations
client = UnifiedCFBDClient(debug=True)

# Check cache status
cache_stats = client.cache_manager.get_cache_stats()
print(f"Cache statistics: {cache_stats}")
```

## Best Practices Summary

### Do's ✅
- ✅ Use the unified client for all CFBD operations
- ✅ Implement proper rate limiting (6 req/sec recommended)
- ✅ Enable caching for static data (games, teams, historical stats)
- ✅ Handle errors gracefully with retry logic
- ✅ Validate API responses before processing
- ✅ Monitor API usage and performance metrics
- ✅ Test with smaller datasets before processing full seasons
- ✅ Use environment variables for API keys and configuration
- ✅ Implement logging for debugging and monitoring

### Don'ts ❌
- ❌ Exceed CFBD rate limits
- ❌ Hardcode API keys in source code
- ❌ Assume all fields are present in API responses
- ❌ Ignore error responses or status codes
- ❌ Make unnecessary API calls when cached data is available
- ❌ Use blocking calls in async contexts
- ❌ Process large datasets without pagination
- ❌ Skip data validation and error handling

## Production Deployment

### Environment Configuration
```bash
# Production environment variables
export CFBD_API_KEY="${CFBD_API_KEY}"
export CFBD_HOST="https://api.collegefootballdata.com"
export CFBD_MAX_REQUESTS_PER_SECOND=6
export CFBD_CACHE_ENABLED=true
export CFBD_CACHE_DIR="/tmp/cfbd_cache"
export CFBD_CACHE_TTL_GAMES=86400
export CFBD_CACHE_TTL_STATS=3600
```

### Production Client Setup
```python
from src.cfbd_client.unified_client import UnifiedCFBDClient, CFBDCacheConfig

# Production-optimized configuration
production_cache_config = CFBDCacheConfig(
    enable_cache=True,
    cache_ttl_games=86400,      # 24 hours
    cache_ttl_stats=3600,       # 1 hour
    cache_ttl_teams=604800,     # 7 days
    cache_ttl_predictions=300,  # 5 minutes
    cache_dir="/tmp/cfbd_cache"
)

client = UnifiedCFBDClient(
    max_requests_per_second=6,
    cache_config=production_cache_config,
    debug=False  # Disable debug logging in production
)
```

This comprehensive guide provides everything needed for successful CFBD integration across all supported platforms and use cases within the Script Ohio 2.0 ecosystem.

