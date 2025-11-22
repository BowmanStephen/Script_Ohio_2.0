"""
Betting Integration Module for Script Ohio 2.0
============================================
Production-grade betting logic integration with Kelly Criterion, confidence intervals,
and value betting identification. Follows established Script Ohio 2.0 patterns.

Features:
- Kelly Criterion bankroll management
- Confidence interval calculations
- Value betting identification
- Risk management and position sizing
- Market analysis integration
- Advanced betting analytics
- Professional-grade risk controls

Author: Script Ohio 2.0 Enhancement Team
Version: 1.0
Compatible with: Model Execution Engine, BaseAgent framework
"""

import os
import json
import math
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from scipy import stats
from abc import ABC, abstractmethod

# Set up logging following project standards
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class BettingOdds:
    """Comprehensive betting odds representation"""
    home_moneyline: Optional[float] = None  # Positive = underdog, Negative = favorite
    away_moneyline: Optional[float] = None
    home_spread: Optional[float] = None      # Points home team is giving/getting
    away_spread: Optional[float] = None      # Points away team is giving/getting
    home_spread_odds: Optional[float] = None  # Odds for home spread bet (-110 typical)
    away_spread_odds: Optional[float] = None  # Odds for away spread bet
    over_under: Optional[float] = None        # Total points line
    over_odds: Optional[float] = None         # Odds for over bet
    under_odds: Optional[float] = None       # Odds for under bet
    implied_home_win_prob: Optional[float] = None
    implied_away_win_prob: Optional[float] = None


@dataclass
class BettingPrediction:
    """Enhanced prediction with betting context"""
    home_team: str
    away_team: str
    home_win_probability: float
    away_win_probability: float
    predicted_margin: float
    confidence_interval: Tuple[float, float]  # Lower, upper bounds for margin
    prediction_confidence: float
    model_confidence: float
    market_analysis: Dict[str, Any]


@dataclass
class KellyCriterionResult:
    """Kelly Criterion calculation result"""
    kelly_fraction: float  # Fraction of bankroll to bet
    suggested_bet_size: float  # Dollar amount to bet
    expected_value: float  # Expected value of the bet
    growth_rate: float  # Expected growth rate
    risk_level: str  # LOW, MEDIUM, HIGH
    recommendation: str


@dataclass
class ValueBetOpportunity:
    """Value betting opportunity identification"""
    is_value_bet: bool
    expected_value: float
    edge_percentage: float  # Percentage edge over market
    confidence_level: float
    bet_type: str  # MONEYLINE, SPREAD, OVER_UNDER
    recommendation: str
    risk_reward_ratio: float


class ConfidenceIntervalCalculator:
    """Calculate confidence intervals for model predictions"""

    @staticmethod
    def calculate_margin_ci(
        predicted_margin: float,
        confidence_level: float = 0.95,
        historical_mae: float = 17.31,
        sample_size: int = 100
    ) -> Tuple[float, float]:
        """
        Calculate confidence interval for margin predictions

        Args:
            predicted_margin: Model's predicted margin
            confidence_level: Confidence level (0.0-1.0)
            historical_mae: Historical mean absolute error
            sample_size: Number of similar games in training data

        Returns:
            Tuple of (lower_bound, upper_bound)
        """
        # Use t-distribution for small sample sizes, normal for large
        if sample_size < 30:
            alpha = 1 - confidence_level
            t_critical = stats.t.ppf(1 - alpha/2, sample_size - 1)
        else:
            alpha = 1 - confidence_level
            t_critical = stats.norm.ppf(1 - alpha/2)

        # Standard error based on historical MAE
        standard_error = historical_mae / math.sqrt(sample_size)

        # Calculate margin of error
        margin_of_error = t_critical * standard_error

        lower_bound = predicted_margin - margin_of_error
        upper_bound = predicted_margin + margin_of_error

        return (lower_bound, upper_bound)

    @staticmethod
    def calculate_probability_ci(
        predicted_probability: float,
        confidence_level: float = 0.95,
        historical_accuracy: float = 0.43,
        sample_size: int = 100
    ) -> Tuple[float, float]:
        """
        Calculate confidence interval for probability predictions

        Args:
            predicted_probability: Model's predicted probability (0.0-1.0)
            confidence_level: Confidence level (0.0-1.0)
            historical_accuracy: Historical model accuracy
            sample_size: Number of similar predictions in training data

        Returns:
            Tuple of (lower_bound, upper_bound)
        """
        # Wilson score interval for binomial proportions
        z = stats.norm.ppf((1 + confidence_level) / 2)

        n = max(sample_size, 1)  # Avoid division by zero
        p = predicted_probability

        # Wilson score interval
        denominator = 1 + (z**2 / n)
        center_adjusted = p + (z**2 / (2 * n))
        margin = z * math.sqrt((p * (1 - p) / n) + (z**2 / (4 * n**2)))

        lower_bound = (center_adjusted - margin) / denominator
        upper_bound = (center_adjusted + margin) / denominator

        # Clamp to [0, 1]
        lower_bound = max(0, min(1, lower_bound))
        upper_bound = max(0, min(1, upper_bound))

        return (lower_bound, upper_bound)


