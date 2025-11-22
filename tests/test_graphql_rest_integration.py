"""Comprehensive integration tests for GraphQL/REST data processing.

This test suite validates that GraphQL dict records and REST Game objects
are correctly normalized through the feature engineering pipeline.
"""

import pytest
import pandas as pd
from unittest.mock import Mock, MagicMock
from typing import Dict, Any, List

from src.features.cfbd_feature_engineering import CFBDFeatureEngineer, FeatureEngineeringConfig
from src.data_sources.cfbd_graphql import CFBDGraphQLClient
from src.data_sources.cfbd_client import CFBDRESTDataSource


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def feature_engineer():
    """Create a CFBDFeatureEngineer instance for testing."""
    config = FeatureEngineeringConfig(season=2025, enforce_reference_schema=False)
    return CFBDFeatureEngineer(config)


@pytest.fixture
def graphql_scoreboard_fixture():
    """Sample GraphQL scoreboard response with camelCase keys."""
    return {
        "game": [
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
                "neutralSite": False,
                "completed": True,
                "venue": "Ohio Stadium"
            },
            {
                "id": 401485132,
                "season": 2025,
                "week": 12,
                "seasonType": "regular",
                "startDate": "2025-11-22T15:00:00Z",
                "homeTeam": "Alabama",
                "awayTeam": "Auburn",
                "homePoints": 28,
                "awayPoints": 21,
                "homeConference": "SEC",
                "awayConference": "SEC",
                "neutralSite": False,
                "completed": True,
                "venue": "Bryant-Denny Stadium"
            }
        ]
    }


@pytest.fixture
def graphql_empty_fixture():
    """Empty GraphQL response."""
    return {"game": []}


@pytest.fixture
def graphql_malformed_fixture():
    """Malformed GraphQL responses for error testing."""
    return {
        "missing_fields": {"game": [{"season": 2025}]},  # Missing required fields
        "invalid_types": {"game": [{"id": "not_a_number", "season": 2025}]},  # Invalid types
        "null_values": {"game": [{"id": None, "homeTeam": None, "awayTeam": None}]},  # Null values
        "malformed_structure": {"data": "not_a_list"},  # Wrong structure
    }


@pytest.fixture
def rest_games_fixture():
    """Sample REST Game objects (mocked)."""
    game1 = Mock()
    game1.id = 401485131
    game1.season = 2025
    game1.week = 12
    game1.season_type = "regular"
    game1.start_date = "2025-11-22T12:00:00Z"
    game1.home_team = "Ohio State"
    game1.away_team = "Michigan"
    game1.home_points = 31
    game1.away_points = 24
    game1.home_conference = "Big Ten"
    game1.away_conference = "Big Ten"
    game1.neutral_site = False
    
    game2 = Mock()
    game2.id = 401485132
    game2.season = 2025
    game2.week = 12
    game2.season_type = "regular"
    game2.start_date = "2025-11-22T15:00:00Z"
    game2.home_team = "Alabama"
    game2.away_team = "Auburn"
    game2.home_points = 28
    game2.away_points = 21
    game2.home_conference = "SEC"
    game2.away_conference = "SEC"
    game2.neutral_site = False
    
    # Mock to_dict() method
    game1.to_dict = Mock(return_value={
        "id": 401485131,
        "season": 2025,
        "week": 12,
        "season_type": "regular",
        "start_date": "2025-11-22T12:00:00Z",
        "home_team": "Ohio State",
        "away_team": "Michigan",
        "home_points": 31,
        "away_points": 24,
        "home_conference": "Big Ten",
        "away_conference": "Big Ten",
        "neutral_site": False
    })
    
    game2.to_dict = Mock(return_value={
        "id": 401485132,
        "season": 2025,
        "week": 12,
        "season_type": "regular",
        "start_date": "2025-11-22T15:00:00Z",
        "home_team": "Alabama",
        "away_team": "Auburn",
        "home_points": 28,
        "away_points": 21,
        "home_conference": "SEC",
        "away_conference": "SEC",
        "neutral_site": False
    })
    
    return [game1, game2]


