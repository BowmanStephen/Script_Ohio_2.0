#!/usr/bin/env python3
"""
Power Ranking Agent
Generates comprehensive team power rankings using multiple metrics
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from pathlib import Path

class PowerRankingAgent:
    """
    Agent responsible for generating comprehensive power rankings
    """
    
    def __init__(self):
        self.data_path = Path("temp/processed_2025_data.csv")
        
    def generate_power_rankings(self) -> Dict[str, Any]:
        """
        Generate comprehensive power rankings using multiple methodologies
        """
        print("🏆 Generating power rankings...")
        
        # Load data
        if not self.data_path.exists():
            raise FileNotFoundError(f"Data not found: {self.data_path}")
        
        df = pd.read_csv(self.data_path)
        
        results = {
            "rankings": {},
            "methodologies": {},
            "top_teams": [],
            "surprise_teams": [],
            "rankings_comparison": {},
            "confidence_scores": {}
        }
        
        # Calculate multiple ranking methodologies
        win_percentage_rankings = self._calculate_win_percentage_rankings(df)
        points_differential_rankings = self._calculate_points_differential_rankings(df)
        strength_of_schedule_rankings = self._calculate_strength_of_schedule_rankings(df)
        
        # Store methodology results
        results["methodologies"] = {
            "win_percentage": win_percentage_rankings,
            "points_differential": points_differential_rankings,
            "strength_of_schedule": strength_of_schedule_rankings
        }
        
        # Generate composite rankings
        composite_rankings = self._generate_composite_rankings(
            win_percentage_rankings,
            points_differential_rankings,
            strength_of_schedule_rankings
        )
        
        results["rankings"] = composite_rankings
        
        # Identify top teams
        top_teams = self._identify_top_teams(composite_rankings)
        results["top_teams"] = top_teams
        
        # Identify surprise teams
        surprise_teams = self._identify_surprise_teams(win_percentage_rankings, composite_rankings)
        results["surprise_teams"] = surprise_teams
        
        # Generate rankings comparison
        rankings_comparison = self._compare_rankings(win_percentage_rankings, composite_rankings)
        results["rankings_comparison"] = rankings_comparison
        
        # Calculate confidence scores
        confidence_scores = self._calculate_confidence_scores(composite_rankings)
        results["confidence_scores"] = confidence_scores
        
        return results
    
    def _calculate_win_percentage_rankings(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate rankings based on win percentage
        """
        rankings = {}
        
        for team in pd.concat([df['home_team'], df['away_team']]).unique():
            team_df = df[(df['home_team'] == team) | (df['away_team'] == team)]
            
            wins = len(team_df[(team_df['home_team'] == team) & (team_df['home_score'] > team_df['away_score'])]) + \
                   len(team_df[(team_df['away_team'] == team) & (team_df['away_score'] > team_df['home_score'])])
            
            win_pct = wins / len(team_df) if len(team_df) > 0 else 0
            
            rankings[team] = {
                "rank": 0,
                "win_percentage": win_pct,
                "wins": wins,
                "games_played": len(team_df),
                "points": win_pct * 100  # Scale to 100 point system
            }
        
        # Sort and assign ranks
        sorted_rankings = sorted(rankings.items(), key=lambda x: x[1]["win_percentage"], reverse=True)
        for rank, (team, data) in enumerate(sorted_rankings, 1):
            rankings[team]["rank"] = rank
        
        return rankings
    
    def _calculate_points_differential_rankings(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate rankings based on points differential
        """
        rankings = {}
        
        for team in pd.concat([df['home_team'], df['away_team']]).unique():
            team_df = df[(df['home_team'] == team) | (df['away_team'] == team)]
            
            differentials = []
            for _, row in team_df.iterrows():
                if row['home_team'] == team:
                    differentials.append(row['home_score'] - row['away_score'])
                else:
                    differentials.append(row['away_score'] - row['home_score'])
            
            avg_differential = np.mean(differentials) if len(differentials) > 0 else 0
            
            rankings[team] = {
                "rank": 0,
                "avg_differential": avg_differential,
                "max_differential": max(differentials) if len(differentials) > 0 else 0,
                "min_differential": min(differentials) if len(differentials) > 0 else 0,
                "points": avg_differential + 50  # Normalize around 50
            }
        
        # Sort and assign ranks
        sorted_rankings = sorted(rankings.items(), key=lambda x: x[1]["avg_differential"], reverse=True)
        for rank, (team, data) in enumerate(sorted_rankings, 1):
            rankings[team]["rank"] = rank
        
        return rankings
    
    def _calculate_strength_of_schedule_rankings(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate rankings based on strength of schedule
        """
        rankings = {}
        
        # Build team win percentages for opponent strength
        team_win_pcts = {}
        for team in pd.concat([df['home_team'], df['away_team']]).unique():
            team_df = df[(df['home_team'] == team) | (df['away_team'] == team)]
            wins = len(team_df[(team_df['home_team'] == team) & (team_df['home_score'] > team_df['away_score'])]) + \
                   len(team_df[(team_df['away_team'] == team) & (team_df['away_score'] > team_df['home_score'])])
            team_win_pcts[team] = wins / len(team_df) if len(team_df) > 0 else 0
        
        # Calculate SOS for each team
        for team in pd.concat([df['home_team'], df['away_team']]).unique():
            team_df = df[(df['home_team'] == team) | (df['away_team'] == team)]
            
            opponent_strengths = []
            for _, row in team_df.iterrows():
                opponent = row['away_team'] if row['home_team'] == team else row['home_team']
                opponent_strengths.append(team_win_pcts[opponent])
            
            avg_opponent_strength = np.mean(opponent_strengths) if len(opponent_strengths) > 0 else 0
            
            # Higher SOS is better (played tougher teams)
            rankings[team] = {
                "rank": 0,
                "avg_opponent_strength": avg_opponent_strength,
                "points": avg_opponent_strength * 100 + 25  # Scale and adjust
            }
        
        # Sort and assign ranks (higher SOS is better)
        sorted_rankings = sorted(rankings.items(), key=lambda x: x[1]["avg_opponent_strength"], reverse=True)
        for rank, (team, data) in enumerate(sorted_rankings, 1):
            rankings[team]["rank"] = rank
        
        return rankings
    
    def _generate_composite_rankings(self, *ranking_methods: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate composite rankings from multiple methodologies
        """
        composite = {}
        
        # Get all teams
        all_teams = set()
        for method in ranking_methods:
            all_teams.update(method.keys())
        
        for team in all_teams:
            total_points = 0
            rank_count = 0
            
            for method in ranking_methods:
                if team in method:
                    total_points += method[team]["points"]
                    rank_count += 1
            
            avg_points = total_points / rank_count if rank_count > 0 else 0
            composite[team] = {
                "composite_points": avg_points,
                "rank": 0,
                "individual_ranks": {}
            }
            
            # Store individual ranks
            for method_name, method_data in zip(["win_percentage", "points_differential", "strength_of_schedule"], ranking_methods):
                if team in method_data:
                    composite[team]["individual_ranks"][method_name] = method_data[team]["rank"]
        
        # Sort and assign composite ranks
        sorted_composite = sorted(composite.items(), key=lambda x: x[1]["composite_points"], reverse=True)
        for rank, (team, data) in enumerate(sorted_composite, 1):
            composite[team]["rank"] = rank
        
        return composite
    
    def _identify_top_teams(self, composite_rankings: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify top teams in composite rankings
        """
        top_teams = []
        sorted_teams = sorted(composite_rankings.items(), key=lambda x: x[1]["composite_points"], reverse=True)
        
        for rank, (team, data) in enumerate(sorted_teams[:10], 1):
            top_teams.append({
                "rank": rank,
                "team": team,
                "composite_points": data["composite_points"],
                "individual_ranks": data["individual_ranks"],
                "confidence": self._calculate_team_confidence(data)
            })
        
        return top_teams
    
    def _identify_surprise_teams(self, win_pct_rankings: Dict[str, Any], composite_rankings: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify surprise teams (those performing better/worse than expected)
        """
        surprise_teams = []
        
        for team in composite_rankings:
            if team in win_pct_rankings:
                win_pct_rank = win_pct_rankings[team]["rank"]
                composite_rank = composite_rankings[team]["rank"]
                
                rank_difference = composite_rank - win_pct_rank
                
                if abs(rank_difference) >= 3:  # Significant difference
                    surprise_teams.append({
                        "team": team,
                        "win_percentage_rank": win_pct_rank,
                        "composite_rank": composite_rank,
                        "rank_difference": rank_difference,
                        "type": "overperforming" if rank_difference < 0 else "underperforming"
                    })
        
        # Sort by absolute rank difference
        surprise_teams.sort(key=lambda x: abs(x["rank_difference"]), reverse=True)
        
        return surprise_teams[:5]
    
    def _compare_rankings(self, win_pct_rankings: Dict[str, Any], composite_rankings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare different ranking methodologies
        """
        comparison = {
            "correlation": self._calculate_rank_correlation(win_pct_rankings, composite_rankings),
            "biggest_movers": self._find_biggest_movers(win_pct_rankings, composite_rankings),
            "consistency_analysis": {}
        }
        
        # Analyze ranking consistency
        for team in composite_rankings:
            if team in win_pct_rankings:
                difference = abs(composite_rankings[team]["rank"] - win_pct_rankings[team]["rank"])
                if difference <= 2:
                    comparison["consistency_analysis"][team] = "consistent"
                elif difference <= 5:
                    comparison["consistency_analysis"][team] = "moderate_movement"
                else:
                    comparison["consistency_analysis"][team] = "significant_movement"
        
        return comparison
    
    def _calculate_confidence_scores(self, composite_rankings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate confidence scores for rankings
        """
        confidence_scores = {}
        
        for team, data in composite_rankings.items():
            # Higher ranked teams have more confidence
            rank = data["rank"]
            max_points = max([team_data["composite_points"] for team_data in composite_rankings.values()])
            
            confidence = max(0, (1 - (rank - 1) / len(composite_rankings))) * 100
            
            confidence_scores[team] = {
                "confidence_score": confidence,
                "rank": rank,
                "rating": self._get_confidence_rating(confidence)
            }
        
        return confidence_scores
    
    # Helper methods
    def _calculate_rank_correlation(self, rankings1: Dict[str, Any], rankings2: Dict[str, Any]) -> float:
        """
        Calculate rank correlation between two ranking systems
        """
        common_teams = set(rankings1.keys()) & set(rankings2.keys())
        if len(common_teams) < 2:
            return 0.0
        
        ranks1 = [rankings1[team]["rank"] for team in common_teams]
        ranks2 = [rankings2[team]["rank"] for team in common_teams]
        
        # Simple rank correlation
        n = len(common_teams)
        if n < 2:
            return 0.0
        
        # Spearman's rank correlation (simplified)
        diff_sum = sum((r1 - r2) ** 2 for r1, r2 in zip(ranks1, ranks2))
        correlation = 1 - (6 * diff_sum) / (n * (n**2 - 1))
        
        return correlation
    
    def _find_biggest_movers(self, rankings1: Dict[str, Any], rankings2: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Find teams with the biggest rank changes
        """
        movers = []
        
        common_teams = set(rankings1.keys()) & set(rankings2.keys())
        for team in common_teams:
            rank1 = rankings1[team]["rank"]
            rank2 = rankings2[team]["rank"]
            change = rank2 - rank1
            
            if abs(change) >= 2:
                movers.append({
                    "team": team,
                    "from_rank": rank1,
                    "to_rank": rank2,
                    "change": change
                })
        
        movers.sort(key=lambda x: abs(x["change"]), reverse=True)
        return movers[:5]
    
    def _calculate_team_confidence(self, team_data: Dict[str, Any]) -> str:
        """
        Determine confidence level for a team's ranking
        """
        rank = team_data["rank"]
        if rank <= 5:
            return "high"
        elif rank <= 10:
            return "medium"
        else:
            return "low"
    
    def _get_confidence_rating(self, confidence_score: float) -> str:
        """
        Convert confidence score to rating
        """
        if confidence_score >= 80:
            return "A+"
        elif confidence_score >= 70:
            return "A"
        elif confidence_score >= 60:
            return "B+"
        elif confidence_score >= 50:
            return "B"
        elif confidence_score >= 40:
            return "C+"
        elif confidence_score >= 30:
            return "C"
        else:
            return "D"

if __name__ == "__main__":
    agent = PowerRankingAgent()
    result = agent.generate_power_rankings()
    print(json.dumps(result, indent=2))
