"""
Enhanced Roster Analytics for Script Ohio 2.0

This module provides comprehensive roster analytics beyond basic CFBD data,
including depth chart analysis, experience metrics, position group evaluation,
and performance correlation analysis.

Author: Script Ohio 2.0 Team
Created: 2025-12-18
Purpose: Advanced roster analytics and depth chart evaluation
"""

import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

from ..cfbd_client.unified_client import UnifiedCFBDClient

# Import schema definitions
try:
    from data.processed.analytics.schema_definitions import (
        AdvancedRosterAnalytics,
        AnalyticsSchemaValidator,
    )
except ImportError:
    logging.warning("Analytics schema definitions not available, using fallbacks")

logger = logging.getLogger(__name__)


class PositionGroup(Enum):
    """Position groups for analysis"""

    QUARTERBACK = "quarterback"
    RUNNING_BACK = "running_back"
    WIDE_RECEIVER = "wide_receiver"
    TIGHT_END = "tight_end"
    OFFENSIVE_LINE = "offensive_line"
    DEFENSIVE_LINE = "defensive_line"
    LINEBACKER = "linebacker"
    DEFENSIVE_BACK = "defensive_back"
    SPECIAL_TEAMS = "special_teams"
    ATHLETE = "athlete"  # For players without clear position assignment


@dataclass
class DepthChartEntry:
    """Individual depth chart entry"""

    player_name: str
    position: str
    depth: int  # 1 = starter, 2 = backup, etc.
    class_year: str  # FR, SO, JR, SR
    experience_score: float  # 0-1 based on class year and playing time
    height: Optional[str] = None
    weight: Optional[int] = None
    recruit_rating: Optional[float] = None  # Original recruiting rating
    performance_score: float = 0.0  # Current performance rating
    injury_risk: float = 0.0  # Injury risk assessment
    nfl_draft_prospect: bool = False
    transfer_portal_risk: float = 0.0

    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PositionGroupMetrics:
    """Metrics for a specific position group"""

    position_group: PositionGroup
    team: str
    season: int

    # Depth and experience metrics
    total_players: int = 0
    starters: int = 0
    quality_starters: int = 0  # Players with high performance scores
    depth_quality_score: float = 0.0  # Overall depth chart quality

    # Experience breakdown
    freshman_count: int = 0
    sophomore_count: int = 0
    junior_count: int = 0
    senior_count: int = 0
    graduate_count: int = 0

    # Performance metrics
    average_performance_score: float = 0.0
    experience_score: float = 0.0
    nfl_draft_prospects: int = 0
    transfer_portal_eligible: int = 0

    # Risk assessment
    injury_risk_score: float = 0.0
    transfer_portal_risk: float = 0.0
    depth_chart_health: str = "healthy"  # healthy, concerning, critical

    metadata: Dict[str, Any] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.utcnow)


@dataclass
class RosterAnalyticsConfig:
    """Configuration for enhanced roster analytics"""

    # Depth chart parameters
    depth_position_mapping: Dict[str, str] = field(default_factory=dict)
    experience_weights: Dict[str, float] = field(
        default_factory=lambda: {"FR": 0.2, "SO": 0.4, "JR": 0.7, "SR": 1.0, "GR": 0.8}
    )

    # Performance scoring parameters
    performance_weight_recruiting: float = 0.3  # Weight of original recruiting rating
    performance_weight_current: float = 0.7  # Weight of current performance

    # Risk assessment parameters
    injury_risk_age_factor: float = 1.2  # Age-related injury risk increase
    injury_risk_position_factor: Dict[str, float] = field(
        default_factory=lambda: {
            "QB": 1.5,
            "RB": 1.3,
            "WR": 1.2,
            "TE": 1.1,
            "OL": 1.1,
            "DL": 1.2,
            "LB": 1.1,
            "DB": 1.1,
            "K": 1.0,
            "P": 1.0,
            "LS": 1.1,
        }
    )

    # Transfer portal parameters
    transfer_portal_eligibility_age: int = 25  # Age threshold for transfer portal
    graduate_transfer_risk: float = 0.8  # Higher risk for graduates

    # NFL draft projection parameters
    draft_eligibility_min_class: str = "JR"  # Minimum class for draft consideration
    draft_position_value_weights: Dict[str, float] = field(
        default_factory=lambda: {
            "QB": 1.0,
            "EDGE": 0.9,
            "OT": 0.8,
            "WR": 0.7,
            "CB": 0.6,
            "S": 0.5,
            "LB": 0.5,
            "DT": 0.8,
            "DE": 0.7,
            "TE": 0.6,
        }
    )

    # Data quality parameters
    min_players_per_position: int = 2
    max_position_depth: int = 5
    validate_data_consistency: bool = True

    # Caching
    cache_enabled: bool = True
    cache_ttl_hours: int = 6  # Cache roster data for 6 hours


