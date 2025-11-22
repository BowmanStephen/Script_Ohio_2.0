# CFBD GraphQL Integration Guide

## Overview

This guide explains how to use the GraphQL API integration with the Script Ohio 2.0 platform. GraphQL access requires a **Patreon Tier 3+ subscription** to CollegeFootballData.com and provides enhanced data access capabilities compared to REST.

## Prerequisites

### 1. Patreon Subscription

GraphQL API access requires a **Patreon Tier 3+ subscription**:
- Sign up at: https://www.patreon.com/collegefootballdata
- Ensure your subscription tier includes GraphQL access
- Your API key will include GraphQL permissions

### 2. Library Installation

Install the `gql` library with requests support:

```bash
pip install gql[requests]>=3.5.0
```

Or install all optional dependencies:

```bash
pip install -r requirements-optional.txt
```

### 3. Environment Configuration

Set your `CFBD_API_KEY` environment variable:

```bash
# Linux/macOS
export CFBD_API_KEY="your_api_key_here"

# Windows (PowerShell)
$env:CFBD_API_KEY="your_api_key_here"

# Windows (CMD)
set CFBD_API_KEY=your_api_key_here
```

Or use a `.env` file:

```bash
# .env
CFBD_API_KEY=your_api_key_here
```

Then load it in Python:

```python
from dotenv import load_dotenv
load_dotenv()
```

## Quick Start

### Prerequisites Check

Before starting, ensure you have:
1. **Patreon Tier 3+ subscription** to CollegeFootballData.com
2. **API Key** set in environment: `export CFBD_API_KEY="your_key_here"`
3. **GraphQL library** installed: `pip install gql[requests]>=3.5.0`

### Using CFBDIntegrationAgent (Recommended)

The easiest way to use GraphQL is through the `CFBDIntegrationAgent`, which automatically handles authentication, rate limiting, and field mapping:

```python
from agents.cfbd_integration_agent import CFBDIntegrationAgent
import os

# Ensure API key is set
if not os.getenv("CFBD_API_KEY"):
    raise ValueError("CFBD_API_KEY environment variable required")

# Initialize agent (automatically detects GraphQL if available)
agent = CFBDIntegrationAgent(agent_id="my_agent")

# Fetch scoreboard data via GraphQL
result = agent._execute_action(
    "graphql_scoreboard",
    {
        "season": 2025,
        "week": 12
    },
    {"user_id": "my_user"}
)

if result["status"] == "success":
    games = result["games"]
    print(f"✅ Fetched {len(games)} games via GraphQL")
    for game in games:
        print(f"{game['homeTeam']} vs {game['awayTeam']}: {game.get('homePoints', 'TBD')}-{game.get('awayPoints', 'TBD')}")
else:
    print(f"❌ Error: {result.get('error', 'Unknown error')}")
```

### Using CFBDGraphQLClient Directly

For more control or custom queries, use the GraphQL client directly:

```python
from src.data_sources.cfbd_graphql import CFBDGraphQLClient
import os

# Initialize client with API key
client = CFBDGraphQLClient(
    api_key=os.getenv("CFBD_API_KEY"),
    host="production"  # or "next" for experimental features
)

# Fetch scoreboard
result = client.get_scoreboard(season=2025, week=12)
games = result.get("game", [])

# Fetch recruiting data
recruiting_result = client.get_recruits(season=2025, team="Ohio State", limit=25)
recruits = recruiting_result.get("recruit", [])

print(f"Fetched {len(games)} games and {len(recruits)} recruits")
```

## GraphQL Scoreboard

### Basic Usage

```python
from agents.cfbd_integration_agent import CFBDIntegrationAgent

agent = CFBDIntegrationAgent(agent_id="cfbd_001")

# Fetch all games for a season
result = agent._execute_action(
    "graphql_scoreboard",
    {"season": 2025},
    {"user_id": "user_001"}
)

# Fetch games for a specific week
result = agent._execute_action(
    "graphql_scoreboard",
    {"season": 2025, "week": 12},
    {"user_id": "user_001"}
)
```

### Response Format

GraphQL scoreboard returns data in this format:

```json
{
  "status": "success",
  "season": 2025,
  "week": 12,
  "games": [
    {
      "id": 401485131,
      "season": 2025,
      "week": 12,
      "seasonType": "regular",
      "startDate": "2025-11-22T12:00:00Z",
      "homeTeam": "Ohio State",
      "awayTeam": "Michigan",
      "homePoints": 31,
      "awayPoints": 24,
      "homeConference": "Big Ten",
      "awayConference": "Big Ten",
      "neutralSite": false,
      "completed": true,
      "venue": "Ohio Stadium"
    }
  ],
  "data_source": "GraphQL API"
}
```

