# CFBD Integration Insights & Best Practices
**Source**: Official CollegeFootballData.com resources  
**Last Updated**: November 2025  
**Purpose**: Document best practices and patterns from official CFBD resources

## Overview

This document captures insights, patterns, and best practices extracted from official CollegeFootballData.com resources to ensure Script Ohio 2.0 aligns with CFBD standards and conventions.

## Official Resources

### Primary Sources
- **Website**: https://collegefootballdata.com/
- **API Documentation**: https://apinext.collegefootballdata.com/
- **Python Client**: https://github.com/CFBD/cfbd-python
- **GitHub Organization**: https://github.com/CFBD

### Client Repositories
- **cfbd-python**: Official Python client (186 stars, actively maintained)
- **cfbd-typescript**: TypeScript client
- **cbbd-python**: College basketball Python client
- **Other clients**: C#, R, Vue implementations available

## API Client Patterns

### Configuration Pattern (From Official Client)

```python
import os
import cfbd
from cfbd.rest import ApiException

# Standard configuration
configuration = cfbd.Configuration(
    access_token=os.environ.get("CFBD_API_KEY"),
    host="https://api.collegefootballdata.com"
)

# For experimental features (Next API)
configuration.host = "https://apinext.collegefootballdata.com"

# Use context manager pattern
with cfbd.ApiClient(configuration) as api_client:
    games_api = cfbd.GamesApi(api_client)
    games = games_api.get_games(year=2025, week=8)
```

### Key Insights
1. **Always use environment variables** for API keys
2. **Use context manager** (`with` statement) for API client
3. **Use specific API classes** (GamesApi, StatsApi, etc.) rather than generic client
4. **Next API** is for experimental features - use standard API for production

## Rate Limiting Best Practices

### Official Rate Limit
- **Standard**: 6 requests per second
- **Calculation**: Minimum 0.17 seconds between requests

### Implementation Pattern

```python
import time

# Batch requests with rate limiting
for week in range(1, 16):
    games = games_api.get_games(year=2025, week=week)
    time.sleep(0.17)  # Respect 6 req/sec limit
```

### Best Practices
1. **Always add delays** in loops that make API calls
2. **Batch requests** when possible to reduce API calls
3. **Cache responses** for repeated queries
4. **Handle 429 errors** (rate limit exceeded) gracefully

## Error Handling Patterns

### Standard Error Handling

```python
from cfbd.rest import ApiException

try:
    games = games_api.get_games(year=2025, week=8)
except ApiException as e:
    if e.status == 429:  # Rate limit
        time.sleep(1)
        # Retry logic
    elif e.status == 401:  # Authentication
        logger.error("Invalid API key")
        # Handle auth error
    elif e.status == 404:  # Not found
        logger.warning("Resource not found")
        # Handle missing resource
    else:
        logger.error(f"API error {e.status}: {e.reason}")
        # Handle other errors
```

### Key Patterns
1. **Always catch ApiException** from cfbd.rest
2. **Check status codes** for specific error types
3. **Implement retry logic** for rate limits (429)
4. **Log errors** with context for debugging

## Code Style & Conventions

### From Official Python Client

1. **Type Hints**: Official client uses type hints extensively
2. **Docstrings**: Comprehensive docstrings for all methods
3. **Error Handling**: Consistent exception handling patterns
4. **Configuration**: Centralized configuration management

### Alignment with Script Ohio 2.0
- ✅ Type hints used in agent code
- ✅ Docstrings present in all agent classes
- ✅ Error handling follows similar patterns
- ✅ Configuration uses environment variables

## API Endpoint Patterns

### Games API
```python
games_api = cfbd.GamesApi(api_client)

# Get games with filters
games = games_api.get_games(
    year=2025,
    week=8,
    season_type="regular",
    team="Ohio State"
)

# Get advanced box score
box_score = games_api.get_advanced_box_score(game_id=401403910)
```

### Stats API
```python
stats_api = cfbd.StatsApi(api_client)

# Get advanced game stats
game_stats = stats_api.get_advanced_game_stats(
    year=2025,
    week=8
)

# Get season stats
season_stats = stats_api.get_advanced_season_stats(
    year=2025,
    team="Ohio State"
)
```

