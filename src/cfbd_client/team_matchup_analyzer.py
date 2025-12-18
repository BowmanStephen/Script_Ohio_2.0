"""
Team Matchup Historical Analyzer
Provides comprehensive historical team matchup analysis and predictive insights
"""

import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import pandas as pd

from .enhanced_unified_client import EnhancedUnifiedCFBDClient

logger = logging.getLogger(__name__)

@dataclass
class HistoricalMatchup:
    """Represents a historical game between two teams"""
    date: str
    season: int
    week: Optional[int]
    home_team: str
    away_team: str
    neutral_site: bool
    home_score: int
    away_score: int
    winner: str
    margin: int
    venue: str
    attendance: Optional[int]

@dataclass
class MatchupStatistics:
    """Statistical summary of team matchups"""
    total_games: int
    team1_wins: int
    team2_wins: int
    ties: int
    team1_win_pct: float
    team2_win_pct: float
    avg_points_team1: float
    avg_points_team2: float
    avg_margin: float
    home_advantage_wins: int
    neutral_site_games: int
    recent_trend: List[str]  # Last 10 games results
    longest_streak: Dict[str, Any]
    biggest_win: Dict[str, Any]
    biggest_loss: Dict[str, Any]

@dataclass
class MatchupPrediction:
    """Predictive analysis for upcoming matchup"""
    team1: str
    team2: str
    predicted_winner: str
    confidence: float
    predicted_margin: int
    prediction_factors: Dict[str, Any]
    historical_advantage: str
    key_trends: List[str]
    similar_matchups: List[Dict[str, Any]]

