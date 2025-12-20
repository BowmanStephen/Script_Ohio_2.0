#!/usr/bin/env python3
"""
Schema definitions for CFBD advanced analytics data.

This module defines the data schemas for EPA/WPA, recruiting, roster, and draft analytics
to ensure consistency across the Script Ohio 2.0 platform.

Author: Script Ohio 2.0 Team
Created: 2025-12-18
Purpose: Schema definitions for advanced CFBD analytics
"""

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class EPAPlayRecord:
    """Schema for individual EPA/WPA play data"""

    play_id: str
    game_id: int
    home_team: str
    away_team: str
    period: int
    clock: str
    yard_line: int
    yards_to_go: int
    down: int
    offense: str
    defense: str
    play_type: str
    yards_gained: int
    offense_epa: float
    defense_epa: float
    win_prob_added: float
    home_win_prob: float
    away_win_prob: float
    timestamp: datetime


@dataclass
class TeamEPASeason:
    """Schema for team EPA/WPA season statistics"""

    team: str
    season: int
    total_offense_epa: float
    total_defense_epa: float
    net_epa: float
    offense_epa_per_play: float
    defense_epa_per_play: float
    total_plays: int
    games_played: int
    explosiveness_rate: float
    success_rate: float
    havoc_rate: float
    power_success_rate: float
    stuff_rate: float
    line_yards: float
    line_yards_new: float
    second_level_yards: float
    open_field_yards: float
    created_at: datetime


@dataclass
class AdvancedTeamMetrics:
    """Schema for comprehensive advanced team metrics"""

    team: str
    season: int
    week: Optional[int]

    # EPA/WPA Metrics
    offense_epa: float
    defense_epa: float
    special_teams_epa: float
    net_epa: float

    # Efficiency Metrics
    success_rate: float
    explosiveness_rate: float
    field_position_rate: float
    finishing_drives_rate: float

    # Advanced Stats
    havoc_rate: float
    power_success: float
    stuff_rate: float
    line_yards_per_game: float
    second_level_yards_per_game: float
    open_field_yards_per_game: float

    # Performance Indicators
    pts_per_play: float
    yards_per_play: float
    turnover_margin_per_game: float

    # Win Probability Metrics
    avg_win_prob_added: float
    close_game_win_rate: float
    comeback_win_rate: float

    metadata: Dict[str, Any]
    created_at: datetime


@dataclass
class RecruitingAnalytics:
    """Schema for advanced recruiting analytics"""

    team: str
    recruiting_class: int

    # Basic Recruiting Data
    total_commits: int
    average_rating: float
    star_rating_average: float
    class_ranking: int

    # Position Breakdown
    position_distribution: Dict[str, int]
    average_rating_by_position: Dict[str, float]

    # Recruiting Momentum
    momentum_score: float
    recent_commits: List[Dict[str, Any]]
    flip_risk: float

    # Talent Correlation
    talent_correlation: float
    production_correlation: float

    # Predictive Analytics
    predicted_class_ranking: int
    predicted_wins_added: float

    metadata: Dict[str, Any]
    created_at: datetime


@dataclass
class AdvancedRosterAnalytics:
    """Schema for advanced roster analytics"""

    team: str
    season: int

    # Roster Composition
    total_players: int
    scholarship_players: int
    walk_on_players: int

    # Position Analysis
    position_breakdown: Dict[str, int]
    position_experience: Dict[str, float]
    position_depth_score: Dict[str, float]

    # Experience Metrics
    average_class: float
    seniors: int
    juniors: int
    sophomores: int
    freshmen: int

    # Performance Metrics
    returning_production_pct: float
    starter_experience_rating: float
    overall_team_experience: float

    # Transfer Portal Impact
    transfers_out: int
    transfers_in: int
    net_transfer_impact: float

    # Health & Availability
    injury_risk_score: float
    depth_chart_health: Dict[str, str]

    metadata: Dict[str, Any]
    created_at: datetime