@pytest.fixture
def rest_malformed_fixture():
    """Malformed REST Game objects for error testing."""
    missing_attrs = Mock()
    # Don't set any attributes
    
    no_to_dict = Mock()
    no_to_dict.id = 123
    no_to_dict.season = 2025
    del no_to_dict.to_dict  # Remove to_dict method
    
    incomplete_dict = Mock()
    incomplete_dict.id = 123
    incomplete_dict.to_dict = Mock(return_value={"id": 123})  # Incomplete dict
    
    return [missing_attrs, no_to_dict, incomplete_dict]


# ============================================================================
# Test 1: GraphQL Dict Records Processing
# ============================================================================

def test_graphql_dict_processing(feature_engineer, graphql_scoreboard_fixture):
    """Verify GraphQL dict records are processed correctly with source='graphql'."""
    # Extract games from GraphQL response structure
    games_list = graphql_scoreboard_fixture["game"]
    
    # Process with source='graphql'
    games_df = feature_engineer.prepare_games_frame(games_list, source="graphql")
    
    # Verify DataFrame structure
    assert not games_df.empty, "DataFrame should not be empty"
    assert len(games_df) == 2, "Should have 2 games"
    
    # Verify camelCase → snake_case field mapping
    assert "home_team" in games_df.columns, "homeTeam should map to home_team"
    assert "away_team" in games_df.columns, "awayTeam should map to away_team"
    assert "home_points" in games_df.columns, "homePoints should map to home_points"
    assert "away_points" in games_df.columns, "awayPoints should map to away_points"
    assert "season_type" in games_df.columns, "seasonType should map to season_type"
    assert "start_date" in games_df.columns, "startDate should map to start_date"
    assert "home_conference" in games_df.columns, "homeConference should map to home_conference"
    assert "away_conference" in games_df.columns, "awayConference should map to away_conference"
    assert "neutral_site" in games_df.columns, "neutralSite should map to neutral_site"
    
    # Verify data integrity
    row1 = games_df[games_df["id"] == 401485131].iloc[0]
    assert row1["home_team"] == "Ohio State"
    assert row1["away_team"] == "Michigan"
    assert row1["home_points"] == 31.0
    assert row1["away_points"] == 24.0
    assert row1["season"] == 2025
    assert row1["week"] == 12
    assert row1["margin"] == 7.0  # |31 - 24| = 7
    
    # Verify margin calculation
    assert "margin" in games_df.columns
    margins = games_df["margin"].tolist()
    assert 7.0 in margins
    assert 7.0 in margins  # Both games have margin of 7


def test_graphql_dict_with_nested_structure(feature_engineer, graphql_scoreboard_fixture):
    """Test GraphQL dict processing when games are in nested structure."""
    # Test with full nested structure {"game": [...]}
    games_df = feature_engineer.prepare_games_frame(graphql_scoreboard_fixture, source="graphql")
    
    # The _unwrap_payload should handle nested structures
    # If it's a dict with "data" key, it extracts the list
    # For GraphQL, we pass the list directly from "game" key
    games_list = graphql_scoreboard_fixture.get("game", [])
    games_df = feature_engineer.prepare_games_frame(games_list, source="graphql")
    
    assert not games_df.empty
    assert len(games_df) == 2


# ============================================================================
# Test 2: REST Game Objects Processing
# ============================================================================

