# CFBD API Best Practices Guide
**Complete Integration Guide for Script Ohio 2.0 Analytics Platform**

---

## 📋 Table of Contents
1. [API Overview](#api-overview)
2. [Authentication Setup](#authentication-setup)
3. [Core Endpoints](#core-endpoints)
4. [Rate Limiting & Usage](#rate-limiting--usage)
5. [Data Integration Patterns](#data-integration-patterns)
6. [Error Handling](#error-handling)
7. [Performance Optimization](#performance-optimization)
8. [Integration with Script Ohio 2.0](#integration-with-script-ohio-20)

---

## 🔌 API Overview

### Platform Details
- **Base URL**: `https://api.collegefootballdata.com`
- **GraphQL**: `https://api.collegefootballdata.com/graphql`
- **Documentation**: [https://api.collegefootballdata.com](https://api.collegefootballdata.com)
- **GitHub**: [https://github.com/CFBD](https://github.com/CFBD)

### API Capabilities
- **Games**: Real-time and historical game data (1869-present)
- **Plays**: Detailed play-by-play data (2003-present)
- **Teams**: Team information, rosters, and recruiting data
- **Ratings**: Multiple rating systems (SP+, FPI, Elo, etc.)
- **Advanced Metrics**: EPA, success rates, havoc rates, explosiveness
- **Statistics**: Comprehensive team and player statistics

---

## 🔐 Authentication Setup

### API Key Requirements
```bash
# Environment Variable Setup
export CFBD_API_KEY="your_api_key_here"

# Or in .env file
echo "CFBD_API_KEY=your_api_key_here" >> .env
```

### Authentication Headers
```python
import requests
import os

# Correct authentication method
headers = {
    "Authorization": f"Bearer {os.getenv('CFBD_API_KEY')}",
    "Content-Type": "application/json"
}

# Common authentication issues:
# ❌ WRONG: "Bearer: key_here" (extra colon)
# ❌ WRONG: "Token key_here" (wrong header name)
# ✅ CORRECT: "Bearer your_api_key_here"
```

### Authentication Troubleshooting
```python
def test_cfbd_auth():
    """Test CFBD API authentication"""
    headers = {
        "Authorization": f"Bearer {os.getenv('CFBD_API_KEY')}"
    }

    response = requests.get(
        "https://api.collegefootballdata.com/games",
        headers=headers,
        params={"year": 2025, "week": 12}
    )

    if response.status_code == 401:
        print("❌ Authentication Failed: Check API key")
        return False
    elif response.status_code == 200:
        print("✅ Authentication Successful")
        return True
    else:
        print(f"⚠️ Unexpected status: {response.status_code}")
        return False
```

---

## 🎯 Core Endpoints

### Games API
```python
# Current season games
GET /games?year=2025&week=12
GET /games?year=2025&seasonType=regular&team=Ohio%20State

# Historical games
GET /games?year=2024&team=Texas&opp=Alabama

# Game results
GET /games?year=2025&week=11&seasonType=regular
```

### Teams API
```python
# Team information
GET /teams
GET /teams?conference=SEC

# Team talent ratings
GET /teams/talent?year=2025
GET /teams/talent?year=2025&conference=Big%20Ten
```

### Player Stats API
```python
# Player statistics
GET /stats/player/season?year=2025&week=12
GET /stats/player/season?year=2025&team=Ohio%20State&category=passing
```

### Advanced Metrics API
```python
# EPA and advanced metrics
GET /stats/season?year=2025&statType=team&team=Texas
GET /metrics/epa?year=2025&team=Alabama&excludeGarbageTime=true
```

### Plays API (Play-by-Play)
```python
# Play-by-play data
GET /plays?year=2025&week=12&team=Ohio%20State
GET /plays?year=2025&gameId=401762851
```

---

## ⚡ Rate Limiting & Usage

### Rate Limits
- **Standard Limit**: ~200 requests per minute
- **Burst Limit**: 10 requests per second
- **Recommended Delay**: 500ms between requests
- **Concurrent Connections**: Max 5

### Rate Limiting Implementation
```python
import time
from datetime import datetime

class CFBDRateLimiter:
    def __init__(self, requests_per_minute=200):
        self.requests_per_minute = requests_per_minute
        self.requests = []

    def wait_if_needed(self):
        now = datetime.now()
        # Remove requests older than 1 minute
        self.requests = [req for req in self.requests
                        if (now - req).total_seconds() < 60]

        if len(self.requests) >= self.requests_per_minute:
            sleep_time = 60 - (now - self.requests[0]).total_seconds()
            time.sleep(sleep_time)
            self.requests.pop(0)

        self.requests.append(now)

# Usage
rate_limiter = CFBDRateLimiter()

def make_cfbd_request(url, params=None):
    rate_limiter.wait_if_needed()
    time.sleep(0.5)  # Additional safety delay

    response = requests.get(url, headers=headers, params=params)
    return response
```

### Batch Request Optimization
```python
def get_week_games_optimized(year, week):
    """Get all games for a week with optimized requests"""

    # Single request for all games (better than team-by-team)
    games_url = "https://api.collegefootballdata.com/games"
    params = {
        "year": year,
        "week": week,
        "seasonType": "regular"
    }

    return make_cfbd_request(games_url, params)

def get_team_stats_batch(teams, year, week):
    """Get stats for multiple teams efficiently"""
    base_url = "https://api.collegefootballdata.com/stats/season"

    for team in teams:
        params = {
            "year": year,
            "week": week,
            "team": team
        }

        rate_limiter.wait_if_needed()
        response = make_cfbd_request(base_url, params)
        yield response.json()
```

---

## 🔄 Data Integration Patterns

### 86-Feature Pipeline Alignment
```python
def transform_cfbd_to_86_features(cfbd_game, cfbd_stats, cfbd_talent):
    """Transform CFBD data to match Script Ohio 2.0 86-feature format"""

    features = {}

    # Team talent ratings (2 features)
    features['home_talent'] = cfbd_talent.get('home_team_talent', 0)
    features['away_talent'] = cfbd_talent.get('away_team_talent', 0)

    # EPA metrics (4 features)
    features['home_adjusted_epa'] = cfbd_stats.get('home_epa', 0)
    features['away_adjusted_epa'] = cfbd_stats.get('away_epa', 0)
    features['home_adjusted_success'] = cfbd_stats.get('home_success_rate', 0)
    features['away_adjusted_success'] = cfbd_stats.get('away_success_rate', 0)

    # Explosiveness metrics (4 features)
    features['home_adjusted_explosiveness'] = cfbd_stats.get('home_explosiveness', 0)
    features['away_adjusted_explosiveness'] = cfbd_stats.get('away_explosiveness', 0)

    # Havoc rates (4 features)
    features['home_total_havoc_offense'] = cfbd_stats.get('home_havoc_rate', 0)
    features['away_total_havoc_offense'] = cfbd_stats.get('away_havoc_rate', 0)

    # Field position (4 features)
    features['home_avg_start_offense'] = cfbd_stats.get('home_avg_start_pos', 0)
    features['away_avg_start_offense'] = cfbd_stats.get('away_avg_start_pos', 0)

    # Continue for all 86 features...
    # This is a template showing the pattern

    return features
```

### Data Validation Pipeline
```python
def validate_cfbd_data_86_features(features_dict):
    """Validate CFBD data matches 86-feature training format"""

    required_features = [
        'home_talent', 'away_talent',  # Talent ratings
        'home_adjusted_epa', 'away_adjusted_epa',  # EPA
        'home_adjusted_success', 'away_adjusted_success',  # Success rates
        # ... all 86 required features
    ]

    missing_features = []
    zero_values = []

    for feature in required_features:
        if feature not in features_dict:
            missing_features.append(feature)
        elif features_dict[feature] == 0:
            zero_values.append(feature)

    if missing_features:
        raise ValueError(f"Missing features: {missing_features}")

    if zero_values:
        print(f"Warning: Zero values in: {zero_values}")

    return True
```

---

## ⚠️ Error Handling

### HTTP Status Code Handling
```python
def handle_cfbd_response(response):
    """Comprehensive CFBD API response handling"""

    if response.status_code == 200:
        return response.json()

    elif response.status_code == 401:
        raise Exception("Authentication failed: Check API key")

    elif response.status_code == 429:
        retry_after = response.headers.get('Retry-After', 60)
        raise Exception(f"Rate limit exceeded. Retry after {retry_after}s")

    elif response.status_code == 404:
        raise Exception("Resource not found: Check endpoint and parameters")

    elif response.status_code == 500:
        raise Exception("CFBD API server error")

    else:
        raise Exception(f"Unexpected status {response.status_code}: {response.text}")

def robust_cfbd_request(url, params=None, max_retries=3):
    """CFBD request with retry logic"""

    for attempt in range(max_retries):
        try:
            rate_limiter.wait_if_needed()
            response = requests.get(url, headers=headers, params=params)
            return handle_cfbd_response(response)

        except Exception as e:
            if attempt == max_retries - 1:
                raise e

            # Exponential backoff
            wait_time = 2 ** attempt
            print(f"Attempt {attempt + 1} failed, retrying in {wait_time}s...")
            time.sleep(wait_time)
```

### Data Quality Validation
```python
def validate_cfbd_game_data(game_data):
    """Validate CFBD game data quality"""

    if not game_data:
        raise ValueError("Empty game data received")

    required_fields = ['id', 'season', 'week', 'home_team', 'away_team']

    for field in required_fields:
        if field not in game_data:
            raise ValueError(f"Missing required field: {field}")

    # Validate logical consistency
    if game_data['season'] != 2025:
        print(f"Warning: Unexpected season {game_data['season']}")

    if game_data['week'] < 1 or game_data['week'] > 15:
        print(f"Warning: Unexpected week {game_data['week']}")

    return True
```

---

## 🚀 Performance Optimization

### Caching Strategy
```python
import json
import hashlib
from pathlib import Path

class CFBDCache:
    def __init__(self, cache_dir="cfbd_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    def get_cache_key(self, url, params):
        """Generate cache key from URL and parameters"""
        key_data = f"{url}{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def get(self, url, params=None):
        """Get cached response if available"""
        cache_key = self.get_cache_key(url, params)
        cache_file = self.cache_dir / f"{cache_key}.json"

        if cache_file.exists():
            with open(cache_file) as f:
                return json.load(f)
        return None

    def set(self, url, params, data):
        """Cache API response"""
        cache_key = self.get_cache_key(url, params)
        cache_file = self.cache_dir / f"{cache_key}.json"

        with open(cache_file, 'w') as f:
            json.dump(data, f)

# Usage
cache = CFBDCache()

def cached_cfbd_request(url, params=None):
    """CFBD request with intelligent caching"""

    # Check cache first
    cached_data = cache.get(url, params)
    if cached_data:
        print(f"Cache hit: {url}")
        return cached_data

    # Make API request
    data = robust_cfbd_request(url, params)

    # Cache the result
    cache.set(url, params, data)

    return data
```

### Parallel Processing
```python
import concurrent.futures

def get_multiple_teams_data(teams, year, week):
    """Get data for multiple teams in parallel"""

    urls = [
        ("https://api.collegefootballdata.com/stats/season",
         {"year": year, "week": week, "team": team})
        for team in teams
    ]

    results = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        future_to_team = {
            executor.submit(cached_cfbd_request, url, params): team
            for (url, params) in urls
        }

        for future in concurrent.futures.as_completed(future_to_team):
            team = future_to_team[future]
            try:
                results[team] = future.result()
            except Exception as e:
                print(f"Error getting {team} data: {e}")
                results[team] = None

    return results
```

---

## 🔗 Integration with Script Ohio 2.0

### Agent System Integration
```python
# agents/cfbd_data_agent.py
from agents.core.agent_framework import BaseAgent
from agents.core.tool_loader import ToolLoader
import cfbd_integration

class CFBDDataAgent(BaseAgent):
    """Specialized agent for CFBD API integration"""

    def __init__(self):
        super().__init__(
            name="CFBD Data Agent",
            description="Fetches and processes CFBD API data",
            permissions=["READ_EXECUTE"],
            tools=["cfbd_games_api", "cfbd_teams_api", "cfbd_stats_api"]
        )

    def get_week12_data(self, year=2025):
        """Get Week 12 game data for analysis"""

        games = cfbd_integration.get_week_games(year, 12)
        teams_data = cfbd_integration.get_teams_talent(year)

        # Transform to 86-feature format
        processed_data = []
        for game in games:
            features = cfbd_integration.transform_to_86_features(
                game, teams_data
            )
            processed_data.append(features)

        return processed_data

    def validate_for_models(self, data):
        """Validate data compatibility with existing models"""

        required_features = 86
        for item in data:
            if len(item) != required_features:
                raise ValueError(f"Expected {required_features} features, got {len(item)}")

        return True
```

### Model Integration
```python
# Integration with existing 2025 models
def make_week12_predictions():
    """Generate Week 12 predictions using CFBD data"""

    # 1. Get current Week 12 data
    cfbd_agent = CFBDDataAgent()
    week12_data = cfbd_agent.get_week12_data()

    # 2. Validate data format
    cfbd_agent.validate_for_models(week12_data)

    # 3. Load existing models
    from joblib import load
    ridge_model = load('model_pack/ridge_model_2025.joblib')
    xgb_model = load('model_pack/xgb_home_win_model_2025.pkl')

    # 4. Make predictions
    predictions = []
    for game_features in week12_data:
        ridge_pred = ridge_model.predict([game_features])[0]
        xgb_pred = xgb_model.predict_proba([game_features])[0]

        predictions.append({
            'ridge_margin': ridge_pred,
            'xgb_win_prob': xgb_pred[1],
            'features': game_features
        })

    return predictions
```

### Quality Assurance Integration
```python
# project_management/QUALITY_ASSURANCE/cfbd_integration_test.py
def test_cfbd_integration():
    """Test CFBD API integration with existing system"""

    # Test authentication
    auth_test = cfbd_integration.test_authentication()
    assert auth_test, "CFBD authentication failed"

    # Test data retrieval
    week12_games = cfbd_integration.get_week_games(2025, 12)
    assert len(week12_games) > 0, "No Week 12 games found"

    # Test feature transformation
    sample_game = week12_games[0]
    features = cfbd_integration.transform_to_86_features(sample_game)
    assert len(features) == 86, f"Expected 86 features, got {len(features)}"

    # Test model compatibility
    predictions = make_week12_predictions()
    assert len(predictions) == len(week12_games), "Prediction count mismatch"

    print("✅ All CFBD integration tests passed")
```

---

## 📊 Monitoring & Analytics

### API Usage Tracking
```python
class CFBDUsageTracker:
    def __init__(self):
        self.requests_made = 0
        self.cache_hits = 0
        self.errors = 0

    def track_request(self, is_cached=False, error=False):
        if is_cached:
            self.cache_hits += 1
        else:
            self.requests_made += 1

        if error:
            self.errors += 1

    def get_efficiency_report(self):
        total = self.requests_made + self.cache_hits
        cache_efficiency = (self.cache_hits / total * 100) if total > 0 else 0
        error_rate = (self.errors / self.requests_made * 100) if self.requests_made > 0 else 0

        return {
            'requests_made': self.requests_made,
            'cache_hits': self.cache_hits,
            'errors': self.errors,
            'cache_efficiency': f"{cache_efficiency:.1f}%",
            'error_rate': f"{error_rate:.1f}%"
        }
```

---

## 🎯 Best Practices Summary

### ✅ Do's
1. **Always use Bearer token authentication** with proper format
2. **Implement rate limiting** with 500ms delays between requests
3. **Cache responses** to reduce API calls and improve performance
4. **Validate data** before processing with models
5. **Handle errors gracefully** with retry logic
6. **Use parallel processing** for multiple team requests
7. **Monitor usage** and track efficiency metrics

### ❌ Don'ts
1. **Don't exceed rate limits** (200 requests/minute)
2. **Don't hardcode API keys** (use environment variables)
3. **Don't skip data validation** (ensure 86-feature compatibility)
4. **Don't ignore error responses** (handle all status codes)
5. **Don't make sequential requests** when batch is available
6. **Don't assume data availability** (always validate structure)

---

## 📞 Support & Resources

### Documentation
- **Official API Docs**: [https://api.collegefootballdata.com](https://api.collegefootballdata.com)
- **GraphQL Explorer**: [https://graphqldocs.collegefootballdata.com](https://graphqldocs.collegefootballdata.com)
- **GitHub Repository**: [https://github.com/CFBD](https://github.com/CFBD)

### Community Support
- **CFBD Discord**: Community discussions and support
- **Reddit**: r/CollegeFootballData for community help
- **GitHub Issues**: Report bugs and request features

### Script Ohio 2.0 Integration
- **Project Documentation**: See project_management/ directory
- **Agent System**: See agents/ directory for integration examples
- **Quality Assurance**: See project_management/QUALITY_ASSURANCE/ for testing

---

*This guide is part of the Script Ohio 2.0 analytics platform documentation. For updates and additions, please follow the project management contribution guidelines.*