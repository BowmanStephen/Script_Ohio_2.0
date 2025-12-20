"""
Draft Tracking and Predictive Analytics System for Script Ohio 2.0

This module provides comprehensive NFL draft analytics including:
- NFL draft prospect evaluation and projection
- Combine performance analysis and prediction
- Draft stock trends and market value analysis
- Team-specific draft needs and fit analysis
- Historical draft patterns and success metrics
- Draft class strength and weakness evaluation
- Mock draft generation and consensus building
- Draft day trade value analysis
"""

import json
import logging
import warnings
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

from data.processed.analytics.schema_definitions import (
    DraftAnalyticsMetrics,
    DraftProspectAnalysis,
    DraftTradeValue,
    MockDraft,
    PlayerDraftProjection,
    TeamDraftNeeds,
)
from src.cfbd_client.unified_client import UnifiedCFBDClient

logger = logging.getLogger(__name__)


class DraftRound(Enum):
    """NFL Draft round enumeration"""

    FIRST = 1
    SECOND = 2
    THIRD = 3
    FOURTH = 4
    FIFTH = 5
    SIXTH = 6
    SEVENTH = 7


class ProspectGrade(Enum):
    """Prospect grade enumeration"""

    ELITE = "Elite"
    FIRST_ROUND = "First Round"
    SECOND_ROUND = "Second Round"
    THIRD_ROUND = "Third Round"
    MIDDLE_ROUNDS = "Middle Rounds"
    LATE_ROUNDS = "Late Rounds"
    PRIORITY_UNDRAFTED = "Priority Undrafted"
    CAMP_BODY = "Camp Body"


@dataclass
class DraftProspectMetrics:
    """Comprehensive draft prospect metrics"""

    player_id: str
    player_name: str
    position: str
    school: str
    height: float  # inches
    weight: int  # pounds
    overall_grade: ProspectGrade
    round_projection: int
    pick_range: Tuple[int, int]  # min, max pick
    positional_rank: int
    overall_rank: int

    # Physical metrics
    forty_time: Optional[float] = None
    bench_press: Optional[int] = None
    vertical_jump: Optional[float] = None
    broad_jump: Optional[float] = None
    three_cone: Optional[float] = None
    twenty_short_shuttle: Optional[float] = None

    # Production metrics
    career_games: int = 0
    career_starts: int = 0
    final_year_stats: Dict[str, Any] = field(default_factory=dict)
    career_stats: Dict[str, Any] = field(default_factory=dict)

    # Advanced metrics
    production_score: float = 0.0
    athleticism_score: float = 0.0
    draft_stock_trend: str = "Stable"  # Rising, Falling, Stable
    risk_factor: float = 0.0  # 0-1 scale
    ceiling_grade: ProspectGrade = ProspectGrade.MIDDLE_ROUNDS
    floor_grade: ProspectGrade = ProspectGrade.CAMP_BODY

    # Team fits
    top_5_team_fits: List[str] = field(default_factory=list)
    scheme_fit_score: float = 0.0  # 0-1 scale

    # Market value
    draft_trade_value: int = 0  # Trade value points
    rookie_contract_estimate: Optional[Dict[str, float]] = None

    # Predictive analytics
    nfl_success_probability: float = 0.0  # 0-1 scale
    pro_bowl_probability: float = 0.0
    career_length_estimate: float = 0.0  # years
    position_adjusted_value: float = 0.0

    # Comparables
    player_comparables: List[str] = field(default_factory=list)
    similarity_scores: List[float] = field(default_factory=list)


@dataclass
class TeamDraftAnalysis:
    """Comprehensive team draft analysis"""

    team: str
    current_picks: List[Tuple[int, int]]  # (round, pick)
    total_pick_value: int  # Trade value points
    positional_needs: Dict[str, float] = field(
        default_factory=dict
    )  # position -> need_score
    roster_gaps: List[str] = field(default_factory=list)

    # Draft strategy
    best_player_available_priority: float = 0.0  # 0-1 scale
    need_based_priority: float = 0.0
    trade_flexibility: float = 0.0

    # Target prospects
    target_prospects: List[str] = field(default_factory=list)
    realistic_targets: List[str] = field(default_factory=list)
    reach_candidates: List[str] = field(default_factory=list)

    # Historical patterns
    position_draft_frequency: Dict[str, float] = field(default_factory=dict)
    round_preferences: Dict[int, float] = field(default_factory=dict)
    success_rate_by_round: Dict[int, float] = field(default_factory=dict)

    # Analytics
    draft_class_grade: str = "B"  # A-F grading
    value_acquired: float = 0.0  # Value vs expected
    risk_assessment: float = 0.0  # 0-1 scale


@dataclass
class MockDraftConsensus:
    """Mock draft consensus building"""

    consensus_round: int
    consensus_pick: int
    prospect_name: str
    position: str
    school: str

    # Source breakdown
    mock_draft_sources: List[str] = field(default_factory=list)
    source_predictions: Dict[str, Tuple[int, int]] = field(default_factory=dict)

    # Consensus metrics
    agreement_level: float = 0.0  # 0-1 scale, higher = more agreement
    confidence_score: float = 0.0  # 0-1 scale
    volatility_score: float = 0.0  # 0-1 scale

    # Range and probability
    pick_range: Tuple[int, int] = (1, 32)  # min, max
    round_probability: Dict[int, float] = field(default_factory=dict)
    team_probability: Dict[str, float] = field(default_factory=dict)