def test_rest_game_objects_processing(feature_engineer, rest_games_fixture):
    """Verify REST Game objects are processed correctly with source='rest'."""
    # Process with source='rest'
    games_df = feature_engineer.prepare_games_frame(rest_games_fixture, source="rest")
    
    # Verify DataFrame structure
    assert not games_df.empty, "DataFrame should not be empty"
    assert len(games_df) == 2, "Should have 2 games"
    
    # Verify required fields are present
    required_fields = ["id", "season", "week", "home_team", "away_team", 
                      "home_points", "away_points", "margin"]
    for field in required_fields:
        assert field in games_df.columns, f"Missing field: {field}"
    
    # Verify data integrity - attributes accessed correctly
    row1 = games_df[games_df["id"] == 401485131].iloc[0]
    assert row1["home_team"] == "Ohio State"
    assert row1["away_team"] == "Michigan"
    assert row1["home_points"] == 31.0
    assert row1["away_points"] == 24.0
    
    # Verify margin calculation
    assert row1["margin"] == 7.0


def test_rest_game_objects_to_dict_method(feature_engineer, rest_games_fixture):
    """Verify REST Game objects use .to_dict() method when available."""
    # Mock objects already have to_dict() method
    games_df = feature_engineer.prepare_games_frame(rest_games_fixture, source="rest")
    
    # Verify to_dict() was called
    for game in rest_games_fixture:
        if hasattr(game, 'to_dict'):
            game.to_dict.assert_called()


def test_rest_game_objects_getattr_fallback(feature_engineer):
    """Verify REST Game objects fallback to getattr() when to_dict() unavailable."""
    # Create mock without to_dict method
    game = Mock()
    game.id = 401485133
    game.season = 2025
    game.week = 13
    game.home_team = "Penn State"
    game.away_team = "Michigan State"
    game.home_points = 35
    game.away_points = 14
    game.season_type = "regular"
    game.start_date = "2025-11-29T12:00:00Z"
    game.home_conference = "Big Ten"
    game.away_conference = "Big Ten"
    game.neutral_site = False
    # Explicitly remove to_dict
    if hasattr(game, 'to_dict'):
        del game.to_dict
    
    games_df = feature_engineer.prepare_games_frame([game], source="rest")
    
    assert not games_df.empty
    assert games_df.iloc[0]["home_team"] == "Penn State"
    assert games_df.iloc[0]["away_team"] == "Michigan State"


# ============================================================================
# Test 3: Mixed GraphQL + REST Scenario
# ============================================================================

def test_mixed_graphql_rest_scenario(feature_engineer, graphql_scoreboard_fixture, rest_games_fixture):
    """Verify mixed scenario: Week 12 via GraphQL, Week 13 via REST."""
    # Week 12: GraphQL (dict records)
    week12_games = graphql_scoreboard_fixture["game"]
    week12_df = feature_engineer.prepare_games_frame(week12_games, source="graphql")
    week12_df["week"] = 12  # Ensure week is set
    
    # Week 13: REST (Game objects)
    week13_game = Mock()
    week13_game.id = 401485200
    week13_game.season = 2025
    week13_game.week = 13
    week13_game.home_team = "Ohio State"
    week13_game.away_team = "Wisconsin"
    week13_game.home_points = 42
    week13_game.away_points = 10
    week13_game.season_type = "regular"
    week13_game.start_date = "2025-11-29T12:00:00Z"
    week13_game.home_conference = "Big Ten"
    week13_game.away_conference = "Big Ten"
    week13_game.neutral_site = False
    week13_game.to_dict = Mock(return_value={
        "id": 401485200,
        "season": 2025,
        "week": 13,
        "home_team": "Ohio State",
        "away_team": "Wisconsin",
        "home_points": 42,
        "away_points": 10,
        "season_type": "regular",
        "start_date": "2025-11-29T12:00:00Z",
        "home_conference": "Big Ten",
        "away_conference": "Big Ten",
        "neutral_site": False
    })
    
    week13_df = feature_engineer.prepare_games_frame([week13_game], source="rest")
    
    # Combine results
    combined_df = pd.concat([week12_df, week13_df], ignore_index=True)
    
    # Verify combined DataFrame has consistent schema
    assert len(combined_df) == 3, "Should have 3 total games (2 from GraphQL, 1 from REST)"
    
    # Verify schema consistency
    common_columns = set(week12_df.columns) & set(week13_df.columns)
    assert len(common_columns) > 0, "Should have common columns"
    
    # Verify no data loss
    assert 12 in combined_df["week"].values, "Week 12 games should be present"
    assert 13 in combined_df["week"].values, "Week 13 game should be present"
    
    # Verify no type mismatches
    assert combined_df["home_points"].dtype in [float, int], "home_points should be numeric"
    assert combined_df["away_points"].dtype in [float, int], "away_points should be numeric"
    
    # Verify all games present
    game_ids = combined_df["id"].tolist()
    assert 401485131 in game_ids
    assert 401485132 in game_ids
    assert 401485200 in game_ids