@dataclass
class DraftProspectAnalysis:
    """Schema for draft prospect analysis"""

    player_name: str
    position: str
    college_team: str
    draft_year: int

    # College Performance
    college_stats: Dict[str, Any]
    epa_wpa_metrics: Dict[str, float]
    advanced_metrics: Dict[str, float]

    # Physical Attributes
    height: Optional[str]
    weight: Optional[int]
    arm_length: Optional[float]
    hand_size: Optional[float]

    # Combine Results (if available)
    forty_yard_dash: Optional[float]
    bench_press: Optional[int]
    vertical_jump: Optional[float]
    broad_jump: Optional[float]
    three_cone_drill: Optional[float]
    twenty_yard_shuttle: Optional[float]

    # Draft Analytics
    projected_round: int
    projected_pick_range: str
    draft_grade: float
    position_rank: int

    # NFL Translational Metrics
    nfl_comparison_player: Optional[str]
    scheme_fit: List[str]
    immediate_impact_potential: float

    # Risk Factors
    injury_history: str
    character_concerns: str
    development_ceiling: str

    metadata: Dict[str, Any]
    created_at: datetime


class AnalyticsSchemaValidator:
    """Validator for analytics data schemas"""

    @staticmethod
    def validate_epa_play_record(data: Dict[str, Any]) -> EPAPlayRecord:
        """Validate and convert EPA play record"""
        required_fields = [
            "play_id",
            "game_id",
            "home_team",
            "away_team",
            "offense",
            "defense",
        ]

        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

        return EPAPlayRecord(
            play_id=str(data["play_id"]),
            game_id=int(data["game_id"]),
            home_team=str(data["home_team"]),
            away_team=str(data["away_team"]),
            period=int(data.get("period", 0)),
            clock=str(data.get("clock", "00:00")),
            yard_line=int(data.get("yard_line", 0)),
            yards_to_go=int(data.get("yards_to_go", 0)),
            down=int(data.get("down", 0)),
            offense=str(data["offense"]),
            defense=str(data["defense"]),
            play_type=str(data.get("play_type", "unknown")),
            yards_gained=int(data.get("yards_gained", 0)),
            offense_epa=float(data.get("offense_epa", 0.0)),
            defense_epa=float(data.get("defense_epa", 0.0)),
            win_prob_added=float(data.get("win_prob_added", 0.0)),
            home_win_prob=float(data.get("home_win_prob", 0.0)),
            away_win_prob=float(data.get("away_win_prob", 0.0)),
            timestamp=datetime.utcnow(),
        )

    @staticmethod
    def validate_team_epa_season(data: Dict[str, Any]) -> TeamEPASeason:
        """Validate and convert team EPA season data"""
        if "team" not in data or "season" not in data:
            raise ValueError("Missing required fields: team, season")

        return TeamEPASeason(
            team=str(data["team"]),
            season=int(data["season"]),
            total_offense_epa=float(data.get("total_offense_epa", 0.0)),
            total_defense_epa=float(data.get("total_defense_epa", 0.0)),
            net_epa=float(data.get("net_epa", 0.0)),
            offense_epa_per_play=float(data.get("offense_epa_per_play", 0.0)),
            defense_epa_per_play=float(data.get("defense_epa_per_play", 0.0)),
            total_plays=int(data.get("total_plays", 0)),
            games_played=int(data.get("games_played", 0)),
            explosiveness_rate=float(data.get("explosiveness_rate", 0.0)),
            success_rate=float(data.get("success_rate", 0.0)),
            havoc_rate=float(data.get("havoc_rate", 0.0)),
            power_success_rate=float(data.get("power_success_rate", 0.0)),
            stuff_rate=float(data.get("stuff_rate", 0.0)),
            line_yards=float(data.get("line_yards", 0.0)),
            line_yards_new=float(data.get("line_yards_new", 0.0)),
            second_level_yards=float(data.get("second_level_yards", 0.0)),
            open_field_yards=float(data.get("open_field_yards", 0.0)),
            created_at=datetime.utcnow(),
        )

    @staticmethod
    def validate_advanced_team_metrics(data: Dict[str, Any]) -> AdvancedTeamMetrics:
        """Validate and convert advanced team metrics"""
        if "team" not in data or "season" not in data:
            raise ValueError("Missing required fields: team, season")

        return AdvancedTeamMetrics(
            team=str(data["team"]),
            season=int(data["season"]),
            week=data.get("week"),
            offense_epa=float(data.get("offense_epa", 0.0)),
            defense_epa=float(data.get("defense_epa", 0.0)),
            special_teams_epa=float(data.get("special_teams_epa", 0.0)),
            net_epa=float(data.get("net_epa", 0.0)),
            success_rate=float(data.get("success_rate", 0.0)),
            explosiveness_rate=float(data.get("explosiveness_rate", 0.0)),
            field_position_rate=float(data.get("field_position_rate", 0.0)),
            finishing_drives_rate=float(data.get("finishing_drives_rate", 0.0)),
            havoc_rate=float(data.get("havoc_rate", 0.0)),
            power_success=float(data.get("power_success", 0.0)),
            stuff_rate=float(data.get("stuff_rate", 0.0)),
            line_yards_per_game=float(data.get("line_yards_per_game", 0.0)),
            second_level_yards_per_game=float(
                data.get("second_level_yards_per_game", 0.0)
            ),
            open_field_yards_per_game=float(data.get("open_field_yards_per_game", 0.0)),
            pts_per_play=float(data.get("pts_per_play", 0.0)),
            yards_per_play=float(data.get("yards_per_play", 0.0)),
            turnover_margin_per_game=float(data.get("turnover_margin_per_game", 0.0)),
            avg_win_prob_added=float(data.get("avg_win_prob_added", 0.0)),
            close_game_win_rate=float(data.get("close_game_win_rate", 0.0)),
            comeback_win_rate=float(data.get("comeback_win_rate", 0.0)),
            metadata=data.get("metadata", {}),
            created_at=datetime.utcnow(),
        )

    @staticmethod
    def save_to_json(data_object: Any, filepath: str) -> None:
        """Save data object to JSON file"""
        data_dict = (
            data_object.__dict__ if hasattr(data_object, "__dict__") else data_object
        )

        # Convert datetime objects to ISO strings
        def convert_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            return obj

        json_data = json.dumps(data_dict, default=convert_datetime, indent=2)

        with open(filepath, "w") as f:
            f.write(json_data)

    @staticmethod
    def load_from_json(filepath: str, schema_class: type):
        """Load and validate data from JSON file"""
        with open(filepath, "r") as f:
            data = json.load(f)

        if schema_class == EPAPlayRecord:
            return AnalyticsSchemaValidator.validate_epa_play_record(data)
        elif schema_class == TeamEPASeason:
            return AnalyticsSchemaValidator.validate_team_epa_season(data)
        elif schema_class == AdvancedTeamMetrics:
            return AnalyticsSchemaValidator.validate_advanced_team_metrics(data)
        else:
            raise ValueError(f"Unsupported schema class: {schema_class}")


