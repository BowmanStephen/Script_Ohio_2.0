#!/usr/bin/env python3
"""
Advanced CFBD Features Integration
=================================

Implements advanced college football analytics features:
- EPA (Expected Points Added) integration
- PPA (Predicted Points Added) metrics
- Recruiting rankings integration
- Player statistics integration
- Team strength metrics beyond basic talent ratings

This script enhances the existing prediction models with advanced CFBD data.
"""

import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from src.cfbd_client.unified_client import UnifiedCFBDClient

    print("✅ CFBD client loaded successfully")
except ImportError as e:
    print(f"❌ CFBD client import error: {e}")
    sys.exit(1)


class AdvancedCFBDFeatures:
    """Advanced CFBD analytics integration system"""

    def __init__(self):
        self.client = UnifiedCFBDClient()
        self.features_data = {}

    def rate_limit_wait(self):
        """CFBD API rate limiting: 6 req/sec = 0.17 sec between requests"""
        time.sleep(0.17)

    def fetch_team_epa_data(self, year: int = 2025) -> dict:
        """Fetch EPA (Expected Points Added) data for all teams"""
        print("📊 Fetching EPA data...")

        try:
            # Get team EPA stats from CFBD using available methods
            epa_data = self.client.get_team_epa_wpa_season(year=year)

            if epa_data:
                # Process EPA data by team
                team_epa = {}

                for game in epa_data:
                    if game.get("team") and game.get("points_added"):
                        team_name = game["team"]
                        if team_name not in team_epa:
                            team_epa[team_name] = {
                                "offense_epa": [],
                                "defense_epa_allowed": [],
                                "special_teams_epa": [],
                                "games_count": 0,
                            }

                        # Store EPA metrics
                        if game.get("offense_points_added"):
                            team_epa[team_name]["offense_epa"].append(
                                game["offense_points_added"]
                            )
                        if game.get("defense_points_added_allowed"):
                            team_epa[team_name]["defense_epa_allowed"].append(
                                game["defense_points_added_allowed"]
                            )
                        if game.get("special_teams_points_added"):
                            team_epa[team_name]["special_teams_epa"].append(
                                game["special_teams_points_added"]
                            )

                        team_epa[team_name]["games_count"] += 1

                # Calculate averages
                for team in team_epa:
                    if team_epa[team]["offense_epa"]:
                        team_epa[team]["avg_offense_epa"] = np.mean(
                            team_epa[team]["offense_epa"]
                        )
                    if team_epa[team]["defense_epa_allowed"]:
                        team_epa[team]["avg_defense_epa_allowed"] = np.mean(
                            team_epa[team]["defense_epa_allowed"]
                        )
                    if team_epa[team]["special_teams_epa"]:
                        team_epa[team]["avg_special_teams_epa"] = np.mean(
                            team_epa[team]["special_teams_epa"]
                        )

                self.features_data["team_epa"] = team_epa
                print(f"✅ EPA data fetched for {len(team_epa)} teams")
                return team_epa

        except Exception as e:
            print(f"⚠️ EPA data fetch error: {e}")

        return {}

    def fetch_ppa_data(self, year: int = 2025) -> dict:
        """Fetch PPA (Predicted Points Added) data"""
        print("📈 Fetching PPA data...")

        try:
            # PPA data might be in advanced stats or player stats
            ppa_data = self.client.get_advanced_stats(year=year)

            if ppa_data:
                team_ppa = {}

                for team_stats in ppa_data:
                    team_name = team_stats.get("team")
                    if team_name:
                        team_ppa[team_name] = {
                            "ppa_offense": team_stats.get("ppa_offense", 0.0),
                            "ppa_defense": team_stats.get("ppa_defense", 0.0),
                            "ppa_overall": team_stats.get("ppa_overall", 0.0),
                            "success_rate_offense": team_stats.get(
                                "success_rate_offense", 0.0
                            ),
                            "success_rate_defense": team_stats.get(
                                "success_rate_defense", 0.0
                            ),
                            "explosiveness_offense": team_stats.get(
                                "explosiveness_offense", 0.0
                            ),
                            "explosiveness_defense": team_stats.get(
                                "explosiveness_defense", 0.0
                            ),
                        }

                self.features_data["team_ppa"] = team_ppa
                print(f"✅ PPA data fetched for {len(team_ppa)} teams")
                return team_ppa

        except Exception as e:
            print(f"⚠️ PPA data fetch error: {e}")

        return {}

    def fetch_recruiting_data(self, year: int = 2025) -> dict:
        """Fetch recruiting rankings data"""
        print("🏈 Fetching recruiting data...")

        try:
            # Get recruiting rankings for recent classes
            recruiting_classes = [
                2024,
                2023,
                2022,
                2021,
            ]  # Recent classes affecting current team
            recruiting_data = {}

            for class_year in recruiting_classes:
                self.rate_limit_wait()

                try:
                    class_data = self.client.get_recruiting(year=class_year)

                    if class_data:
                        for team in class_data:
                            team_name = team.get("team")
                            if team_name:
                                if team_name not in recruiting_data:
                                    recruiting_data[team_name] = {
                                        "classes": [],
                                        "total_points": 0,
                                        "avg_ranking": None,
                                        "five_star_count": 0,
                                        "four_star_count": 0,
                                    }

                                recruiting_data[team_name]["classes"].append(
                                    {
                                        "year": class_year,
                                        "ranking": team.get("ranking"),
                                        "points": team.get("points"),
                                        "five_star": team.get("five_stars", 0),
                                        "four_star": team.get("four_stars", 0),
                                    }
                                )

                                if team.get("points"):
                                    recruiting_data[team_name]["total_points"] += team[
                                        "points"
                                    ]
                                if team.get("five_stars"):
                                    recruiting_data[team_name][
                                        "five_star_count"
                                    ] += team["five_stars"]
                                if team.get("four_stars"):
                                    recruiting_data[team_name][
                                        "four_star_count"
                                    ] += team["four_stars"]

                except Exception as e:
                    print(f"⚠️ Recruiting data error for {class_year}: {e}")
                    continue

            # Calculate averages
            for team in recruiting_data:
                if recruiting_data[team]["classes"]:
                    rankings = [
                        c["ranking"]
                        for c in recruiting_data[team]["classes"]
                        if c["ranking"]
                    ]
                    if rankings:
                        recruiting_data[team]["avg_ranking"] = np.mean(rankings)
                        recruiting_data[team]["class_count"] = len(rankings)

            self.features_data["recruiting"] = recruiting_data
            print(f"✅ Recruiting data fetched for {len(recruiting_data)} teams")
            return recruiting_data

        except Exception as e:
            print(f"⚠️ Recruiting data fetch error: {e}")

        return {}

    def fetch_player_stats(self, year: int = 2025) -> dict:
        """Fetch player statistics data"""
        print("👥 Fetching player stats...")

        try:
            # Get player statistics using available method
            player_stats = self.client.get_stats(year=year, category="player")

            if player_stats:
                team_player_stats = {}

                for player in player_stats:
                    team_name = player.get("team")
                    if team_name:
                        if team_name not in team_player_stats:
                            team_player_stats[team_name] = {
                                "total_players": 0,
                                "positions": {},
                                "total_passing_yards": 0,
                                "total_rushing_yards": 0,
                                "total_receiving_yards": 0,
                                "total_tackles": 0,
                                "total_sacks": 0,
                                "avg_experience": 0.0,
                            }

                        # Aggregate stats by team
                        team_player_stats[team_name]["total_players"] += 1

                        position = player.get("position", "Unknown")
                        if position not in team_player_stats[team_name]["positions"]:
                            team_player_stats[team_name]["positions"][position] = 0
                        team_player_stats[team_name]["positions"][position] += 1

                        # Accumulate key stats
                        if player.get("passing_yards"):
                            team_player_stats[team_name][
                                "total_passing_yards"
                            ] += player["passing_yards"]
                        if player.get("rushing_yards"):
                            team_player_stats[team_name][
                                "total_rushing_yards"
                            ] += player["rushing_yards"]
                        if player.get("receiving_yards"):
                            team_player_stats[team_name][
                                "total_receiving_yards"
                            ] += player["receiving_yards"]
                        if player.get("tackles"):
                            team_player_stats[team_name]["total_tackles"] += player[
                                "tackles"
                            ]
                        if player.get("sacks"):
                            team_player_stats[team_name]["total_sacks"] += player[
                                "sacks"
                            ]

                self.features_data["player_stats"] = team_player_stats
                print(f"✅ Player stats fetched for {len(team_player_stats)} teams")
                return team_player_stats

        except Exception as e:
            print(f"⚠️ Player stats fetch error: {e}")

        return {}

    def calculate_advanced_team_ratings(self) -> dict:
        """Calculate advanced team ratings combining all features"""
        print("🧮 Calculating advanced team ratings...")

        advanced_ratings = {}

        # Get all unique teams from all data sources
        all_teams = set()
        if "team_epa" in self.features_data:
            all_teams.update(self.features_data["team_epa"].keys())
        if "team_ppa" in self.features_data:
            all_teams.update(self.features_data["team_ppa"].keys())
        if "recruiting" in self.features_data:
            all_teams.update(self.features_data["recruiting"].keys())
        if "player_stats" in self.features_data:
            all_teams.update(self.features_data["player_stats"].keys())

        for team in all_teams:
            rating = {
                "team": team,
                "epa_score": 0.0,
                "ppa_score": 0.0,
                "recruiting_score": 0.0,
                "experience_score": 0.0,
                "depth_score": 0.0,
                "overall_advanced_rating": 0.0,
            }

            # EPA score (normalized -2 to +2, typical EPA range)
            if team in self.features_data.get("team_epa", {}):
                epa_data = self.features_data["team_epa"][team]
                offense_epa = epa_data.get("avg_offense_epa", 0.0)
                defense_epa = epa_data.get("avg_defense_epa_allowed", 0.0)
                rating["epa_score"] = max(-2, min(2, (offense_epa - defense_epa) / 2))

            # PPA score (normalized 0-100)
            if team in self.features_data.get("team_ppa", {}):
                ppa_data = self.features_data["team_ppa"][team]
                ppa_overall = ppa_data.get("ppa_overall", 0.0)
                rating["ppa_score"] = max(0, min(100, ppa_overall))

            # Recruiting score (inverse ranking, lower ranking = higher score)
            if team in self.features_data.get("recruiting", {}):
                rec_data = self.features_data["recruiting"][team]
                avg_ranking = rec_data.get(
                    "avg_ranking", 100
                )  # Default to 100 if no ranking
                # Convert ranking to score (1=100, 130=1)
                rating["recruiting_score"] = max(1, min(100, 131 - avg_ranking))

            # Experience and depth from player stats
            if team in self.features_data.get("player_stats", {}):
                player_data = self.features_data["player_stats"][team]
                total_players = player_data.get("total_players", 0)
                rating["depth_score"] = min(
                    100, total_players * 2
                )  # 50 players = 100 points

            # Calculate overall advanced rating (weighted combination)
            rating["overall_advanced_rating"] = (
                rating["epa_score"] * 25  # 25% weight
                + rating["ppa_score"] * 0.25  # 25% weight (PPA is 0-100)
                + rating["recruiting_score"] * 0.20  # 20% weight
                + rating["depth_score"] * 0.30  # 30% weight
            )

            advanced_ratings[team] = rating

        self.features_data["advanced_ratings"] = advanced_ratings
        print(f"✅ Advanced ratings calculated for {len(advanced_ratings)} teams")
        return advanced_ratings

    def save_features_data(self, filename: str = None):
        """Save all features data to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"advanced_cfbd_features_{timestamp}.json"

        filepath = PROJECT_ROOT / "data" / "processed" / "features" / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Add metadata
        output_data = {
            "generated_at": datetime.now().isoformat(),
            "season": 2025,
            "data_sources": ["EPA", "PPA", "Recruiting", "Player Stats"],
            "total_teams": len(self.features_data.get("advanced_ratings", {})),
            "features_data": self.features_data,
        }

        with open(filepath, "w") as f:
            json.dump(output_data, f, indent=2, default=str)

        print(f"✅ Advanced features saved to: {filepath}")
        return filepath

    def generate_enhanced_predictions(self, bowl_games_file: str) -> dict:
        """Generate enhanced predictions using advanced features"""
        print("🎯 Generating enhanced predictions with advanced features...")

        try:
            # Load FBS bowl games
            with open(bowl_games_file, "r") as f:
                bowl_data = json.load(f)

            enhanced_predictions = []

            for game in bowl_data.get("games", []):
                home_team = game["home_team"]
                away_team = game["away_team"]

                # Get advanced ratings
                home_rating = self.features_data.get("advanced_ratings", {}).get(
                    home_team, {}
                )
                away_rating = self.features_data.get("advanced_ratings", {}).get(
                    away_team, {}
                )

                # Calculate advanced features for prediction
                advanced_margin_prediction = (
                    home_rating.get("overall_advanced_rating", 50)
                    - away_rating.get("overall_advanced_rating", 50)
                ) / 10

                # Add advanced features to game prediction
                enhanced_game = {
                    **game,  # Keep original game data
                    "advanced_features": {
                        "home_advanced_rating": home_rating.get(
                            "overall_advanced_rating", 50
                        ),
                        "away_advanced_rating": away_rating.get(
                            "overall_advanced_rating", 50
                        ),
                        "epa_advantage": (
                            home_rating.get("epa_score", 0)
                            - away_rating.get("epa_score", 0)
                        ),
                        "ppa_advantage": (
                            home_rating.get("ppa_score", 0)
                            - away_rating.get("ppa_score", 0)
                        ),
                        "recruiting_advantage": (
                            home_rating.get("recruiting_score", 0)
                            - away_rating.get("recruiting_score", 0)
                        ),
                        "advanced_margin_prediction": advanced_margin_prediction,
                    },
                }

                enhanced_predictions.append(enhanced_game)

            result = {
                "generated_at": datetime.now().isoformat(),
                "enhanced_method": "advanced_cfbd_features",
                "total_games": len(enhanced_predictions),
                "games": enhanced_predictions,
            }

            return result

        except Exception as e:
            print(f"❌ Enhanced prediction generation error: {e}")
            return {}


def main():
    """Main function to run advanced CFBD features integration"""
    print("🚀 ADVANCED CFBD FEATURES INTEGRATION")
    print("=" * 60)

    # Initialize advanced features system
    advanced_features = AdvancedCFBDFeatures()

    # Step 1: Fetch all advanced data sources
    print("\n📥 Step 1: Fetching Advanced Data Sources")
    print("-" * 40)

    # EPA data
    advanced_features.fetch_team_epa_data(year=2025)

    # PPA data
    advanced_features.fetch_ppa_data(year=2025)

    # Recruiting data
    advanced_features.fetch_recruiting_data(year=2025)

    # Player statistics
    advanced_features.fetch_player_stats(year=2025)

    # Step 2: Calculate advanced team ratings
    print("\n🧮 Step 2: Calculating Advanced Team Ratings")
    print("-" * 40)
    advanced_ratings = advanced_features.calculate_advanced_team_ratings()

    # Step 3: Save features data
    print("\n💾 Step 3: Saving Features Data")
    print("-" * 40)
    features_file = advanced_features.save_features_data()

    # Step 4: Generate enhanced predictions
    print("\n🎯 Step 4: Generating Enhanced Predictions")
    print("-" * 40)

    # Look for existing FBS bowl predictions
    bowl_predictions_file = (
        PROJECT_ROOT / "predictions" / "fbs_bowl_predictions_latest.json"
    )

    if bowl_predictions_file.exists():
        enhanced_predictions = advanced_features.generate_enhanced_predictions(
            str(bowl_predictions_file)
        )

        # Save enhanced predictions
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        enhanced_file = (
            PROJECT_ROOT / "predictions" / f"enhanced_bowl_predictions_{timestamp}.json"
        )

        with open(enhanced_file, "w") as f:
            json.dump(enhanced_predictions, f, indent=2, default=str)

        print(f"✅ Enhanced predictions saved: {enhanced_file}")
        print(
            f"📊 Enhanced {enhanced_predictions.get('total_games', 0)} games with advanced features"
        )

    # Summary
    print("\n🎉 ADVANCED CFBD FEATURES INTEGRATION COMPLETE!")
    print("=" * 60)
    print(
        f"✅ EPA Data: {len(advanced_features.features_data.get('team_epa', {}))} teams"
    )
    print(
        f"✅ PPA Data: {len(advanced_features.features_data.get('team_ppa', {}))} teams"
    )
    print(
        f"✅ Recruiting Data: {len(advanced_features.features_data.get('recruiting', {}))} teams"
    )
    print(
        f"✅ Player Stats: {len(advanced_features.features_data.get('player_stats', {}))} teams"
    )
    print(f"✅ Advanced Ratings: {len(advanced_ratings)} teams")
    print(f"✅ Features File: {features_file}")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
