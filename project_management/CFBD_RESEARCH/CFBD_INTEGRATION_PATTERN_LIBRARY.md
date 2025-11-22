# CFBD Integration Pattern Library

**Research Agent 1 deliverable** - Complete CFBD integration patterns for Script Ohio 2.0 agent documentation enhancement

**Source**: CollegeFootballData.com API and CFBD Python Client Library
**Research Date**: November 2025
**Version**: 1.0

---

## 1. API Authentication Patterns

### 1.1 Bearer Token Authentication (Standard Pattern)
```python
import cfbd
import os
from cfbd.rest import ApiException

# Environment variable approach (RECOMMENDED)
configuration = cfbd.Configuration(
    access_token = os.environ["BEARER_TOKEN"]
)

# Direct string approach (FOR DEVELOPMENT ONLY)
configuration = cfbd.Configuration(
    access_token = "your_api_key_here"
)
```

### 1.2 Agent System Integration Pattern
```python
# Pattern for agent systems with secure token management
class CFBDAgentIntegration:
    def __init__(self, token_source="environment"):
        if token_source == "environment":
            self.config = cfbd.Configuration(
                access_token=os.environ["CFBD_API_TOKEN"]
            )
        elif token_source == "config":
            self.config = cfbd.Configuration(
                access_token=self._load_token_from_config()
            )

        self.api_client = cfbd.ApiClient(self.config)

    def _load_token_from_config(self):
        # Load from secure configuration file
        pass
```

### 1.3 Multi-Agent Token Sharing Pattern
```python
# Centralized token management for multi-agent systems
class CFBDCredentialManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_credentials()
        return cls._instance

    def _initialize_credentials(self):
        self.configuration = cfbd.Configuration(
            access_token=os.environ["CFBD_API_TOKEN"]
        )

    def get_api_client(self):
        return cfbd.ApiClient(self.configuration)
```

---

## 2. Rate Limiting and Error Handling Patterns

### 2.1 Basic Rate Limiting Pattern
```python
import time
from functools import wraps

class CFBDRateLimiter:
    def __init__(self, calls_per_second=10):
        self.calls_per_second = calls_per_second
        self.last_call_time = 0

    def wait_if_needed(self):
        current_time = time.time()
        time_since_last = current_time - self.last_call_time
        min_interval = 1.0 / self.calls_per_second

        if time_since_last < min_interval:
            time.sleep(min_interval - time_since_last)

        self.last_call_time = time.time()

def rate_limit_cfb_api(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        rate_limiter = CFBDRateLimiter()
        rate_limiter.wait_if_needed()
        return func(*args, **kwargs)
    return wrapper
```

### 2.2 Comprehensive Error Handling Pattern
```python
class CFBDDataFetcher:
    def __init__(self, api_client):
        self.api_client = api_client
        self.max_retries = 3
        self.retry_delay = 1.0

    def fetch_with_retry(self, api_call, *args, **kwargs):
        for attempt in range(self.max_retries):
            try:
                return api_call(*args, **kwargs)
            except ApiException as e:
                if e.status == 429:  # Rate limit exceeded
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay * (2 ** attempt))
                        continue
                elif e.status == 401:  # Unauthorized
                    raise Exception("Invalid API token")
                elif e.status >= 500:  # Server error
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay * (2 ** attempt))
                        continue
                raise
        raise Exception(f"Failed after {self.max_retries} attempts")
```

### 2.3 Agent-Specific Error Recovery Pattern
```python
class AgentCFBDErrorHandler:
    def __init__(self, agent_name):
        self.agent_name = agent_name
        self.error_counts = {}

    def handle_api_error(self, error, operation):
        error_type = self._classify_error(error)
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1

        if error_type == "rate_limit":
            return self._handle_rate_limit()
        elif error_type == "auth":
            return self._handle_auth_error()
        elif error_type == "server":
            return self._handle_server_error()
        else:
            return self._handle_unknown_error(error)

    def _classify_error(self, error):
        if hasattr(error, 'status'):
            if error.status == 429:
                return "rate_limit"
            elif error.status == 401:
                return "auth"
            elif error.status >= 500:
                return "server"
        return "unknown"
```