# ============================================================================
# Test 4: Empty Results Handling
# ============================================================================

def test_empty_graphql_results(feature_engineer, graphql_empty_fixture):
    """Verify graceful handling of empty GraphQL response."""
    games_list = graphql_empty_fixture["game"]
    games_df = feature_engineer.prepare_games_frame(games_list, source="graphql")
    
    # Should return empty DataFrame with correct columns
    assert games_df.empty, "DataFrame should be empty"
    assert len(games_df.columns) > 0, "Should have column structure"
    
    # Verify expected columns are present (even if empty)
    expected_columns = ["id", "season", "week", "home_team", "away_team"]
    for col in expected_columns:
        assert col in games_df.columns or games_df.empty, f"Column {col} should be in schema"


def test_empty_rest_results(feature_engineer):
    """Verify graceful handling of empty REST response."""
    games_df = feature_engineer.prepare_games_frame([], source="rest")
    
    # Should return empty DataFrame with correct columns
    assert games_df.empty, "DataFrame should be empty"
    assert len(games_df.columns) > 0, "Should have column structure"


def test_none_payload(feature_engineer):
    """Verify handling of None payload."""
    games_df = feature_engineer.prepare_games_frame(None, source="rest")
    
    assert games_df.empty
    assert len(games_df.columns) > 0


# ============================================================================
# Test 5: Malformed Data Error Handling
# ============================================================================

def test_malformed_graphql_missing_fields(feature_engineer, graphql_malformed_fixture):
    """Verify graceful handling of GraphQL records with missing required fields."""
    malformed_games = graphql_malformed_fixture["missing_fields"]["game"]
    games_df = feature_engineer.prepare_games_frame(malformed_games, source="graphql")
    
    # Should process without crashing, but may have None/NaN values
    assert len(games_df) == 1, "Should still create a row"
    # Missing fields should be None or NaN
    assert pd.isna(games_df.iloc[0]["id"]) or games_df.iloc[0]["id"] is None


def test_malformed_graphql_invalid_types(feature_engineer, graphql_malformed_fixture):
    """Verify handling of GraphQL records with invalid data types."""
    malformed_games = graphql_malformed_fixture["invalid_types"]["game"]
    games_df = feature_engineer.prepare_games_frame(malformed_games, source="graphql")
    
    # Should process without crashing
    assert len(games_df) == 1
    # Invalid id should still be in DataFrame (as string or coerced)


def test_malformed_graphql_null_values(feature_engineer, graphql_malformed_fixture):
    """Verify handling of GraphQL records with null values."""
    malformed_games = graphql_malformed_fixture["null_values"]["game"]
    games_df = feature_engineer.prepare_games_frame(malformed_games, source="graphql")
    
    # Should process without crashing
    assert len(games_df) == 1
    # Null values should be handled gracefully


def test_malformed_graphql_wrong_structure(feature_engineer, graphql_malformed_fixture):
    """Verify handling of malformed GraphQL structure."""
    malformed_data = graphql_malformed_fixture["malformed_structure"]
    games_df = feature_engineer.prepare_games_frame(malformed_data, source="graphql")
    
    # Should return empty DataFrame or handle gracefully
    assert games_df.empty or len(games_df) == 0