class TeamMatchupAnalyzer:
    """
    Analyzes historical team matchups and provides predictive insights
    """

    def __init__(self, config=None):
        """Initialize matchup analyzer"""
        self.client = EnhancedUnifiedCFBDClient(config)
        self.matchup_cache: Dict[str, Tuple[List[HistoricalMatchup], MatchupStatistics]] = {}

    def get_historical_matchups(self, team1: str, team2: str, limit_years: int = 20) -> List[HistoricalMatchup]:
        """
        Get historical matchups between two teams

        Args:
            team1: First team name
            team2: Second team name
            limit_years: Number of years to look back (default 20)

        Returns:
            List of HistoricalMatchup objects
        """
        cache_key = f"{team1.lower()}_{team2.lower()}_{limit_years}"
        if cache_key in self.matchup_cache:
            logger.debug(f"📦 Retrieved historical matchups from cache for {team1} vs {team2}")
            return self.matchup_cache[cache_key][0]

        try:
            logger.info(f"🔍 Analyzing historical matchups: {team1} vs {team2}")

            # Get matchups from CFBD API
            matchups_data = self.client.get_team_matchup(team1, team2)

            if not matchups_data:
                logger.warning(f"No historical matchups found between {team1} and {team2}")
                return []

            # Process matchup data
            current_year = datetime.now().year
            cutoff_year = current_year - limit_years

            historical_matchups = []
            for game in matchups_data:
                try:
                    season = game.get('season', 0)
                    if season < cutoff_year:
                        continue  # Skip games outside our time window

                    matchup = HistoricalMatchup(
                        date=game.get('start_date', ''),
                        season=season,
                        week=game.get('week'),
                        home_team=game.get('home_team', ''),
                        away_team=game.get('away_team', ''),
                        neutral_site=game.get('neutral_site', False),
                        home_score=game.get('home_points', 0) or 0,
                        away_score=game.get('away_points', 0) or 0,
                        winner=self._determine_winner(game),
                        margin=abs((game.get('home_points', 0) or 0) - (game.get('away_points', 0) or 0)),
                        venue=game.get('venue', ''),
                        attendance=game.get('attendance')
                    )

                    historical_matchups.append(matchup)

                except Exception as e:
                    logger.warning(f"Error processing matchup game: {e}")
                    continue

            # Sort by date (most recent first)
            historical_matchups.sort(key=lambda x: x.date, reverse=True)

            logger.info(f"📊 Found {len(historical_matchups)} historical matchups")
            return historical_matchups

        except Exception as e:
            logger.error(f"❌ Error getting historical matchups: {e}")
            return []

    def analyze_matchup_statistics(self, team1: str, team2: str, limit_years: int = 20) -> MatchupStatistics:
        """
        Analyze comprehensive statistics for team matchups

        Args:
            team1: First team name
            team2: Second team name
            limit_years: Number of years to analyze

        Returns:
            MatchupStatistics object with comprehensive analysis
        """
        cache_key = f"{team1.lower()}_{team2.lower()}_{limit_years}"
        if cache_key in self.matchup_cache:
            return self.matchup_cache[cache_key][1]

        # Get historical matchups
        matchups = self.get_historical_matchups(team1, team2, limit_years)

        if not matchups:
            return MatchupStatistics(
                total_games=0, team1_wins=0, team2_wins=0, ties=0,
                team1_win_pct=0.0, team2_win_pct=0.0,
                avg_points_team1=0.0, avg_points_team2=0.0,
                avg_margin=0.0, home_advantage_wins=0,
                neutral_site_games=0, recent_trend=[],
                longest_streak={}, biggest_win={}, biggest_loss={}
            )

        # Calculate basic statistics
        total_games = len(matchups)
        team1_wins = sum(1 for m in matchups if m.winner == team1)
        team2_wins = sum(1 for m in matchups if m.winner == team2)
        ties = total_games - team1_wins - team2_wins

        team1_win_pct = (team1_wins / total_games * 100) if total_games > 0 else 0
        team2_win_pct = (team2_wins / total_games * 100) if total_games > 0 else 0

        # Calculate average scores
        team1_scores = []
        team2_scores = []
        for matchup in matchups:
            if matchup.home_team == team1:
                team1_scores.append(matchup.home_score)
                team2_scores.append(matchup.away_score)
            else:
                team1_scores.append(matchup.away_score)
                team2_scores.append(matchup.home_score)

        avg_points_team1 = sum(team1_scores) / len(team1_scores) if team1_scores else 0
        avg_points_team2 = sum(team2_scores) / len(team2_scores) if team2_scores else 0
        avg_margin = sum(m.margin for m in matchups) / total_games

        # Home advantage analysis
        home_advantage_wins = 0
        neutral_site_games = 0
        for matchup in matchups:
            if matchup.neutral_site:
                neutral_site_games += 1
            elif matchup.home_team == matchup.winner:
                home_advantage_wins += 1

        # Recent trend (last 10 games)
        recent_games = matchups[:10]
        recent_trend = []
        for game in recent_games:
            if game.winner == team1:
                recent_trend.append(f"{team1} {game.home_score if game.home_team == team1 else game.away_score}-{game.away_score if game.home_team == team1 else game.home_score} {team2}")
            else:
                recent_trend.append(f"{team2} {game.away_score if game.home_team == team1 else game.home_score}-{game.home_score if game.home_team == team1 else game.away_score} {team1}")

        # Find longest winning streak
        longest_streak = self._find_longest_streak(matchups, team1, team2)

        # Find biggest wins and losses
        biggest_win = self._find_biggest_win(matchups, team1, team2)
        biggest_loss = self._find_biggest_loss(matchups, team1, team2)

        stats = MatchupStatistics(
            total_games=total_games,
            team1_wins=team1_wins,
            team2_wins=team2_wins,
            ties=ties,
            team1_win_pct=team1_win_pct,
            team2_win_pct=team2_win_pct,
            avg_points_team1=avg_points_team1,
            avg_points_team2=avg_points_team2,
            avg_margin=avg_margin,
            home_advantage_wins=home_advantage_wins,
            neutral_site_games=neutral_site_games,
            recent_trend=recent_trend,
            longest_streak=longest_streak,
            biggest_win=biggest_win,
            biggest_loss=biggest_loss
        )

        # Cache the results
        self.matchup_cache[cache_key] = (matchups, stats)

        return stats

    def predict_matchup_outcome(self, team1: str, team2: str, current_form: Optional[Dict[str, float]] = None) -> MatchupPrediction:
        """
        Predict outcome of upcoming matchup based on historical data

        Args:
            team1: First team name
            team2: Second team name
            current_form: Optional current season performance metrics

        Returns:
            MatchupPrediction with prediction and confidence
        """
        # Get historical statistics
        stats = self.analyze_matchup_statistics(team1, team2)

        if stats.total_games == 0:
            # No historical data - return neutral prediction
            return MatchupPrediction(
                team1=team1,
                team2=team2,
                predicted_winner="No historical data",
                confidence=0.0,
                predicted_margin=0,
                prediction_factors={},
                historical_advantage="None",
                key_trends=["No historical matchups available"],
                similar_matchups=[]
            )

        # Base prediction on historical win percentages
        team1_base_prob = stats.team1_win_pct / 100
        team2_base_prob = stats.team2_win_pct / 100

        # Adjust for recent form if provided
        if current_form:
            team1_form = current_form.get(team1, 0.5)  # 0.0 to 1.0 scale
            team2_form = current_form.get(team2, 0.5)

            # Weight historical (60%) and current form (40%)
            team1_prob = team1_base_prob * 0.6 + team1_form * 0.4
            team2_prob = team2_base_prob * 0.6 + team2_form * 0.4
        else:
            team1_prob = team1_base_prob
            team2_prob = team2_base_prob

        # Determine winner and confidence
        if team1_prob > team2_prob:
            predicted_winner = team1
            confidence = team1_prob
        elif team2_prob > team1_prob:
            predicted_winner = team2
            confidence = team2_prob
        else:
            predicted_winner = "Toss-up"
            confidence = 0.5

        # Predict margin based on historical averages
        predicted_margin = round(abs(stats.avg_points_team1 - stats.avg_points_team2))

        # Identify prediction factors
        prediction_factors = {
            'historical_win_pct': f"{stats.team1_win_pct:.1f}% vs {stats.team2_win_pct:.1f}%",
            'avg_points_diff': f"{abs(stats.avg_points_team1 - stats.avg_points_team2):.1f} points",
            'home_advantage': f"{stats.home_advantage_wins} home wins" if stats.home_advantage_wins > 0 else "No home advantage data",
            'recent_form': "Considered" if current_form else "Not available"
        }

        # Determine historical advantage
        if stats.team1_win_pct > 60:
            historical_advantage = f"{team1} dominates historically ({stats.team1_win_pct:.1f}%)"
        elif stats.team2_win_pct > 60:
            historical_advantage = f"{team2} dominates historically ({stats.team2_win_pct:.1f}%)"
        elif stats.team1_win_pct > 50:
            historical_advantage = f"{team1} has slight historical edge ({stats.team1_win_pct:.1f}%)"
        elif stats.team2_win_pct > 50:
            historical_advantage = f"{team2} has slight historical edge ({stats.team2_win_pct:.1f}%)"
        else:
            historical_advantage = "Evenly matched historically"

        # Identify key trends
        key_trends = [
            f"{stats.total_games} total meetings since {datetime.now().year - 20}",
            f"Average margin: {stats.avg_margin:.1f} points",
            f"Home team wins: {stats.home_advantage_wins}/{stats.total_games - stats.neutral_site_games}"
        ]

        if stats.longest_streak:
            key_trends.append(f"Longest streak: {stats.longest_streak['team']} ({stats.longest_streak['length']} games)")

        # Find similar historical matchups
        similar_matchups = self._find_similar_matchups(team1, team2, stats)

        return MatchupPrediction(
            team1=team1,
            team2=team2,
            predicted_winner=predicted_winner,
            confidence=confidence,
            predicted_margin=predicted_margin,
            prediction_factors=prediction_factors,
            historical_advantage=historical_advantage,
            key_trends=key_trends,
            similar_matchups=similar_matchups
        )

    def _determine_winner(self, game: Dict[str, Any]) -> str:
        """Determine winner from game data"""
        home_score = game.get('home_points', 0) or 0
        away_score = game.get('away_points', 0) or 0
        home_team = game.get('home_team', '')

        if home_score > away_score:
            return home_team
        elif away_score > home_score:
            return game.get('away_team', '')
        else:
            return "Tie"

    def _find_longest_streak(self, matchups: List[HistoricalMatchup], team1: str, team2: str) -> Dict[str, Any]:
        """Find longest winning streak in the series"""
        if not matchups:
            return {}

        longest_streak = {'team': '', 'length': 0, 'start_year': 0, 'end_year': 0}
        current_streak = {'team': '', 'length': 0, 'start_year': 0}

        for matchup in matchups:
            winner = matchup.winner

            if winner == current_streak['team']:
                current_streak['length'] += 1
            else:
                # Streak ended, check if it was the longest
                if current_streak['length'] > longest_streak['length']:
                    longest_streak = current_streak.copy()

                # Start new streak
                current_streak = {'team': winner, 'length': 1, 'start_year': matchup.season}

            if current_streak['length'] == 1:
                current_streak['start_year'] = matchup.season

        # Check final streak
        if current_streak['length'] > longest_streak['length']:
            longest_streak = current_streak.copy()

        if longest_streak['team']:
            longest_streak['end_year'] = longest_streak['start_year'] + longest_streak['length'] - 1

        return longest_streak

    def _find_biggest_win(self, matchups: List[HistoricalMatchup], team1: str, team2: str) -> Dict[str, Any]:
        """Find biggest win for team1"""
        biggest_win = {'margin': 0, 'date': '', 'score': '', 'opponent': team2}

        for matchup in matchups:
            if matchup.winner == team1 and matchup.margin > biggest_win['margin']:
                biggest_win = {
                    'margin': matchup.margin,
                    'date': matchup.date,
                    'score': f"{matchup.home_score}-{matchup.away_score}",
                    'opponent': team2,
                    'season': matchup.season
                }

        return biggest_win

    def _find_biggest_loss(self, matchups: List[HistoricalMatchup], team1: str, team2: str) -> Dict[str, Any]:
        """Find biggest loss for team1"""
        biggest_loss = {'margin': 0, 'date': '', 'score': '', 'opponent': team2}

        for matchup in matchups:
            if matchup.winner == team2 and matchup.margin > biggest_loss['margin']:
                biggest_loss = {
                    'margin': matchup.margin,
                    'date': matchup.date,
                    'score': f"{matchup.home_score}-{matchup.away_score}",
                    'opponent': team2,
                    'season': matchup.season
                }

        return biggest_loss

    def _find_similar_matchups(self, team1: str, team2: str, stats: MatchupStatistics) -> List[Dict[str, Any]]:
        """Find similar historical matchups based on scoring patterns"""
        similar = []

        # Look for games with similar margins to the average
        avg_margin = stats.avg_margin
        tolerance = 7  # +/- 7 points

        # This would search through actual historical data
        # For now, provide placeholder similar matchups
        if stats.total_games > 0:
            similar.append({
                'description': f"Close games (margin < 10)",
                'count': len([m for m in self.get_historical_matchups(team1, team2) if m.margin < 10]),
                'record': "Varies by team"
            })
            similar.append({
                'description': f"High-scoring games (>60 total points)",
                'count': len([m for m in self.get_historical_matchups(team1, team2) if (m.home_score + m.away_score) > 60]),
                'record': "Varies by team"
            })

        return similar

    def get_rivalry_analysis(self, team1: str, team2: str) -> Dict[str, Any]:
        """Comprehensive rivalry analysis"""
        stats = self.analyze_matchup_statistics(team1, team2, limit_years=30)  # 30-year window for rivalries

        rivalry_score = 0
        rivalry_factors = []

        # Calculate rivalry score (0-100)
        if stats.total_games >= 20:
            rivalry_score += 30  # Frequent meetings
            rivalry_factors.append("Frequent historical meetings")
        elif stats.total_games >= 10:
            rivalry_score += 15
            rivalry_factors.append("Regular historical meetings")

        # Competitive balance
        win_diff = abs(stats.team1_win_pct - stats.team2_win_pct)
        if win_diff < 10:
            rivalry_score += 25  # Very competitive
            rivalry_factors.append("Highly competitive series")
        elif win_diff < 20:
            rivalry_score += 15
            rivalry_factors.append("Competitive series")

        # Close games
        if stats.avg_margin < 10:
            rivalry_score += 20
            rivalry_factors.append("Historically close games")
        elif stats.avg_margin < 15:
            rivalry_score += 10
            rivalry_factors.append("Moderately close games")

        # Recent streaks
        if stats.longest_streak and stats.longest_streak['length'] >= 5:
            rivalry_score += 15
            rivalry_factors.append("Significant winning streaks")

        # Big games/championships
        # This would check for conference championships, bowl games, etc.

        rivalry_level = "Intense Rivalry" if rivalry_score >= 70 else \
                      "Strong Rivalry" if rivalry_score >= 50 else \
                      "Historical Matchup" if rivalry_score >= 30 else \
                      "Occasional Matchup"

        return {
            'rivalry_score': rivalry_score,
            'rivalry_level': rivalry_level,
            'rivalry_factors': rivalry_factors,
            'total_meetings': stats.total_games,
            'competitive_balance': f"{abs(stats.team1_win_pct - stats.team2_win_pct):.1f}% win rate difference",
            'avg_margin': stats.avg_margin,
            'notable_games': {
                'biggest_win': stats.biggest_win,
                'biggest_loss': stats.biggest_loss,
                'longest_streak': stats.longest_streak
            }
        }

    def export_matchup_analysis_to_dataframe(self, matchup_pairs: List[Tuple[str, str]]) -> pd.DataFrame:
        """Export multiple matchup analyses to DataFrame"""
        data = []

        for team1, team2 in matchup_pairs:
            try:
                stats = self.analyze_matchup_statistics(team1, team2)
                rivalry = self.get_rivalry_analysis(team1, team2)

                row = {
                    'team1': team1,
                    'team2': team2,
                    'total_games': stats.total_games,
                    'team1_win_pct': stats.team1_win_pct,
                    'team2_win_pct': stats.team2_win_pct,
                    'avg_points_team1': stats.avg_points_team1,
                    'avg_points_team2': stats.avg_points_team2,
                    'avg_margin': stats.avg_margin,
                    'rivalry_score': rivalry['rivalry_score'],
                    'rivalry_level': rivalry['rivalry_level']
                }
                data.append(row)

                # Small delay to respect rate limits
                time.sleep(0.2)

            except Exception as e:
                logger.error(f"Error analyzing {team1} vs {team2}: {e}")
                continue

        return pd.DataFrame(data)