class KellyCriterionCalculator:
    """Professional Kelly Criterion implementation for sports betting"""

    def __init__(self, min_bet_size: float = 1.0, max_kelly_fraction: float = 0.25):
        """
        Initialize Kelly Criterion calculator

        Args:
            min_bet_size: Minimum bet size in dollars
            max_kelly_fraction: Maximum fraction of bankroll to bet (safety limit)
        """
        self.min_bet_size = min_bet_size
        self.max_kelly_fraction = max_kelly_fraction
        logger.info(f"Kelly Calculator initialized: min=${min_bet_size}, max_kelly={max_kelly_fraction*100}%")

    def calculate_kelly_fraction(
        self,
        implied_probability: float,
        true_probability: float,
        decimal_odds: Optional[float] = None,
        american_odds: Optional[float] = None
    ) -> KellyCriterionResult:
        """
        Calculate optimal Kelly fraction for a bet

        Args:
            implied_probability: Market implied probability
            true_probability: Model's true probability estimate
            decimal_odds: Decimal odds (optional)
            american_odds: American odds (optional)

        Returns:
            KellyCriterionResult with detailed analysis
        """
        # Convert odds to decimal if not provided
        if decimal_odds is None:
            if american_odds is not None:
                decimal_odds = self.american_to_decimal(american_odds)
            else:
                decimal_odds = 1 / implied_probability

        # Calculate edge (difference between true and implied probability)
        edge = true_probability - implied_probability

        # Kelly fraction formula: f = (bp - q) / b
        # where b = decimal odds - 1, p = true probability, q = 1 - p
        b = decimal_odds - 1
        p = true_probability
        q = 1 - p

        if b <= 0:
            # No positive expected value
            kelly_fraction = 0.0
            expected_value = -1.0  # Losing proposition
        else:
            kelly_fraction = (b * p - q) / b
            expected_value = (p * b) - q  # Expected return per $1 bet

        # Apply safety limits
        kelly_fraction = max(0, min(kelly_fraction, self.max_kelly_fraction))

        # Calculate growth rate (logarithmic growth)
        growth_rate = p * math.log(1 + b * kelly_fraction) + q * math.log(1 - kelly_fraction)

        # Determine risk level
        if kelly_fraction <= 0.01:  # 1% or less
            risk_level = "LOW"
            recommendation = "Small bet or pass - minimal edge"
        elif kelly_fraction <= 0.05:  # 1-5%
            risk_level = "MEDIUM"
            recommendation = "Conservative bet with solid edge"
        elif kelly_fraction <= 0.10:  # 5-10%
            risk_level = "MEDIUM-HIGH"
            recommendation = "Strong bet with good edge"
        elif kelly_fraction <= 0.20:  # 10-20%
            risk_level = "HIGH"
            recommendation = "Very strong bet - consider fractional Kelly for safety"
        else:  # Over 20%
            risk_level = "VERY HIGH"
            recommendation = "Exceptional edge - use fractional Kelly (25-50%) for safety"

        return KellyCriterionResult(
            kelly_fraction=kelly_fraction,
            suggested_bet_size=max(self.min_bet_size, kelly_fraction * 1000),  # Assume $1k bankroll
            expected_value=expected_value,
            growth_rate=growth_rate,
            risk_level=risk_level,
            recommendation=recommendation
        )

    def calculate_fractional_kelly(
        self,
        base_kelly: float,
        fraction: float = 0.5,
        bankroll: float = 1000.0
    ) -> KellyCriterionResult:
        """
        Calculate fractional Kelly for more conservative betting

        Args:
            base_kelly: Base Kelly fraction
            fraction: Fraction of Kelly to use (0.0-1.0)
            bankroll: Total bankroll amount

        Returns:
            KellyCriterionResult with fractional Kelly applied
        """
        fractional_kelly = base_kelly * fraction
        bet_size = max(self.min_bet_size, fractional_kelly * bankroll)

        # Adjust recommendation for fractional Kelly
        if fraction <= 0.25:
            safety_note = "Very conservative approach - suitable for new bettors"
        elif fraction <= 0.5:
            safety_note = "Conservative approach - good balance of growth and safety"
        elif fraction <= 0.75:
            safety_note = "Moderate approach - decent growth with reasonable risk"
        else:
            safety_note = "Aggressive approach - higher growth potential"

        return KellyCriterionResult(
            kelly_fraction=fractional_kelly,
            suggested_bet_size=bet_size,
            expected_value=base_kelly * (1 + fraction),  # Adjusted EV
            growth_rate=base_kelly * fraction,
            risk_level="ADJUSTED",
            recommendation=f"Fractional Kelly ({fraction*100}%): {safety_note}"
        )

    def american_to_decimal(self, american_odds: float) -> float:
        """Convert American odds to decimal odds"""
        if american_odds > 0:
            return 1 + (american_odds / 100)
        else:
            return 1 - (100 / american_odds)

    def decimal_to_american(self, decimal_odds: float) -> float:
        """Convert decimal odds to American odds"""
        if decimal_odds >= 2:
            return (decimal_odds - 1) * 100
        else:
            return -100 / (decimal_odds - 1)


