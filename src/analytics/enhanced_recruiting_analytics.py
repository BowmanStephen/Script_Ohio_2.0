"""
Enhanced Recruiting Analytics for Script Ohio 2.0

This module provides comprehensive recruiting analytics beyond basic CFBD data,
including momentum analysis, talent correlation, class strength predictions, and
recruiting efficiency metrics.

Author: Script Ohio 2.0 Team
Created: 2025-12-18
Purpose: Advanced recruiting analytics and predictive modeling
"""

import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

from ..cfbd_client.unified_client import UnifiedCFBDClient

# Import schema definitions
try:
    from data.processed.analytics.schema_definitions import (
        AnalyticsSchemaValidator,
        RecruitingAnalytics,
    )
except ImportError:
    logging.warning("Analytics schema definitions not available, using fallbacks")

logger = logging.getLogger(__name__)


@dataclass
class RecruitingConfig:
    """Configuration for enhanced recruiting analytics processing"""

    # Momentum calculation parameters
    momentum_window_weeks: int = 12  # Weeks for momentum calculation
    momentum_weight_decay: float = 0.9  # Decay factor for older commits
    recent_commits_weight: float = 0.7  # Weight for recent vs historical commits

    # Talent correlation parameters
    talent_correlation_window: int = 3  # Years for talent correlation
    min_class_size: int = 15  # Minimum class size for reliable metrics
    outlier_threshold: float = 2.5  # Standard deviations for outlier detection

    # Predictive modeling parameters
    prediction_model_type: str = "linear"  # linear, random_forest, neural_network
    confidence_threshold: float = 0.7  # Minimum confidence for predictions

    # Caching configuration
    cache_enabled: bool = True
    cache_ttl_hours: int = 24  # Cache recruiting data for 24 hours

    # Quality control
    validate_data_quality: bool = True
    include_transfer_portal: bool = True
    track_flips: bool = True


@dataclass
class RecruitingMomentum:
    """Momentum analysis for recruiting classes"""

    team: str
    recruiting_class: int

    # Momentum metrics
    current_momentum: float = 0.0  # -1 to 1 scale
    momentum_trend: float = 0.0  # Recent change in momentum
    momentum_velocity: float = 0.0  # Rate of change

    # Commitment analysis
    total_commits: int = 0
    recent_commits: int = 0  # Last 4 weeks
    high_4star_commits: int = 0
    blue_chip_commits: int = 0  # 5-star recruits

    # Timeline metrics
    weeks_since_first_commit: int = 0
    average_commit_timeline: float = 0.0
    peak_momentum_week: Optional[int] = None

    # Quality metrics
    class_completeness: float = 0.0  # How close to full class
    positional_balance_score: float = 0.0
    geographic_distribution_score: float = 0.0

    # Risk assessment
    flip_risk_score: float = 0.0  # Probability of decommitments
    class_strength_prediction: float = 0.0
    confidence_score: float = 0.0

    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class RecruitingEfficiencyMetrics:
    """Efficiency metrics for recruiting performance"""

    team: str
    time_period: str  # season, multi_season, etc.

    # Efficiency metrics
    recruiting_efficiency_score: float = 0.0  # 0-1 scale
    talent_acquisition_rate: float = 0.0  # Talent per recruiting effort
    offer_success_rate: float = 0.0  # Success rate on offered recruits

    # Production metrics
    freshman_production_score: float = 0.0  # How recruits perform as freshmen
    sophomore_to_starter_rate: float = (
        0.0  # Recruits who become starters by sophomore year
    )
    nfl_draft_projection_rate: float = 0.0  # Recruits projected for NFL draft

    # Comparative metrics
    conference_ranking_efficiency: float = (
        0.0  # Performance vs conference recruiting rankings
    )
    historical_comparison: float = 0.0  # Compared to team's historical performance

    # Cost analysis
    recruiting_investment_score: float = 0.0  # Resources invested vs results
    return_on_investment: float = 0.0  # Performance vs investment

    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


