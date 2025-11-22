# CFBD Integration Agent

**Type**: `cfbd_integration`
**Permission Level**: `READ_EXECUTE`
**Source**: [`agents/cfbd_integration_agent.py`](../../agents/cfbd_integration_agent.py)

## Description

Provides normalized CFBD datasets and live scoreboard snapshots.

This agent centralizes CFBD data access for the Script Ohio 2.0 platform,
supporting both REST and GraphQL APIs. GraphQL capabilities are automatically
registered when available, with graceful degradation to REST when not available.

## Capabilities

| Capability | Description | Permissions | Tools | Est. Time |
| --- | --- | --- | --- | --- |
| `team_snapshot` | Return normalized CFBD snapshot for a single team | READ_EXECUTE | `cfbd_client` | 1.0s |
| `live_scoreboard` | Return the latest live scoreboard events (REST-based) | READ_EXECUTE | `cfbd_rest_client` | 0.2s |

## Usage Examples

### Example 1

```python
def test_graphql_capabilities_registered(self, agent_with_graphql):
    """Test that GraphQL capabilities are registered when available"""
    capabilities = agent_with_graphql._define_capabilities()
    capability_names = [cap.name for cap in capabilities]

    assert "graphql_scoreboard" in capability_names
    assert "graphql_recruiting" in capability_names
```

### Example 2

```python
def test_graphql_capabilities_not_registered_when_unavailable(self, agent_without_graphql):
    """Test that GraphQL capabilities are not registered when unavailable"""
    capabilities = agent_without_graphql._define_capabilities()
    capability_names = [cap.name for cap in capabilities]

    assert "graphql_scoreboard" not in capability_names
    assert "graphql_recruiting" not in capability_names
```

### Example 3

```python
def test_graphql_scoreboard_success(self, agent_with_graphql, mock_graphql_client):
    """Test successful GraphQL scoreboard request"""
    result = agent_with_graphql._execute_action(
        "graphql_scoreboard",
        {"season": 2025, "week": 12},
        {}
    )

    assert result["status"] == "success"
    assert result["season"] == 2025
    assert result["week"] == 12
    assert len(result["games"]) == 1
    assert result["games"][0]["homeTeam"] == "Ohio State"
    assert result["data_source"] == "GraphQL API"
    mock_graphql_client.get_scoreboard.assert_called_once_with(season=2025, week=12)
```