class ValueBetDetector:
    """Identify value betting opportunities"""

    def __init__(self, min_edge_threshold: float = 0.02):
        """
        Initialize value bet detector

        Args:
            min_edge_threshold: Minimum edge percentage to consider a value bet
        """
        self.min_edge_threshold = min_edge_threshold
        logger.info(f"Value Bet Detector initialized: min edge={min_edge_threshold*100}%")

    def identify_value_bets(
        self,
        prediction: BettingPrediction,
        odds: BettingOdds,
        bankroll: float = 1000.0
    ) -> Dict[str, ValueBetOpportunity]:
        """
        Identify value betting opportunities across different bet types

        Args:
            prediction: Model's betting prediction
            odds: Current market odds
            bankroll: Available bankroll

        Returns:
            Dictionary of value bet opportunities by bet type
        """
        opportunities = {}

        # Moneyline value bet
        if odds.home_moneyline is not None:
            opportunities['MONEYLINE_HOME'] = self._analyze_moneyline_value(
                prediction.home_win_probability,
                odds.home_moneyline,
                'HOME',
                bankroll
            )

        if odds.away_moneyline is not None:
            opportunities['MONEYLINE_AWAY'] = self._analyze_moneyline_value(
                prediction.away_win_probability,
                odds.away_moneyline,
                'AWAY',
                bankroll
            )

        # Spread value bet
        if odds.home_spread is not None and odds.home_spread_odds is not None:
            opportunities['SPREAD_HOME'] = self._analyze_spread_value(
                prediction,
                odds.home_spread,
                odds.home_spread_odds,
                'HOME',
                bankroll
            )

        # Over/Under value bet
        if odds.over_under is not None and odds.over_odds is not None:
            opportunities['OVER_UNDER'] = self._analyze_total_value(
                prediction,
                odds.over_under,
                odds.over_odds,
                bankroll
            )

        return opportunities

    def _analyze_moneyline_value(
        self,
        true_probability: float,
        american_odds: float,
        team: str,
        bankroll: float
    ) -> ValueBetOpportunity:
        """Analyze moneyline value bet"""
        # Convert to implied probability
        implied_prob = self._american_to_implied_probability(american_odds)

        # Calculate edge
        edge = true_probability - implied_prob
        edge_percentage = edge / implied_prob

        # Calculate expected value
        if american_odds > 0:
            payout = american_odds / 100
        else:
            payout = 100 / abs(american_odds)

        expected_value = (true_probability * payout) - (1 - true_probability)

        # Determine if it's a value bet
        is_value_bet = edge_percentage > self.min_edge_threshold and expected_value > 0

        # Risk-reward ratio
        risk_reward_ratio = abs(payout) if expected_value > 0 else -abs(expected_value)

        # Generate recommendation
        if is_value_bet:
            if edge_percentage > 0.10:  # 10%+ edge
                recommendation = f"STRONG VALUE: {team} has {edge_percentage:.1%} edge"
            elif edge_percentage > 0.05:  # 5-10% edge
                recommendation = f"GOOD VALUE: {team} has {edge_percentage:.1%} edge"
            else:  # 2-5% edge
                recommendation = f"MARGINAL VALUE: {team} has {edge_percentage:.1%} edge"
        else:
            if edge_percentage < -self.min_edge_threshold:
                recommendation = f"AVOID: {team} is overvalued by {abs(edge_percentage):.1%}"
            else:
                recommendation = f"NEUTRAL: {team} is fairly priced"

        return ValueBetOpportunity(
            is_value_bet=is_value_bet,
            expected_value=expected_value,
            edge_percentage=edge_percentage,
            confidence_level=min(true_probability, 1 - true_probability) * 2,  # Conservative confidence
            bet_type="MONEYLINE",
            recommendation=recommendation,
            risk_reward_ratio=risk_reward_ratio
        )

    def _analyze_spread_value(
        self,
        prediction: BettingPrediction,
        spread: float,
        spread_odds: float,
        team: str,
        bankroll: float
    ) -> ValueBetOpportunity:
        """Analyze spread betting value"""
        # Calculate spread cover probability
        if team == 'HOME':
            margin_to_cover = -spread  # Home team needs to win by more than spread
            cover_prob = self._calculate_cover_probability(
                prediction.predicted_margin,
                prediction.confidence_interval,
                margin_to_cover
            )
        else:
            margin_to_cover = spread   # Away team needs to win or lose by less than spread
            cover_prob = 1 - self._calculate_cover_probability(
                prediction.predicted_margin,
                prediction.confidence_interval,
                -margin_to_cover
            )

        # Calculate implied probability from spread odds
        implied_prob = self._american_to_implied_probability(spread_odds)

        # Calculate edge and EV
        edge = cover_prob - implied_prob
        edge_percentage = edge / implied_prob

        # Expected value calculation
        if spread_odds > 0:
            payout = spread_odds / 100
        else:
            payout = 100 / abs(spread_odds)

        expected_value = (cover_prob * payout) - (1 - cover_prob)

        is_value_bet = edge_percentage > self.min_edge_threshold and expected_value > 0

        return ValueBetOpportunity(
            is_value_bet=is_value_bet,
            expected_value=expected_value,
            edge_percentage=edge_percentage,
            confidence_level=cover_prob,
            bet_type="SPREAD",
            recommendation=f"{'VALUE' if is_value_bet else 'NO VALUE'}: {team} cover {spread} ({edge_percentage:.1%} edge)",
            risk_reward_ratio=abs(payout) if expected_value > 0 else -abs(expected_value)
        )

    def _analyze_total_value(
        self,
        prediction: BettingPrediction,
        total_line: float,
        over_odds: float,
        bankroll: float
    ) -> ValueBetOpportunity:
        """Analyze over/under value bet"""
        # Predicted total (simplified - would normally use points prediction model)
        predicted_total = abs(prediction.predicted_margin) + 45  # Rough estimate
        # In practice, this would come from a separate points total model

        # Probability of going over
        # This is a simplified calculation - would use model confidence intervals
        over_prob = 0.5 + (predicted_total - total_line) / 20  # Rough scaling
        over_prob = max(0.1, min(0.9, over_prob))  # Clamp to reasonable range

        # Calculate implied probability
        implied_prob = self._american_to_implied_probability(over_odds)

        # Calculate edge and EV
        edge = over_prob - implied_prob
        edge_percentage = edge / implied_prob

        if over_odds > 0:
            payout = over_odds / 100
        else:
            payout = 100 / abs(over_odds)

        expected_value = (over_prob * payout) - (1 - over_prob)

        is_value_bet = edge_percentage > self.min_edge_threshold and expected_value > 0

        return ValueBetOpportunity(
            is_value_bet=is_value_bet,
            expected_value=expected_value,
            edge_percentage=edge_percentage,
            confidence_level=over_prob,
            bet_type="OVER_UNDER",
            recommendation=f"{'VALUE' if is_value_bet else 'NO VALUE'}: Over {total_line} ({edge_percentage:.1%} edge)",
            risk_reward_ratio=abs(payout) if expected_value > 0 else -abs(expected_value)
        )

    def _american_to_implied_probability(self, american_odds: float) -> float:
        """Convert American odds to implied probability (including vig)"""
        if american_odds > 0:
            return 100 / (american_odds + 100)
        else:
            return abs(american_odds) / (abs(american_odds) + 100)

    def _calculate_cover_probability(
        self,
        predicted_margin: float,
        confidence_interval: Tuple[float, float],
        margin_to_cover: float
    ) -> float:
        """
        Calculate probability of covering a given spread

        Args:
            predicted_margin: Predicted margin
            confidence_interval: (lower, upper) bounds
            margin_to_cover: Margin needed to cover the spread

        Returns:
            Probability of covering the spread
        """
        # Use normal distribution approximation
        std_dev = (confidence_interval[1] - confidence_interval[0]) / 4  # Rough std dev estimate

        # Z-score for margin to cover
        z_score = (predicted_margin - margin_to_cover) / std_dev

        # Probability using normal CDF
        cover_prob = 1 - stats.norm.cdf(z_score)

        return max(0.01, min(0.99, cover_prob))  # Clamp to reasonable range


