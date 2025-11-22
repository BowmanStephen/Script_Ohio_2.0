"""
Offense vs Defense Matchup Comparison.
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from sklearn.preprocessing import StandardScaler

class OffenseDefenseComparison:
    """
    Analyzes and compares offensive vs defensive metrics between teams.
    """
    
    def __init__(self, stats_df: pd.DataFrame):
        self.stats_df = stats_df.copy()
        self.metrics = [
            'offense_ppa', 'offense_successRate', 'offense_explosiveness',
            'defense_ppa', 'defense_successRate', 'defense_explosiveness'
        ]
        self._normalize_metrics()

    def _normalize_metrics(self):
        """Calculate z-scores for all metrics."""
        scaler = StandardScaler()
        # Filter numeric columns only for scaling if needed, but strict metrics list is better
        available_metrics = [m for m in self.metrics if m in self.stats_df.columns]
        
        if available_metrics:
            self.z_scores = pd.DataFrame(
                scaler.fit_transform(self.stats_df[available_metrics]),
                columns=available_metrics,
                index=self.stats_df.index
            )
            self.z_scores['team'] = self.stats_df['team']

    def normalize_matchup_metrics(self, offense_team: str, defense_team: str) -> Dict[str, float]:
        """
        Get normalized metrics for a specific matchup (Team A Offense vs Team B Defense).
        
        Args:
            offense_team: Name of the offensive team
            defense_team: Name of the defensive team
            
        Returns:
            Dictionary of z-scores for relevant metrics
        """
        off_stats = self.z_scores[self.z_scores['team'] == offense_team]
        def_stats = self.z_scores[self.z_scores['team'] == defense_team]
        
        if off_stats.empty or def_stats.empty:
            return {}
            
        result = {}
        for m in ['offense_ppa', 'offense_successRate', 'offense_explosiveness']:
            if m in off_stats.columns:
                result[m] = float(off_stats[m].iloc[0])
                
        for m in ['defense_ppa', 'defense_successRate', 'defense_explosiveness']:
            if m in def_stats.columns:
                result[m] = float(def_stats[m].iloc[0])
                
        return result

    def generate_matchup_comparison(self, team1: str, team2: str) -> Dict[str, Any]:
        """
        Generate full comparison for a game (Team1 vs Team2).
        
        Args:
            team1: Home team (usually)
            team2: Away team
            
        Returns:
            Dictionary containing both offensive/defensive matchups
        """
        return {
            'team1_off_vs_team2_def': self.normalize_matchup_metrics(team1, team2),
            'team2_off_vs_team1_def': self.normalize_matchup_metrics(team2, team1)
        }

def normalize_matchup_metrics(stats_df: pd.DataFrame, offense_team: str, defense_team: str) -> Dict[str, float]:
    """Functional interface for normalized matchup metrics."""
    model = OffenseDefenseComparison(stats_df)
    return model.normalize_matchup_metrics(offense_team, defense_team)

def generate_matchup_comparison(stats_df: pd.DataFrame, team1: str, team2: str) -> Dict[str, Any]:
    """Functional interface for full matchup comparison."""
    model = OffenseDefenseComparison(stats_df)
    return model.generate_matchup_comparison(team1, team2)