# Schema registry for easy access
ANALYTICS_SCHEMAS = {
    "epa_play_record": EPAPlayRecord,
    "team_epa_season": TeamEPASeason,
    "advanced_team_metrics": AdvancedTeamMetrics,
    "recruiting_analytics": RecruitingAnalytics,
    "advanced_roster_analytics": AdvancedRosterAnalytics,
    "draft_prospect_analysis": DraftProspectAnalysis,
}

# Data type mapping for caching and optimization
CACHE_TTL_MAPPING = {
    "epa_wpa": 1800,  # 30 minutes
    "team_metrics": 3600,  # 1 hour
    "recruiting": 7200,  # 2 hours
    "roster": 7200,  # 2 hours
    "draft": 14400,  # 4 hours
}

if __name__ == "__main__":
    # Example usage
    print("Analytics Schema Definitions Loaded")
    print(f"Available schemas: {list(ANALYTICS_SCHEMAS.keys())}")

    # Test schema validation
    test_epa_data = {
        "play_id": "test_001",
        "game_id": 401234567,
        "home_team": "Ohio State",
        "away_team": "Michigan",
        "offense": "Ohio State",
        "defense": "Michigan",
    }

    try:
        epa_record = AnalyticsSchemaValidator.validate_epa_play_record(test_epa_data)
        print(
            f"✅ EPA Play Record validated: {epa_record.home_team} vs {epa_record.away_team}"
        )
    except Exception as e:
        print(f"❌ Validation error: {e}")