class DraftTrackingPredictiveAnalytics:
    """
    Comprehensive draft tracking and predictive analytics system

    Provides advanced NFL draft analysis including prospect evaluation,
    team needs assessment, mock draft consensus, and predictive modeling
    for draft outcomes and NFL success.
    """

    def __init__(self, client: Optional[UnifiedCFBDClient] = None):
        """
        Initialize the draft tracking analytics system

        Args:
            client: Optional UnifiedCFBDClient instance
        """
        self.client = client or UnifiedCFBDClient()
        self.logger = logging.getLogger(__name__)

        # Configuration
        self.config = {
            "cache_hours": 24,  # Draft data changes infrequently
            "min_games_for_analysis": 15,
            "comparables_count": 5,
            "mock_sources_weight": {
                "espn": 0.2,
                "nfl": 0.15,
                "drafttek": 0.15,
                "walterfootball": 0.1,
                "draft_network": 0.1,
                "sports_illustrated": 0.1,
                "bleacher_report": 0.1,
                "pro_football_focus": 0.1,
            },
        }

        # Position-specific weights for analysis
        self.position_weights = {
            "QB": {"production": 0.4, "athleticism": 0.3, "character": 0.3},
            "RB": {"production": 0.35, "athleticism": 0.4, "character": 0.25},
            "WR": {"production": 0.3, "athleticism": 0.45, "character": 0.25},
            "TE": {"production": 0.3, "athleticism": 0.35, "character": 0.35},
            "OT": {"production": 0.25, "athleticism": 0.45, "character": 0.3},
            "OG": {"production": 0.3, "athleticism": 0.4, "character": 0.3},
            "C": {"production": 0.35, "athleticism": 0.35, "character": 0.3},
            "DE": {"production": 0.3, "athleticism": 0.45, "character": 0.25},
            "DT": {"production": 0.35, "athleticism": 0.4, "character": 0.25},
            "EDGE": {"production": 0.3, "athleticism": 0.5, "character": 0.2},
            "LB": {"production": 0.35, "athleticism": 0.35, "character": 0.3},
            "CB": {"production": 0.3, "athleticism": 0.45, "character": 0.25},
            "S": {"production": 0.35, "athleticism": 0.35, "character": 0.3},
            "K": {"production": 0.5, "athleticism": 0.2, "character": 0.3},
            "P": {"production": 0.5, "athleticism": 0.2, "character": 0.3},
            "LS": {"production": 0.4, "athleticism": 0.3, "character": 0.3},
        }

        # Historical draft patterns and success rates
        self.historical_patterns = self._load_historical_patterns()

        # Mock draft sources
        self.mock_draft_sources = [
            "espn",
            "nfl",
            "drafttek",
            "walterfootball",
            "draft_network",
            "sports_illustrated",
            "bleacher_report",
            "pro_football_focus",
        ]

        self.logger.info("Draft tracking and predictive analytics initialized")

    def analyze_draft_prospect(
        self,
        player_id: str,
        player_data: Dict[str, Any],
        combine_data: Optional[Dict[str, Any]] = None,
        production_data: Optional[Dict[str, Any]] = None,
    ) -> DraftProspectMetrics:
        """
        Comprehensive analysis of a draft prospect

        Args:
            player_id: Unique player identifier
            player_data: Basic player information
            combine_data: Optional combine performance data
            production_data: Optional college production data

        Returns:
            Comprehensive draft prospect metrics
        """
        try:
            self.logger.info(
                f"Analyzing draft prospect: {player_data.get('name', 'Unknown')}"
            )

            # Extract basic information
            name = player_data.get("name", "Unknown")
            position = player_data.get("position", "Unknown")
            school = player_data.get("school", "Unknown")

            # Calculate overall grades and projections
            overall_grade = self._calculate_overall_grade(
                player_data, combine_data, production_data
            )
            round_projection = self._project_draft_round(overall_grade, position)
            pick_range = self._calculate_pick_range(
                overall_grade, position, round_projection
            )

            # Calculate production and athleticism scores
            production_score = self._calculate_production_score(
                production_data, position
            )
            athleticism_score = self._calculate_athleticism_score(
                combine_data, position
            )

            # Assess risk factors and potential
            risk_factor = self._assess_risk_factor(
                player_data, combine_data, production_data
            )
            ceiling_grade = self._calculate_ceiling_grade(
                overall_grade, athleticism_score, production_score
            )
            floor_grade = self._calculate_floor_grade(overall_grade, risk_factor)

            # Find comparable players
            comparables = self._find_player_comparables(
                position, production_score, athleticism_score
            )

            # Predict NFL success
            nfl_success_prob = self._predict_nfl_success_probability(
                position, production_score, athleticism_score, risk_factor
            )
            pro_bowl_prob = self._predict_pro_bowl_probability(
                position, overall_grade, athleticism_score
            )
            career_length = self._estimate_career_length(risk_factor, position)

            # Calculate positional value
            position_value = self._calculate_position_adjusted_value(
                position, overall_grade
            )

            # Determine team fits
            team_fits = self._determine_team_fits(position, overall_grade, player_data)
            scheme_fit_score = self._calculate_scheme_fit_score(position, player_data)

            # Calculate trade value
            draft_trade_value = self._calculate_draft_trade_value(
                round_projection, pick_range
            )

            # Estimate rookie contract
            rookie_contract = self._estimate_rookie_contract(
                round_projection, pick_range
            )

            # Determine draft stock trend
            draft_stock_trend = self._analyze_draft_stock_trend(player_data)

            return DraftProspectMetrics(
                player_id=player_id,
                player_name=name,
                position=position,
                school=school,
                height=player_data.get("height", 0),
                weight=player_data.get("weight", 0),
                overall_grade=overall_grade,
                round_projection=round_projection,
                pick_range=pick_range,
                positional_rank=player_data.get("positional_rank", 0),
                overall_rank=player_data.get("overall_rank", 0),
                forty_time=combine_data.get("forty_yd") if combine_data else None,
                bench_press=combine_data.get("bench") if combine_data else None,
                vertical_jump=combine_data.get("vertical") if combine_data else None,
                broad_jump=combine_data.get("broad_jump") if combine_data else None,
                three_cone=combine_data.get("three_cone") if combine_data else None,
                twenty_short_shuttle=(
                    combine_data.get("shuttle") if combine_data else None
                ),
                career_games=(
                    production_data.get("career_games", 0) if production_data else 0
                ),
                career_starts=(
                    production_data.get("career_starts", 0) if production_data else 0
                ),
                final_year_stats=(
                    production_data.get("final_year", {}) if production_data else {}
                ),
                career_stats=(
                    production_data.get("career", {}) if production_data else {}
                ),
                production_score=production_score,
                athleticism_score=athleticism_score,
                draft_stock_trend=draft_stock_trend,
                risk_factor=risk_factor,
                ceiling_grade=ceiling_grade,
                floor_grade=floor_grade,
                top_5_team_fits=team_fits[:5],
                scheme_fit_score=scheme_fit_score,
                draft_trade_value=draft_trade_value,
                rookie_contract_estimate=rookie_contract,
                nfl_success_probability=nfl_success_prob,
                pro_bowl_probability=pro_bowl_probability,
                career_length_estimate=career_length,
                position_adjusted_value=position_value,
                player_comparables=comparables["players"],
                similarity_scores=comparables["scores"],
            )

        except Exception as e:
            self.logger.error(f"Error analyzing draft prospect {player_id}: {e}")
            raise

    def analyze_team_draft_needs(
        self,
        team: str,
        roster_data: Dict[str, Any],
        current_picks: List[Tuple[int, int]],
    ) -> TeamDraftAnalysis:
        """
        Comprehensive analysis of team draft needs and strategy

        Args:
            team: Team name
            roster_data: Current roster composition and quality
            current_picks: List of current draft picks (round, pick)

        Returns:
            Comprehensive team draft analysis
        """
        try:
            self.logger.info(f"Analyzing draft needs for: {team}")

            # Calculate positional needs
            positional_needs = self._calculate_positional_needs(roster_data)

            # Identify roster gaps
            roster_gaps = self._identify_roster_gaps(roster_data, positional_needs)

            # Analyze current pick value
            total_pick_value = sum(
                self._get_pick_trade_value(round_num, pick_num)
                for round_num, pick_num in current_picks
            )

            # Determine draft strategy priorities
            bpa_priority = self._calculate_bpa_priority(roster_data)
            need_priority = self._calculate_need_priority(positional_needs)
            trade_flexibility = self._calculate_trade_flexibility(
                current_picks, total_pick_value
            )

            # Analyze historical draft patterns
            position_frequency = self._get_position_draft_frequency(team)
            round_preferences = self._get_round_preferences(team)
            success_rates = self._get_success_rates_by_round(team)

            # Identify target prospects
            target_prospects = self._identify_target_prospects(
                team, positional_needs, current_picks
            )
            realistic_targets = self._filter_realistic_targets(
                target_prospects, current_picks
            )
            reach_candidates = self._identify_reach_candidates(team, current_picks)

            return TeamDraftAnalysis(
                team=team,
                current_picks=current_picks,
                total_pick_value=total_pick_value,
                positional_needs=positional_needs,
                roster_gaps=roster_gaps,
                best_player_available_priority=bpa_priority,
                need_based_priority=need_priority,
                trade_flexibility=trade_flexibility,
                target_prospects=[p["name"] for p in target_prospects],
                realistic_targets=[p["name"] for p in realistic_targets],
                reach_candidates=[p["name"] for p in reach_candidates],
                position_draft_frequency=position_frequency,
                round_preferences=round_preferences,
                success_rate_by_round=success_rates,
                draft_class_grade="B",  # Will be updated after draft analysis
                value_acquired=0.0,  # Will be calculated post-draft
                risk_assessment=self._calculate_team_risk_assessment(target_prospects),
            )

        except Exception as e:
            self.logger.error(f"Error analyzing team draft needs for {team}: {e}")
            raise

    def build_mock_draft_consensus(
        self, round_num: int = 1, prospects: Optional[List[Dict[str, Any]]] = None
    ) -> List[MockDraftConsensus]:
        """
        Build consensus mock draft from multiple sources

        Args:
            round_num: Draft round to analyze
            prospects: List of available prospects (optional)

        Returns:
            List of consensus mock draft picks
        """
        try:
            self.logger.info(f"Building mock draft consensus for Round {round_num}")

            # Collect mock drafts from various sources
            mock_drafts = self._collect_mock_drafts(round_num)

            # Build consensus for each pick
            consensus_picks = []
            picks_in_round = 32 if round_num == 1 else 32  # Simplified for all rounds

            for pick_num in range(1, picks_in_round + 1):
                # Get all predictions for this pick
                predictions_for_pick = []
                for source, mock in mock_drafts.items():
                    if len(mock) >= pick_num:
                        predictions_for_pick.append(
                            {
                                "source": source,
                                "prospect": mock[pick_num - 1]["prospect"],
                                "position": mock[pick_num - 1]["position"],
                                "school": mock[pick_num - 1]["school"],
                            }
                        )

                if predictions_for_pick:
                    # Calculate consensus
                    consensus = self._calculate_pick_consensus(
                        predictions_for_pick, pick_num, round_num
                    )
                    consensus_picks.append(consensus)

            return consensus_picks

        except Exception as e:
            self.logger.error(f"Error building mock draft consensus: {e}")
            raise

    def generate_draft_predictions(
        self,
        prospects: List[DraftProspectMetrics],
        team_analyses: Dict[str, TeamDraftAnalysis],
        simulation_runs: int = 1000,
    ) -> Dict[str, Any]:
        """
        Generate comprehensive draft predictions using Monte Carlo simulation

        Args:
            prospects: List of analyzed prospects
            team_analyses: Dictionary of team draft analyses
            simulation_runs: Number of simulation runs for probability calculations

        Returns:
            Comprehensive draft predictions with probabilities
        """
        try:
            self.logger.info(
                f"Generating draft predictions with {simulation_runs} simulations"
            )

            # Run Monte Carlo simulations
            simulation_results = []

            for run in range(simulation_runs):
                draft_result = self._simulate_draft(prospects, team_analyses)
                simulation_results.append(draft_result)

            # Analyze simulation results
            predictions = self._analyze_simulation_results(
                simulation_results, prospects
            )

            # Generate team-specific predictions
            team_predictions = {}
            for team, analysis in team_analyses.items():
                team_predictions[team] = self._generate_team_predictions(
                    team, analysis, simulation_results
                )

            # Calculate draft class quality metrics
            class_quality = self._assess_draft_class_quality(predictions)

            # Identify value picks and reaches
            value_analysis = self._identify_value_picks_and_reaches(predictions)

            return {
                "prospect_predictions": predictions,
                "team_predictions": team_predictions,
                "class_quality_metrics": class_quality,
                "value_analysis": value_analysis,
                "simulation_metadata": {
                    "runs": simulation_runs,
                    "prospects_analyzed": len(prospects),
                    "teams_analyzed": len(team_analyses),
                    "generation_timestamp": datetime.now().isoformat(),
                },
            }

        except Exception as e:
            self.logger.error(f"Error generating draft predictions: {e}")
            raise

    def analyze_draft_trade_value(
        self,
        current_pick: Tuple[int, int],
        target_pick: Tuple[int, int],
        trade_scenario: str = "standard",
    ) -> DraftTradeValue:
        """
        Analyze draft trade value and scenarios

        Args:
            current_pick: Current team's pick (round, pick)
            target_pick: Target pick to trade for (round, pick)
            trade_scenario: Type of trade scenario

        Returns:
            Comprehensive trade value analysis
        """
        try:
            self.logger.info(f"Analyzing trade value: {current_pick} for {target_pick}")

            # Calculate pick values using trade chart
            current_value = self._get_pick_trade_value(current_pick[0], current_pick[1])
            target_value = self._get_pick_trade_value(target_pick[0], target_pick[1])

            # Calculate value difference
            value_difference = target_value - current_value

            # Determine fair compensation
            compensation_picks = self._calculate_fair_compensation(
                current_value, target_value, trade_scenario
            )

            # Assess trade probability
            trade_probability = self._assess_trade_probability(
                current_pick, target_pick, value_difference
            )

            # Analyze historical similar trades
            similar_trades = self._find_similar_trades(current_pick, target_pick)

            # Calculate risk/reward metrics
            risk_assessment = self._assess_trade_risk(
                current_pick, target_pick, compensation_picks
            )
            reward_potential = self._assess_trade_reward(
                current_pick, target_pick, compensation_picks
            )

            return DraftTradeValue(
                current_pick=current_pick,
                target_pick=target_pick,
                current_pick_value=current_value,
                target_pick_value=target_value,
                value_difference=value_difference,
                recommended_compensation=compensation_picks,
                trade_probability=trade_probability,
                risk_assessment=risk_assessment,
                reward_potential=reward_potential,
                similar_historical_trades=similar_trades,
                trade_scenario_type=trade_scenario,
            )

        except Exception as e:
            self.logger.error(f"Error analyzing draft trade value: {e}")
            raise

    def _calculate_overall_grade(
        self,
        player_data: Dict[str, Any],
        combine_data: Optional[Dict[str, Any]] = None,
        production_data: Optional[Dict[str, Any]] = None,
    ) -> ProspectGrade:
        """Calculate overall prospect grade"""
        position = player_data.get("position", "Unknown")
        weights = self.position_weights.get(position, self.position_weights["OG"])

        # Component scores (0-100 scale)
        production_score = (
            self._calculate_production_score(production_data, position) * 100
        )
        athleticism_score = (
            self._calculate_athleticism_score(combine_data, position) * 100
        )

        # Character/Intangibles (estimated from available data)
        character_score = self._estimate_character_score(player_data) * 100

        # Weighted calculation
        overall_score = (
            production_score * weights["production"]
            + athleticism_score * weights["athleticism"]
            + character_score * weights["character"]
        )

        # Convert to grade
        if overall_score >= 90:
            return ProspectGrade.ELITE
        elif overall_score >= 85:
            return ProspectGrade.FIRST_ROUND
        elif overall_score >= 80:
            return ProspectGrade.SECOND_ROUND
        elif overall_score >= 75:
            return ProspectGrade.THIRD_ROUND
        elif overall_score >= 70:
            return ProspectGrade.MIDDLE_ROUNDS
        elif overall_score >= 65:
            return ProspectGrade.LATE_ROUNDS
        elif overall_score >= 60:
            return ProspectGrade.PRIORITY_UNDRAFTED
        else:
            return ProspectGrade.CAMP_BODY

    def _project_draft_round(self, grade: ProspectGrade, position: str) -> int:
        """Project draft round based on grade and position"""
        grade_to_round = {
            ProspectGrade.ELITE: 1,
            ProspectGrade.FIRST_ROUND: 1,
            ProspectGrade.SECOND_ROUND: 2,
            ProspectGrade.THIRD_ROUND: 3,
            ProspectGrade.MIDDLE_ROUNDS: 4,
            ProspectGrade.LATE_ROUNDS: 6,
            ProspectGrade.PRIORITY_UNDRAFTED: 7,
            ProspectGrade.CAMP_BODY: 7,
        }

        base_round = grade_to_round[grade]

        # Position adjustments (premium positions may get bumped up)
        position_bumps = {
            "QB": 0,
            "OT": 0,
            "EDGE": 0,
            "CB": 0,  # Premium positions
            "WR": 0,
            "DT": 0,
            "RB": 1,
            "TE": 1,
            "LB": 1,
            "S": 1,  # Slight demotion
            "OG": 1,
            "C": 1,
            "DE": 1,
            "K": 2,
            "P": 2,
            "LS": 2,  # Significant demotion
        }

        bump = position_bumps.get(position, 0)
        projected_round = max(1, min(7, base_round + bump))

        return projected_round

    def _calculate_pick_range(
        self, grade: ProspectGrade, position: str, projected_round: int
    ) -> Tuple[int, int]:
        """Calculate likely pick range"""
        # Base ranges by grade
        grade_ranges = {
            ProspectGrade.ELITE: (1, 5),
            ProspectGrade.FIRST_ROUND: (1, 15),
            ProspectGrade.SECOND_ROUND: (33, 50),
            ProspectGrade.THIRD_ROUND: (65, 90),
            ProspectGrade.MIDDLE_ROUNDS: (100, 180),
            ProspectGrade.LATE_ROUNDS: (180, 230),
            ProspectGrade.PRIORITY_UNDRAFTED: (230, 260),
            ProspectGrade.CAMP_BODY: (250, 260),
        }

        base_range = grade_ranges[grade]

        # Convert to pick numbers based on projected round
        if projected_round == 1:
            round_picks = 32
            start_of_round = 1
        elif projected_round == 2:
            round_picks = 32
            start_of_round = 33
        elif projected_round == 3:
            round_picks = 32
            start_of_round = 65
        else:
            round_picks = 32
            start_of_round = 32 * (projected_round - 1) + 1

        # Adjust range for projected round
        if projected_round <= 3:
            min_pick = start_of_round
            max_pick = min(
                start_of_round + round_picks - 1,
                start_of_round + int((base_range[1] - base_range[0]) / 2),
            )
        else:
            min_pick = base_range[0]
            max_pick = base_range[1]

        return (min_pick, max_pick)

    def _calculate_production_score(
        self, production_data: Optional[Dict[str, Any]], position: str
    ) -> float:
        """Calculate production score (0-1 scale)"""
        if not production_data:
            return 0.5  # Default average score

        # Position-specific production metrics
        position_metrics = {
            "QB": ["passing_yards", "passing_tds", "completion_pct", "passer_rating"],
            "RB": ["rushing_yards", "rushing_tds", "yards_per_carry", "receptions"],
            "WR": [
                "receiving_yards",
                "receiving_tds",
                "receptions",
                "yards_per_reception",
            ],
            "TE": [
                "receiving_yards",
                "receiving_tds",
                "receptions",
                "yards_per_reception",
            ],
            "DE": ["sacks", "tackles_for_loss", "total_tackles", "qb_pressures"],
            "DT": ["sacks", "tackles_for_loss", "total_tackles", "run_stuffs"],
            "LB": ["total_tackles", "tackles_for_loss", "sacks", "interceptions"],
            "CB": [
                "interceptions",
                "passes_defended",
                "completion_pct_allowed",
                "tackles",
            ],
            "S": ["interceptions", "passes_defended", "total_tackles", "sacks"],
        }

        metrics = position_metrics.get(position, ["total_tackles"])

        # Calculate normalized scores for each metric
        scores = []
        for metric in metrics:
            if metric in production_data:
                # Normalize based on position-specific benchmarks
                normalized = self._normalize_production_metric(
                    metric, production_data[metric], position
                )
                scores.append(normalized)

        # Return average score
        return np.mean(scores) if scores else 0.5

    def _calculate_athleticism_score(
        self, combine_data: Optional[Dict[str, Any]], position: str
    ) -> float:
        """Calculate athleticism score based on combine performance"""
        if not combine_data:
            return 0.5  # Default average score

        # Position-specific important metrics
        position_metrics = {
            "QB": ["forty_yd", "three_cone", "shuttle"],
            "RB": ["forty_yd", "vertical", "broad_jump", "shuttle"],
            "WR": ["forty_yd", "vertical", "broad_jump", "shuttle"],
            "TE": ["forty_yd", "vertical", "broad_jump", "three_cone"],
            "OT": ["forty_yd", "bench", "shuttle", "three_cone"],
            "OG": ["forty_yd", "bench", "shuttle"],
            "C": ["forty_yd", "bench", "shuttle"],
            "DE": ["forty_yd", "vertical", "bench", "three_cone"],
            "DT": ["forty_yd", "bench", "three_cone"],
            "LB": ["forty_yd", "vertical", "broad_jump", "shuttle", "three_cone"],
            "CB": ["forty_yd", "vertical", "broad_jump", "shuttle", "three_cone"],
            "S": ["forty_yd", "vertical", "broad_jump", "shuttle", "three_cone"],
        }

        metrics = position_metrics.get(position, ["forty_yd"])

        # Calculate normalized scores for each metric
        scores = []
        for metric in metrics:
            if metric in combine_data and combine_data[metric] is not None:
                # Normalize based on position-specific benchmarks
                normalized = self._normalize_athleticism_metric(
                    metric, combine_data[metric], position
                )
                scores.append(normalized)

        # Return average score
        return np.mean(scores) if scores else 0.5

    def _normalize_production_metric(
        self, metric: str, value: float, position: str
    ) -> float:
        """Normalize production metric to 0-1 scale"""
        # Simplified normalization - in real implementation would use historical data
        benchmarks = {
            "passing_yards": {"QB": {"max": 4000, "min": 2000}},
            "rushing_yards": {"RB": {"max": 2000, "min": 800}},
            "receiving_yards": {
                "WR": {"max": 1500, "min": 600},
                "TE": {"max": 1000, "min": 400},
            },
            "sacks": {"DE": {"max": 15, "min": 5}, "DT": {"max": 10, "min": 3}},
            "interceptions": {"CB": {"max": 8, "min": 2}, "S": {"max": 6, "min": 1}},
        }

        if metric in benchmarks and position in benchmarks[metric]:
            benchmark = benchmarks[metric][position]
            normalized = (value - benchmark["min"]) / (
                benchmark["max"] - benchmark["min"]
            )
            return max(0, min(1, normalized))

        # Default normalization (assume good performance is 70th percentile)
        return min(1, value / 100)  # Very simplified

    def _normalize_athleticism_metric(
        self, metric: str, value: float, position: str
    ) -> float:
        """Normalize athleticism metric to 0-1 scale"""
        # Position-specific athletic benchmarks
        benchmarks = {
            "forty_yd": {
                "WR": {"min": 4.2, "max": 4.6},  # Lower is better
                "RB": {"min": 4.3, "max": 4.7},
                "QB": {"min": 4.5, "max": 5.0},
                "OT": {"min": 5.0, "max": 5.4},
                "DE": {"min": 4.5, "max": 5.0},
            },
            "vertical": {
                "WR": {"min": 35, "max": 45},  # Higher is better
                "RB": {"min": 30, "max": 40},
                "TE": {"min": 30, "max": 38},
                "CB": {"min": 35, "max": 42},
            },
            "bench": {
                "OT": {"min": 25, "max": 40},
                "OG": {"min": 25, "max": 40},
                "DT": {"min": 25, "max": 40},
            },
        }

        if metric in benchmarks and position in benchmarks[metric]:
            benchmark = benchmarks[metric][position]

            if metric == "forty_yd":  # Lower is better
                normalized = (benchmark["max"] - value) / (
                    benchmark["max"] - benchmark["min"]
                )
            else:  # Higher is better
                normalized = (value - benchmark["min"]) / (
                    benchmark["max"] - benchmark["min"]
                )

            return max(0, min(1, normalized))

        # Default normalization
        return 0.5

    def _estimate_character_score(self, player_data: Dict[str, Any]) -> float:
        """Estimate character/intangibles score from available data"""
        # This would use disciplinary records, leadership indicators, etc.
        # For now, return a neutral score
        return 0.7

    def _assess_risk_factor(
        self,
        player_data: Dict[str, Any],
        combine_data: Optional[Dict[str, Any]] = None,
        production_data: Optional[Dict[str, Any]] = None,
    ) -> float:
        """Assess risk factor (0-1 scale, higher = more risk)"""
        risk_factors = []

        # Injury history risk
        injury_games_missed = player_data.get("games_missed_injury", 0)
        if injury_games_missed > 6:
            risk_factors.append(0.3)
        elif injury_games_missed > 0:
            risk_factors.append(0.1)

        # Production consistency risk
        if production_data:
            career_games = production_data.get("career_games", 0)
            if career_games < 20:
                risk_factors.append(0.2)
            elif career_games < 30:
                risk_factors.append(0.1)

        # Size/athleticism mismatch risk
        position = player_data.get("position", "Unknown")
        if combine_data and position:
            size_athleticism_risk = self._assess_size_athleticism_risk(
                combine_data, position, player_data
            )
            risk_factors.append(size_athleticism_risk)

        # Character/off-field concerns (simplified)
        disciplinary_issues = player_data.get("disciplinary_issues", 0)
        if disciplinary_issues > 0:
            risk_factors.append(0.2 * disciplinary_issues)

        return min(1.0, sum(risk_factors))

    def _assess_size_athleticism_risk(
        self, combine_data: Dict[str, Any], position: str, player_data: Dict[str, Any]
    ) -> float:
        """Assess risk based on size/athleticism profile for position"""
        # Simplified - would use position-specific size/speed thresholds
        if position in ["OT", "OG", "C"]:
            height = player_data.get("height", 0)
            weight = player_data.get("weight", 0)
            forty_time = combine_data.get("forty_yd", 6.0)

            if height < 76 or weight < 300 or forty_time > 5.5:
                return 0.2

        elif position in ["WR", "RB", "CB"]:
            forty_time = combine_data.get("forty_yd", 5.0)
            if forty_time > 4.6:
                return 0.15

        return 0.0

    def _calculate_ceiling_grade(
        self,
        overall_grade: ProspectGrade,
        athleticism_score: float,
        production_score: float,
    ) -> ProspectGrade:
        """Calculate ceiling grade based on potential"""
        # If athleticism is elite, can bump up ceiling
        if athleticism_score >= 0.9 and production_score >= 0.7:
            return ProspectGrade.ELITE
        elif athleticism_score >= 0.8 and production_score >= 0.6:
            return ProspectGrade.FIRST_ROUND
        elif athleticism_score >= 0.7 and production_score >= 0.5:
            return ProspectGrade.SECOND_ROUND
        else:
            return overall_grade

    def _calculate_floor_grade(
        self, overall_grade: ProspectGrade, risk_factor: float
    ) -> ProspectGrade:
        """Calculate floor grade based on risk factors"""
        if risk_factor > 0.5:
            # High risk drops floor significantly
            floor_mapping = {
                ProspectGrade.ELITE: ProspectGrade.THIRD_ROUND,
                ProspectGrade.FIRST_ROUND: ProspectGrade.MIDDLE_ROUNDS,
                ProspectGrade.SECOND_ROUND: ProspectGrade.LATE_ROUNDS,
                ProspectGrade.THIRD_ROUND: ProspectGrade.PRIORITY_UNDRAFTED,
                ProspectGrade.MIDDLE_ROUNDS: ProspectGrade.CAMP_BODY,
            }
            return floor_mapping.get(overall_grade, ProspectGrade.CAMP_BODY)
        elif risk_factor > 0.3:
            # Moderate risk
            floor_mapping = {
                ProspectGrade.ELITE: ProspectGrade.SECOND_ROUND,
                ProspectGrade.FIRST_ROUND: ProspectGrade.THIRD_ROUND,
                ProspectGrade.SECOND_ROUND: ProspectGrade.MIDDLE_ROUNDS,
                ProspectGrade.THIRD_ROUND: ProspectGrade.LATE_ROUNDS,
            }
            return floor_mapping.get(overall_grade, ProspectGrade.PRIORITY_UNDRAFTED)
        else:
            # Low risk
            return overall_grade

    def _find_player_comparables(
        self, position: str, production_score: float, athleticism_score: float
    ) -> Dict[str, List]:
        """Find historically comparable players"""
        # This would use a database of historical players
        # For now, return mock data
        position_comparables = {
            "QB": ["Patrick Mahomes", "Josh Allen", "Lamar Jackson"],
            "RB": ["Christian McCaffrey", "Alvin Kamara", "Derrick Henry"],
            "WR": ["Justin Jefferson", "Ja'Marr Chase", "Cooper Kupp"],
            "TE": ["Travis Kelce", "George Kittle", "Mark Andrews"],
            "OT": ["Trent Williams", "David Bakhtiari", "Ryan Ramczyk"],
            "DE": ["Nick Bosa", "Myles Garrett", "Joey Bosa"],
            "DT": ["Aaron Donald", "Chris Jones", "Jeffrey Simmons"],
            "LB": ["Bobby Wagner", "Fred Warner", "Darius Leonard"],
            "CB": ["Jaire Alexander", "Marlon Humphrey", "Jalen Ramsey"],
            "S": ["Kevin Byard", "Justin Simmons", "Minkah Fitzpatrick"],
        }

        comparables = position_comparables.get(
            position, ["Generic Player 1", "Generic Player 2"]
        )

        # Generate mock similarity scores
        similarity_scores = [0.85, 0.82, 0.78][: len(comparables)]

        return {"players": comparables, "scores": similarity_scores}

    def _predict_nfl_success_probability(
        self,
        position: str,
        production_score: float,
        athleticism_score: float,
        risk_factor: float,
    ) -> float:
        """Predict probability of NFL success"""
        # Base probabilities by position
        base_probabilities = {
            "QB": 0.35,  # Lower due to complexity
            "OT": 0.75,  # Higher due to demand and measurables
            "DE": 0.65,
            "WR": 0.55,
            "CB": 0.60,
            "DT": 0.60,
            "LB": 0.58,
            "RB": 0.45,
            "TE": 0.50,
            "OG": 0.65,
            "S": 0.55,
            "C": 0.62,
        }

        base_prob = base_probabilities.get(position, 0.5)

        # Adjust based on scores
        production_adjustment = (production_score - 0.5) * 0.3
        athleticism_adjustment = (athleticism_score - 0.5) * 0.3
        risk_adjustment = -risk_factor * 0.2

        final_probability = (
            base_prob + production_adjustment + athleticism_adjustment + risk_adjustment
        )

        return max(0.1, min(0.95, final_probability))

    def _predict_pro_bowl_probability(
        self, position: str, overall_grade: ProspectGrade, athleticism_score: float
    ) -> float:
        """Predict probability of making Pro Bowl"""
        # Base probabilities by grade
        grade_probabilities = {
            ProspectGrade.ELITE: 0.7,
            ProspectGrade.FIRST_ROUND: 0.4,
            ProspectGrade.SECOND_ROUND: 0.2,
            ProspectGrade.THIRD_ROUND: 0.1,
            ProspectGrade.MIDDLE_ROUNDS: 0.05,
            ProspectGrade.LATE_ROUNDS: 0.02,
        }

        base_prob = grade_probabilities.get(overall_grade, 0.01)

        # Adjust for elite athleticism
        if athleticism_score >= 0.9:
            base_prob *= 1.3

        return min(0.8, base_prob)

    def _estimate_career_length(self, risk_factor: float, position: float) -> float:
        """Estimate NFL career length in years"""
        # Base career length by position
        base_lengths = {
            "QB": 6.5,
            "OT": 8.2,
            "OG": 7.8,
            "C": 8.0,
            "DE": 7.5,
            "DT": 7.2,
            "LB": 7.0,
            "CB": 6.8,
            "S": 6.5,
            "WR": 6.2,
            "TE": 6.0,
            "RB": 4.5,  # Shorter careers due to wear
        }

        base_length = base_lengths.get(position, 6.0)

        # Adjust for risk factor
        risk_adjustment = -risk_factor * 3.0  # High risk reduces career length

        estimated_length = base_length + risk_adjustment

        return max(2.0, min(15.0, estimated_length))

    def _calculate_position_adjusted_value(
        self, position: str, overall_grade: ProspectGrade
    ) -> float:
        """Calculate position-adjusted draft value"""
        # Position premium multipliers
        position_premiums = {
            "QB": 1.5,  # Highest premium
            "OT": 1.3,  # High premium
            "DE": 1.25,  # High premium
            "EDGE": 1.25,  # High premium
            "CB": 1.2,  # Moderate-high premium
            "WR": 1.15,  # Moderate premium
            "DT": 1.1,  # Moderate premium
            "TE": 1.05,  # Slight premium
            "LB": 1.0,  # Baseline
            "S": 1.0,  # Baseline
            "OG": 0.95,  # Slight discount
            "C": 0.95,  # Slight discount
            "RB": 0.9,  # Discount due to NFL trends
            "K": 0.3,  # Major discount
            "P": 0.3,  # Major discount
            "LS": 0.2,  # Major discount
        }

        # Grade value multipliers
        grade_values = {
            ProspectGrade.ELITE: 1.0,
            ProspectGrade.FIRST_ROUND: 0.9,
            ProspectGrade.SECOND_ROUND: 0.75,
            ProspectGrade.THIRD_ROUND: 0.6,
            ProspectGrade.MIDDLE_ROUNDS: 0.4,
            ProspectGrade.LATE_ROUNDS: 0.25,
            ProspectGrade.PRIORITY_UNDRAFTED: 0.1,
            ProspectGrade.CAMP_BODY: 0.05,
        }

        position_multiplier = position_premiums.get(position, 1.0)
        grade_multiplier = grade_values.get(overall_grade, 0.5)

        return position_multiplier * grade_multiplier

    def _determine_team_fits(
        self, position: str, overall_grade: ProspectGrade, player_data: Dict[str, Any]
    ) -> List[str]:
        """Determine best team fits based on scheme and needs"""
        # This would use actual team data and scheme analysis
        # For now, return mock data based on position
        position_team_fits = {
            "QB": ["Raiders", "Panthers", "Commanders", "Vikings", "Titans"],
            "OT": ["Bears", "Jets", "Bengals", "Cardinals", "Panthers"],
            "WR": ["Ravens", "Chiefs", "Bills", "Packers", "Patriots"],
            "DE": ["Lions", "Seahawks", "Bears", "Falcons", "Texans"],
            "CB": ["Cardinals", "Raiders", "Texans", "Bengals", "Panthers"],
            "RB": ["Bills", "Ravens", "49ers", "Cowboys", "Dolphins"],
        }

        return position_team_fits.get(
            position, ["Team 1", "Team 2", "Team 3", "Team 4", "Team 5"]
        )

    def _calculate_scheme_fit_score(
        self, position: str, player_data: Dict[str, Any]
    ) -> float:
        """Calculate scheme fit score (0-1 scale)"""
        # This would analyze how player fits different NFL schemes
        # For now, return a reasonable default
        return 0.75

    def _calculate_draft_trade_value(
        self, round_num: int, pick_range: Tuple[int, int]
    ) -> int:
        """Calculate draft trade value points"""
        # Use Jimmy Johnson trade chart values (simplified)
        pick_values = {
            1: 3000,
            2: 2600,
            3: 2200,
            4: 1800,
            5: 1700,
            6: 1600,
            7: 1500,
            8: 1400,
            9: 1350,
            10: 1300,
            11: 1250,
            12: 1200,
            13: 1150,
            14: 1100,
            15: 1050,
            16: 1000,
            17: 950,
            18: 900,
            19: 875,
            20: 850,
            21: 825,
            22: 800,
            23: 775,
            24: 750,
            25: 725,
            26: 700,
            27: 675,
            28: 650,
            29: 625,
            30: 600,
            31: 575,
            32: 550,
            # Additional picks would continue...
        }

        # Use average of range for pick value
        avg_pick = (pick_range[0] + pick_range[1]) // 2

        if avg_pick <= 32:
            return pick_values.get(avg_pick, 500)
        else:
            # Simplified calculation for later rounds
            return max(100, 500 - (avg_pick - 32) * 5)

    def _estimate_rookie_contract(
        self, round_num: int, pick_range: Tuple[int, int]
    ) -> Optional[Dict[str, float]]:
        """Estimate rookie contract details"""
        if round_num > 7:
            return None

        # Simplified contract estimation based on 2023 NFL rookie scale
        avg_pick = (pick_range[0] + pick_range[1]) // 2

        # Contract values in millions (simplified)
        if round_num == 1:
            total_value = 35.0 - (avg_pick - 1) * 0.8
            signing_bonus = total_value * 0.6
        elif round_num == 2:
            total_value = 12.0 - (avg_pick - 33) * 0.2
            signing_bonus = total_value * 0.4
        elif round_num == 3:
            total_value = 6.0 - (avg_pick - 65) * 0.1
            signing_bonus = total_value * 0.3
        else:
            total_value = 4.0
            signing_bonus = total_value * 0.2

        return {
            "total_value_millions": max(total_value, 0.5),
            "signing_bonus_millions": max(signing_bonus, 0.1),
            "years": 4,
            "fifth_year_option": round_num == 1,
        }

    def _analyze_draft_stock_trend(self, player_data: Dict[str, Any]) -> str:
        """Analyze draft stock trend"""
        # This would analyze mock draft movement over time
        # For now, return mock data
        import random

        trends = ["Rising", "Stable", "Falling"]
        weights = [0.2, 0.6, 0.2]  # Most players are stable

        return random.choices(trends, weights=weights)[0]

    def _calculate_positional_needs(
        self, roster_data: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate team positional needs (0-1 scale)"""
        # This would analyze roster quality and depth
        # For now, return mock needs
        return {
            "QB": 0.8,  # High need
            "OT": 0.9,  # Very high need
            "WR": 0.6,  # Moderate need
            "DE": 0.7,  # Moderate-high need
            "CB": 0.5,  # Low-moderate need
        }

    def _identify_roster_gaps(
        self, roster_data: Dict[str, Any], positional_needs: Dict[str, float]
    ) -> List[str]:
        """Identify specific roster gaps"""
        gaps = []
        for position, need_score in positional_needs.items():
            if need_score >= 0.7:
                gaps.append(position)
        return gaps

    def _get_pick_trade_value(self, round_num: int, pick_num: int) -> int:
        """Get trade value for specific pick"""
        overall_pick = (round_num - 1) * 32 + pick_num

        # Simplified Jimmy Johnson trade chart
        if overall_pick <= 32:
            return max(100, 3000 - (overall_pick - 1) * 80)
        else:
            return max(20, 1000 - (overall_pick - 32) * 20)

    def _calculate_bpa_priority(self, roster_data: Dict[str, Any]) -> float:
        """Calculate Best Player Available priority"""
        # If roster is strong across board, can prioritize BPA
        roster_quality = roster_data.get("overall_quality", 0.5)
        return min(1.0, roster_quality * 1.5)

    def _calculate_need_priority(self, positional_needs: Dict[str, float]) -> float:
        """Calculate need-based priority"""
        if not positional_needs:
            return 0.5

        # Use highest need as priority indicator
        max_need = max(positional_needs.values())
        return max_need

    def _calculate_trade_flexibility(
        self, current_picks: List[T[int, int]], total_value: int
    ) -> float:
        """Calculate trade flexibility based on pick capital"""
        # More picks = more flexibility
        pick_count = len(current_picks)

        # Normalize flexibility (0-1 scale)
        flexibility = min(1.0, (pick_count - 3) / 4)  # 3 picks = 0, 7+ picks = 1

        return max(0.0, flexibility)

    def _get_position_draft_frequency(self, team: str) -> Dict[str, float]:
        """Get historical position draft frequency for team"""
        # This would use historical draft data
        # For now, return mock data
        return {
            "OT": 0.15,  # 15% of picks
            "DE": 0.12,
            "WR": 0.10,
            "CB": 0.10,
            "QB": 0.08,
        }

    def _get_round_preferences(self, team: str) -> Dict[int, float]:
        """Get team's round preference patterns"""
        # Mock data - would use historical analysis
        return {1: 0.2, 2: 0.2, 3: 0.15, 4: 0.15, 5: 0.1, 6: 0.1, 7: 0.1}

    def _get_success_rates_by_round(self, team: str) -> Dict[int, float]:
        """Get team's success rates by draft round"""
        # Mock data - would use historical analysis
        return {1: 0.75, 2: 0.60, 3: 0.45, 4: 0.30, 5: 0.20, 6: 0.15, 7: 0.10}

    def _identify_target_prospects(
        self,
        team: str,
        positional_needs: Dict[str, float],
        current_picks: List[T[int, int]],
    ) -> List[Dict[str, Any]]:
        """Identify target prospects for team"""
        # This would match prospects to team needs and draft position
        # For now, return mock data
        targets = []

        for position, need_score in positional_needs.items():
            if need_score >= 0.6:  # Only target positions with need
                targets.append(
                    {
                        "name": f"Prospect at {position}",
                        "position": position,
                        "round_fit": self._estimate_round_fit(need_score),
                        "fit_score": need_score,
                    }
                )

        return targets

    def _estimate_round_fit(self, need_score: float) -> int:
        """Estimate which round to target based on need"""
        if need_score >= 0.9:
            return 1  # Target round 1
        elif need_score >= 0.7:
            return 2  # Target round 2
        else:
            return 3  # Target round 3+

    def _filter_realistic_targets(
        self, targets: List[Dict[str, Any]], current_picks: List[T[int, int]]
    ) -> List[Dict[str, Any]]:
        """Filter targets based on actual draft position"""
        # Remove targets that would be reaches based on current picks
        available_rounds = [pick[0] for pick in current_picks]

        realistic = []
        for target in targets:
            if target["round_fit"] in available_rounds:
                realistic.append(target)

        return realistic

    def _identify_reach_candidates(
        self, team: str, current_picks: List[T[int, int]]
    ) -> List[Dict[str, Any]]:
        """Identify potential reach candidates"""
        # Mock data - would identify prospects that might be reaches
        return [
            {"name": "Reach Candidate 1", "position": "OT", "reach_factor": 0.3},
            {"name": "Reach Candidate 2", "position": "QB", "reach_factor": 0.4},
        ]

    def _calculate_team_risk_assessment(
        self, target_prospects: List[Dict[str, Any]]
    ) -> float:
        """Calculate overall risk assessment for team's targets"""
        if not target_prospects:
            return 0.5

        # Average risk factor from target prospects
        total_risk = sum(p.get("risk_factor", 0.3) for p in target_prospects)
        avg_risk = total_risk / len(target_prospects)

        return avg_risk

    def _collect_mock_drafts(self, round_num: int) -> Dict[str, List[Dict]]:
        """Collect mock drafts from various sources"""
        # This would scrape or fetch actual mock drafts
        # For now, return mock data
        mock_drafts = {}

        for source in self.mock_draft_sources:
            mock_drafts[source] = self._generate_mock_draft(source, round_num)

        return mock_drafts

    def _generate_mock_draft(self, source: str, round_num: int) -> List[Dict]:
        """Generate mock mock draft data"""
        # Mock prospects
        prospects = [
            "Caleb Williams",
            "Drake Maye",
            "Jayden Daniels",
            "Marvin Harrison Jr.",
            "Joe Alt",
            "Dallas Turner",
            "Jared Verse",
            "Quinyon Mitchell",
            "Brock Bowers",
            "Olumuyiwa Fashanu",
            "Taliese Fuaga",
            "Byron Murphy II",
            "Nabors",
            "Kool-Aid McKinstry",
            "Cooper DeJean",
            "Chop Robinson",
            "Laiatu Latu",
            "J.J. McCarthy",
            "Keon Coleman",
            "Adonai Mitchell",
        ]

        mock_draft = []
        for i, prospect in enumerate(prospects[:32]):  # 32 picks per round
            mock_draft.append(
                {
                    "prospect": prospect,
                    "position": self._mock_position_for_prospect(prospect),
                    "school": "Mock University",
                }
            )

        return mock_draft

    def _mock_position_for_prospect(self, prospect_name: str) -> str:
        """Get mock position for prospect"""
        positions = {
            "Caleb Williams": "QB",
            "Drake Maye": "QB",
            "Jayden Daniels": "QB",
            "J.J. McCarthy": "QB",
            "Marvin Harrison Jr.": "WR",
            "Keon Coleman": "WR",
            "Adonai Mitchell": "WR",
            "Joe Alt": "OT",
            "Olumuyiwa Fashanu": "OT",
            "Taliese Fuaga": "OT",
            "Dallas Turner": "DE",
            "Jared Verse": "DE",
            "Chop Robinson": "DE",
            "Laiatu Latu": "DE",
            "Quinyon Mitchell": "CB",
            "Kool-Aid McKinstry": "CB",
            "Cooper DeJean": "CB",
            "Brock Bowers": "TE",
            "Byron Murphy II": "DT",
        }
        return positions.get(prospect_name, "Unknown")

    def _calculate_pick_consensus(
        self, predictions: List[Dict], pick_num: int, round_num: int
    ) -> MockDraftConsensus:
        """Calculate consensus for a specific pick"""
        # Count predictions for each prospect
        prospect_counts = {}
        prospect_positions = {}
        prospect_schools = {}
        source_predictions = {}

        for pred in predictions:
            prospect = pred["prospect"]
            source = pred["source"]

            if prospect not in prospect_counts:
                prospect_counts[prospect] = 0
                prospect_positions[prospect] = pred["position"]
                prospect_schools[prospect] = pred["school"]
                source_predictions[prospect] = []

            prospect_counts[prospect] += 1
            source_predictions[prospect].append((round_num, pick_num))

        # Find consensus prospect (most predicted)
        consensus_prospect = max(
            prospect_counts.keys(), key=lambda x: prospect_counts[x]
        )
        consensus_count = prospect_counts[consensus_prospect]
        total_predictions = len(predictions)

        # Calculate metrics
        agreement_level = consensus_count / total_predictions
        confidence_score = min(1.0, agreement_level * 1.5)  # Boost confidence
        volatility_score = 1.0 - agreement_level  # Higher volatility = less agreement

        return MockDraftConsensus(
            consensus_round=round_num,
            consensus_pick=pick_num,
            prospect_name=consensus_prospect,
            position=prospect_positions[consensus_prospect],
            school=prospect_schools[consensus_prospect],
            mock_draft_sources=list(
                source_predictions[consensus_prospect][0][1]
                if source_predictions[consensus_prospect]
                else []
            ),
            source_predictions={source: pred for pred in predictions},
            agreement_level=agreement_level,
            confidence_score=confidence_score,
            volatility_score=volatility_score,
            pick_range=(pick_num - 2, pick_num + 2),  # Mock range
            round_probability={round_num: confidence_score},
            team_probability={},  # Would need team mapping
        )

    def _simulate_draft(
        self,
        prospects: List[DraftProspectMetrics],
        team_analyses: Dict[str, TeamDraftAnalysis],
    ) -> Dict[str, Any]:
        """Simulate one draft using Monte Carlo methods"""
        # Sort prospects by overall grade
        sorted_prospects = sorted(
            prospects, key=lambda x: x.position_adjusted_value, reverse=True
        )

        draft_results = []
        remaining_prospects = sorted_prospects.copy()

        # Get draft order (simplified - would use actual NFL draft order)
        draft_order = list(team_analyses.keys())[:32]  # First round only for now

        for pick_num, team in enumerate(draft_order, 1):
            if not remaining_prospects:
                break

            # Team selection logic
            team_analysis = team_analyses[team]
            selected_prospect = self._select_prospect_for_team(
                team, team_analysis, remaining_prospects, pick_num
            )

            if selected_prospect:
                draft_results.append(
                    {
                        "pick": pick_num,
                        "team": team,
                        "prospect": selected_prospect.player_name,
                        "position": selected_prospect.position,
                        "school": selected_prospect.school,
                        "value": selected_prospect.position_adjusted_value,
                    }
                )

                remaining_prospects.remove(selected_prospect)

        return {
            "draft_results": draft_results,
            "undrafted_prospects": [p.player_name for p in remaining_prospects],
        }

    def _select_prospect_for_team(
        self,
        team: str,
        team_analysis: TeamDraftAnalysis,
        prospects: List[DraftProspectMetrics],
        pick_num: int,
    ) -> Optional[DraftProspectMetrics]:
        """Select best prospect for team at specific pick"""
        if not prospects:
            return None

        # Calculate selection score for each prospect
        prospect_scores = []

        for prospect in prospects:
            # BPA component
            bpa_score = prospect.position_adjusted_value

            # Need component
            position_need = team_analysis.positional_needs.get(prospect.position, 0.0)
            need_score = position_need

            # Combine BPA and need based on team strategy
            bpa_weight = team_analysis.best_player_available_priority
            need_weight = team_analysis.need_based_priority

            combined_score = bpa_score * bpa_weight + need_score * need_weight

            # Add some randomness for unpredictability
            combined_score += np.random.normal(0, 0.1)

            prospect_scores.append((prospect, combined_score))

        # Select prospect with highest score
        prospect_scores.sort(key=lambda x: x[1], reverse=True)

        return prospect_scores[0][0]

    def _analyze_simulation_results(
        self, simulation_results: List[Dict], prospects: List[DraftProspectMetrics]
    ) -> Dict[str, Any]:
        """Analyze results of Monte Carlo draft simulations"""
        # Calculate draft probabilities for each prospect
        prospect_draft_stats = {}

        for prospect in prospects:
            draft_positions = []
            draft_teams = []

            for sim in simulation_results:
                for pick in sim["draft_results"]:
                    if pick["prospect"] == prospect.player_name:
                        draft_positions.append(pick["pick"])
                        draft_teams.append(pick["team"])
                        break

            if draft_positions:
                prospect_draft_stats[prospect.player_name] = {
                    "draft_probability": len(draft_positions) / len(simulation_results),
                    "average_pick": np.mean(draft_positions),
                    "pick_range": (min(draft_positions), max(draft_positions)),
                    "most_common_team": max(set(draft_teams), key=draft_teams.count),
                    "team_probability": {
                        team: draft_teams.count(team) / len(draft_positions)
                        for team in set(draft_teams)
                    },
                }
            else:
                prospect_draft_stats[prospect.player_name] = {
                    "draft_probability": 0.0,
                    "average_pick": None,
                    "pick_range": None,
                    "most_common_team": None,
                    "team_probability": {},
                }

        return prospect_draft_stats

    def _generate_team_predictions(
        self,
        team: str,
        team_analysis: TeamDraftAnalysis,
        simulation_results: List[Dict],
    ) -> Dict[str, Any]:
        """Generate team-specific draft predictions"""
        team_picks = []

        for sim in simulation_results:
            for pick in sim["draft_results"]:
                if pick["team"] == team:
                    team_picks.append(
                        {
                            "prospect": pick["prospect"],
                            "position": pick["position"],
                            "value": pick["value"],
                            "pick": pick["pick"],
                        }
                    )

        # Analyze team picks
        if team_picks:
            positions_drafted = [p["position"] for p in team_picks]
            values_acquired = [p["value"] for p in team_picks]

            return {
                "most_drafted_position": max(
                    set(positions_drafted), key=positions_drafted.count
                ),
                "average_value_acquired": np.mean(values_acquired),
                "top_5_prospects": [
                    p["prospect"]
                    for p in sorted(team_picks, key=lambda x: x["value"], reverse=True)[
                        :5
                    ]
                ],
                "total_simulation_picks": len(team_picks),
            }
        else:
            return {
                "most_drafted_position": None,
                "average_value_acquired": 0.0,
                "top_5_prospects": [],
                "total_simulation_picks": 0,
            }

    def _assess_draft_class_quality(
        self, predictions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess overall quality of draft class"""
        drafted_prospects = [
            name
            for name, stats in predictions.items()
            if stats["draft_probability"] > 0.5
        ]

        return {
            "total_prospects_analyzed": len(predictions),
            "likely_drafted_count": len(drafted_prospects),
            "draft_quality_score": (
                len(drafted_prospects) / len(predictions) if predictions else 0
            ),
            "top_tier_prospects": [
                name
                for name, stats in predictions.items()
                if stats["draft_probability"] > 0.9
            ],
        }

    def _identify_value_picks_and_reaches(
        self, predictions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Identify potential value picks and reaches"""
        value_picks = []
        reaches = []

        for prospect_name, stats in predictions.items():
            if stats["draft_probability"] > 0.3 and stats["average_pick"]:
                # This would compare predicted pick vs consensus ranking
                # For now, use mock logic
                if stats["average_pick"] and stats["average_pick"] > 50:
                    value_picks.append(
                        {
                            "prospect": prospect_name,
                            "predicted_pick": stats["average_pick"],
                            "value_score": 1.0
                            - (stats["draft_probability"] - 0.3) / 0.7,
                        }
                    )
                elif stats["average_pick"] and stats["average_pick"] < 20:
                    reaches.append(
                        {
                            "prospect": prospect_name,
                            "predicted_pick": stats["average_pick"],
                            "reach_risk": (20 - stats["average_pick"]) / 20,
                        }
                    )

        return {
            "value_picks": sorted(
                value_picks, key=lambda x: x["value_score"], reverse=True
            )[:10],
            "potential_reaches": sorted(
                reaches, key=lambda x: x["reach_risk"], reverse=True
            )[:10],
        }

    def _calculate_fair_compensation(
        self, current_value: int, target_value: int, trade_scenario: str
    ) -> List[Tuple[int, int]]:
        """Calculate fair compensation for draft trades"""
        value_difference = abs(target_value - current_value)

        if current_value > target_value:
            # Trading down - need additional picks
            return self._calculate_trade_down_compensation(value_difference)
        else:
            # Trading up - need to give up picks
            return self._calculate_trade_up_compensation(value_difference)

    def _calculate_trade_down_compensation(
        self, value_difference: int
    ) -> List[Tuple[int, int]]:
        """Calculate compensation for trading down"""
        compensation = []
        remaining_value = value_difference

        # Simplified logic - would use actual trade chart
        if remaining_value >= 500:
            compensation.append((3, 1))  # 3rd round pick
            remaining_value -= 200

        if remaining_value >= 200:
            compensation.append((4, 1))  # 4th round pick
            remaining_value -= 100

        if remaining_value >= 50:
            compensation.append((5, 1))  # 5th round pick

        return compensation

    def _calculate_trade_up_compensation(
        self, value_difference: int
    ) -> List[Tuple[int, int]]:
        """Calculate compensation needed for trading up"""
        compensation = []
        remaining_value = value_difference

        # Simplified logic
        if remaining_value >= 1000:
            compensation.append((1, 1))  # 1st round pick
        elif remaining_value >= 500:
            compensation.append((2, 1))  # 2nd round pick
        elif remaining_value >= 300:
            compensation.append((3, 1))  # 3rd round pick

        if remaining_value % 100 > 0:
            compensation.append((6, 1))  # 6th round pick

        return compensation

    def _assess_trade_probability(
        self,
        current_pick: Tuple[int, int],
        target_pick: Tuple[int, int],
        value_difference: int,
    ) -> float:
        """Assess probability of trade happening"""
        # Higher value differences = lower probability
        base_probability = 0.3

        if abs(value_difference) < 100:
            return base_probability * 1.5  # Small difference = more likely
        elif abs(value_difference) < 300:
            return base_probability
        elif abs(value_difference) < 600:
            return base_probability * 0.7
        else:
            return base_probability * 0.3  # Large difference = less likely

    def _find_similar_trades(
        self, current_pick: Tuple[int, int], target_pick: Tuple[int, int]
    ) -> List[Dict[str, Any]]:
        """Find similar historical trades"""
        # This would query a database of historical trades
        # For now, return mock data
        return [
            {
                "year": 2022,
                "team": "Example Team",
                "trade": f"Traded {current_pick} for {target_pick}",
                "outcome": "Successful",
            }
        ]

    def _assess_trade_risk(
        self,
        current_pick: Tuple[int, int],
        target_pick: Tuple[int, int],
        compensation: List[Tuple[int, int]],
    ) -> float:
        """Assess risk level of trade"""
        # Higher round trades = higher risk
        if target_pick[0] <= 2:  # Trading into first 2 rounds
            return 0.7
        elif target_pick[0] <= 4:
            return 0.5
        else:
            return 0.3

    def _assess_trade_reward(
        self,
        current_pick: Tuple[int, int],
        target_pick: Tuple[int, int],
        compensation: List[Tuple[int, int]],
    ) -> float:
        """Assess potential reward of trade"""
        # Earlier picks = higher potential reward
        if target_pick[0] == 1:
            return 0.9
        elif target_pick[0] == 2:
            return 0.7
        elif target_pick[0] == 3:
            return 0.5
        else:
            return 0.3

    def _load_historical_patterns(self) -> Dict[str, Any]:
        """Load historical draft patterns and success rates"""
        # This would load from a database
        # For now, return mock data
        return {
            "position_success_rates": {
                "QB": 0.45,
                "OT": 0.65,
                "DE": 0.60,
                "WR": 0.50,
                "CB": 0.55,
                "DT": 0.58,
                "LB": 0.52,
                "RB": 0.40,
            },
            "round_success_rates": {
                1: 0.75,
                2: 0.60,
                3: 0.45,
                4: 0.30,
                5: 0.20,
                6: 0.15,
                7: 0.10,
            },
            "team_draft_patterns": {},  # Would contain team-specific patterns
        }

    def generate_draft_dashboard_data(
        self,
        prospects: List[DraftProspectMetrics],
        team_analyses: Dict[str, TeamDraftAnalysis],
        consensus_data: List[MockDraftConsensus],
    ) -> Dict[str, Any]:
        """
        Generate comprehensive dashboard data for draft analysis

        Args:
            prospects: List of analyzed prospects
            team_analyses: Dictionary of team draft analyses
            consensus_data: Consensus mock draft data

        Returns:
            Dashboard-ready data structure
        """
        try:
            self.logger.info("Generating draft dashboard data")

            # Top prospects by position
            top_by_position = {}
            for prospect in prospects:
                position = prospect.position
                if position not in top_by_position:
                    top_by_position[position] = []
                top_by_position[position].append(prospect)

            # Sort each position by overall grade
            for position in top_by_position:
                top_by_position[position].sort(
                    key=lambda x: x.position_adjusted_value, reverse=True
                )
                top_by_position[position] = top_by_position[position][
                    :5
                ]  # Top 5 per position

            # Team needs summary
            team_needs_summary = {}
            for team, analysis in team_analyses.items():
                top_needs = sorted(
                    analysis.positional_needs.items(), key=lambda x: x[1], reverse=True
                )[:3]
                team_needs_summary[team] = {
                    "needs": top_needs,
                    "total_pick_value": analysis.total_pick_value,
                    "draft_capital_rank": self._calculate_draft_capital_rank(
                        analysis.total_pick_value, team_analyses
                    ),
                }

            # Consensus pick accuracy
            consensus_accuracy = self._calculate_consensus_accuracy(consensus_data)

            # Draft value trends
            value_trends = self._analyze_draft_value_trends(prospects)

            # Risk assessment summary
            risk_summary = self._generate_risk_assessment_summary(prospects)

            return {
                "top_prospects_by_position": {
                    pos: [
                        {
                            "name": p.player_name,
                            "school": p.school,
                            "grade": p.overall_grade.value,
                            "round_projection": p.round_projection,
                            "value": p.position_adjusted_value,
                        }
                        for p in prospects
                    ]
                    for pos, prospects in top_by_position.items()
                },
                "team_needs_summary": team_needs_summary,
                "consensus_accuracy": consensus_accuracy,
                "draft_value_trends": value_trends,
                "risk_assessment_summary": risk_summary,
                "draft_class_metrics": {
                    "total_prospects": len(prospects),
                    "first_round_candidates": len(
                        [p for p in prospects if p.round_projection == 1]
                    ),
                    "high_risk_prospects": len(
                        [p for p in prospects if p.risk_factor > 0.6]
                    ),
                    "elite_athletes": len(
                        [p for p in prospects if p.athleticism_score > 0.9]
                    ),
                },
                "generation_timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            self.logger.error(f"Error generating draft dashboard data: {e}")
            raise

    def _calculate_draft_capital_rank(
        self, team_value: int, all_analyses: Dict[str, TeamDraftAnalysis]
    ) -> int:
        """Calculate team's draft capital rank among all teams"""
        values = [analysis.total_pick_value for analysis in all_analyses.values()]
        values.sort(reverse=True)

        try:
            return values.index(team_value) + 1
        except ValueError:
            return len(values) + 1

    def _calculate_consensus_accuracy(
        self, consensus_data: List[MockDraftConsensus]
    ) -> Dict[str, float]:
        """Calculate mock draft consensus accuracy metrics"""
        if not consensus_data:
            return {"overall_accuracy": 0.0, "high_confidence_picks": 0.0}

        high_confidence_count = len(
            [c for c in consensus_data if c.confidence_score > 0.8]
        )
        avg_agreement = np.mean([c.agreement_level for c in consensus_data])

        return {
            "overall_accuracy": avg_agreement,
            "high_confidence_picks": high_confidence_count / len(consensus_data),
            "total_picks_analyzed": len(consensus_data),
        }

    def _analyze_draft_value_trends(
        self, prospects: List[DraftProspectMetrics]
    ) -> Dict[str, Any]:
        """Analyze draft value trends by position and round"""
        position_values = {}
        round_values = {}

        for prospect in prospects:
            position = prospect.position
            round_proj = prospect.round_projection
            value = prospect.position_adjusted_value

            if position not in position_values:
                position_values[position] = []
            position_values[position].append(value)

            if round_proj not in round_values:
                round_values[round_proj] = []
            round_values[round_proj].append(value)

        # Calculate averages
        position_averages = {
            pos: np.mean(values) for pos, values in position_values.items()
        }
        round_averages = {rnd: np.mean(values) for rnd, values in round_values.items()}

        return {
            "position_value_averages": position_averages,
            "round_value_averages": round_averages,
            "highest_value_positions": sorted(
                position_averages.items(), key=lambda x: x[1], reverse=True
            )[:5],
            "value_by_round_trend": round_averages,
        }

    def _generate_risk_assessment_summary(
        self, prospects: List[DraftProspectMetrics]
    ) -> Dict[str, Any]:
        """Generate comprehensive risk assessment summary"""
        if not prospects:
            return {"total_prospects": 0}

        risk_levels = {"Low": 0, "Medium": 0, "High": 0, "Very High": 0}
        position_risks = {}

        for prospect in prospects:
            # Categorize risk level
            if prospect.risk_factor <= 0.25:
                risk_levels["Low"] += 1
            elif prospect.risk_factor <= 0.5:
                risk_levels["Medium"] += 1
            elif prospect.risk_factor <= 0.75:
                risk_levels["High"] += 1
            else:
                risk_levels["Very High"] += 1

            # Track risk by position
            position = prospect.position
            if position not in position_risks:
                position_risks[position] = []
            position_risks[position].append(prospect.risk_factor)

        # Calculate averages by position
        position_risk_averages = {
            pos: np.mean(risks) for pos, risks in position_risks.items()
        }

        return {
            "total_prospects": len(prospects),
            "risk_distribution": risk_levels,
            "average_risk_score": np.mean([p.risk_factor for p in prospects]),
            "risk_by_position": position_risk_averages,
            "highest_risk_positions": sorted(
                position_risk_averages.items(), key=lambda x: x[1], reverse=True
            )[:5],
            "safest_positions": sorted(
                position_risk_averages.items(), key=lambda x: x[1]
            )[:5],
        }
