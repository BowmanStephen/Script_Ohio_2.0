#!/usr/bin/env python3
"""
Matchup Prediction Agent
Generates matchup predictions with confidence scores
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from pathlib import Path

class MatchupPredictionAgent:
    """
    Agent responsible for generating matchup predictions
    """
    
    def __init__(self):
        self.data_path = Path("temp/processed_2025_data.csv")
        
    def generate_matchup_predictions(self) -> Dict[str, Any]:
        """
        Generate matchup predictions with confidence scores
        """
        print("🎯 Generating matchup predictions...")
        
        # Load data
        if not self.data_path.exists():
            raise FileNotFoundError(f"Data not found: {self.data_path}")
        
        df = pd.read_csv(self.data_path)
        
        results = {
            "predictions": [],
            "upset_predictions": [],
            "confidence_analysis": {},
            "matchup_trends": {},
            "top_matchups": []
        }
        
        # Generate predictions for existing matchups
        matchup_predictions = self._predict_existing_matchups(df)
        results["predictions"] = matchup_predictions
        
        # Identify potential upset predictions
        upset_predictions = self._identify_upset_predictions(matchup_predictions)
        results["upset_predictions"] = upset_predictions
        
        # Analyze confidence levels
        confidence_analysis = self._analyze_confidence_levels(matchup_predictions)
        results["confidence_analysis"] = confidence_analysis
        
        # Analyze matchup trends
        matchup_trends = self._analyze_matchup_trends(df)
        results["matchup_trends"] = matchup_trends
        
        # Identify top matchups of interest
        top_matchups = self._identify_top_matchups(matchup_predictions)
        results["top_matchups"] = top_matchups
        
        return results
    
    def _predict_existing_matchups(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Predict outcomes for existing game matchups
        """
        predictions = []
        
        for _, row in df.iterrows():
            home_team = row['home_team']
            away_team = row['away_team']
            
            # Calculate team strengths
            home_strength = self._calculate_team_strength(df, home_team)
            away_strength = self._calculate_team_strength(df, away_team)
            
            # Predict winner and spread
            prediction = self._predict_matchup_outcome(home_team, away_team, home_strength, away_strength)
            prediction["game_info"] = {
                "home_team": home_team,
                "away_team": away_team,
                "actual_home_score": row['home_score'],
                "actual_away_score": row['away_score'],
                "week": row.get('week', 'unknown'),
                "year": row.get('year', 2025)
            }
            
            predictions.append(prediction)
        
        return predictions
    
    def _identify_upset_predictions(self, predictions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Identify potential upset predictions
        """
        upset_predictions = []
        
        for prediction in predictions:
            home_team = prediction["home_team"]
            away_team = prediction["away_team"]
            predicted_winner = prediction["predicted_winner"]
            
            # Determine if this is an upset situation
            if predicted_winner in [home_team, away_team]:
                underdog = away_team if predicted_winner == home_team else home_team
                favorite = home_team if predicted_winner == home_team else away_team
                
                # Check if confidence is moderate and spread is small
                if prediction["confidence_score"] < 75 and abs(prediction["predicted_spread"]) < 7:
                    upset = {
                        "underdog": underdog,
                        "favorite": favorite,
                        "predicted_winner": predicted_winner,
                        "confidence_score": prediction["confidence_score"],
                        "reasoning": f"Potential upset: {underdog} could beat {favorite}",
                        "risk_level": self._calculate_upset_risk(prediction)
                    }
                    upset_predictions.append(upset)
        
        return upset_predictions[:10]  # Top 10 upset predictions
    
    def _analyze_confidence_levels(self, predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze confidence levels across predictions
        """
        confidence_scores = [p["confidence_score"] for p in predictions]
        
        analysis = {
            "average_confidence": np.mean(confidence_scores),
            "confidence_distribution": {
                "high_confidence": len([c for c in confidence_scores if c >= 80]),
                "medium_confidence": len([c for c in confidence_scores if 60 <= c < 80]),
                "low_confidence": len([c for c in confidence_scores if c < 60])
            },
            "most_confident_predictions": sorted(predictions, key=lambda x: x["confidence_score"], reverse=True)[:5],
            "least_confident_predictions": sorted(predictions, key=lambda x: x["confidence_score"])[:5]
        }
        
        return analysis
    
    def _analyze_matchup_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze matchup trends and patterns
        """
        trends = {
            "home_team_advantage": self._calculate_home_advantage(df),
            "point_spread_trends": self._analyze_spread_trends(df),
            "high_scoring_games": self._identify_high_scoring_games(df),
            "competitive_games": self._identify_competitive_games(df)
        }
        
        return trends
    
    def _identify_top_matchups(self, predictions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Identify top matchups of interest
        """
        top_matchups = []
        
        for prediction in predictions:
            # Calculate matchup interest score
            home_team = prediction["home_team"]
            away_team = prediction["away_team"]
            confidence = prediction["confidence_score"]
            spread = abs(prediction["predicted_spread"])
            
            # High interest criteria
            interest_score = 0
            
            # Close games are interesting
            if spread <= 10:
                interest_score += 3
            
            # Moderate confidence games are interesting
            if 60 <= confidence <= 80:
                interest_score += 2
            
            # High-profile teams (simplified - would use team rankings)
            if home_team in ["Ohio State", "Michigan", "Alabama", "Clemson"] or \
               away_team in ["Ohio State", "Michigan", "Alabama", "Clemson"]:
                interest_score += 2
            
            if interest_score >= 5:
                top_matchups.append({
                    "home_team": home_team,
                    "away_team": away_team,
                    "predicted_winner": prediction["predicted_winner"],
                    "predicted_spread": prediction["predicted_spread"],
                    "confidence_score": confidence,
                    "interest_score": interest_score,
                    "reasoning": self._get_interest_reasoning(home_team, away_team, spread, confidence)
                })
        
        return sorted(top_matchups, key=lambda x: x["interest_score"], reverse=True)[:10]
    
    def _calculate_team_strength(self, df: pd.DataFrame, team: str) -> float:
        """
        Calculate team strength based on multiple factors
        """
        team_df = df[(df['home_team'] == team) | (df['away_team'] == team)]
        
        if len(team_df) == 0:
            return 0.5  # Default strength
        
        # Win percentage
        wins = len(team_df[(team_df['home_team'] == team) & (team_df['home_score'] > team_df['away_score'])]) + \
               len(team_df[(team_df['away_team'] == team) & (team_df['away_score'] > team_df['home_score'])])
        win_pct = wins / len(team_df)
        
        # Average margin
        margins = []
        for _, row in team_df.iterrows():
            if row['home_team'] == team:
                margins.append(row['home_score'] - row['away_score'])
            else:
                margins.append(row['away_score'] - row['home_score'])
        avg_margin = np.mean(margins) if len(margins) > 0 else 0
        
        # Combine metrics (normalized to 0-1 scale)
        strength = (win_pct * 0.6) + (max(0, avg_margin) / 30 * 0.4)
        return max(0, min(1, strength))
    
    def _predict_matchup_outcome(self, home_team: str, away_team: str, home_strength: float, away_strength: float) -> Dict[str, Any]:
        """
        Predict matchup outcome between two teams
        """
        # Calculate win probability
        if home_strength > away_strength:
            home_win_prob = home_strength / (home_strength + away_strength)
            predicted_winner = home_team
            predicted_spread = (home_strength - away_strength) * 14  # Convert to points
        else:
            home_win_prob = away_strength / (home_strength + away_strength)
            predicted_winner = away_team
            predicted_spread = (away_strength - home_strength) * -14  # Negative spread for away win
        
        # Adjust for home field advantage (simplified)
        home_win_prob = home_win_prob * 0.55 + 0.45  # 55% home advantage
        predicted_spread += 2.5  # Home field advantage in points
        
        # Calculate confidence score
        confidence_score = min(100, home_win_prob * 100)
        
        return {
            "home_team": home_team,
            "away_team": away_team,
            "predicted_winner": predicted_winner,
            "predicted_spread": predicted_spread,
            "home_win_probability": home_win_prob,
            "confidence_score": confidence_score,
            "reasoning": self._get_prediction_reasoning(home_team, away_team, home_strength, away_strength)
        }
    
    # Helper methods
    def _calculate_upset_risk(self, prediction: Dict[str, Any]) -> str:
        """Calculate risk level for upset prediction"""
        confidence = prediction["confidence_score"]
        spread = abs(prediction["predicted_spread"])
        
        if confidence < 50 and spread <= 3:
            return "High"
        elif confidence < 65 and spread <= 7:
            return "Medium"
        else:
            return "Low"
    
    def _calculate_home_advantage(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate home team advantage statistics"""
        home_wins = len(df[df['home_score'] > df['away_score']])
        total_games = len(df)
        home_win_pct = home_wins / total_games
        
        return {
            "home_win_percentage": home_win_pct,
            "total_games": total_games,
            "home_wins": home_wins,
            "average_home_margin": (df['home_score'] - df['away_score']).mean()
        }
    
    def _analyze_spread_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze point spread trends"""
        spreads = df['spread'].dropna()
        
        return {
            "average_spread": spreads.mean(),
            "median_spread": spreads.median(),
            "max_spread": spreads.max(),
            "min_spread": spreads.min(),
            "spread_distribution": {
                "small_spreads": len(spreads[spreads.abs() <= 7]),
                "medium_spreads": len(spreads[(spreads.abs() > 7) & (spreads.abs() <= 14)]),
                "large_spreads": len(spreads[spreads.abs() > 14])
            }
        }
    
    def _identify_high_scoring_games(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Identify high-scoring games"""
        high_scoring = df[df['total_points'] > 70]
        
        results = []
        for _, row in high_scoring.iterrows():
            results.append({
                "home_team": row['home_team'],
                "away_team": row['away_team'],
                "total_points": row['total_points'],
                "home_score": row['home_score'],
                "away_score": row['away_score']
            })
        
        return sorted(results, key=lambda x: x["total_points"], reverse=True)[:5]
    
    def _identify_competitive_games(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Identify competitive games (close scores)"""
        competitive = df[df['spread'].abs() <= 7]
        
        results = []
        for _, row in competitive.iterrows():
            results.append({
                "home_team": row['home_team'],
                "away_team": row['away_team'],
                "margin": abs(row['home_score'] - row['away_score']),
                "total_points": row['total_points']
            })
        
        return sorted(results, key=lambda x: x["margin"])[:5]
    
    def _get_interest_reasoning(self, home_team: str, away_team: str, spread: float, confidence: float) -> str:
        """Get reasoning for why a matchup is interesting"""
        reasons = []
        
        if spread <= 7:
            reasons.append("Close matchup")
        if 60 <= confidence <= 80:
            reasons.append("Moderate confidence creates intrigue")
        if home_team in ["Ohio State", "Michigan", "Alabama", "Clemson"] or \
           away_team in ["Ohio State", "Michigan", "Alabama", "Clemson"]:
            reasons.append("High-profile teams involved")
        
        return "; ".join(reasons) if reasons else "Regular matchup"
    
    def _get_prediction_reasoning(self, home_team: str, away_team: str, home_strength: float, away_strength: float) -> str:
        """Get reasoning for prediction"""
        diff = abs(home_strength - away_strength)
        if diff > 0.3:
            stronger = home_team if home_strength > away_strength else away_team
            weaker = away_team if home_strength > away_strength else home_team
            return f"{stronger} significantly stronger than {weaker}"
        elif diff > 0.1:
            return "Relatively evenly matched teams"
        else:
            return "Very evenly matched teams"

if __name__ == "__main__":
    agent = MatchupPredictionAgent()
    result = agent.generate_matchup_predictions()
    print(json.dumps(result, indent=2))
