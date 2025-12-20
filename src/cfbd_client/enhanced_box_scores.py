"""
Enhanced Box Scores System
Provides comprehensive game performance metrics and detailed analytics
"""

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from .enhanced_unified_client import EnhancedUnifiedCFBDClient

logger = logging.getLogger(__name__)


@dataclass
class TeamBoxScore:
    """Comprehensive team box score metrics"""

    team: str
    final_score: int
    quarters: List[int]  # Score by quarter
    first_downs: int
    third_down_eff: str  # "X-Y" format
    fourth_down_eff: str
    total_yards: int
    passing_yards: int
    rushing_yards: int
    penalties: int
    penalty_yards: int
    turnovers: int
    time_of_possession: str
    sacks: int
    sack_yards: int
    fumbles: int
    interceptions: int
    red_zone_eff: str


@dataclass
class PlayerStats:
    """Individual player performance statistics"""

    player_name: str
    position: str
    team: str
    attempts: int
    completions: int
    passing_yards: int
    passing_touchdowns: int
    interceptions: int
    carries: int
    rushing_yards: int
    rushing_touchdowns: int
    receptions: int
    receiving_yards: int
    receiving_touchdowns: int
    tackles: int
    sacks: int
    tackles_for_loss: int
    passes_defended: int
    interceptions_defended: int


@dataclass
class EnhancedGameBoxScore:
    """Complete game box score with advanced metrics"""

    game_id: int
    date: str
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    venue: str
    attendance: Optional[int]
    duration: Optional[str]
    weather: Optional[Dict[str, Any]]
    home_box_score: TeamBoxScore
    away_box_score: TeamBoxScore
    player_stats: List[PlayerStats]
    advanced_metrics: Dict[str, Any]
    momentum_shifts: List[Dict[str, Any]]
    key_drives: List[Dict[str, Any]]