### Metrics API
```python
metrics_api = cfbd.MetricsApi(api_client)

# Get win probability
win_prob = metrics_api.get_win_probability(
    game_id=401403910
)

# Get predicted points
predicted_points = metrics_api.get_predicted_points(
    down=1,
    distance=10
)
```

## Data Handling Patterns

### Column Naming
- **Official Standard**: `snake_case` for all fields
- **Examples**: `home_team`, `away_team`, `home_points`, `away_points`
- **Consistency**: Script Ohio 2.0 matches this convention ✅

### Data Types
- **Dates**: ISO format strings or datetime objects
- **IDs**: Integer or string identifiers
- **Scores**: Integer values
- **Probabilities**: Float values (0.0-1.0)

## Testing Patterns

### From Official Client
- Unit tests for each API class
- Integration tests for end-to-end workflows
- Mock responses for testing without API calls

### Recommendations for Script Ohio 2.0
1. **Mock CFBD API calls** in tests to avoid rate limits
2. **Test error handling** for various API error scenarios
3. **Validate data transformations** after API calls
4. **Test rate limiting** logic

## Documentation Standards

### From Official Resources
1. **Clear examples** for each API endpoint
2. **Parameter descriptions** with types and requirements
3. **Error code documentation** with handling guidance
4. **Rate limiting information** prominently displayed

### Alignment
- ✅ Script Ohio 2.0 documents API usage patterns
- ✅ Error handling documented in AGENTS.md
- ✅ Rate limiting mentioned in .cursorrules and AGENTS.md

## Security Best Practices

### API Key Management
1. **Never commit keys** to version control
2. **Use environment variables** exclusively
3. **Rotate keys** if accidentally exposed
4. **Use different keys** for development/production

### Data Privacy
1. **Respect data licensing** (personal, non-commercial use)
2. **Don't redistribute** CFBD data without permission
3. **Attribute appropriately** when sharing analysis

## Performance Optimization

### Caching Strategies
1. **Cache API responses** for repeated queries
2. **Use local data files** when available (starter_pack/data/)
3. **Batch API calls** to reduce overhead
4. **Implement request deduplication**

### Code Optimization
1. **Use vectorized operations** (pandas/numpy)
2. **Avoid unnecessary API calls** (check cache first)
3. **Parallelize independent requests** when possible
4. **Profile and optimize** hot paths

## Integration Examples

### Complete Integration Pattern

```python
import os
import time
import cfbd
from cfbd.rest import ApiException
import pandas as pd

def fetch_season_games(year: int, team: str = None) -> pd.DataFrame:
    """
    Fetch all games for a season with proper rate limiting.
    
    Args:
        year: Season year
        team: Optional team filter
    
    Returns:
        DataFrame with game data
    """
    configuration = cfbd.Configuration(
        access_token=os.environ.get("CFBD_API_KEY"),
        host="https://api.collegefootballdata.com"
    )
    
    all_games = []
    
    with cfbd.ApiClient(configuration) as api_client:
        games_api = cfbd.GamesApi(api_client)
        
        # Fetch all weeks
        for week in range(1, 16):
            try:
                games = games_api.get_games(
                    year=year,
                    week=week,
                    team=team,
                    season_type="regular"
                )
                all_games.extend(games)
                time.sleep(0.17)  # Rate limiting
                
            except ApiException as e:
                if e.status == 429:
                    time.sleep(1)  # Wait longer for rate limit
                    continue
                else:
                    logger.error(f"Error fetching week {week}: {e}")
                    raise
    
    return pd.DataFrame([game.to_dict() for game in all_games])
```

## Recommendations for Script Ohio 2.0

### Already Aligned ✅
1. Environment variable usage for API keys
2. Official cfbd client usage
3. Rate limiting awareness
4. Error handling patterns
5. Code style and conventions

### Areas for Enhancement
1. **Add API response caching** to reduce calls
2. **Implement retry logic** for transient failures
3. **Add API call monitoring** for usage tracking
4. **Create API wrapper utilities** for common patterns

## Conclusion

Script Ohio 2.0 demonstrates **strong alignment** with official CFBD patterns and best practices. The project correctly uses the official Python client, follows security best practices, and implements proper error handling. Minor enhancements around caching and monitoring would further improve alignment.

---

**Sources**:
- https://github.com/CFBD/cfbd-python
- https://apinext.collegefootballdata.com/
- https://collegefootballdata.com/

**Last Updated**: November 2025