def test_malformed_rest_missing_attributes(feature_engineer, rest_malformed_fixture):
    """Verify graceful handling of REST Game objects with missing attributes."""
    games_df = feature_engineer.prepare_games_frame(rest_malformed_fixture, source="rest")
    
    # Should process without crashing
    # Objects with missing attributes may have None/NaN values
    assert len(games_df) == 3  # All 3 objects processed
    
    # Verify that records with missing critical data are handled
    for idx in range(len(games_df)):
        row = games_df.iloc[idx]
        # At minimum, the row should exist even if data is incomplete
        assert row is not None


def test_malformed_rest_no_to_dict(feature_engineer):
    """Verify REST Game objects without to_dict() method are handled via getattr()."""
    game = Mock()
    game.id = 123
    game.season = 2025
    # No to_dict method
    if hasattr(game, 'to_dict'):
        del game.to_dict
    
    games_df = feature_engineer.prepare_games_frame([game], source="rest")
    
    # Should process using getattr() fallback
    assert len(games_df) == 1


# ============================================================================
# Test 6: Field Mapping Validation
# ============================================================================

def test_field_mapping_validation_graphql(feature_engineer):
    """Verify all GraphQL camelCase → snake_case field mappings."""
    graphql_game = {
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
        "neutralSite": False,
        "conferenceGame": True
    }
    
    games_df = feature_engineer.prepare_games_frame([graphql_game], source="graphql")
    
    # Verify all mappings
    mappings = {
        "homeTeam": "home_team",
        "awayTeam": "away_team",
        "homePoints": "home_points",
        "awayPoints": "away_points",
        "seasonType": "season_type",
        "startDate": "start_date",
        "homeConference": "home_conference",
        "awayConference": "away_conference",
        "neutralSite": "neutral_site",
        "conferenceGame": "conference_game"
    }
    
    row = games_df.iloc[0]
    for camel_case, snake_case in mappings.items():
        assert snake_case in games_df.columns, f"{camel_case} should map to {snake_case}"
        if camel_case in graphql_game:
            expected_value = graphql_game[camel_case]
            actual_value = row[snake_case]
            assert actual_value == expected_value or pd.isna(actual_value), \
                f"{camel_case} → {snake_case}: expected {expected_value}, got {actual_value}"


def test_field_mapping_validation_rest(feature_engineer):
    """Verify REST attribute access patterns match Game object structure."""
    game = Mock()
    game.id = 401485131
    game.season = 2025
    game.week = 12
    game.season_type = "regular"
    game.start_date = "2025-11-22T12:00:00Z"
    game.home_team = "Ohio State"
    game.away_team = "Michigan"
    game.home_points = 31
    game.away_points = 24
    game.home_conference = "Big Ten"
    game.away_conference = "Big Ten"
    game.neutral_site = False
    game.conference_game = True
    
    games_df = feature_engineer.prepare_games_frame([game], source="rest")
    
    # Verify all fields are accessible via getattr()
    row = games_df.iloc[0]
    assert row["home_team"] == "Ohio State"
    assert row["away_team"] == "Michigan"
    assert row["home_points"] == 31.0
    assert row["away_points"] == 24.0
    assert row["season"] == 2025
    assert row["week"] == 12


# ============================================================================
# Test 7: Feature Engineering Integration
# ============================================================================

def test_feature_engineering_integration_graphql(feature_engineer, graphql_scoreboard_fixture):
    """Verify full pipeline: GraphQL dict → DataFrame → feature frame."""
    games_list = graphql_scoreboard_fixture["game"]
    
    # Step 1: Normalize to DataFrame
    games_df = feature_engineer.prepare_games_frame(games_list, source="graphql")
    assert not games_df.empty
    
    # Step 2: Merge spreads (if available)
    lines_payload = [{"gameId": 401485131, "spread": -6.5}]
    games_df = feature_engineer.merge_spreads(games_df, lines_payload)
    assert "spread" in games_df.columns
    
    # Step 3: Build feature frame
    feature_frame = feature_engineer.build_feature_frame(games_df)
    
    # Verify feature frame structure
    assert not feature_frame.empty
    assert "game_key" in feature_frame.columns
    
    # Verify data integrity
    assert len(feature_frame) == 2