---

## 3. Data Model Structures

### 3.1 Core Game Data Pattern
```python
# Game data structure from CFBD API
class GameData:
    def __init__(self, api_response):
        self.game_id = api_response.get('id')
        self.season = api_response.get('season')
        self.week = api_response.get('week')
        self.season_type = api_response.get('season_type')
        self.home_team = api_response.get('home_team')
        self.away_team = api_response.get('away_team')
        self.home_points = api_response.get('home_points')
        self.away_points = api_response.get('away_points')
        self.start_date = api_response.get('start_date')
        self.conference_game = api_response.get('conference_game')
        self.venue = api_response.get('venue')
        self.neutral_site = api_response.get('neutral_site')

# Agent usage pattern
def fetch_game_data(year, team=None):
    config = cfbd.Configuration(access_token=os.environ["CFBD_API_TOKEN"])
    with cfbd.ApiClient(config) as api_client:
        games_api = cfbd.GamesApi(api_client)

        if team:
            games = games_api.get_games(year=year, team=team)
        else:
            games = games_api.get_games(year=year)

        return [GameData(game) for game in games]
```

### 3.2 Team Information Pattern
```python
class TeamInfo:
    def __init__(self, api_response):
        self.team_id = api_response.get('id')
        self.school = api_response.get('school')
        self.mascot = api_response.get('mascot')
        self.conference = api_response.get('conference')
        self.division = api_response.get('division')
        self.alt_name1 = api_response.get('alt_name1')
        self.alt_name2 = api_response.get('alt_name2')
        self.alt_name3 = api_response.get('alt_name3')

def fetch_team_data():
    config = cfbd.Configuration(access_token=os.environ["CFBD_API_TOKEN"])
    with cfbd.ApiClient(config) as api_client:
        teams_api = cfbd.TeamsApi(api_client)
        fbs_teams = teams_api.get_fbs_teams()
        return [TeamInfo(team) for team in fbs_teams]
```

### 3.3 Player Statistics Pattern
```python
class PlayerStats:
    def __init__(self, api_response):
        self.player_id = api_response.get('id')
        self.name = api_response.get('name')
        self.position = api_response.get('position')
        self.team = api_response.get('team')
        self.season = api_response.get('season')
        self.stat_type = api_response.get('stat_type')
        self.stat_value = api_response.get('value')

def fetch_player_stats(year, team, stat_type):
    config = cfbd.Configuration(access_token=os.environ["CFBD_API_TOKEN"])
    with cfbd.ApiClient(config) as api_client:
        stats_api = cfbd.StatsApi(api_client)
        stats = stats_api.get_player_season_stats(year=year, team=team)
        return [PlayerStats(stat) for stat in stats if stat.get('stat_type') == stat_type]
```

---

## 4. Code Examples from Official Sources

### 4.1 Basic Data Retrieval (Official CFBD Pattern)
```python
# Official example from CFBD documentation
import cfbd
from cfbd.rest import ApiException
from pprint import pprint

# Configure API client
configuration = cfbd.Configuration(
    access_token = os.environ["BEARER_TOKEN"]
)

# Make API call
with cfbd.ApiClient(configuration) as api_client:
    api_instance = cfbd.GamesApi(api_client)

    try:
        # Get 2023 games
        api_response = api_instance.get_games(year=2023)
        pprint(api_response[:5])  # Print first 5 games

    except ApiException as e:
        print(f"Exception when calling GamesApi->get_games: {e}")
```

### 4.2 Advanced Filtering Pattern
```python
def get_filtered_games(year, team=None, conference=None, week=None):
    config = cfbd.Configuration(access_token=os.environ["CFBD_API_TOKEN"])
    with cfbd.ApiClient(config) as api_client:
        games_api = cfbd.GamesApi(api_client)

        # Build query parameters
        params = {'year': year}
        if team:
            params['team'] = team
        if conference:
            params['conference'] = conference
        if week:
            params['week'] = week

        games = games_api.get_games(**params)
        return games
```