class BettingAnalyticsEngine:
    """
    Main betting analytics engine that integrates with the existing Model Execution Engine
    following Script Ohio 2.0 patterns and BaseAgent framework.
    """

    def __init__(self, model_execution_engine=None):
        """
        Initialize betting analytics engine

        Args:
            model_execution_engine: Existing model execution engine instance
        """
        self.model_engine = model_execution_engine
        self.ci_calculator = ConfidenceIntervalCalculator()
        self.kelly_calculator = KellyCriterionCalculator()
        self.value_detector = ValueBetDetector()

        # Betting analytics state
        self.betting_history = []
        self.performance_metrics = {
            'total_bets_analyzed': 0,
            'value_bets_identified': 0,
            'average_edge': 0.0,
            'win_rate': 0.0,
            'roi': 0.0
        }

        logger.info("🎲 Betting Analytics Engine initialized with Kelly Criterion and Value Detection")

    def create_betting_prediction(
        self,
        model_prediction: Dict[str, Any],
        home_team: str,
        away_team: str
    ) -> BettingPrediction:
        """
        Convert model prediction to betting prediction with confidence intervals

        Args:
            model_prediction: Result from model execution engine
            home_team: Home team name
            away_team: Away team name

        Returns:
            BettingPrediction with confidence intervals and betting context
        """
        try:
            # Extract prediction data
            if model_prediction.get('model_type') == 'regression':
                # Margin prediction model
                predicted_margin = model_prediction.get('predicted_margin', 0)
                model_confidence = model_prediction.get('confidence', 0.5)

                # Convert margin to win probability
                home_win_prob = 1 / (1 + math.exp(-predicted_margin / 10))  # Logistic function
                away_win_prob = 1 - home_win_prob

            else:
                # Win probability model
                home_win_prob = model_prediction.get('home_win_probability', 0.5)
                away_win_prob = model_prediction.get('away_win_probability', 0.5)
                predicted_margin = (home_win_prob - away_win_prob) * 20  # Rough conversion
                model_confidence = model_prediction.get('confidence', 0.5)

            # Calculate confidence intervals
            margin_ci = self.ci_calculator.calculate_margin_ci(
                predicted_margin=predicted_margin,
                confidence_level=0.95,
                historical_mae=17.31,  # From model metadata
                sample_size=100
            )

            prob_ci = self.ci_calculator.calculate_probability_ci(
                predicted_probability=home_win_prob,
                confidence_level=0.95,
                historical_accuracy=0.431,  # From model metadata
                sample_size=100
            )

            # Market analysis (simplified - would integrate with real market data)
            market_analysis = {
                'market_efficiency': 'UNKNOWN',
                'line_movement': 'STABLE',
                'public_sentiment': 'NEUTRAL',
                'sharp_money': 'NEUTRAL'
            }

            return BettingPrediction(
                home_team=home_team,
                away_team=away_team,
                home_win_probability=home_win_prob,
                away_win_probability=away_win_prob,
                predicted_margin=predicted_margin,
                confidence_interval=margin_ci,
                prediction_confidence=model_confidence,
                model_confidence=model_confidence,
                market_analysis=market_analysis
            )

        except Exception as e:
            logger.error(f"Error creating betting prediction: {e}")
            raise

    def analyze_betting_opportunity(
        self,
        home_team: str,
        away_team: str,
        odds: BettingOdds,
        model_type: str = 'ridge_model_2025',
        features: Optional[Dict[str, Any]] = None,
        bankroll: float = 1000.0
    ) -> Dict[str, Any]:
        """
        Comprehensive betting opportunity analysis

        Args:
            home_team: Home team name
            away_team: Away team name
            odds: Current betting odds
            model_type: Which model to use for prediction
            features: Model input features
            bankroll: Available bankroll

        Returns:
            Complete betting analysis with Kelly Criterion and value detection
        """
        try:
            # Get model prediction
            if self.model_engine:
                prediction_request = {
                    'home_team': home_team,
                    'away_team': away_team,
                    'model_type': model_type,
                    'features': features or {},
                    'include_confidence': True,
                    'include_explanation': False
                }

                model_result = self.model_engine._predict_game_outcome(prediction_request, {})

                if not model_result['success']:
                    return {
                        'success': False,
                        'error_message': model_result.get('error_message', 'Model prediction failed'),
                        'analysis': {}
                    }

                model_prediction = model_result['prediction']
            else:
                # Fallback prediction
                model_prediction = {
                    'model_type': model_type,
                    'predicted_margin': 7.0,
                    'confidence': 0.6,
                    'home_win_probability': 0.65
                }

            # Create betting prediction
            betting_prediction = self.create_betting_prediction(
                model_prediction, home_team, away_team
            )

            # Analyze value betting opportunities
            value_opportunities = self.value_detector.identify_value_bets(
                betting_prediction, odds, bankroll
            )

            # Calculate Kelly Criterion for each opportunity
            kelly_recommendations = {}
            for bet_type, opportunity in value_opportunities.items():
                if opportunity.is_value_bet:
                    if 'MONEYLINE' in bet_type:
                        if 'HOME' in bet_type and odds.home_moneyline:
                            kelly_result = self.kelly_calculator.calculate_kelly_fraction(
                                implied_probability=betting_prediction.home_win_probability,
                                true_probability=betting_prediction.home_win_probability * (1 + opportunity.edge_percentage),
                                american_odds=odds.home_moneyline
                            )
                        elif 'AWAY' in bet_type and odds.away_moneyline:
                            kelly_result = self.kelly_calculator.calculate_kelly_fraction(
                                implied_probability=betting_prediction.away_win_probability,
                                true_probability=betting_prediction.away_win_probability * (1 + opportunity.edge_percentage),
                                american_odds=odds.away_moneyline
                            )
                    else:
                        # Simplified Kelly for other bet types
                        kelly_result = KellyCriterionResult(
                            kelly_fraction=0.05,  # Conservative 5% suggestion
                            suggested_bet_size=bankroll * 0.05,
                            expected_value=opportunity.expected_value,
                            growth_rate=opportunity.expected_value * 0.05,
                            risk_level="MEDIUM",
                            recommendation="Conservative Kelly Criterion applied"
                        )

                    kelly_recommendations[bet_type] = kelly_result

            # Update analytics
            self._update_betting_analytics(value_opportunities)

            # Compile comprehensive analysis
            analysis = {
                'success': True,
                'game_info': {
                    'home_team': home_team,
                    'away_team': away_team,
                    'model_used': model_type
                },
                'prediction': asdict(betting_prediction),
                'odds': asdict(odds),
                'value_opportunities': {k: asdict(v) for k, v in value_opportunities.items()},
                'kelly_recommendations': {k: asdict(v) for k, v in kelly_recommendations.items()},
                'summary': self._generate_betting_summary(betting_prediction, value_opportunities, kelly_recommendations),
                'risk_assessment': self._assess_betting_risk(betting_prediction, value_opportunities),
                'recommendations': self._generate_betting_recommendations(betting_prediction, value_opportunities, kelly_recommendations)
            }

            # Store in history
            self.betting_history.append({
                'timestamp': pd.Timestamp.now(),
                'home_team': home_team,
                'away_team': away_team,
                'analysis': analysis
            })

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing betting opportunity: {e}")
            return {
                'success': False,
                'error_message': f"Betting analysis failed: {str(e)}",
                'analysis': {}
            }

    def _update_betting_analytics(self, value_opportunities: Dict[str, ValueBetOpportunity]):
        """Update betting performance analytics"""
        self.performance_metrics['total_bets_analyzed'] += len(value_opportunities)
        value_bets = sum(1 for op in value_opportunities.values() if op.is_value_bet)
        self.performance_metrics['value_bets_identified'] += value_bets

        # Update running averages
        if value_opportunities:
            edges = [op.edge_percentage for op in value_opportunities.values() if op.edge_percentage > 0]
            if edges:
                current_avg = self.performance_metrics['average_edge']
                n = self.performance_metrics['total_bets_analyzed']
                new_avg = ((current_avg * (n - len(edges))) + sum(edges)) / n
                self.performance_metrics['average_edge'] = new_avg

    def _generate_betting_summary(
        self,
        prediction: BettingPrediction,
        opportunities: Dict[str, ValueBetOpportunity],
        kelly_recs: Dict[str, KellyCriterionResult]
    ) -> Dict[str, Any]:
        """Generate summary of betting analysis"""
        value_bets = [k for k, v in opportunities.items() if v.is_value_bet]
        best_edge = max(opportunities.values(), key=lambda x: x.edge_percentage)
        max_kelly = max(kelly_recs.values(), key=lambda x: x.kelly_fraction) if kelly_recs else None

        return {
            'total_opportunities': len(opportunities),
            'value_bets_found': len(value_bets),
            'best_edge_type': max(opportunities.keys(), key=lambda k: opportunities[k].edge_percentage),
            'best_edge_percentage': best_edge.edge_percentage,
            'max_kelly_fraction': max_kelly.kelly_fraction if max_kelly else 0,
            'predicted_winner': prediction.home_team if prediction.home_win_probability > 0.5 else prediction.away_team,
            'confidence_level': prediction.prediction_confidence,
            'market_analysis': prediction.market_analysis
        }

    def _assess_betting_risk(
        self,
        prediction: BettingPrediction,
        opportunities: Dict[str, ValueBetOpportunity]
    ) -> Dict[str, Any]:
        """Assess overall betting risk"""
        risk_factors = []
        risk_score = 0

        # Low model confidence
        if prediction.prediction_confidence < 0.6:
            risk_factors.append("Low model confidence increases prediction uncertainty")
            risk_score += 20

        # Wide confidence intervals
        margin_width = prediction.confidence_interval[1] - prediction.confidence_interval[0]
        if margin_width > 30:  # Very wide CI
            risk_factors.append("Wide prediction confidence interval indicates uncertainty")
            risk_score += 15

        # No value bets found
        value_bets = [op for op in opportunities.values() if op.is_value_bet]
        if not value_bets:
            risk_factors.append("No value betting opportunities identified")
            risk_score += 10

        # High negative edges
        negative_edges = [op.edge_percentage for op in opportunities.values() if op.edge_percentage < -0.05]
        if negative_edges:
            risk_factors.append(f"Market appears efficient or overvalued ({len(negative_edges)} bets)")
            risk_score += 10

        # Overall risk assessment
        if risk_score < 15:
            risk_level = "LOW"
            assessment = "Low risk - good value opportunities available"
        elif risk_score < 30:
            risk_level = "MEDIUM"
            assessment = "Moderate risk - some opportunities but exercise caution"
        elif risk_score < 50:
            risk_level = "HIGH"
            assessment = "High risk - limited value, consider waiting for better opportunities"
        else:
            risk_level = "VERY HIGH"
            assessment = "Very high risk - avoid betting on this game"

        return {
            'risk_level': risk_level,
            'risk_score': risk_score,
            'risk_factors': risk_factors,
            'assessment': assessment
        }

    def _generate_betting_recommendations(
        self,
        prediction: BettingPrediction,
        opportunities: Dict[str, ValueBetOpportunity],
        kelly_recs: Dict[str, KellyCriterionResult]
    ) -> List[str]:
        """Generate actionable betting recommendations"""
        recommendations = []

        # Value bet recommendations
        value_bets = [(k, v) for k, v in opportunities.items() if v.is_value_bet]
        if value_bets:
            best_bet = max(value_bets, key=lambda x: x[1].edge_percentage)
            recommendations.append(
                f"STRONGEST VALUE: {best_bet[0]} with {best_bet[1].edge_percentage:.1%} edge - {best_bet[1].recommendation}"
            )

            for bet_type, opportunity in value_bets:
                if bet_type != best_bet[0]:  # Don't repeat best bet
                    recommendations.append(f"Additional Value: {bet_type} ({opportunity.edge_percentage:.1%} edge)")

        # Kelly Criterion recommendations
        if kelly_recs:
            max_kelly = max(kelly_recs.values(), key=lambda x: x.kelly_fraction)
            if max_kelly.kelly_fraction > 0.01:
                recommendations.append(
                    f"Kelly Criterion: Bet ${max_kelly.suggested_bet_size:.2f} ({max_kelly.kelly_fraction:.1%} of bankroll)"
                )
                recommendations.append(f"Risk Level: {max_kelly.risk_level} - {max_kelly.recommendation}")

        # Model confidence recommendations
        if prediction.prediction_confidence > 0.7:
            recommendations.append("High model confidence - consider larger position sizing")
        elif prediction.prediction_confidence < 0.5:
            recommendations.append("Low model confidence - consider smaller bets or skip")

        # Market efficiency recommendations
        if len(value_bets) == 0:
            recommendations.append("Market appears efficient - consider waiting for line movement")
        elif len(value_bets) >= 3:
            recommendations.append("Multiple value opportunities - diversify across bet types")

        # Risk management recommendations
        recommendations.append("Never bet more than 25% of bankroll on a single game")
        recommendations.append("Consider fractional Kelly (50-75%) for conservative approach")

        return recommendations

    def get_betting_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive betting performance report"""
        if not self.betting_history:
            return {
                'success': False,
                'message': 'No betting history available'
            }

        # Calculate performance metrics
        total_analyses = len(self.betting_history)
        recent_analyses = self.betting_history[-10:]  # Last 10 analyses

        return {
            'success': True,
            'total_analyses': total_analyses,
            'performance_metrics': self.performance_metrics,
            'recent_trends': {
                'recent_value_bets': sum(1 for analysis in recent_analyses
                                     if analysis['analysis']['summary']['value_bets_found'] > 0),
                'average_recent_edge': np.mean([
                    analysis['analysis']['summary']['best_edge_percentage']
                    for analysis in recent_analyses
                ]) if recent_analyses else 0
            },
            'recommendations': self._generate_performance_recommendations()
        }

    def _generate_performance_recommendations(self) -> List[str]:
        """Generate performance improvement recommendations"""
        recommendations = []

        if self.performance_metrics['average_edge'] < 0.02:
            recommendations.append("Consider refining models to increase edge detection")
        elif self.performance_metrics['average_edge'] > 0.08:
            recommendations.append("Excellent edge detection - consider increasing bet sizes appropriately")

        value_rate = (self.performance_metrics['value_bets_identified'] /
                     max(self.performance_metrics['total_bets_analyzed'], 1))
        if value_rate < 0.2:
            recommendations.append("Low value bet rate - wait for better opportunities or improve models")
        elif value_rate > 0.5:
            recommendations.append("Good value bet rate - system working effectively")

        recommendations.append("Track actual betting results to validate predictions")
        recommendations.append("Monitor model performance and adjust as needed")
        recommendations.append("Consider market timing for optimal odds")

        return recommendations


# Factory function for easy integration
def create_betting_analytics_engine(model_execution_engine=None) -> BettingAnalyticsEngine:
    """
    Factory function to create betting analytics engine with optimal configuration

    Args:
        model_execution_engine: Existing model execution engine instance

    Returns:
        BettingAnalyticsEngine: Configured betting analytics engine
    """
    return BettingAnalyticsEngine(model_execution_engine)


# Quick test function
def test_betting_integration():
    """Test betting integration functionality"""
    try:
        logger.info("🧪 Testing Betting Integration")

        # Create engine
        engine = create_betting_analytics_engine()
        logger.info("✅ Betting analytics engine created")

        # Test with sample data
        sample_prediction = {
            'model_type': 'regression',
            'predicted_margin': 7.5,
            'confidence': 0.7,
            'home_win_probability': 0.68
        }

        # Get sample teams from data
        from src.utils.data import get_sample_matchup
        sample_home, sample_away = get_sample_matchup()
        betting_prediction = engine.create_betting_prediction(
            sample_prediction, sample_home, sample_away
        )
        logger.info(f"✅ Betting prediction created: {betting_prediction.home_team} {betting_prediction.home_win_probability:.1%}")

        # Test Kelly Criterion
        kelly = engine.kelly_calculator.calculate_kelly_fraction(
            implied_probability=0.45,
            true_probability=0.55,
            american_odds=-110
        )
        logger.info(f"✅ Kelly Criterion: {kelly.kelly_fraction:.1%} bankroll, {kelly.recommendation}")

        # Test Value Detection
        odds = BettingOdds(
            home_moneyline=-150,
            away_moneyline=130,
            home_spread=-7.0,
            home_spread_odds=-110
        )

        opportunities = engine.value_detector.identify_value_bets(
            betting_prediction, odds, 1000
        )
        logger.info(f"✅ Value bets found: {len([o for o in opportunities.values() if o.is_value_bet])}")

        return True

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False


if __name__ == "__main__":
    # Run test
    success = test_betting_integration()
    if success:
        print("🎉 Betting Integration test successful!")
    else:
        print("❌ Betting Integration test failed!")