# Example usage
def demo_matchup_analyzer():
    """Demonstration of matchup analyzer functionality"""
    print("🏈 Team Matchup Analyzer Demo")
    print("=" * 35)

    analyzer = TeamMatchupAnalyzer()

    # Example matchups
    matchups = [
        ("Alabama", "Georgia"),
        ("Ohio State", "Michigan"),
        ("USC", "UCLA"),
        ("Texas", "Oklahoma")
    ]

    for team1, team2 in matchups:
        print(f"\n📊 {team1} vs {team2}")
        print("-" * (len(team1) + len(team2) + 5))

        try:
            # Get historical statistics
            stats = analyzer.analyze_matchup_statistics(team1, team2)
            print(f"   Total Games: {stats.total_games}")
            print(f"   {team1} Win %: {stats.team1_win_pct:.1f}%")
            print(f"   {team2} Win %: {stats.team2_win_pct:.1f}%")
            print(f"   Average Margin: {stats.avg_margin:.1f} points")

            # Get rivalry analysis
            rivalry = analyzer.get_rivalry_analysis(team1, team2)
            print(f"   Rivalry Level: {rivalry['rivalry_level']} ({rivalry['rivalry_score']}/100)")

            # Get prediction
            prediction = analyzer.predict_matchup_outcome(team1, team2)
            print(f"   Predicted Winner: {prediction.predicted_winner}")
            print(f"   Confidence: {prediction.confidence:.1%}")

        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    demo_matchup_analyzer()