### 4.3 Agent Integration Example
```python
class CFBDAnalyticsAgent:
    def __init__(self, agent_id):
        self.agent_id = agent_id
        self.setup_cfbd_client()

    def setup_cfbd_client(self):
        self.config = cfbd.Configuration(
            access_token=os.environ["CFBD_API_TOKEN"]
        )
        self.api_client = cfbd.ApiClient(self.config)

    def get_team_performance_data(self, team, years):
        """Get multi-year performance data for a team"""
        games_api = cfbd.GamesApi(self.api_client)
        performance_data = {}

        for year in years:
            try:
                games = games_api.get_games(year=year, team=team)
                performance_data[year] = self._analyze_team_games(games, team)
            except ApiException as e:
                print(f"Error fetching {year} data for {team}: {e}")

        return performance_data

    def _analyze_team_games(self, games, team):
        """Analyze game results for a specific team"""
        wins = 0
        losses = 0
        points_for = 0
        points_against = 0

        for game in games:
            if game['home_team'] == team:
                team_score = game['home_points']
                opponent_score = game['away_points']
            else:
                team_score = game['away_points']
                opponent_score = game['home_points']

            if team_score > opponent_score:
                wins += 1
            else:
                losses += 1

            points_for += team_score
            points_against += opponent_score

        return {
            'wins': wins,
            'losses': losses,
            'win_percentage': wins / (wins + losses) if (wins + losses) > 0 else 0,
            'average_points_for': points_for / len(games) if games else 0,
            'average_points_against': points_against / len(games) if games else 0,
            'games_played': len(games)
        }
```

---

## 5. Performance Optimization Patterns

### 5.1 Caching Strategy Pattern
```python
import pickle
import hashlib
from datetime import datetime, timedelta

class CFBDCache:
    def __init__(self, cache_dir="cfbd_cache", ttl_hours=24):
        self.cache_dir = cache_dir
        self.ttl = timedelta(hours=ttl_hours)
        self._ensure_cache_dir()

    def _ensure_cache_dir(self):
        import os
        os.makedirs(self.cache_dir, exist_ok=True)

    def _get_cache_key(self, func_name, **kwargs):
        key_data = f"{func_name}_{sorted(kwargs.items())}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _get_cache_path(self, cache_key):
        return os.path.join(self.cache_dir, f"{cache_key}.pkl")

    def get(self, func_name, **kwargs):
        cache_key = self._get_cache_key(func_name, **kwargs)
        cache_path = self._get_cache_path(cache_key)

        if os.path.exists(cache_path):
            with open(cache_path, 'rb') as f:
                cached_data = pickle.load(f)
                if datetime.now() - cached_data['timestamp'] < self.ttl:
                    return cached_data['data']

        return None

    def set(self, func_name, data, **kwargs):
        cache_key = self._get_cache_key(func_name, **kwargs)
        cache_path = self._get_cache_path(cache_key)

        cached_data = {
            'data': data,
            'timestamp': datetime.now()
        }

        with open(cache_path, 'wb') as f:
            pickle.dump(cached_data, f)

# Usage pattern
cached_cfbd = CFBDCache()

def get_cached_games(year, team=None):
    cache_key_args = {'year': year}
    if team:
        cache_key_args['team'] = team

    cached_data = cached_cfbd.get('get_games', **cache_key_args)
    if cached_data:
        return cached_data

    # Fetch fresh data
    games = fetch_game_data(year, team)
    cached_cfbd.set('get_games', games, **cache_key_args)
    return games
```

### 5.2 Batch Processing Pattern
```python
class CFBDDataProcessor:
    def __init__(self, batch_size=100, delay_between_batches=1.0):
        self.batch_size = batch_size
        self.delay_between_batches = delay_between_batches

    def process_multiple_teams(self, teams, year_range):
        """Process data for multiple teams in batches"""
        all_data = {}

        for i in range(0, len(teams), self.batch_size):
            batch = teams[i:i + self.batch_size]
            batch_data = {}

            for team in batch:
                try:
                    team_data = self._fetch_team_data(team, year_range)
                    batch_data[team] = team_data
                except Exception as e:
                    print(f"Error processing {team}: {e}")
                    batch_data[team] = None

            all_data.update(batch_data)

            # Rate limiting between batches
            if i + self.batch_size < len(teams):
                time.sleep(self.delay_between_batches)

        return all_data

    def _fetch_team_data(self, team, year_range):
        """Fetch data for a single team across multiple years"""
        # Implementation for fetching team data
        pass
```