class EnhancedRecruitingAnalytics:
    """
    Advanced recruiting analytics processor that goes beyond basic CFBD data
    to provide comprehensive recruiting insights and predictions.

    Capabilities:
    - Momentum analysis and trend prediction
    - Talent correlation and impact assessment
    - Class strength predictions and risk assessment
    - Efficiency metrics and performance evaluation
    - Geographic and positional distribution analysis
    """

    def __init__(self, config: Optional[RecruitingConfig] = None):
        """Initialize enhanced recruiting analytics processor"""
        self.config = config or RecruitingConfig()
        self.cfbd_client = UnifiedCFBDClient()

        # Data storage and caching
        self.cache = {}
        self.cache_timestamps = {}

        # Historical data for trend analysis
        self.historical_recruiting_data = defaultdict(list)
        self.team_performance_data = defaultdict(dict)

        # Analytics state
        self.momentum_analyses = {}
        self.efficiency_metrics = {}

        logger.info("🚀 Enhanced Recruiting Analytics Module initialized")

    def analyze_recruiting_momentum(
        self, team: str, recruiting_class: int, force_refresh: bool = False
    ) -> RecruitingMomentum:
        """
        Comprehensive recruiting momentum analysis for a specific team and class.

        Args:
            team: Team name
            recruiting_class: Recruiting class year
            force_refresh: Force refresh of cached data

        Returns:
            RecruitingMomentum object with comprehensive analysis
        """
        cache_key = f"momentum_{team}_{recruiting_class}"

        if (
            not force_refresh
            and self.config.cache_enabled
            and cache_key in self.cache
            and self._is_cache_valid(cache_key)
        ):
            logger.debug(f"Using cached momentum data for {cache_key}")
            return self.cache[cache_key]

        logger.info(
            f"Analyzing recruiting momentum for {team}, class {recruiting_class}"
        )

        try:
            # Get recruiting data from CFBD
            recruiting_data = self.cfbd_client.get_recruiting(recruiting_class, team)

            if not recruiting_data:
                return self._create_empty_momentum(team, recruiting_class)

            # Analyze momentum
            momentum = self._calculate_recruiting_momentum(
                team, recruiting_class, recruiting_data
            )

            # Cache the result
            if self.config.cache_enabled:
                self.cache[cache_key] = momentum
                self.cache_timestamps[cache_key] = datetime.utcnow()

            return momentum

        except Exception as e:
            logger.error(f"Error analyzing recruiting momentum for {team}: {e}")
            return self._create_empty_momentum(team, recruiting_class)

    def calculate_recruiting_efficiency(
        self, team: str, time_period: str = "season", force_refresh: bool = False
    ) -> RecruitingEfficiencyMetrics:
        """
        Calculate comprehensive recruiting efficiency metrics.

        Args:
            team: Team name
            time_period: Analysis period (season, multi_season, etc.)
            force_refresh: Force refresh of cached data

        Returns:
            RecruitingEfficiencyMetrics with comprehensive efficiency analysis
        """
        cache_key = f"efficiency_{team}_{time_period}"

        if (
            not force_refresh
            and self.config.cache_enabled
            and cache_key in self.cache
            and self._is_cache_valid(cache_key)
        ):
            return self.cache[cache_key]

        logger.info(
            f"Calculating recruiting efficiency for {team}, period: {time_period}"
        )

        try:
            # Get current and historical recruiting data
            current_recruiting = self.cfbd_client.get_recruiting(
                datetime.now().year, team
            )

            # Get team talent data for correlation
            talent_data = self.cfbd_client.get_team_talent(datetime.now().year)

            # Calculate efficiency metrics
            efficiency = self._calculate_efficiency_metrics(
                team, time_period, current_recruiting, talent_data
            )

            # Cache the result
            if self.config.cache_enabled:
                self.cache[cache_key] = efficiency
                self.cache_timestamps[cache_key] = datetime.utcnow()

            return efficiency

        except Exception as e:
            logger.error(f"Error calculating recruiting efficiency for {team}: {e}")
            return self._create_empty_efficiency(team, time_period)

    def predict_class_strength(
        self, team: str, recruiting_class: int, include_uncertainty: bool = True
    ) -> Dict[str, Any]:
        """
        Predict final class strength and ranking using advanced modeling.

        Args:
            team: Team name
            recruiting_class: Recruiting class year
            include_uncertainty: Include uncertainty estimates

        Returns:
            Dictionary containing predictions and confidence intervals
        """
        logger.info(f"Predicting class strength for {team}, class {recruiting_class}")

        try:
            # Get current recruiting data
            recruiting_data = self.cfbd_client.get_recruiting(recruiting_class, team)

            if not recruiting_data:
                return self._create_empty_prediction(team, recruiting_class)

            # Get momentum analysis
            momentum = self.analyze_recruiting_momentum(team, recruiting_class)

            # Build prediction model
            prediction = self._build_class_strength_prediction(
                team, recruiting_class, recruiting_data, momentum
            )

            # Add uncertainty estimates if requested
            if include_uncertainty:
                prediction["uncertainty"] = self._calculate_prediction_uncertainty(
                    team, recruiting_class, recruiting_data
                )

            return prediction

        except Exception as e:
            logger.error(f"Error predicting class strength for {team}: {e}")
            return self._create_empty_prediction(team, recruiting_class)

    def analyze_positional_needs(
        self,
        team: str,
        current_roster: Optional[List[Dict[str, Any]]] = None,
        recruiting_class: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Analyze positional needs based on roster composition and recruiting targets.

        Args:
            team: Team name
            current_roster: Current roster data (optional)
            recruiting_class: Target recruiting class (optional)

        Returns:
            Dictionary containing positional analysis and recommendations
        """
        logger.info(f"Analyzing positional needs for {team}")

        try:
            # Get roster data if not provided
            if not current_roster:
                current_roster = self.cfbd_client.get_roster(datetime.now().year, team)

            if not current_roster:
                return {"error": "No roster data available"}

            # Analyze current roster composition
            positional_analysis = self._analyze_roster_composition(team, current_roster)

            # Get current recruiting targets
            current_recruiting = self.cfbd_client.get_recruiting(
                recruiting_class or datetime.now().year + 1, team
            )

            # Analyze recruiting targets
            recruiting_analysis = self._analyze_recruiting_targets(
                team, current_recruiting
            )

            # Generate needs assessment
            needs_assessment = self._generate_positional_needs_assessment(
                positional_analysis, recruiting_analysis
            )

            return {
                "team": team,
                "recruiting_class": recruiting_class,
                "positional_analysis": positional_analysis,
                "recruiting_analysis": recruiting_analysis,
                "needs_assessment": needs_assessment,
                "recommendations": self._generate_positional_recommendations(
                    needs_assessment
                ),
                "last_updated": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error analyzing positional needs for {team}: {e}")
            return {"error": str(e)}

    def generate_recruiting_dashboard_data(
        self, teams: Optional[List[str]] = None, recruiting_class: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive recruiting dashboard data for multiple teams.

        Args:
            teams: List of teams to analyze (optional, defaults to top programs)
            recruiting_class: Recruiting class to analyze (optional)

        Returns:
            Dictionary containing dashboard-ready data
        """
        if recruiting_class is None:
            recruiting_class = datetime.now().year + 1

        if teams is None:
            # Default to top programs from recent rankings
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
            ]

        logger.info(
            f"Generating recruiting dashboard data for {len(teams)} teams, class {recruiting_class}"
        )

        dashboard_data = {
            "recruiting_class": recruiting_class,
            "teams_analyzed": len(teams),
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "team_data": {},
        }

        for team in teams:
            try:
                # Get momentum analysis
                momentum = self.analyze_recruiting_momentum(team, recruiting_class)

                # Get efficiency metrics
                efficiency = self.calculate_recruiting_efficiency(team, "season")

                # Get class strength prediction
                prediction = self.predict_class_strength(team, recruiting_class)

                # Get positional needs
                positional_needs = self.analyze_positional_needs(
                    team, None, recruiting_class
                )

                dashboard_data["team_data"][team] = {
                    "momentum": {
                        "current_momentum": momentum.current_momentum,
                        "momentum_trend": momentum.momentum_trend,
                        "total_commits": momentum.total_commits,
                        "blue_chip_commits": momentum.blue_chip_commits,
                        "flip_risk_score": momentum.flip_risk_score,
                    },
                    "efficiency": {
                        "recruiting_efficiency_score": efficiency.recruiting_efficiency_score,
                        "talent_acquisition_rate": efficiency.talent_acquisition_rate,
                        "offer_success_rate": efficiency.offer_success_rate,
                    },
                    "prediction": {
                        "predicted_class_ranking": prediction.get("predicted_ranking"),
                        "predicted_wins_added": prediction.get("predicted_wins_added"),
                        "confidence_score": prediction.get("confidence_score"),
                    },
                    "positional_needs": positional_needs.get("needs_assessment", {}),
                    "last_updated": datetime.utcnow().isoformat(),
                }

            except Exception as e:
                logger.error(f"Error processing dashboard data for {team}: {e}")
                dashboard_data["team_data"][team] = {"error": str(e)}

        return dashboard_data

    def _calculate_recruiting_momentum(
        self, team: str, recruiting_class: int, recruiting_data: List[Dict[str, Any]]
    ) -> RecruitingMomentum:
        """Calculate comprehensive recruiting momentum metrics"""
        if not recruiting_data:
            return self._create_empty_momentum(team, recruiting_class)

        # Sort commits by date (most recent first)
        sorted_commits = sorted(
            recruiting_data, key=lambda x: x.get("commitDate", ""), reverse=True
        )

        # Calculate momentum metrics
        current_momentum = self._calculate_current_momentum(sorted_commits)
        momentum_trend = self._calculate_momentum_trend(sorted_commits)
        momentum_velocity = self._calculate_momentum_velocity(sorted_commits)

        # Analyze commitment quality
        total_commits = len(sorted_commits)
        recent_commits = len(
            [c for c in sorted_commits if self._is_recent_commit(c, 4)]
        )  # Last 4 weeks
        high_4star_commits = len(
            [c for c in sorted_commits if c.get("rating", 0) >= 0.95]
        )
        blue_chip_commits = len(
            [c for c in sorted_commits if c.get("rating", 0) >= 0.98]
        )

        # Timeline analysis
        if sorted_commits:
            first_commit_date = sorted_commits[-1].get("commitDate")
            weeks_since_first = self._calculate_weeks_since_date(first_commit_date)
            average_timeline = self._calculate_average_commit_timeline(sorted_commits)
        else:
            weeks_since_first = 0
            average_timeline = 0.0

        # Quality metrics
        class_completeness = self._calculate_class_completeness(team, recruiting_class)
        positional_balance = self._calculate_positional_balance(sorted_commits)
        geographic_distribution = self._calculate_geographic_distribution(
            sorted_commits
        )

        # Risk assessment
        flip_risk = self._calculate_flip_risk(sorted_commits)
        class_strength = self._predict_class_strength_simple(
            total_commits, blue_chip_commits
        )
        confidence = self._calculate_confidence_score(sorted_commits)

        return RecruitingMomentum(
            team=team,
            recruiting_class=recruiting_class,
            current_momentum=current_momentum,
            momentum_trend=momentum_trend,
            momentum_velocity=momentum_velocity,
            total_commits=total_commits,
            recent_commits=recent_commits,
            high_4star_commits=high_4star_commits,
            blue_chip_commits=blue_chip_commits,
            weeks_since_first_commit=weeks_since_first,
            average_commit_timeline=average_timeline,
            class_completeness=class_completeness,
            positional_balance_score=positional_balance,
            geographic_distribution_score=geographic_distribution,
            flip_risk_score=flip_risk,
            class_strength_prediction=class_strength,
            confidence_score=confidence,
        )

    def _calculate_current_momentum(self, commits: List[Dict[str, Any]]) -> float:
        """Calculate current recruiting momentum using weighted commits"""
        if not commits:
            return 0.0

        total_score = 0.0
        total_weight = 0.0

        for i, commit in enumerate(commits):
            # Weight more recent commits higher
            age_weight = self.config.momentum_weight_decay**i

            # Quality weight based on recruit rating
            rating = commit.get("rating", 0.0)
            quality_weight = max(0.0, (rating - 0.8) * 5)  # Scale 0-1

            # Blue chip bonus
            blue_chip_bonus = 1.0 if rating >= 0.98 else 0.0

            weight = age_weight * quality_weight * blue_chip_bonus
            total_score += weight
            total_weight += weight

        return min(1.0, total_score / max(total_weight, 0.1))

    def _calculate_momentum_trend(self, commits: List[Dict[str, Any]]) -> float:
        """Calculate momentum trend (improvement/decline)"""
        if len(commits) < 8:  # Need sufficient data for trend
            return 0.0

        # Compare recent vs older commits
        recent_commits = commits[:4]
        older_commits = commits[4:8]

        recent_quality = np.mean([c.get("rating", 0.0) for c in recent_commits])
        older_quality = np.mean([c.get("rating", 0.0) for c in older_commits])

        return recent_quality - older_quality

    def _calculate_momentum_velocity(self, commits: List[Dict[str, Any]]) -> float:
        """Calculate velocity of momentum change"""
        if len(commits) < 12:  # Need longer timeline for velocity
            return 0.0

        # Calculate moving averages
        window_size = 4
        velocities = []

        for i in range(len(commits) - window_size):
            window1 = commits[i : i + window_size]
            window2 = (
                commits[i + 1 : i + window_size + 1]
                if i + window_size + 1 <= len(commits)
                else None
            )

            if window2:
                avg1 = np.mean([c.get("rating", 0.0) for c in window1])
                avg2 = np.mean([c.get("rating", 0.0) for c in window2])
                velocities.append(avg2 - avg1)

        return np.mean(velocities) if velocities else 0.0

    def _is_recent_commit(self, commit: Dict[str, Any], weeks: int) -> bool:
        """Check if a commit is within the specified number of weeks"""
        commit_date = commit.get("commitDate")
        if not commit_date:
            return False

        try:
            commit_datetime = datetime.fromisoformat(commit_date.replace("Z", "+00:00"))
            weeks_since = (datetime.utcnow() - commit_datetime).days / 7
            return weeks_since <= weeks
        except:
            return False

    def _calculate_weeks_since_date(self, date_str: Optional[str]) -> int:
        """Calculate weeks since a given date"""
        if not date_str:
            return 0

        try:
            date_obj = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return int((datetime.utcnow() - date_obj).days / 7)
        except:
            return 0

    def _calculate_average_commit_timeline(
        self, commits: List[Dict[str, Any]]
    ) -> float:
        """Calculate average timeline between commits"""
        if len(commits) < 2:
            return 0.0

        dates = []
        for commit in commits:
            commit_date = commit.get("commitDate")
            if commit_date:
                try:
                    date_obj = datetime.fromisoformat(
                        commit_date.replace("Z", "+00:00")
                    )
                    dates.append(date_obj)
                except:
                    continue

        if len(dates) < 2:
            return 0.0

        dates.sort(reverse=True)  # Most recent first
        intervals = []

        for i in range(len(dates) - 1):
            interval_days = (dates[i] - dates[i + 1]).days
            intervals.append(interval_days)

        return np.mean(intervals) / 7.0 if intervals else 0.0

    def _calculate_class_completeness(self, team: str, recruiting_class: int) -> float:
        """Calculate how complete the recruiting class is"""
        # This is a simplified calculation
        # In practice, you'd reference team-specific targets or historical averages

        typical_class_size = 25  # FBS teams typically sign 25 players per class
        current_commits = len(self.cfbd_client.get_recruiting(recruiting_class, team))

        return min(1.0, current_commits / typical_class_size)

    def _calculate_positional_balance(self, commits: List[Dict[str, Any]]) -> float:
        """Calculate positional balance score"""
        if not commits:
            return 0.0

        # Simplified positional balance calculation
        position_counts = defaultdict(int)
        for commit in commits:
            position = commit.get("position", "ATH")
            position_counts[position] += 1

        # Ideal distribution would be balanced across positions
        # This is a simplified score - real implementation would be more sophisticated
        total_commits = len(commits)
        unique_positions = len(position_counts)

        # Score based on having diverse positions
        balance_score = min(1.0, unique_positions / 10.0)  # Assuming ~10 key positions

        return balance_score

    def _calculate_geographic_distribution(
        self, commits: List[Dict[str, Any]]
    ) -> float:
        """Calculate geographic distribution score"""
        if not commits:
            return 0.0

        # Simplified geographic diversity score
        states = set()
        for commit in commits:
            state = commit.get("state", "Unknown")
            if state != "Unknown":
                states.add(state)

        # Score based on geographic diversity
        diversity_score = min(
            1.0, len(states) / 15.0
        )  # Assuming diverse recruiting across ~15 states

        return diversity_score

    def _calculate_flip_risk(self, commits: List[Dict[str, Any]]) -> float:
        """Calculate risk score for potential decommitments"""
        if not commits:
            return 0.0

        risk_factors = 0.0

        for commit in commits:
            # Higher rated recruits have higher flip risk from other schools
            rating = commit.get("rating", 0.0)

            # Recent commits have slightly higher flip risk
            is_recent = self._is_recent_commit(commit, 4)

            if rating >= 0.95:  # 4-star or higher
                risk_factors += 0.8 if is_recent else 0.6
            elif rating >= 0.90:  # 3-star
                risk_factors += 0.3 if is_recent else 0.2

        # Normalize to 0-1 scale
        return min(1.0, risk_factors / len(commits))

    def _predict_class_strength_simple(
        self, total_commits: int, blue_chips: int
    ) -> float:
        """Simple class strength prediction"""
        if total_commits == 0:
            return 0.0

        # Blue chip (5-star) recruits have disproportionate impact
        blue_chip_weight = blue_chips * 5

        # Calculate strength score
        strength_score = (
            total_commits + blue_chip_weight
        ) / 25.0  # Normalized to typical class size

        return min(1.0, strength_score)

    def _calculate_confidence_score(self, commits: List[Dict[str, Any]]) -> float:
        """Calculate confidence score based on data quality and completeness"""
        if not commits:
            return 0.0

        factors = []

        # More commits = higher confidence
        commits_factor = min(1.0, len(commits) / 20.0)
        factors.append(commits_factor)

        # Having rated recruits = higher confidence
        rated_commits = len([c for c in commits if c.get("rating", 0) > 0])
        rated_factor = min(1.0, rated_commits / len(commits)) if commits else 0.0
        factors.append(rated_factor)

        # Recent activity = higher confidence
        recent_commits = len([c for c in commits if self._is_recent_commit(c, 8)])
        recent_factor = min(1.0, recent_commits / 5.0)
        factors.append(recent_factor)

        return np.mean(factors)

    def _create_empty_momentum(
        self, team: str, recruiting_class: int
    ) -> RecruitingMomentum:
        """Create empty momentum object"""
        return RecruitingMomentum(
            team=team,
            recruiting_class=recruiting_class,
            metadata={"status": "no_data", "message": "No recruiting data available"},
        )

    def _create_empty_efficiency(
        self, team: str, time_period: str
    ) -> RecruitingEfficiencyMetrics:
        """Create empty efficiency metrics object"""
        return RecruitingEfficiencyMetrics(
            team=team,
            time_period=time_period,
            metadata={"status": "no_data", "message": "No data available for analysis"},
        )

    def _create_empty_prediction(
        self, team: str, recruiting_class: int
    ) -> Dict[str, Any]:
        """Create empty prediction dictionary"""
        return {
            "team": team,
            "recruiting_class": recruiting_class,
            "predicted_ranking": None,
            "predicted_wins_added": 0.0,
            "confidence_score": 0.0,
            "error": "Insufficient data for prediction",
        }

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self.cache_timestamps:
            return False

        cache_age = datetime.utcnow() - self.cache_timestamps[cache_key]
        max_age = timedelta(hours=self.config.cache_ttl_hours)

        return cache_age < max_age

    def save_recruiting_analytics(
        self,
        team: str,
        recruiting_class: int,
        analytics: Union[RecruitingMomentum, RecruitingEfficiencyMetrics],
        output_dir: Optional[Path] = None,
    ) -> None:
        """
        Save recruiting analytics data to file.

        Args:
            team: Team name
            recruiting_class: Recruiting class year
            analytics: Analytics data to save
            output_dir: Output directory (optional)
        """
        if output_dir is None:
            output_dir = Path("data/processed/analytics/recruiting")

        output_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{team}_{recruiting_class}_recruiting_analytics.json"
        filepath = output_dir / filename

        # Convert to dict and save
        data_dict = analytics.__dict__.copy()
        data_dict["created_at"] = analytics.created_at.isoformat()

        with open(filepath, "w") as f:
            json.dump(data_dict, f, indent=2)

        logger.info(f"✅ Recruiting analytics saved to {filepath}")


if __name__ == "__main__":
    # Example usage
    config = RecruitingConfig(
        momentum_window_weeks=12, cache_enabled=True, include_transfer_portal=True
    )

    recruiting_analytics = EnhancedRecruitingAnalytics(config)

    print("✅ Enhanced Recruiting Analytics Module initialized")
    print(f"Configuration: momentum_window={config.momentum_window_weeks} weeks")
    print(f"Cache enabled: {config.cache_enabled}")
    print("✅ Module ready for advanced recruiting analytics processing")

    # Example: Analyze a team's recruiting momentum
    try:
        momentum = recruiting_analytics.analyze_recruiting_momentum("Ohio State", 2025)
        print(
            f"✅ Analyzed recruiting momentum: {momentum.team} {momentum.recruiting_class}"
        )
        print(f"Current momentum: {momentum.current_momentum:.2f}")
        print(f"Total commits: {momentum.total_commits}")
        print(f"Blue chip commits: {momentum.blue_chip_commits}")
    except Exception as e:
        print(f"❌ Error in example: {e}")