### Field Mapping

GraphQL returns **camelCase** field names. The feature engineering pipeline automatically converts them to **snake_case** for compatibility with the ML models:

- `homeTeam` → `home_team`
- `awayTeam` → `away_team`
- `homePoints` → `home_points`
- `awayPoints` → `away_points`
- `seasonType` → `season_type`
- `startDate` → `start_date`
- `homeConference` → `home_conference`
- `awayConference` → `away_conference`
- `neutralSite` → `neutral_site`
- `conferenceGame` → `conference_game`

## GraphQL Recruiting

### Basic Usage

```python
from agents.cfbd_integration_agent import CFBDIntegrationAgent

agent = CFBDIntegrationAgent(agent_id="cfbd_001")

# Fetch all recruits for a year
result = agent._execute_action(
    "graphql_recruiting",
    {"year": 2025},
    {"user_id": "user_001"}
)

# Fetch recruits for a specific school
result = agent._execute_action(
    "graphql_recruiting",
    {"year": 2025, "school": "Ohio State", "limit": 10},
    {"user_id": "user_001"}
)
```

### Flexible Parameters

The recruiting capability accepts flexible parameter names:

- `year` or `season`: Recruiting class year (required)
- `school` or `team`: Team name filter (optional)
- `limit`: Maximum number of recruits to return (default: 25)

```python
# Both work:
result1 = agent._execute_action(
    "graphql_recruiting",
    {"year": 2025, "school": "Ohio State"},
    {"user_id": "user_001"}
)

result2 = agent._execute_action(
    "graphql_recruiting",
    {"season": 2025, "team": "Ohio State"},
    {"user_id": "user_001"}
)
```

### Response Format

```json
{
  "status": "success",
  "year": 2025,
  "school": "Ohio State",
  "recruits": [
    {
      "id": 12345,
      "name": "Five Star QB",
      "stars": 5,
      "rating": 98.5,
      "year": 2025,
      "college": {
        "school": "Ohio State",
        "conference": "Big Ten"
      },
      "position": {
        "position": "QB",
        "positionGroup": "Offense"
      }
    }
  ],
  "data_source": "GraphQL API"
}
```

## GraphQL Subscriptions (WebSocket)

GraphQL supports real-time subscriptions via WebSocket connections for live scoreboard updates and other streaming data. This is one of the key advantages of GraphQL over REST.

### Subscription Setup

Subscriptions use WebSocket connections to the GraphQL endpoint. The endpoint URL for subscriptions is:

**WebSocket Endpoint:**
```
wss://graphql.collegefootballdata.com/v1/graphql
```

**Authentication:**
- Include your API key in the WebSocket connection headers:
  ```
  Authorization: Bearer YOUR_CFBD_API_KEY
  ```
- The API key must have Patreon Tier 3+ permissions

### Basic Subscription Example

```python
from src.data_sources.cfbd_graphql import CFBDGraphQLClient
import os
import asyncio

# Initialize client with API key
client = CFBDGraphQLClient(
    api_key=os.getenv("CFBD_API_KEY"),
    host="production"
)

# Example subscription query for live scoreboard updates
subscription_query = """
subscription ScoreboardFeed {
  scoreboard {
    gameId
    season
    week
    homeTeam
    awayTeam
    homePoints
    awayPoints
    status
    startDate
  }
}
"""

# Note: Full subscription implementation requires async/await patterns
# See notebooks/CFBD_GraphQL_Playground.ipynb for complete examples
```

### WebSocket Connection Details

- **Protocol**: WebSocket Secure (WSS)
- **Endpoint**: `wss://graphql.collegefootballdata.com/v1/graphql`
- **Authentication**: Bearer token in connection headers
- **Rate Limits**: Same 6 req/sec limit as REST API
- **Reconnection**: Implement exponential backoff for connection failures

### Integration with Live Pipelines

Subscriptions can be integrated into existing pipelines by:

1. **Writing subscription events to the same data store** as REST data
2. **Using the same field mapping** (camelCase → snake_case) for consistency
3. **Applying the same feature engineering pipeline** to subscription events
4. **Handling connection failures** with automatic reconnection logic

For complete subscription setup, WebSocket authentication examples, and integration patterns, see `notebooks/CFBD_GraphQL_Playground.ipynb`.

## Caching

GraphQL requests are automatically cached for performance:

- **Scoreboard**: 1 hour TTL (games update frequently during live season)
- **Recruiting**: 24 hour TTL (relatively stable data)