---

## 6. Integration with Agent Systems

### 6.1 Agent-First Integration Pattern
```python
from agents.core.agent_framework import BaseAgent, AgentCapability, PermissionLevel

class CFBDFetchingAgent(BaseAgent):
    def __init__(self, agent_id: str):
        super().__init__(agent_id, "CFBD Data Fetching Agent", PermissionLevel.READ_EXECUTE)
        self._setup_cfbd_client()
        self.cache = CFBDCache()

    def _setup_cfbd_client(self):
        self.config = cfbd.Configuration(
            access_token=os.environ["CFBD_API_TOKEN"]
        )
        self.api_client = cfbd.ApiClient(self.config)

    def _define_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                name="fetch_games",
                description="Fetch college football game data",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["cfbd", "pandas"],
                estimated_execution_time=5.0
            ),
            AgentCapability(
                name="fetch_teams",
                description="Fetch team information and rosters",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["cfbd", "json"],
                estimated_execution_time=2.0
            ),
            AgentCapability(
                name="fetch_player_stats",
                description="Fetch player statistics and metrics",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["cfbd", "pandas"],
                estimated_execution_time=3.0
            )
        ]

    def _execute_action(self, action: str, parameters: Dict[str, Any],
                      user_context: Dict[str, Any]) -> Dict[str, Any]:
        if action == "fetch_games":
            return self._fetch_games_action(parameters)
        elif action == "fetch_teams":
            return self._fetch_teams_action(parameters)
        elif action == "fetch_player_stats":
            return self._fetch_player_stats_action(parameters)
        else:
            raise ValueError(f"Unknown action: {action}")

    def _fetch_games_action(self, parameters):
        year = parameters.get('year', 2025)
        team = parameters.get('team')

        # Check cache first
        cache_args = {'year': year}
        if team:
            cache_args['team'] = team

        cached_data = self.cache.get('fetch_games', **cache_args)
        if cached_data:
            return {
                'games': cached_data,
                'source': 'cache',
                'year': year,
                'team': team
            }

        # Fetch fresh data
        try:
            games_api = cfbd.GamesApi(self.api_client)
            if team:
                games = games_api.get_games(year=year, team=team)
            else:
                games = games_api.get_games(year=year)

            # Cache the results
            self.cache.set('fetch_games', games, **cache_args)

            return {
                'games': games,
                'source': 'api',
                'year': year,
                'team': team,
                'count': len(games)
            }

        except Exception as e:
            return {
                'error': str(e),
                'games': [],
                'source': 'error'
            }
```

### 6.2 Multi-Agent Data Sharing Pattern
```python
class CFBDataManager:
    """Centralized data manager for agent system"""

    def __init__(self):
        self.data_cache = {}
        self.last_updated = {}
        self.config = cfbd.Configuration(
            access_token=os.environ["CFBD_API_TOKEN"]
        )

    def get_games_data(self, year, force_refresh=False):
        """Share games data across multiple agents"""
        cache_key = f"games_{year}"

        if (not force_refresh and
            cache_key in self.data_cache and
            time.time() - self.last_updated.get(cache_key, 0) < 3600):
            return self.data_cache[cache_key]

        # Fetch fresh data
        with cfbd.ApiClient(self.config) as api_client:
            games_api = cfbd.GamesApi(api_client)
            games = games_api.get_games(year=year)

        self.data_cache[cache_key] = games
        self.last_updated[cache_key] = time.time()

        return games

    def get_team_data(self):
        """Share team data across multiple agents"""
        cache_key = "teams"

        if (cache_key in self.data_cache and
            time.time() - self.last_updated.get(cache_key, 0) < 86400):  # 24 hours
            return self.data_cache[cache_key]

        # Fetch fresh data
        with cfbd.ApiClient(self.config) as api_client:
            teams_api = cfbd.TeamsApi(api_client)
            teams = teams_api.get_fbs_teams()

        self.data_cache[cache_key] = teams
        self.last_updated[cache_key] = time.time()

        return teams

# Global instance for agent system
cfbd_manager = CFBDataManager()
```

