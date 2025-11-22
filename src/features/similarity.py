"""
Team Similarity Analysis using K-Nearest Neighbors (KNN).
Based on starter_pack/04_team_similarity.ipynb.
"""
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors
from typing import List, Tuple, Dict, Optional, Union

class TeamSimilarityModel:
    """
    Implements KNN-based team similarity analysis.
    """
    
    DEFAULT_METRICS = [
        'offense_ppa', 'offense_successRate', 'offense_explosiveness',
        'defense_ppa', 'defense_successRate', 'defense_explosiveness',
        'offense_lineYards', 'offense_secondLevelYards', 'offense_pointsPerOpportunity',
        'defense_lineYards', 'defense_secondLevelYards', 'defense_pointsPerOpportunity'
    ]

    def __init__(self, stats_df: pd.DataFrame, metrics: Optional[List[str]] = None):
        """
        Initialize and fit the similarity model.
        
        Args:
            stats_df: DataFrame containing team advanced stats
            metrics: List of column names to use for similarity (defaults to standard advanced stats)
        """
        self.metrics = metrics or self.DEFAULT_METRICS
        self.stats_df = stats_df.copy()
        
        # Filter to teams with data
        self.teams_data = self.stats_df.dropna(subset=self.metrics).reset_index(drop=True)
        
        if self.teams_data.empty:
            raise ValueError("No teams found with complete data for specified metrics")

        self.team_names = self.teams_data['team'].tolist()
        
        # Standardize and Fit
        self.scaler = StandardScaler()
        self.X = self.teams_data[self.metrics].copy()
        self.X_scaled = self.scaler.fit_transform(self.X)
        
        # Initialize KNN
        self.knn = NearestNeighbors(n_neighbors=min(len(self.teams_data), 20), metric='euclidean')
        self.knn.fit(self.X_scaled)

    def find_similar_teams(self, team_name: str, top_n: int = 5) -> List[Tuple[str, float]]:
        """
        Find most similar teams to the given team.
        
        Args:
            team_name: Name of the team to query
            top_n: Number of similar teams to return
            
        Returns:
            List of (team_name, distance) tuples
        """
        try:
            idx = self.team_names.index(team_name)
        except ValueError:
            print(f"Team '{team_name}' not found.")
            return []
        
        # Get k+1 neighbors (including itself)
        distances, indices = self.knn.kneighbors([self.X_scaled[idx]], n_neighbors=top_n + 1)
        
        results = []
        # Skip the first one (itself)
        for i in range(1, len(indices[0])):
            team_idx = indices[0][i]
            dist = distances[0][i]
            results.append((self.team_names[team_idx], float(dist)))
            
        return results

    def calculate_team_similarity_matrix(self) -> pd.DataFrame:
        """
        Calculate distance matrix for all teams.
        
        Returns:
            DataFrame where index and columns are team names, values are distances
        """
        # Calculate full distance matrix (using kneighbors_graph or pairwise distances)
        # For exact distances, we can use sklearn.metrics.pairwise.euclidean_distances
        from sklearn.metrics.pairwise import euclidean_distances
        
        dist_matrix = euclidean_distances(self.X_scaled, self.X_scaled)
        return pd.DataFrame(dist_matrix, index=self.team_names, columns=self.team_names)

    def get_team_profile(self, team_name: str) -> Optional[Dict[str, float]]:
        """Get standard metrics for a specific team."""
        if team_name not in self.team_names:
            return None
        
        record = self.teams_data[self.teams_data['team'] == team_name].iloc[0]
        return {m: float(record[m]) for m in self.metrics}

def find_similar_teams(stats_df: pd.DataFrame, team_name: str, top_n: int = 5) -> List[Tuple[str, float]]:
    """Functional interface for finding similar teams."""
    model = TeamSimilarityModel(stats_df)
    return model.find_similar_teams(team_name, top_n)

def calculate_team_similarity_matrix(stats_df: pd.DataFrame) -> pd.DataFrame:
    """Functional interface for similarity matrix."""
    model = TeamSimilarityModel(stats_df)
    return model.calculate_team_similarity_matrix()