Cache keys include query parameters to ensure proper invalidation:

```
graphql_scoreboard:season:2025:week:12
graphql_recruiting:school:Ohio State:year:2025:limit:25
```

Cache can be disabled by setting `CFBD_CACHE_DISABLED=1` environment variable.

## Error Handling

### Missing Dependencies

If the `gql` library is not installed, GraphQL capabilities are automatically disabled:

```python
agent = CFBDIntegrationAgent(agent_id="cfbd_001")
capabilities = agent.capabilities

# Check if GraphQL is available
graphql_caps = [cap for cap in capabilities if "graphql" in cap.name]
if len(graphql_caps) == 0:
    print("GraphQL not available - install gql[requests]")
```

### Missing API Key

If `CFBD_API_KEY` is not set:

```python
result = agent._execute_action(
    "graphql_scoreboard",
    {"season": 2025},
    {"user_id": "user_001"}
)

if result["status"] == "error":
    print(f"Error: {result['error']}")
    # Error message: "GraphQL client not available. Ensure CFBD_API_KEY is set..."
```

### API Errors

GraphQL API errors are handled gracefully:

```python
result = agent._execute_action(
    "graphql_scoreboard",
    {"season": 2025, "week": 12},
    {"user_id": "user_001"}
)

if result["status"] == "error":
    # Error details in result["error"]
    print(f"API Error: {result['error']}")
```

## Integration with Feature Engineering

GraphQL data can be seamlessly integrated with the feature engineering pipeline:

```python
from agents.cfbd_integration_agent import CFBDIntegrationAgent
from src.features.cfbd_feature_engineering import CFBDFeatureEngineer, FeatureEngineeringConfig

# Fetch data via GraphQL
agent = CFBDIntegrationAgent(agent_id="cfbd_001")
result = agent._execute_action(
    "graphql_scoreboard",
    {"season": 2025, "week": 12},
    {"user_id": "user_001"}
)

# Process with feature engineering
games_list = result.get("games", [])
engineer = CFBDFeatureEngineer(FeatureEngineeringConfig(season=2025))
games_df = engineer.prepare_games_frame(games_list, source="graphql")

# Now games_df has snake_case columns compatible with ML models
print(games_df.columns)
# ['id', 'season', 'week', 'home_team', 'away_team', 'home_points', ...]
```

## Using with AnalyticsOrchestrator

GraphQL queries can be routed automatically through the orchestrator, which provides a unified interface for both REST and GraphQL data access.

### Basic Orchestrator Usage

```python
from agents.analytics_orchestrator import AnalyticsOrchestrator, AnalyticsRequest

orchestrator = AnalyticsOrchestrator()

# GraphQL query (automatically detected by keywords)
request = AnalyticsRequest(
    user_id="user_001",
    query="Get scoreboard via GraphQL for week 12",
    query_type="data_acquisition",
    parameters={"season": 2025, "week": 12},
    context_hints={"role": "analyst"}
)

response = orchestrator.process_analytics_request(request)

if response.status == "success":
    games = response.data.get("games", [])
    print(f"Fetched {len(games)} games via GraphQL")
```

### Agent Integration with Tool Wrappers

For more advanced use cases, you can create tool wrappers that integrate GraphQL capabilities:

```python
from agents.cfbd_integration_agent import CFBDIntegrationAgent
from agents.analytics_orchestrator import AnalyticsOrchestrator

# Create a tool wrapper function
def graphql_scoreboard_tool(season: int, week: int = None):
    """Tool wrapper for GraphQL scoreboard queries"""
    agent = CFBDIntegrationAgent(agent_id="tool_wrapper")
    result = agent._execute_action(
        "graphql_scoreboard",
        {"season": season, "week": week} if week else {"season": season},
        {"user_id": "tool_user"}
    )
    return result.get("games", [])

# Use with orchestrator
orchestrator = AnalyticsOrchestrator()

# The orchestrator can call tool wrappers automatically
request = AnalyticsRequest(
    user_id="user_001",
    query="Fetch current week games using GraphQL",
    query_type="data_acquisition",
    parameters={"season": 2025},
    context_hints={"use_graphql": True}
)

response = orchestrator.process_analytics_request(request)
```

### Supported GraphQL Keywords

The orchestrator automatically detects GraphQL queries based on these keywords:
- `graphql`, `gql`
- `scoreboard via graphql`, `recruiting via graphql`
- `graphql api`

Example queries that route to GraphQL:

- "Get scoreboard via GraphQL for week 12"
- "Fetch games using GraphQL API"
- "GraphQL recruiting data for Ohio State"
- "Get recruiting via GraphQL"