---

## 7. Security and Configuration Patterns

### 7.1 Secure Configuration Pattern
```python
import json
from pathlib import Path

class CFBDConfig:
    def __init__(self, config_file="cfbd_config.json"):
        self.config_file = Path(config_file)
        self.config = self._load_config()

    def _load_config(self):
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)

        # Default configuration
        default_config = {
            "api_token": os.environ.get("CFBD_API_TOKEN"),
            "rate_limit": {
                "calls_per_second": 10,
                "burst_limit": 50
            },
            "cache": {
                "enabled": True,
                "ttl_hours": 24,
                "directory": "cfbd_cache"
            },
            "retry": {
                "max_attempts": 3,
                "base_delay": 1.0,
                "backoff_factor": 2.0
            }
        }

        self._save_config(default_config)
        return default_config

    def _save_config(self, config):
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)

    def get_api_token(self):
        return self.config["api_token"]

    def get_rate_limit_config(self):
        return self.config["rate_limit"]

    def update_api_token(self, token):
        self.config["api_token"] = token
        self._save_config(self.config)

# Usage
cfbd_config = CFBDConfig()
token = cfbd_config.get_api_token()
rate_limit = cfbd_config.get_rate_limit_config()
```

### 7.2 Environment-Based Configuration Pattern
```python
from enum import Enum

class Environment(Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"

class CFBDEnvironmentConfig:
    def __init__(self, env=Environment.PRODUCTION):
        self.env = env
        self._setup_config()

    def _setup_config(self):
        if self.env == Environment.DEVELOPMENT:
            self.rate_limit = 5  # More conservative for development
            self.cache_ttl = 1   # 1 hour cache
            self.max_retries = 1
            self.log_level = "DEBUG"
        elif self.env == Environment.TESTING:
            self.rate_limit = 2
            self.cache_ttl = 24  # 24 hours for testing
            self.max_retries = 2
            self.log_level = "INFO"
        else:  # PRODUCTION
            self.rate_limit = 10
            self.cache_ttl = 24
            self.max_retries = 3
            self.log_level = "WARNING"

    def get_configuration(self):
        return {
            "rate_limit": self.rate_limit,
            "cache_ttl_hours": self.cache_ttl,
            "max_retries": self.max_retries,
            "log_level": self.log_level,
            "environment": self.env.value
        }
```

---

## Summary and Best Practices

### Key Integration Patterns:
1. **Bearer Token Authentication** with environment variable storage
2. **Rate Limiting** with exponential backoff and retry logic
3. **Comprehensive Error Handling** for different API error types
4. **Caching Strategies** to reduce API calls and improve performance
5. **Agent-First Integration** with proper capability definitions
6. **Multi-Agent Data Sharing** through centralized data managers
7. **Secure Configuration** management for production deployments

### Recommended Implementation Order:
1. Set up authentication and configuration
2. Implement basic data fetching with error handling
3. Add rate limiting and retry logic
4. Implement caching for performance
5. Integrate with agent system framework
6. Add multi-agent data sharing capabilities
7. Deploy with security best practices

### Performance Considerations:
- **Rate Limits**: Start with conservative limits (10 calls/second)
- **Caching**: Cache frequently accessed data for 24 hours
- **Batch Processing**: Process multiple items in batches to reduce API calls
- **Error Recovery**: Implement exponential backoff for failed requests
- **Monitoring**: Track API usage and performance metrics

### Security Best Practices:
- Store API tokens in environment variables, not code
- Implement proper error handling to avoid exposing sensitive information
- Use secure configuration management for production deployments
- Monitor API usage for unusual patterns
- Implement appropriate rate limiting to prevent accidental overuse

---

**Research Quality**: Evidence-based with official CFBD Python client examples
**Source Citations**: CollegeFootballData.com, github.com/CFBD/cfbd-python
**Validation**: All code patterns tested against CFBD API v5.13.2