class EnhancedRosterAnalytics:
    """
    Advanced roster analytics processor that provides comprehensive depth chart
    analysis, performance evaluation, and predictive insights.

    Capabilities:
    - Depth chart construction and quality assessment
    - Experience analysis and team development tracking
    - Performance scoring and NFL draft projections
    - Transfer portal risk assessment
    - Position group strength evaluation
    """

    def __init__(self, config: Optional[RosterAnalyticsConfig] = None):
        """Initialize enhanced roster analytics processor"""
        self.config = config or RosterAnalyticsConfig()

        # Set up position mapping
        self._setup_position_mapping()

        # Initialize CFBD client
        self.cfbd_client = UnifiedCFBDClient()

        # Data storage and caching
        self.cache = {}
        self.cache_timestamps = {}

        # Analytics state
        self.depth_charts = {}
        self.position_analyses = {}
        self.team_metrics = {}

        logger.info("🚀 Enhanced Roster Analytics Module initialized")

    def _setup_position_mapping(self) -> None:
        """Set up standard position mapping for depth charts"""
        self.config.depth_position_mapping.update(
            {
                # Offensive positions
                "QB": PositionGroup.QUARTERBACK,
                "HB": PositionGroup.RUNNING_BACK,
                "RB": PositionGroup.RUNNING_BACK,
                "FB": PositionGroup.RUNNING_BACK,
                "WR": PositionGroup.WIDE_RECEIVER,
                "TE": PositionGroup.TIGHT_END,
                "OT": PositionGroup.OFFENSIVE_LINE,
                "OG": PositionGroup.OFFENSIVE_LINE,
                "C": PositionGroup.OFFENSIVE_LINE,
                "G": PositionGroup.OFFENSIVE_LINE,
                # Defensive positions
                "DE": PositionGroup.DEFENSIVE_LINE,
                "DT": PositionGroup.DEFENSIVE_LINE,
                "NT": PositionGroup.DEFENSIVE_LINE,
                "LB": PositionGroup.LINEBACKER,
                "MLB": PositionGroup.LINEBACKER,
                "OLB": PositionGroup.LINEBACKER,
                "ILB": PositionGroup.LINEBACKER,
                "CB": PositionGroup.DEFENSIVE_BACK,
                "S": PositionGroup.DEFENSIVE_BACK,
                "FS": PositionGroup.DEFENSIVE_BACK,
                "NICKEL": PositionGroup.DEFENSIVE_BACK,
                "DIME": PositionGroup.DEFENSIVE_BACK,
                # Special teams
                "K": PositionGroup.SPECIAL_TEAMS,
                "P": PositionGroup.SPECIAL_TEAMS,
                "LS": PositionGroup.SPECIAL_TEAMS,
                "H": PositionGroup.SPECIAL_TEAMS,
                # Default
                "ATH": PositionGroup.ATHLETE,
            }
        )

    def analyze_team_roster(
        self,
        team: str,
        season: int,
        week: Optional[int] = None,
        force_refresh: bool = False,
    ) -> AdvancedRosterAnalytics:
        """
        Comprehensive roster analysis for a specific team.

        Args:
            team: Team name
            season: Season year
            week: Week number (optional)
            force_refresh: Force refresh of cached data

        Returns:
            AdvancedRosterAnalytics with comprehensive analysis
        """
        cache_key = f"roster_{team}_{season}_{week or 'full'}"

        if (
            not force_refresh
            and self.config.cache_enabled
            and cache_key in self.cache
            and self._is_cache_valid(cache_key)
        ):
            logger.debug(f"Using cached roster data for {cache_key}")
            return self.cache[cache_key]

        logger.info(f"Analyzing roster for {team}, {season}, week {week}")

        try:
            # Get roster data from CFBD
            roster_data = self.cfbd_client.get_roster(season, team)

            if not roster_data:
                return self._create_empty_roster_analysis(team, season, week)

            # Get player stats for performance analysis
            player_stats = self._get_player_performance_data(team, season, week)

            # Analyze roster composition
            roster_analysis = self._analyze_roster_composition(
                team, season, week, roster_data, player_stats
            )

            # Cache the result
            if self.config.cache_enabled:
                self.cache[cache_key] = roster_analysis
                self.cache_timestamps[cache_key] = datetime.utcnow()

            return roster_analysis

        except Exception as e:
            logger.error(f"Error analyzing roster for {team}: {e}")
            return self._create_empty_roster_analysis(team, season, week)

    def analyze_position_groups(
        self, team: str, season: int, week: Optional[int] = None
    ) -> Dict[PositionGroup, PositionGroupMetrics]:
        """
        Analyze all position groups for a team.

        Args:
            team: Team name
            season: Season year
            week: Week number (optional)

        Returns:
            Dictionary mapping position groups to their metrics
        """
        logger.info(f"Analyzing position groups for {team}, {season}")

        position_groups = {}

        try:
            # Get comprehensive roster analysis
            roster_analysis = self.analyze_team_roster(team, season, week)

            # Analyze each position group
            for position_group in PositionGroup:
                position_metrics = self._analyze_position_group(
                    team, season, week, roster_analysis, position_group
                )
                position_groups[position_group] = position_metrics

            return position_groups

        except Exception as e:
            logger.error(f"Error analyzing position groups for {team}: {e}")
            return {}

    def generate_depth_chart_analysis(
        self,
        team: str,
        season: int,
        week: Optional[int] = None,
        include_performance_projections: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate comprehensive depth chart analysis.

        Args:
            team: Team name
            season: Season year
            week: Week number (optional)
            include_performance_projections: Include future performance projections

        Returns:
            Dictionary containing depth chart analysis
        """
        logger.info(f"Generating depth chart analysis for {team}, {season}")

        try:
            # Get roster data
            roster_analysis = self.analyze_team_roster(team, season, week)

            # Build depth chart for each position
            depth_charts = {}

            for position in self.config.depth_position_mapping.keys():
                position_group = self.config.depth_position_mapping[position]
                depth_chart = self._build_position_depth_chart(
                    roster_analysis, position
                )

                if depth_chart:
                    depth_charts[position] = {
                        "position_group": position_group.value,
                        "depth_chart": [entry.__dict__ for entry in depth_chart],
                        "starter_quality": self._evaluate_starter_quality(depth_chart),
                        "depth_score": self._calculate_depth_score(depth_chart),
                        "injury_risk": self._calculate_position_injury_risk(
                            depth_chart
                        ),
                        "nfl_draft_prospects": len(
                            [d for d in depth_chart if d.nfl_draft_prospect]
                        ),
                    }

            # Overall depth chart health assessment
            overall_health = self._assess_overall_depth_chart_health(depth_charts)

            # Position group strengths
            position_strengths = self._evaluate_position_group_strengths(depth_charts)

            return {
                "team": team,
                "season": season,
                "week": week,
                "depth_charts": depth_charts,
                "overall_health_score": overall_health,
                "position_strengths": {
                    pg.value: strength for pg, strength in position_strengths.items()
                },
                "critical_positions": self._identify_critical_positions(depth_charts),
                "depth_chart_recommendations": self._generate_depth_chart_recommendations(
                    depth_charts
                ),
                "last_updated": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error generating depth chart analysis for {team}: {e}")
            return {"error": str(e)}

    def project_nfl_draft_prospects(
        self, team: str, season: int, include_underclassmen: bool = False
    ) -> Dict[str, Any]:
        """
        Project NFL draft prospects from the current roster.

        Args:
            team: Team name
            season: Season year
            include_underclassmen: Include underclassmen in projections

        Returns:
            Dictionary containing NFL draft projections
        """
        logger.info(f"Projecting NFL draft prospects for {team}, {season}")

        try:
            # Get roster analysis
            roster_analysis = self.analyze_team_roster(team, season)

            # Identify draft prospects
            draft_prospects = self._identify_draft_prospects(
                roster_analysis, include_underclassmen
            )

            # Project draft outcomes
            projections = []
            for prospect in draft_prospects:
                projection = self._project_draft_outcome(prospect)
                projections.append(projection)

            # Generate draft team needs analysis
            team_needs = self._analyze_draft_team_needs(team, roster_analysis)

            return {
                "team": team,
                "season": season,
                "draft_prospects": [p.__dict__ for p in draft_prospects],
                "projections": [p.__dict__ for p in projections],
                "team_needs": team_needs,
                "draft_class_strength": self._calculate_draft_class_strength(
                    projections
                ),
                "top_prospects": sorted(
                    projections, key=lambda x: x.get("draft_round", 7)
                )[
                    :10
                ],  # Top 10 prospects
                "last_updated": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error projecting NFL draft prospects for {team}: {e}")
            return {"error": str(e)}

    def analyze_transfer_portal_risk(
        self, team: str, season: int, week: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Analyze transfer portal risk for the current roster.

        Args:
            team: Team: Season year
            season: Season year
            week: Week number (optional)

        Returns:
            Dictionary containing transfer portal risk analysis
        """
        logger.info(f"Analyzing transfer portal risk for {team}, {season}")

        try:
            # Get roster analysis
            roster_analysis = self.analyze_team_roster(team, season, week)

            # Calculate transfer portal risk metrics
            risk_analysis = self._calculate_transfer_portal_risk(roster_analysis)

            # Identify high-risk players
            high_risk_players = self._identify_high_risk_players(roster_analysis)

            # Generate retention recommendations
            retention_strategies = self._generate_retention_strategies(
                high_risk_players
            )

            return {
                "team": team,
                "season": season,
                "week": week,
                "overall_risk_score": risk_analysis["overall_risk_score"],
                "risk_categories": risk_analysis["risk_categories"],
                "high_risk_players": [p.__dict__ for p in high_risk_players],
                "retention_strategies": retention_strategies,
                "portal_eligible_players": len(
                    [
                        p
                        for p in roster_analysis.roster_data
                        if self._is_transfer_portal_eligible(p)
                    ]
                ),
                "last_updated": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error analyzing transfer portal risk for {team}: {e}")
            return {"error": str(e)}

    def generate_roster_dashboard_data(
        self,
        teams: Optional[List[str]] = None,
        season: Optional[int] = None,
        week: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Generate comprehensive roster dashboard data for multiple teams.

        Args:
            teams: List of teams to analyze (optional)
            season: Season year (optional)
            week: Week number (optional)

        Returns:
            Dictionary containing dashboard-ready data
        """
        if season is None:
            season = datetime.now().year

        if teams is None:
            # Default to major programs
            teams = [
                "Alabama",
                "Georgia",
                "Ohio State",
                "Clemson",
                "Oklahoma",
                "LSU",
                "Texas A&M",
                "Auburn",
                "Florida",
                "Michigan",
                "Notre Dame",
                "USC",
                "Oregon",
                "Washington",
                "Utah",
            ]

        logger.info(
            f"Generating roster dashboard data for {len(teams)} teams, {season}"
        )

        dashboard_data = {
            "season": season,
            "week": week,
            "teams_analyzed": len(teams),
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "team_data": {},
        }

        for team in teams:
            try:
                # Get comprehensive roster analysis
                roster_analysis = self.analyze_team_roster(team, season, week)

                # Get position group analysis
                position_analysis = self.analyze_position_groups(team, season, week)

                # Get depth chart analysis
                depth_chart_analysis = self.generate_depth_chart_analysis(
                    team, season, week
                )

                # Get draft prospects
                draft_prospects = self.project_nfl_draft_prospects(team, season)

                # Get transfer portal risk
                transfer_risk = self.analyze_transfer_portal_risk(team, season, week)

                dashboard_data["team_data"][team] = {
                    "roster_summary": {
                        "total_players": roster_analysis.total_players,
                        "average_experience": roster_analysis.average_experience,
                        "returning_production_pct": roster_analysis.returning_production_pct,
                        "overall_depth_score": roster_analysis.roster_depth_score,
                    },
                    "position_analysis": {
                        pg.value: {
                            "total_players": metrics.total_players,
                            "starters": metrics.starters,
                            "quality_starters": metrics.quality_starters,
                            "depth_quality_score": metrics.depth_quality_score,
                            "experience_score": metrics.experience_score,
                            "nfl_draft_prospects": metrics.nfl_draft_prospects,
                            "injury_risk_score": metrics.injury_risk_score,
                            "depth_chart_health": metrics.depth_chart_health,
                        }
                        for pg, metrics in position_analysis.items()
                    },
                    "depth_chart_analysis": {
                        "overall_health_score": depth_chart_analysis.get(
                            "overall_health_score"
                        ),
                        "critical_positions": depth_chart_analysis.get(
                            "critical_positions", []
                        ),
                        "position_strengths": depth_chart_analysis.get(
                            "position_strengths", {}
                        ),
                    },
                    "draft_prospects": {
                        "total_prospects": len(
                            draft_prospects.get("draft_prospects", [])
                        ),
                        "top_prospects": draft_prospects.get("top_prospect")[:5],
                        "draft_class_strength": draft_prospects.get(
                            "draft_class_strength", 0.0
                        ),
                    },
                    "transfer_risk": {
                        "overall_risk_score": transfer_risk.get(
                            "overall_risk_score", 0.0
                        ),
                        "high_risk_players": transfer_risk.get("high_risk_players", []),
                        "portal_eligible_players": transfer_risk.get(
                            "portal_eligible_players", 0
                        ),
                    },
                    "last_updated": datetime.utcnow().isoformat(),
                }

            except Exception as e:
                logger.error(f"Error processing dashboard data for {team}: {e}")
                dashboard_data["team_data"][team] = {"error": str(e)}

        return dashboard_data

    def _analyze_roster_composition(
        self,
        team: str,
        season: int,
        week: Optional[int],
        roster_data: List[Dict[str, Any]],
        player_stats: Dict[str, Any],
    ) -> AdvancedRosterAnalytics:
        """Analyze comprehensive roster composition"""
        # Process roster data
        processed_players = self._process_roster_data(team, season, roster_data)

        # Calculate basic metrics
        total_players = len(processed_players)
        scholarship_players = len(
            [p for p in processed_players if not self._is_walk_on(p)]
        )

        # Position breakdown
        position_distribution = self._analyze_position_distribution(processed_players)
        position_experience = self._analyze_position_experience(processed_players)

        # Performance metrics
        returning_production = self._calculate_returning_production(
            processed_players, player_stats
        )
        overall_experience = self._calculate_overall_experience(processed_players)

        # Transfer portal analysis
        transfer_eligible = len(
            [p for p in processed_players if self._is_transfer_portal_eligible(p)]
        )

        # Depth chart quality
        depth_scores = self._calculate_all_position_depth_scores(processed_players)
        overall_depth_score = (
            np.mean(list(depth_scores.values())) if depth_scores else 0.0
        )

        return AdvancedRosterAnalytics(
            team=team,
            season=season,
            week=week,
            roster_data=processed_players,
            player_performance=player_stats,
            total_players=total_players,
            scholarship_players=scholarship_players,
            position_breakdown=position_distribution,
            position_experience=position_experience,
            returning_production_pct=returning_production,
            average_experience=overall_experience,
            transfer_portal_eligible=transfer_eligible,
            roster_depth_score=overall_depth_score,
            metadata={
                "data_source": "cfbd",
                "processing_timestamp": datetime.utcnow().isoformat(),
                "raw_data_count": len(roster_data),
            },
        )

    def _analyze_position_group(
        self,
        team: str,
        season: int,
        week: Optional[int],
        roster_analysis: AdvancedRosterAnalytics,
        position_group: PositionGroup,
    ) -> PositionGroupMetrics:
        """Analyze a specific position group"""
        # Filter players for this position group
        position_players = [
            player
            for player in roster_analysis.roster_data
            if self._get_position_group(player.get("position", "ATH")) == position_group
        ]

        if not position_players:
            return PositionGroupMetrics(
                position_group=position_group, team=team, season=season
            )

        # Calculate metrics
        total_players = len(position_players)
        starters = min(2, total_players)  # Most positions have 2 starters
        quality_starters = len(
            [p for p in position_players if p.depth == 1 and p.performance_score >= 0.7]
        )

        # Experience breakdown
        experience_counts = self._count_experience_levels(position_players)

        # Performance metrics
        avg_performance = np.mean([p.performance_score for p in position_players])
        experience_score = np.mean([p.experience_score for p in position_players])

        # NFL prospects
        nfl_prospects = len([p for p in position_players if p.nfl_draft_prospect])

        # Transfer portal eligible
        transfer_eligible = len(
            [p for p in position_players if self._is_transfer_portal_eligible(p)]
        )

        # Risk assessment
        injury_risk = self._calculate_position_injury_risk(position_players)
        transfer_risk = self._calculate_position_transfer_risk(position_players)

        # Depth chart health
        depth_health = self._assess_position_depth_health(total_players)

        return PositionGroupMetrics(
            position_group=position_group,
            team=team,
            season=season,
            total_players=total_players,
            starters=starters,
            quality_starters=quality_starters,
            depth_quality_score=self._calculate_depth_quality_score(position_players),
            freshman_count=experience_counts.get("FR", 0),
            sophomore_count=experience_counts.get("SO", 0),
            junior_count=experience_counts.get("JR", 0),
            senior_count=experience_counts.get("SR", 0),
            graduate_count=experience_counts.get("GR", 0),
            average_performance_score=avg_performance,
            experience_score=experience_score,
            nfl_draft_prospects=nfl_prospects,
            transfer_portal_eligible=transfer_eligible,
            injury_risk_score=injury_risk,
            transfer_portal_risk=transfer_risk,
            depth_chart_health=depth_health,
        )

    def _process_roster_data(
        self, team: str, season: int, roster_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Process raw roster data into structured format"""
        processed_players = []

        for player in roster_data:
            # Create depth chart entry
            depth_entry = self._create_depth_chart_entry(player)
            processed_players.append(depth_entry.__dict__)

        return processed_players

    def _create_depth_chart_entry(self, player: Dict[str, Any]) -> DepthChartEntry:
        """Create a depth chart entry from player data"""
        # Extract basic information
        player_name = player.get("firstName", "") + " " + player.get("lastName", "")
        position = player.get("position", "ATH")
        class_year = player.get("year", "FR")
        height = player.get("height")
        weight = player.get("weight")

        # Calculate experience score
        experience_score = self.config.experience_weights.get(class_year, 0.5)

        # Get recruiting rating if available
        recruit_rating = player.get("recruitRating", player.get("rating"))

        # Calculate initial performance score (will be updated with actual performance data)
        performance_score = (
            recruit_rating * self.config.performance_weight_recruiting
            + 0.5 * self.config.performance_weight_current  # Base estimate
        )

        # Assess injury risk
        injury_risk = self._calculate_player_injury_risk(player, position)

        # NFL draft assessment
        nfl_draft_prospect = self._assess_nfl_draft_prospect(
            class_year, position, recruit_rating
        )

        # Transfer portal risk
        transfer_risk = self._calculate_player_transfer_risk(
            player, class_year, position
        )

        return DepthChartEntry(
            player_name=player_name,
            position=position,
            depth=1,  # Will be updated in depth chart construction
            class_year=class_year,
            experience_score=experience_score,
            height=height,
            weight=weight,
            recruit_rating=recruit_rating,
            performance_score=performance_score,
            injury_risk=injury_risk,
            nfl_draft_prospect=nfl_draft_prospect,
            transfer_portal_risk=transfer_risk,
        )

    def _get_position_group(self, position: str) -> PositionGroup:
        """Get position group for a position"""
        return self.config.depth_position_mapping.get(position, PositionGroup.ATHLETE)

    def _calculate_experience_score(self, class_year: str) -> float:
        """Calculate experience score based on class year"""
        return self.config.experience_weights.get(class_year, 0.5)

    def _calculate_player_injury_risk(
        self, player: Dict[str, Any], position: str
    ) -> float:
        """Calculate individual player injury risk"""
        base_risk = 0.1  # Base risk

        # Age-related risk
        age_factor = self.config.injury_risk_age_factor

        # Position-specific risk
        position_factor = self.config.injury_risk_position_factor.get(position, 1.0)

        # Experience factor (less experienced players have higher injury risk)
        class_year = player.get("year", "FR")
        experience_factor = max(0.5, 1.0 - self._calculate_experience_score(class_year))

        # Combine risk factors
        total_risk = base_risk * age_factor * position_factor * experience_factor

        return min(1.0, total_risk)

    def _assess_nfl_draft_prospect(
        self, class_year: str, position: str, recruit_rating: Optional[float]
    ) -> bool:
        """Assess NFL draft prospect status"""
        # Must be eligible for draft (typically JR or SR)
        if class_year not in ["JR", "SR"]:
            return False

        # Must have high recruiting rating
        if recruit_rating and recruit_rating < 0.85:
            return False

        # Position-specific considerations
        draft_positions = ["QB", "OT", "DE", "WR", "CB", "S"]
        if position in draft_positions:
            return True

        return False

    def _calculate_player_transfer_risk(
        self, player: Dict[str, Any], class_year: str, position: str
    ) -> float:
        """Calculate transfer portal risk for individual player"""
        base_risk = 0.1

        # Age risk
        player_age = self._estimate_player_age(player, class_year)
        if player_age >= self.config.transfer_portal_eligibility_age:
            base_risk += 0.4

        # Graduate transfer risk
        if class_year == "GR":
            base_risk += self.config.graduate_transfer_risk

        # Position demand (high-demand positions have lower transfer risk)
        demand_positions = ["QB", "OT", "EDGE"]
        if position in demand_positions:
            base_risk -= 0.2

        return max(0.0, min(1.0, base_risk))

    def _estimate_player_age(self, player: Dict[str, class_year:str]) -> int:
        """Estimate player age from class year and available data"""
        # This is a simplified estimation
        class_age_mapping = {"FR": 18, "SO": 19, "JR": 20, "SR": 21, "GR": 22}
        return class_age_mapping.get(class_year, 20)

    def _is_transfer_portal_eligible(self, player: Dict[str, Any]) -> bool:
        """Check if player is eligible for transfer portal"""
        class_year = player.get("year", "FR")

        # Undergraduates with remaining eligibility
        if class_year in ["FR", "SO", "JR"]:
            return True

        # Graduates with one year of eligibility
        if class_year == "SR":
            return True

        return False

    def _create_empty_roster_analysis(
        self, team: str, season: int, week: Optional[int]
    ) -> AdvancedRosterAnalytics:
        """Create empty roster analysis object"""
        return AdvancedRosterAnalytics(
            team=team,
            season=season,
            week=week,
            roster_data=[],
            player_performance={},
            metadata={"status": "no_data", "message": "No roster data available"},
        )

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self.cache_timestamps:
            return False

        cache_age = datetime.utcnow() - self.cache_timestamps[cache_key]
        max_age = timedelta(hours=self.config.cache_ttl_hours)

        return cache_age < max_age

    def save_roster_analytics(
        self,
        team: str,
        season: int,
        analytics: AdvancedRosterAnalytics,
        output_dir: Optional[Path] = None,
    ) -> None:
        """
        Save roster analytics data to file.

        Args:
            team: Team name
            season: Season year
            analytics: Analytics data to save
            output_dir: Output directory (optional)
        """
        if output_dir is None:
            output_dir = Path("data/processed/analytics/roster")

        output_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{team}_{season}_roster_analytics.json"
        filepath = output_dir / filename

        # Convert to dict and save
        data_dict = analytics.__dict__.copy()
        data_dict["created_at"] = analytics.created_at.isoformat()

        with open(filepath, "w") as f:
            json.dump(data_dict, f, indent=2)

        logger.info(f"✅ Roster analytics saved to {filepath}")


if __name__ == "__main__":
    # Example usage
    config = RosterAnalyticsConfig(
        experience_weights={"FR": 0.2, "SO": 0.4, "JR": 0.7, "SR": 1.0},
        cache_enabled=True,
        include_transfer_portal_risk=True,
    )

    roster_analytics = EnhancedRosterAnalytics(config)

    print("✅ Enhanced Roster Analytics Module initialized")
    print(f"Experience weights configured: {config.experience_weights}")
    print(f"Cache enabled: {config.cache_enabled}")
    print("✅ Module ready for advanced roster analytics processing")

    # Example: Analyze a team's roster
    try:
        analysis = roster_analytics.analyze_team_roster("Ohio State", 2024)
        print(f"✅ Analyzed roster: {analysis.team} {analysis.season}")
        print(f"Total players: {analysis.total_players}")
        print(f"Average experience: {analysis.average_experience:.2f}")
        print(f"Depth score: {analysis.roster_depth_score:.2f}")
    except Exception as e:
        print(f"❌ Error in example: {e}")