## Troubleshooting

### Issue: "GraphQL client not available"

**Solution**: Install the `gql` library:

```bash
pip install gql[requests]>=3.5.0
```

### Issue: "CFBD_API_KEY is required"

**Solution**: Set your API key:

```bash
export CFBD_API_KEY="your_key_here"
```

Or verify it's set:

```python
import os
if not os.getenv("CFBD_API_KEY"):
    print("CFBD_API_KEY not set!")
```

### Issue: ImportError for gql library

**Solution**: Install with requests support:

```bash
pip install 'gql[requests]>=3.5.0'
```

### Issue: GraphQL capabilities not showing

**Solution**: Check that:
1. `gql` library is installed
2. `CFBD_API_KEY` is set
3. Agent is initialized after both are configured

```python
from agents.cfbd_integration_agent import CFBDIntegrationAgent, GRAPHQL_AVAILABLE

print(f"GraphQL available: {GRAPHQL_AVAILABLE}")

agent = CFBDIntegrationAgent(agent_id="test")
capabilities = agent.capabilities
graphql_caps = [cap for cap in capabilities if "graphql" in cap.name]
print(f"GraphQL capabilities: {len(graphql_caps)}")
```

### Issue: API errors or timeouts

**Solution**: 
1. Verify your Patreon subscription tier (Tier 3+ required)
2. Check API key permissions
3. Verify network connectivity to GraphQL endpoint
4. Check rate limits (GraphQL shares rate limits with REST API)

## Performance

GraphQL capabilities are optimized for performance:

- **Scoreboard**: <1.5s execution time
- **Recruiting**: <2.0s execution time
- **Cache hits**: <0.1s (cached responses)

Performance metrics are tracked automatically by the agent system.

## Backward Compatibility

GraphQL capabilities are **additive** - existing REST capabilities continue to work:

- REST capabilities (`team_snapshot`, `live_scoreboard`) work regardless of GraphQL availability
- GraphQL capabilities only available when `gql` library is installed
- Agent automatically detects GraphQL availability at initialization
- No breaking changes to existing REST workflows

## Additional Resources

- **CFBD API Documentation**: https://collegefootballdata.com/
- **Official CFBD GraphQL Documentation**: See the main CFBD API documentation for complete GraphQL schema details and query reference
- **GraphQL Endpoint**: https://graphql.collegefootballdata.com/v1/graphql
- **GraphQL WebSocket Endpoint**: wss://graphql.collegefootballdata.com/v1/graphql (for subscriptions)
- **Next API Endpoint**: https://apinext.collegefootballdata.com/v1/graphql
- **Patreon**: https://www.patreon.com/collegefootballdata
- **Python Client**: https://github.com/CFBD/cfbd-python

## Example Workflows

### Complete Scoreboard Analysis

```python
from agents.cfbd_integration_agent import CFBDIntegrationAgent
from src.features.cfbd_feature_engineering import CFBDFeatureEngineer, FeatureEngineeringConfig

agent = CFBDIntegrationAgent(agent_id="cfbd_001")
engineer = CFBDFeatureEngineer(FeatureEngineeringConfig(season=2025))

# Fetch scoreboard
result = agent._execute_action(
    "graphql_scoreboard",
    {"season": 2025, "week": 12},
    {"user_id": "user_001"}
)

games = result.get("games", [])

# Process for ML models
games_df = engineer.prepare_games_frame(games, source="graphql")
feature_frame = engineer.build_feature_frame(games_df)

# Use with ML models
from agents.model_execution_engine import ModelExecutionEngine
model_engine = ModelExecutionEngine(agent_id="model_001")
predictions = model_engine._execute_action(
    "predict_game_outcome",
    {"games_df": feature_frame},
    {"user_id": "user_001"}
)
```

### Recruiting Analysis

```python
from agents.cfbd_integration_agent import CFBDIntegrationAgent
import pandas as pd

agent = CFBDIntegrationAgent(agent_id="cfbd_001")

# Fetch recruiting data
result = agent._execute_action(
    "graphql_recruiting",
    {"year": 2025, "school": "Ohio State", "limit": 50},
    {"user_id": "user_001"}
)

recruits = result.get("recruits", [])

# Convert to DataFrame for analysis
df = pd.DataFrame(recruits)

# Analyze star ratings
print(f"Average rating: {df['rating'].mean()}")
print(f"5-star recruits: {len(df[df['stars'] == 5])}")
print(f"Average overall rank: {df['overallRank'].mean()}")
```