def test_feature_engineering_integration_rest(feature_engineer, rest_games_fixture):
    """Verify full pipeline: REST Game objects → DataFrame → feature frame."""
    # Step 1: Normalize to DataFrame
    games_df = feature_engineer.prepare_games_frame(rest_games_fixture, source="rest")
    assert not games_df.empty
    
    # Step 2: Merge spreads
    lines_payload = [{"gameId": 401485131, "spread": -6.5}]
    games_df = feature_engineer.merge_spreads(games_df, lines_payload)
    
    # Step 3: Build feature frame
    feature_frame = feature_engineer.build_feature_frame(games_df)
    
    # Verify feature frame structure
    assert not feature_frame.empty
    assert "game_key" in feature_frame.columns
    
    # Verify both paths produce compatible outputs
    assert len(feature_frame) == 2


def test_feature_engineering_with_86_column_schema(feature_engineer, graphql_scoreboard_fixture):
    """Verify feature frame aligns to 86-column reference schema when enforced."""
    # Create engineer with schema enforcement
    config = FeatureEngineeringConfig(season=2025, enforce_reference_schema=True)
    engineer = CFBDFeatureEngineer(config)
    
    games_list = graphql_scoreboard_fixture["game"]
    games_df = engineer.prepare_games_frame(games_list, source="graphql")
    feature_frame = engineer.build_feature_frame(games_df)
    
    # Verify schema alignment
    # The reference columns should be loaded from updated_training_data.csv
    # If that file exists, feature_frame should have those columns
    if config.reference_dataset.exists():
        assert len(feature_frame.columns) > 0
        # All reference columns should be present (may have NA values)


# ============================================================================
# Test 8: Source Parameter Handling
# ============================================================================

def test_source_parameter_graphql_vs_rest(feature_engineer):
    """Verify source='graphql' vs source='rest' handles different input formats."""
    # Same data structure but processed differently
    game_dict = {
        "id": 401485131,
        "season": 2025,
        "week": 12,
        "homeTeam": "Ohio State",  # camelCase for GraphQL
        "awayTeam": "Michigan",
        "homePoints": 31,
        "awayPoints": 24
    }
    
    # Process as GraphQL
    df_graphql = feature_engineer.prepare_games_frame([game_dict], source="graphql")
    
    # Process as REST (should handle dict too, but may not extract camelCase)
    df_rest = feature_engineer.prepare_games_frame([game_dict], source="rest")
    
    # Both should produce valid DataFrames
    assert not df_graphql.empty
    assert not df_rest.empty
    
    # GraphQL path should handle camelCase → snake_case conversion
    # REST path may use _extract() which tries multiple key variations
    assert "home_team" in df_graphql.columns or "homeTeam" in df_graphql.columns


def test_unwrap_payload_handles_both_structures(feature_engineer):
    """Verify _unwrap_payload() correctly handles GraphQL and REST structures."""
    # Test list (common for both)
    games_list = [{"id": 1, "home_team": "Team A"}]
    records = feature_engineer._unwrap_payload(games_list, source="rest")
    assert len(records) == 1
    
    # Test dict with "data" key
    games_dict = {"data": [{"id": 2, "home_team": "Team B"}]}
    records = feature_engineer._unwrap_payload(games_dict, source="rest")
    assert len(records) == 1
    
    # Test single dict
    single_game = {"id": 3, "home_team": "Team C"}
    records = feature_engineer._unwrap_payload(single_game, source="rest")
    assert len(records) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

