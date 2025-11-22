#!/usr/bin/env python3
"""
Team Metrics Agent
Calculates comprehensive team metrics and performance analysis
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from pathlib import Path

class TeamMetricsAgent:
    """
    Agent responsible for calculating comprehensive team metrics
    """
    
    def __init__(self):
        self.data_path = Path("temp/processed_2025_data.csv")
        
    def calculate_comprehensive_metrics(self) -> Dict[str, Any]:
        """
        Calculate comprehensive team metrics for 2025 data
        """
        print("📊 Calculating comprehensive team metrics...")
        
        # Load data
        if not self.data_path.exists():
            raise FileNotFoundError(f"Data not found: {self.data_path}")
        
        df = pd.read_csv(self.data_path)
        
        results = {
            "team_metrics": {},
            "conference_metrics": {},
            "efficiency_metrics": {},
            "defensive_metrics": {},
            "offensive_metrics": {},
            "top_teams": [],
            "metric_summary": {}
        }
        
        # Calculate team-level metrics
        team_metrics = self._calculate_team_level_metrics(df)
        results["team_metrics"] = team_metrics
        
        # Calculate conference metrics
        conference_metrics = self._calculate_conference_metrics(df, team_metrics)
        results["conference_metrics"] = conference_metrics
        
        # Calculate efficiency metrics
        efficiency_metrics = self._calculate_efficiency_metrics(df)
        results["efficiency_metrics"] = efficiency_metrics
        
        # Calculate defensive and offensive metrics
        defensive_metrics = self._calculate_defensive_metrics(df, team_metrics)
        results["defensive_metrics"] = defensive_metrics
        
        offensive_metrics = self._calculate_offensive_metrics(df, team_metrics)
        results["offensive_metrics"] = offensive_metrics
        
        # Identify top teams across metrics
        top_teams = self._identify_top_teams(team_metrics)
        results["top_teams"] = top_teams
        
        # Generate metric summary
        metric_summary = self._generate_metric_summary(team_metrics, efficiency_metrics)
        results["metric_summary"] = metric_summary
        
        return results
    
    def _calculate_team_level_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate team-level performance metrics
        """
        team_metrics = {}
        
        for team in pd.concat([df['home_team'], df['away_team']]).unique():
            team_df = df[(df['home_team'] == team) | (df['away_team'] == team)]
            
            metrics = {
                "team": team,
                "games_played": len(team_df),
                "wins": len(team_df[(team_df['home_team'] == team) & (team_df['home_score'] > team_df['away_score'])]) +
                       len(team_df[(team_df['away_team'] == team) & (team_df['away_score'] > team_df['home_score'])]),
                "losses": len(team_df) - self._get_wins_for_team(team_df, team),
                "win_percentage": self._calculate_win_percentage(team_df, team),
                "avg_points_scored": self._get_avg_points_scored(team_df, team),
                "avg_points_allowed": self._get_avg_points_allowed(team_df, team),
                "avg_margin": self._get_avg_margin(team_df, team),
                "home_record": self._get_home_record(team_df, team),
                "away_record": self._get_away_record(team_df, team),
                "strength_of_schedule": self._calculate_strength_of_schedule(team_df, team)
            }
            
            team_metrics[team] = metrics
        
        return team_metrics
    
    def _calculate_conference_metrics(self, df: pd.DataFrame, team_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate conference-level metrics (placeholder implementation)
        """
        conference_metrics = {}
        
        # This would require conference information in the data
        # For now, return basic structure
        conference_metrics["conferences"] = ["Big Ten", "SEC", "ACC", "Big 12", "Pac-12"]
        conference_metrics["team_count"] = len(team_metrics)
        
        return conference_metrics
    
    def _calculate_efficiency_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate team efficiency metrics
        """
        efficiency_metrics = {}
        
        # Calculate points per possession efficiency (simplified)
        for team in pd.concat([df['home_team'], df['away_team']]).unique():
            team_df = df[(df['home_team'] == team) | (df['away_team'] == team)]
            
            # Simplified efficiency calculation
            games = len(team_df)
            if games > 0:
                avg_points = self._get_avg_points_scored(team_df, team)
                avg_points_allowed = self._get_avg_points_allowed(team_df, team)
                
                efficiency_metrics[team] = {
                    "points_per_game": avg_points,
                    "points_against_per_game": avg_points_allowed,
                    "differential": avg_points - avg_points_allowed,
                    "efficiency_rating": self._calculate_efficiency_rating(avg_points, avg_points_allowed)
                }
        
        return efficiency_metrics
    
    def _calculate_defensive_metrics(self, df: pd.DataFrame, team_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate defensive performance metrics
        """
        defensive_metrics = {}
        
        for team, metrics in team_metrics.items():
            defensive_metrics[team] = {
                "points_allowed_per_game": metrics["avg_points_allowed"],
                "avg_points_scored_against": metrics["avg_points_allowed"],
                "defensive_efficiency": self._calculate_defensive_efficiency(metrics["avg_points_allowed"]),
                "shutout_games": 0,  # Would need play-by-play data
                "avg_points_allowed_overall": metrics["avg_points_allowed"]
            }
        
        return defensive_metrics
    
    def _calculate_offensive_metrics(self, df: pd.DataFrame, team_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate offensive performance metrics
        """
        offensive_metrics = {}
        
        for team, metrics in team_metrics.items():
            offensive_metrics[team] = {
                "points_per_game": metrics["avg_points_scored"],
                "scoring_efficiency": self._calculate_scoring_efficiency(metrics["avg_points_scored"]),
                "avg_points_scored_overall": metrics["avg_points_scored"],
                "high_scoring_games": self._get_high_scoring_games(team, metrics),
                "consistency_score": self._calculate_scoring_consistency(team, df)
            }
        
        return offensive_metrics
    
    def _identify_top_teams(self, team_metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify top teams across different metrics
        """
        top_teams = []
        
        # Sort by win percentage
        sorted_by_win_pct = sorted(team_metrics.items(), 
                                 key=lambda x: x[1]["win_percentage"], 
                                 reverse=True)
        
        # Top 5 teams by win percentage
        for team, metrics in sorted_by_win_pct[:5]:
            top_teams.append({
                "rank": len(top_teams) + 1,
                "team": team,
                "win_percentage": metrics["win_percentage"],
                "avg_margin": metrics["avg_margin"],
                "wins": metrics["wins"],
                "games_played": metrics["games_played"]
            })
        
        return top_teams
    
    def _generate_metric_summary(self, team_metrics: Dict[str, Any], efficiency_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate summary of key metrics
        """
        summary = {
            "total_teams": len(team_metrics),
            "avg_win_percentage": sum(m["win_percentage"] for m in team_metrics.values()) / len(team_metrics),
            "avg_points_scored": sum(m["avg_points_scored"] for m in team_metrics.values()) / len(team_metrics),
            "avg_points_allowed": sum(m["avg_points_allowed"] for m in team_metrics.values()) / len(team_metrics),
            "top_offensive_teams": self._get_top_teams_by_metric(efficiency_metrics, "points_per_game")[:3],
            "top_defensive_teams": self._get_top_teams_by_metric(efficiency_metrics, "points_against_per_game")[:3],
            "most_improved_teams": [],
            "underperforming_teams": []
        }
        
        return summary
    
    # Helper methods
    def _get_wins_for_team(self, team_df: pd.DataFrame, team: str) -> int:
        return len(team_df[(team_df['home_team'] == team) & (team_df['home_score'] > team_df['away_score'])]) + \
               len(team_df[(team_df['away_team'] == team) & (team_df['away_score'] > team_df['home_score'])])
    
    def _calculate_win_percentage(self, team_df: pd.DataFrame, team: str) -> float:
        wins = self._get_wins_for_team(team_df, team)
        return wins / len(team_df)
    
    def _get_avg_points_scored(self, team_df: pd.DataFrame, team: str) -> float:
        home_points = team_df[team_df['home_team'] == team]['home_score'].mean()
        away_points = team_df[team_df['away_team'] == team]['away_score'].mean()
        return pd.Series([home_points, away_points]).mean()
    
    def _get_avg_points_allowed(self, team_df: pd.DataFrame, team: str) -> float:
        home_allowed = team_df[team_df['home_team'] == team]['away_score'].mean()
        away_allowed = team_df[team_df['away_team'] == team]['home_score'].mean()
        return pd.Series([home_allowed, away_allowed]).mean()
    
    def _get_avg_margin(self, team_df: pd.DataFrame, team: str) -> float:
        margins = []
        for _, row in team_df.iterrows():
            if row['home_team'] == team:
                margins.append(row['home_score'] - row['away_score'])
            else:
                margins.append(row['away_score'] - row['home_score'])
        return pd.Series(margins).mean()
    
    def _get_home_record(self, team_df: pd.DataFrame, team: str) -> Dict[str, int]:
        home_games = team_df[team_df['home_team'] == team]
        wins = len(home_games[home_games['home_score'] > home_games['away_score']])
        return {"wins": wins, "losses": len(home_games) - wins}
    
    def _get_away_record(self, team_df: pd.DataFrame, team: str) -> Dict[str, int]:
        away_games = team_df[team_df['away_team'] == team]
        wins = len(away_games[away_games['away_score'] > away_games['home_score']])
        return {"wins": wins, "losses": len(away_games) - wins}
    
    def _calculate_strength_of_schedule(self, team_df: pd.DataFrame, team: str) -> float:
        # Simplified SOS calculation
        opponent_strengths = []
        for _, row in team_df.iterrows():
            opponent = row['away_team'] if row['home_team'] == team else row['home_team']
            # This would need actual opponent strength calculation
            opponent_strengths.append(0.5)  # Placeholder
        
        return pd.Series(opponent_strengths).mean()
    
    def _calculate_efficiency_rating(self, points_scored: float, points_allowed: float) -> float:
        return (points_scored - points_allowed) / points_scored
    
    def _calculate_defensive_efficiency(self, points_allowed: float) -> float:
        return max(0, 1 - (points_allowed / 35))  # Assuming 35 is average scoring
    
    def _calculate_scoring_efficiency(self, points_scored: float) -> float:
        return min(1.0, points_scored / 30)  # Assuming 30 is good scoring average
    
    def _get_high_scoring_games(self, team: str, metrics: Dict[str, Any]) -> int:
        # Would need actual game data to identify high scoring games
        return 0
    
    def _calculate_scoring_consistency(self, team: str, df: pd.DataFrame) -> float:
        # Would need point variance calculation
        return 0.8  # Placeholder
    
    def _get_top_teams_by_metric(self, metrics: Dict[str, Any], metric_name: str) -> List[str]:
        sorted_teams = sorted(metrics.items(), key=lambda x: x[1].get(metric_name, 0), reverse=True)
        return [team[0] for team in sorted_teams[:5]]

if __name__ == "__main__":
    agent = TeamMetricsAgent()
    result = agent.calculate_comprehensive_metrics()
    print(json.dumps(result, indent=2))