class EnhancedBoxScoreClient:
    """
    Client for enhanced box scores and detailed game analytics
    """

    def __init__(self, config=None):
        """Initialize enhanced box score client"""
        self.client = EnhancedUnifiedCFBDClient(config)
        self.game_cache: Dict[int, EnhancedGameBoxScore] = {}

    def get_enhanced_box_score(self, game_id: int) -> Optional[EnhancedGameBoxScore]:
        """
        Get comprehensive box score for a specific game

        Args:
            game_id: CFBD game ID

        Returns:
            EnhancedGameBoxScore with complete game statistics
        """
        try:
            # Check cache first
            if game_id in self.game_cache:
                logger.debug(f"📦 Retrieved enhanced box score {game_id} from cache")
                return self.game_cache[game_id]

            # Get basic box score from CFBD
            basic_box_score = self.client.get_game_box_score(game_id)
            if not basic_box_score:
                logger.warning(f"No box score found for game {game_id}")
                return None

            # Get additional game details
            game_details = self._get_game_details(game_id)
            if not game_details:
                logger.warning(f"No game details found for game {game_id}")
                return None

            # Build enhanced box score
            enhanced_box = self._build_enhanced_box_score(basic_box_score, game_details)

            # Cache the result
            self.game_cache[game_id] = enhanced_box

            logger.info(f"📊 Generated enhanced box score for game {game_id}")
            return enhanced_box

        except Exception as e:
            logger.error(f"❌ Error getting enhanced box score for game {game_id}: {e}")
            return None

    def _get_game_details(self, game_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed game information"""
        try:
            # Get all games and find the specific one
            # In production, this would be optimized with direct API calls
            games = self.client.get_games(year=2025)
            for game in games:
                if game.get("id") == game_id:
                    return game
            return None
        except Exception as e:
            logger.error(f"Error getting game details for {game_id}: {e}")
            return None

    def _build_enhanced_box_score(
        self, basic_box: Dict[str, Any], game_details: Dict[str, Any]
    ) -> EnhancedGameBoxScore:
        """Build enhanced box score from basic data and game details"""

        # Extract team information
        home_team = game_details.get("home_team", "")
        away_team = game_details.get("away_team", "")

        # Build team box scores (simulated data - would come from actual API)
        home_stats = basic_box.get("home_team", {})
        away_stats = basic_box.get("away_team", {})

        home_box_score = TeamBoxScore(
            team=home_team,
            final_score=game_details.get("home_points", 0) or 0,
            quarters=self._extract_quarter_scores(basic_box, "home"),
            first_downs=home_stats.get("first_downs", 0),
            third_down_eff=f"{home_stats.get('third_down_conversions', 0)}-{home_stats.get('third_down_attempts', 0)}",
            fourth_down_eff=f"{home_stats.get('fourth_down_conversions', 0)}-{home_stats.get('fourth_down_attempts', 0)}",
            total_yards=home_stats.get("total_yards", 0),
            passing_yards=home_stats.get("passing_yards", 0),
            rushing_yards=home_stats.get("rushing_yards", 0),
            penalties=home_stats.get("penalties", 0),
            penalty_yards=home_stats.get("penalty_yards", 0),
            turnovers=home_stats.get("turnovers", 0),
            time_of_possession=home_stats.get("time_of_possession", "00:00"),
            sacks=home_stats.get("sacks", 0),
            sack_yards=home_stats.get("sack_yards", 0),
            fumbles=home_stats.get("fumbles", 0),
            interceptions=home_stats.get("interceptions", 0),
            red_zone_eff=f"{home_stats.get('red_zone_conversions', 0)}-{home_stats.get('red_zone_attempts', 0)}",
        )

        away_box_score = TeamBoxScore(
            team=away_team,
            final_score=game_details.get("away_points", 0) or 0,
            quarters=self._extract_quarter_scores(basic_box, "away"),
            first_downs=away_stats.get("first_downs", 0),
            third_down_eff=f"{away_stats.get('third_down_conversions', 0)}-{away_stats.get('third_down_attempts', 0)}",
            fourth_down_eff=f"{away_stats.get('fourth_down_conversions', 0)}-{away_stats.get('fourth_down_attempts', 0)}",
            total_yards=away_stats.get("total_yards", 0),
            passing_yards=away_stats.get("passing_yards", 0),
            rushing_yards=away_stats.get("rushing_yards", 0),
            penalties=away_stats.get("penalties", 0),
            penalty_yards=away_stats.get("penalty_yards", 0),
            turnovers=away_stats.get("turnovers", 0),
            time_of_possession=away_stats.get("time_of_possession", "00:00"),
            sacks=away_stats.get("sacks", 0),
            sack_yards=away_stats.get("sack_yards", 0),
            fumbles=away_stats.get("fumbles", 0),
            interceptions=away_stats.get("interceptions", 0),
            red_zone_eff=f"{away_stats.get('red_zone_conversions', 0)}-{away_stats.get('red_zone_attempts', 0)}",
        )

        # Generate player stats (simulated)
        player_stats = self._generate_player_stats(home_team, away_team, basic_box)

        # Calculate advanced metrics
        advanced_metrics = self._calculate_advanced_metrics(
            home_box_score, away_box_score, player_stats
        )

        # Generate momentum shifts (simulated)
        momentum_shifts = self._analyze_momentum_shifts(basic_box, home_team, away_team)

        # Identify key drives (simulated)
        key_drives = self._identify_key_drives(basic_box, home_team, away_team)

        return EnhancedGameBoxScore(
            game_id=game_details.get("id", 0),
            date=game_details.get("start_date", ""),
            home_team=home_team,
            away_team=away_team,
            home_score=home_box_score.final_score,
            away_score=away_box_score.final_score,
            venue=game_details.get("venue", ""),
            attendance=game_details.get("attendance"),
            duration=game_details.get("duration"),
            weather=game_details.get("weather"),
            home_box_score=home_box_score,
            away_box_score=away_box_score,
            player_stats=player_stats,
            advanced_metrics=advanced_metrics,
            momentum_shifts=momentum_shifts,
            key_drives=key_drives,
        )

    def _extract_quarter_scores(
        self, basic_box: Dict[str, Any], team: str
    ) -> List[int]:
        """Extract quarterly scoring"""
        # This would extract actual quarter scores from the box score data
        # For now, return placeholder data
        return [0, 0, 0, 0]

    def _generate_player_stats(
        self, home_team: str, away_team: str, basic_box: Dict[str, Any]
    ) -> List[PlayerStats]:
        """Generate player statistics from box score data"""
        player_stats = []

        # This would extract actual player stats from CFBD API
        # For now, generate sample data
        sample_players = [
            # Home team players
            PlayerStats(
                player_name="QB Home",
                position="QB",
                team=home_team,
                attempts=25,
                completions=18,
                passing_yards=245,
                passing_touchdowns=2,
                interceptions=1,
                carries=5,
                rushing_yards=23,
                rushing_touchdowns=0,
                receptions=0,
                receiving_yards=0,
                receiving_touchdowns=0,
                tackles=0,
                sacks=0,
                tackles_for_loss=0,
                passes_defended=0,
                interceptions_defended=0,
            ),
            PlayerStats(
                player_name="RB Home",
                position="RB",
                team=home_team,
                attempts=0,
                completions=0,
                passing_yards=0,
                passing_touchdowns=0,
                interceptions=0,
                carries=18,
                rushing_yards=87,
                rushing_touchdowns=1,
                receptions=3,
                receiving_yards=45,
                receiving_touchdowns=0,
                tackles=2,
                sacks=0,
                tackles_for_loss=0,
                passes_defended=0,
                interceptions_defended=0,
            ),
            # Away team players
            PlayerStats(
                player_name="QB Away",
                position="QB",
                team=away_team,
                attempts=32,
                completions=21,
                passing_yards=287,
                passing_touchdowns=3,
                interceptions=0,
                carries=3,
                rushing_yards=12,
                rushing_touchdowns=0,
                receptions=0,
                receiving_yards=0,
                receiving_touchdowns=0,
                tackles=0,
                sacks=0,
                tackles_for_loss=0,
                passes_defended=0,
                interceptions_defended=0,
            ),
        ]

        player_stats.extend(sample_players)
        return player_stats

    def _calculate_advanced_metrics(
        self,
        home_box: TeamBoxScore,
        away_box: TeamBoxScore,
        player_stats: List[PlayerStats],
    ) -> Dict[str, Any]:
        """Calculate advanced performance metrics"""

        # Calculate team efficiency metrics
        home_efficiency = self._calculate_team_efficiency(home_box)
        away_efficiency = self._calculate_team_efficiency(away_box)

        # Calculate player performance ratings
        player_ratings = self._calculate_player_ratings(player_stats)

        # Calculate game statistics
        total_plays = self._estimate_total_plays(home_box, away_box)
        yards_per_play = (
            (home_box.total_yards + away_box.total_yards) / total_plays
            if total_plays > 0
            else 0
        )

        return {
            "home_efficiency": home_efficiency,
            "away_efficiency": away_efficiency,
            "player_ratings": player_ratings,
            "game_pace": {
                "total_plays": total_plays,
                "yards_per_play": round(yards_per_play, 1),
                "scoring_drives": self._count_scoring_drives(home_box, away_box),
            },
            "explosive_plays": self._calculate_explosive_plays(player_stats),
            "turnover_battle": {
                "home_turnovers": home_box.turnovers,
                "away_turnovers": away_box.turnovers,
                "turnover_margin": home_box.turnovers - away_box.turnovers,
            },
        }

    def _calculate_team_efficiency(self, box_score: TeamBoxScore) -> Dict[str, float]:
        """Calculate team efficiency metrics"""
        return {
            "yards_per_point": box_score.total_yards / max(box_score.final_score, 1),
            "third_down_pct": self._parse_efficiency_pct(box_score.third_down_eff),
            "fourth_down_pct": self._parse_efficiency_pct(box_score.fourth_down_eff),
            "red_zone_pct": self._parse_efficiency_pct(box_score.red_zone_eff),
            "yards_per_play": box_score.total_yards
            / max(self._estimate_plays_from_yards(box_score.total_yards), 1),
        }

    def _parse_efficiency_pct(self, efficiency_str: str) -> float:
        """Parse efficiency string like '5-10' to percentage"""
        try:
            if "-" in efficiency_str:
                made, attempted = efficiency_str.split("-")
                return (int(made) / max(int(attempted), 1)) * 100
        except:
            pass
        return 0.0

    def _estimate_plays_from_yards(self, total_yards: int) -> int:
        """Estimate number of plays from total yards"""
        # Average yards per play in college football is around 5.5
        return max(int(total_yards / 5.5), 1)

    def _estimate_total_plays(
        self, home_box: TeamBoxScore, away_box: TeamBoxScore
    ) -> int:
        """Estimate total plays in the game"""
        home_plays = self._estimate_plays_from_yards(home_box.total_yards)
        away_plays = self._estimate_plays_from_yards(away_box.total_yards)
        return home_plays + away_plays

    def _count_scoring_drives(
        self, home_box: TeamBoxScore, away_box: TeamBoxScore
    ) -> int:
        """Estimate number of scoring drives"""
        # Approximate scoring drives based on touchdowns and field goals
        home_scoring = (home_box.final_score // 7) + (home_box.final_score % 7 // 3)
        away_scoring = (away_box.final_score // 7) + (away_box.final_score % 7 // 3)
        return home_scoring + away_scoring

    def _calculate_player_ratings(
        self, player_stats: List[PlayerStats]
    ) -> Dict[str, float]:
        """Calculate performance ratings for key players"""
        ratings = {}

        for player in player_stats:
            rating = 0.0

            # Passing rating
            if player.attempts > 0:
                completion_pct = (player.completions / player.attempts) * 100
                yards_per_attempt = player.passing_yards / player.attempts
                touchdown_rate = (player.passing_touchdowns / player.attempts) * 100
                interception_rate = (player.interceptions / player.attempts) * 100

                # Simplified passer rating
                rating += (
                    completion_pct * 0.1
                    + yards_per_attempt * 0.2
                    + touchdown_rate * 0.4
                    - interception_rate * 0.2
                )

            # Rushing rating
            if player.carries > 0:
                yards_per_carry = player.rushing_yards / player.carries
                touchdown_rate = (player.rushing_touchdowns / player.carries) * 100
                rating += yards_per_carry * 10 + touchdown_rate * 0.5

            # Receiving rating
            if player.receptions > 0:
                yards_per_reception = player.receiving_yards / player.receptions
                touchdown_rate = (player.receiving_touchdowns / player.receptions) * 100
                rating += yards_per_reception * 5 + touchdown_rate * 0.3

            ratings[player.player_name] = round(rating, 1)

        return ratings

    def _calculate_explosive_plays(
        self, player_stats: List[PlayerStats]
    ) -> Dict[str, int]:
        """Count explosive plays (10+ yards rush, 20+ yards pass)"""
        explosive = {"rush_explosive": 0, "pass_explosive": 0}

        for player in player_stats:
            # Count explosive rushing plays
            if player.carries > 0:
                yards_per_carry = player.rushing_yards / player.carries
                if yards_per_carry >= 10:
                    explosive["rush_explosive"] += int(
                        player.carries * 0.15
                    )  # Estimate

            # Count explosive passing plays
            if player.attempts > 0:
                yards_per_attempt = player.passing_yards / player.attempts
                if yards_per_attempt >= 20:
                    explosive["pass_explosive"] += int(
                        player.attempts * 0.1
                    )  # Estimate

        return explosive

    def _analyze_momentum_shifts(
        self, basic_box: Dict[str, Any], home_team: str, away_team: str
    ) -> List[Dict[str, Any]]:
        """Analyze momentum shifts in the game"""
        # This would analyze actual play-by-play data to identify momentum changes
        # For now, return placeholder data
        return [
            {
                "quarter": 2,
                "time": "8:45",
                "team": home_team,
                "type": "turnover",
                "impact": "high",
                "description": f"{home_team} interception stops {away_team} drive",
            }
        ]

    def _identify_key_drives(
        self, basic_box: Dict[str, Any], home_team: str, away_team: str
    ) -> List[Dict[str, Any]]:
        """Identify key drives that changed the game"""
        # This would analyze actual drive data
        # For now, return placeholder data
        return [
            {
                "quarter": 4,
                "time": "2:15",
                "team": home_team,
                "result": "touchdown",
                "impact": "game_winning",
                "description": f"{home_team} game-winning drive",
            }
        ]

    def get_multiple_box_scores(
        self, game_ids: List[int]
    ) -> Dict[int, EnhancedGameBoxScore]:
        """Get multiple enhanced box scores efficiently"""
        results = {}

        for game_id in game_ids:
            try:
                box_score = self.get_enhanced_box_score(game_id)
                if box_score:
                    results[game_id] = box_score
                # Small delay to respect rate limits
                time.sleep(0.2)
            except Exception as e:
                logger.error(f"Error getting box score for game {game_id}: {e}")
                continue

        return results

    def get_week_box_scores(
        self, year: int, week: int
    ) -> Dict[int, EnhancedGameBoxScore]:
        """Get all enhanced box scores for a specific week"""
        try:
            # Get games for the week
            games = self.client.get_games(year=year, week=week)

            # Filter for completed games
            completed_games = [game for game in games if game.get("complete", False)]
            game_ids = [game.get("id") for game in completed_games if game.get("id")]

            logger.info(
                f"📊 Processing {len(game_ids)} completed games for week {week}"
            )

            return self.get_multiple_box_scores(game_ids)

        except Exception as e:
            logger.error(f"Error getting week {week} box scores: {e}")
            return {}

    def export_box_scores_to_dataframe(
        self, box_scores: Dict[int, EnhancedGameBoxScore]
    ) -> pd.DataFrame:
        """Export box scores to pandas DataFrame for analysis"""
        data = []

        for game_id, box_score in box_scores.items():
            row = {
                "game_id": game_id,
                "date": box_score.date,
                "home_team": box_score.home_team,
                "away_team": box_score.away_team,
                "home_score": box_score.home_score,
                "away_score": box_score.away_score,
                "home_total_yards": box_score.home_box_score.total_yards,
                "away_total_yards": box_score.away_box_score.total_yards,
                "home_passing_yards": box_score.home_box_score.passing_yards,
                "away_passing_yards": box_score.away_box_score.passing_yards,
                "home_rushing_yards": box_score.home_box_score.rushing_yards,
                "away_rushing_yards": box_score.away_box_score.rushing_yards,
                "home_turnovers": box_score.home_box_score.turnovers,
                "away_turnovers": box_score.away_box_score.turnovers,
                "home_time_of_possession": box_score.home_box_score.time_of_possession,
                "away_time_of_possession": box_score.away_box_score.time_of_possession,
            }
            data.append(row)

        return pd.DataFrame(data)

    def save_box_scores_to_json(
        self, box_scores: Dict[int, EnhancedGameBoxScore], filename: str
    ):
        """Save box scores to JSON file"""
        # Convert to serializable format
        serializable = {}
        for game_id, box_score in box_scores.items():
            serializable[game_id] = asdict(box_score)

        with open(filename, "w") as f:
            json.dump(serializable, f, indent=2, default=str)

        logger.info(f"💾 Saved {len(box_scores)} box scores to {filename}")


# Example usage
def demo_enhanced_box_scores():
    """Demonstration of enhanced box scores functionality"""
    print("🚀 Enhanced Box Scores Demo")
    print("=" * 30)

    client = EnhancedBoxScoreClient()

    # Get games for a specific week
    print("📅 Getting week 15 games...")
    try:
        games = client.client.get_games(year=2025, week=15)
        completed_games = [g for g in games if g.get("complete", False)]

        if completed_games:
            game_id = completed_games[0].get("id")
            print(
                f"🏈 Processing game {game_id}: {completed_games[0].get('home_team')} vs {completed_games[0].get('away_team')}"
            )

            # Get enhanced box score
            box_score = client.get_enhanced_box_score(game_id)
            if box_score:
                print(f"✅ Enhanced box score generated!")
                print(
                    f"   Final Score: {box_score.home_team} {box_score.home_score} - {box_score.away_score} {box_score.away_team}"
                )
                print(
                    f"   Total Yards: {box_score.home_box_score.total_yards} - {box_score.away_box_score.total_yards}"
                )
                print(f"   Player Stats: {len(box_score.player_stats)} players")
                print(
                    f"   Advanced Metrics: {len(box_score.advanced_metrics)} categories"
                )
        else:
            print("⚠️ No completed games found for week 15")

    except Exception as e:
        print(f"❌ Error in demo: {e}")


if __name__ == "__main__":
    demo_enhanced_box_scores()
