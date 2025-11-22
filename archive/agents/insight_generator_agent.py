#!/usr/bin/env python3
"""
Insight Generation Agent
Generates actionable insights and recommendations for betting/fantasy decisions
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from pathlib import Path

class InsightGeneratorAgent:
    """
    Agent responsible for generating actionable insights and recommendations
    """
    
    def __init__(self):
        self.data_path = Path("temp/processed_2025_data.csv")
        
    def generate_actionable_insights(self) -> Dict[str, Any]:
        """
        Generate actionable insights for betting and fantasy decisions
        """
        print("💡 Generating actionable insights...")
        
        # Load data
        if not self.data_path.exists():
            raise FileNotFoundError(f"Data not found: {self.data_path}")
        
        df = pd.read_csv(self.data_path)
        
        results = {
            "insights": [],
            "betting_recommendations": [],
            "fantasy_recommendations": [],
            "trend_analysis": [],
            "risk_assessment": {},
            "value_opportunities": [],
            "strategic_insights": []
        }
        
        # Generate betting recommendations
        betting_recs = self._generate_betting_recommendations(df)
        results["betting_recommendations"] = betting_recs
        results["insights"].extend([{"type": "betting", "insight": rec["recommendation"], "confidence": rec["confidence"]} for rec in betting_recs])
        
        # Generate fantasy recommendations
        fantasy_recs = self._generate_fantasy_recommendations(df)
        results["fantasy_recommendations"] = fantasy_recs
        results["insights"].extend([{"type": "fantasy", "insight": rec["recommendation"], "confidence": rec["confidence"]} for rec in fantasy_recs])
        
        # Analyze trends
        trend_analysis = self._analyze_trends(df)
        results["trend_analysis"] = trend_analysis
        results["insights"].extend([{"type": "trend", "insight": trend["insight"], "significance": trend["significance"]} for trend in trend_analysis])
        
        # Assess risks
        risk_assessment = self._assess_risks(df)
        results["risk_assessment"] = risk_assessment
        
        # Identify value opportunities
        value_opps = self._identify_value_opportunities(df)
        results["value_opportunities"] = value_opps
        
        # Generate strategic insights
        strategic_insights = self._generate_strategic_insights(df)
        results["strategic_insights"] = strategic_insights
        
        return results
    
    def _generate_betting_recommendations(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Generate betting recommendations with confidence levels
        """
        recommendations = []
        
        # Home team advantage analysis
        home_advantage = self._analyze_home_advantage(df)
        if home_advantage["home_win_pct"] > 0.55:
            recommendations.append({
                "type": "home_team_advantage",
                "recommendation": f"Home teams win {home_advantage['home_win_pct']:.1%} of the time - favor home teams in close matchups",
                "confidence": min(90, home_advantage['home_win_pct'] * 100),
                "data_support": f"{home_advantage['home_wins']}/{home_advantage['total_games']} home wins"
            })
        
        # Against the spread analysis
        ats_performance = self._analyze_ats_performance(df)
        if ats_performance["favorite_ats_pct"] < 0.45:
            recommendations.append({
                "type": "ats_favorite_buster",
                "recommendation": "Favorites are underperforming against the spread - consider backing underdogs",
                "confidence": 85,
                "data_support": f"Favorites only cover {ats_performance['favorite_ats_pct']:.1%} of spreads"
            })
        
        # Over/under analysis
        ou_performance = self._analyze_over_under_performance(df)
        if ou_performance["over_pct"] > 0.55:
            recommendations.append({
                "type": "over_favor",
                "recommendation": "Games are trending towards over the total - consider over bets",
                "confidence": min(80, ou_performance['over_pct'] * 100),
                "data_support": f"Over hits {ou_performance['over_pct']:.1%} of the time"
            })
        
        # Team-specific recommendations
        team_recommendations = self._generate_team_specific_betting_recs(df)
        recommendations.extend(team_recommendations)
        
        return sorted(recommendations, key=lambda x: x["confidence"], reverse=True)[:10]
    
    def _generate_fantasy_recommendations(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Generate fantasy football recommendations
        """
        recommendations = []
        
        # High-scoring teams
        high_scoring_teams = self._identify_high_scoring_teams(df)
        for team in high_scoring_teams[:5]:
            recommendations.append({
                "type": "high_scoring_team",
                "team": team["team"],
                "recommendation": f"Start players from {team['team']} - they average {team['avg_points']:.1f} PPG",
                "confidence": team["confidence"],
                "fantasy_positions": ["QB", "WR", "RB"]  # Positions likely to benefit
            })
        
        # Good matchups
        favorable_matchups = self._identify_fantasy_matchups(df)
        for matchup in favorable_matchups[:5]:
            recommendations.append({
                "type": "favorable_matchup",
                "team": matchup["team"],
                "opponent": matchup["opponent"],
                "recommendation": f"Start {matchup['team']} players against {matchup['opponent']} defense",
                "confidence": matchup["confidence"],
                "fantasy_positions": matchup["positions"]
            })
        
        # Consistent performers
        consistent_teams = self._identify_consistent_teams(df)
        for team in consistent_teams[:3]:
            recommendations.append({
                "type": "consistent_performance",
                "team": team["team"],
                "recommendation": f"Start {team['team']} players for consistent production",
                "confidence": team["consistency_score"],
                "fantasy_positions": ["FLEX", "D/ST"]
            })
        
        return recommendations
    
    def _analyze_trends(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Analyze trends and patterns in the data
        """
        trends = []
        
        # Scoring trends
        scoring_trend = self._analyze_scoring_trends(df)
        trends.append({
            "trend": "scoring",
            "insight": scoring_trend["insight"],
            "direction": scoring_trend["direction"],
            "significance": scoring_trend["significance"]
        })
        
        # Competitive game trends
        competitive_trend = self._analyze_competitive_trends(df)
        trends.append({
            "trend": "competitive_games",
            "insight": competitive_trend["insight"],
            "direction": competitive_trend["direction"],
            "significance": competitive_trend["significance"]
        })
        
        # Home/away performance trends
        home_away_trend = self._analyze_home_away_trends(df)
        trends.append({
            "trend": "home_away_performance",
            "insight": home_away_trend["insight"],
            "direction": home_away_trend["direction"],
            "significance": home_away_trend["significance"]
        })
        
        return trends
    
    def _assess_risks(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Assess various risk factors
        """
        risk_assessment = {
            "volatility_risk": self._assess_volatility_risk(df),
            "upset_risk": self._assess_upset_risk(df),
            "injury_impact_risk": self._assess_injury_impact_risk(df),
            "weather_impact_risk": self._assess_weather_impact_risk(df),
            "overall_risk_level": "Moderate"
        }
        
        # Calculate overall risk level
        risk_factors = [
            risk_assessment["volatility_risk"]["level"],
            risk_assessment["upset_risk"]["level"],
            risk_assessment["injury_impact_risk"]["level"],
            risk_assessment["weather_impact_risk"]["level"]
        ]
        
        risk_counts = {"High": 0, "Medium": 0, "Low": 0}
        for risk in risk_factors:
            risk_counts[risk] += 1
        
        if risk_counts["High"] >= 2:
            risk_assessment["overall_risk_level"] = "High"
        elif risk_counts["Medium"] >= 3 or risk_counts["High"] == 1:
            risk_assessment["overall_risk_level"] = "Moderate"
        else:
            risk_assessment["overall_risk_level"] = "Low"
        
        return risk_assessment
    
    def _identify_value_opportunities(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Identify value betting opportunities
        """
        opportunities = []
        
        # Undervalued teams
        undervalued_teams = self._identify_undervalued_teams(df)
        for team in undervalued_teams[:5]:
            opportunities.append({
                "type": "undervalued_team",
                "team": team["team"],
                "reason": team["reason"],
                "value_score": team["value_score"],
                "expected_return": team["expected_return"]
            })
        
        # Market inefficiencies
        market_inefficiencies = self._identify_market_inefficiencies(df)
        for inefficiency in market_inefficiencies[:3]:
            opportunities.append({
                "type": "market_inefficiency",
                "market": inefficiency["market"],
                "inefficiency": inefficiency["inefficiency"],
                "potential_value": inefficiency["potential_value"],
                "urgency": inefficiency["urgency"]
            })
        
        return opportunities
    
    def _generate_strategic_insights(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Generate strategic insights for decision making
        """
        insights = []
        
        # Key matchup strategies
        matchup_strategies = self._generate_matchup_strategies(df)
        insights.extend(matchup_strategies)
        
        # Long-term strategic recommendations
        strategic_recs = self._generate_strategic_recommendations(df)
        insights.extend(strategic_recs)
        
        return insights
    
    # Helper methods for betting recommendations
    def _analyze_home_advantage(self, df: pd.DataFrame) -> Dict[str, Any]:
        home_wins = len(df[df['home_score'] > df['away_score']])
        total_games = len(df)
        home_win_pct = home_wins / total_games
        return {
            "home_wins": home_wins,
            "total_games": total_games,
            "home_win_pct": home_win_pct
        }
    
    def _analyze_ats_performance(self, df: pd.DataFrame) -> Dict[str, Any]:
        # This is simplified - would need actual spread data
        favorites = df[df['spread'] > 0]
        favorite_wins = len(favorites[favorites['home_score'] > favorites['away_score']])
        favorite_ats_pct = favorite_wins / len(favorites) if len(favorites) > 0 else 0.5
        return {"favorite_ats_pct": favorite_ats_pct}
    
    def _analyze_over_under_performance(self, df: pd.DataFrame) -> Dict[str, Any]:
        over_hits = len(df[df['total_points'] > df['over_under']])
        over_pct = over_hits / len(df) if len(df) > 0 else 0.5
        return {"over_pct": over_pct}
    
    def _generate_team_specific_betting_recs(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        # Generate specific team betting recommendations
        recs = []
        
        for team in pd.concat([df['home_team'], df['away_team']]).unique():
            team_df = df[(df['home_team'] == team) | (df['away_team'] == team)]
            
            if len(team_df) >= 3:  # Minimum sample size
                home_record = len(team_df[team_df['home_team'] == team & (team_df['home_score'] > team_df['away_score'])])
                away_record = len(team_df[team_df['away_team'] == team & (team_df['away_score'] > team_df['home_score'])])
                
                if home_record > away_record and home_record / len(team_df[team_df['home_team'] == team]) > 0.7:
                    recs.append({
                        "type": "team_home_advantage",
                        "team": team,
                        "recommendation": f"{team} is dominant at home ({home_record}/{len(team_df[team_df['home_team'] == team])})",
                        "confidence": min(85, (home_record / len(team_df[team_df['home_team'] == team])) * 100)
                    })
        
        return recs[:3]
    
    # Helper methods for fantasy recommendations
    def _identify_high_scoring_teams(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        team_scores = {}
        
        for team in pd.concat([df['home_team'], df['away_team']]).unique():
            team_df = df[(df['home_team'] == team) | (df['away_team'] == team)]
            
            scores = []
            for _, row in team_df.iterrows():
                if row['home_team'] == team:
                    scores.append(row['home_score'])
                else:
                    scores.append(row['away_score'])
            
            if len(scores) > 0:
                team_scores[team] = {
                    "team": team,
                    "avg_points": np.mean(scores),
                    "confidence": min(90, len(scores) * 10)
                }
        
        return sorted(team_scores.values(), key=lambda x: x["avg_points"], reverse=True)
    
    def _identify_fantasy_matchups(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        # Simplified - would need defensive rankings
        return []
    
    def _identify_consistent_teams(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        team_consistency = {}
        
        for team in pd.concat([df['home_team'], df['away_team']]).unique():
            team_df = df[(df['home_team'] == team) | (df['away_team'] == team)]
            
            scores = []
            for _, row in team_df.iterrows():
                if row['home_team'] == team:
                    scores.append(row['home_score'])
                else:
                    scores.append(row['away_score'])
            
            if len(scores) > 2:
                std_dev = np.std(scores)
                avg_score = np.mean(scores)
                consistency_score = max(0, 1 - (std_dev / avg_score)) if avg_score > 0 else 0
                
                team_consistency[team] = {
                    "team": team,
                    "consistency_score": consistency_score * 100,
                    "std_dev": std_dev
                }
        
        return sorted(team_consistency.values(), key=lambda x: x["consistency_score"], reverse=True)
    
    # Other helper methods (simplified implementations)
    def _analyze_scoring_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        avg_score = (df['home_score'] + df['away_score']).mean()
        return {
            "insight": f"Average score is {avg_score:.1f} points per game",
            "direction": "stable" if 40 <= avg_score <= 50 else "increasing" if avg_score > 50 else "decreasing",
            "significance": "High"
        }
    
    def _analyze_competitive_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        close_games = len(df[abs(df['home_score'] - df['away_score']) <= 7])
        close_pct = close_games / len(df)
        return {
            "insight": f"{close_pct:.1%} of games are decided by 7 points or less",
            "direction": "competitive" if close_pct > 0.4 else "decisive",
            "significance": "Medium"
        }
    
    def _analyze_home_away_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        home_win_pct = len(df[df['home_score'] > df['away_score']]) / len(df)
        return {
            "insight": f"Home teams win {home_win_pct:.1%} of games",
            "direction": "home_favorable" if home_win_pct > 0.55 else "balanced",
            "significance": "High"
        }
    
    # Risk assessment methods
    def _assess_volatility_risk(self, df: pd.DataFrame) -> Dict[str, Any]:
        score_diffs = abs(df['home_score'] - df['away_score'])
        avg_diff = score_diffs.mean()
        if avg_diff > 20:
            return {"level": "High", "reason": "High scoring variance"}
        elif avg_diff > 15:
            return {"level": "Medium", "reason": "Moderate scoring variance"}
        else:
            return {"level": "Low", "reason": "Low scoring variance"}
    
    def _assess_upset_risk(self, df: pd.DataFrame) -> Dict[str, Any]:
        upsets = len(df[abs(df['home_score'] - df['away_score']) <= 3])
        upset_pct = upsets / len(df)
        if upset_pct > 0.3:
            return {"level": "High", "reason": "High upset frequency"}
        elif upset_pct > 0.2:
            return {"level": "Medium", "reason": "Moderate upset frequency"}
        else:
            return {"level": "Low", "reason": "Low upset frequency"}
    
    def _assess_injury_impact_risk(self, df: pd.DataFrame) -> Dict[str, Any]:
        # Simplified - would need injury data
        return {"level": "Medium", "reason": "Standard injury risk"}
    
    def _assess_weather_impact_risk(self, df: pd.DataFrame) -> Dict[str, Any]:
        # Simplified - would need weather data
        return {"level": "Low", "reason": "No significant weather data available"}
    
    # Value opportunity methods
    def _identify_undervalued_teams(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        # Simplified value identification
        undervalued = []
        for team in pd.concat([df['home_team'], df['away_team']]).unique():
            team_df = df[(df['home_team'] == team) | (df['away_team'] == team)]
            
            wins = len(team_df[(team_df['home_team'] == team) & (team_df['home_score'] > team_df['away_score'])]) + \
                   len(team_df[(team_df['away_team'] == team) & (team_df['away_score'] > team_df['home_score'])])
            
            win_pct = wins / len(team_df) if len(team_df) > 0 else 0
            
            if win_pct > 0.6 and len(team_df) > 2:
                undervalued.append({
                    "team": team,
                    "reason": f"{team} has {win_pct:.1%} win rate",
                    "value_score": win_pct * 100,
                    "expected_return": f"+{(win_pct - 0.5) * 100:.1f}%"
                })
        
        return sorted(undervalued, key=lambda x: x["value_score"], reverse=True)
    
    def _identify_market_inefficiencies(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        # Simplified market inefficiency detection
        return []
    
    # Strategic insights methods
    def _generate_matchup_strategies(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        strategies = []
        
        # High-scoring game strategy
        high_scoring_games = df[df['total_points'] > 65]
        if len(high_scoring_games) > len(df) * 0.4:
            strategies.append({
                "type": "matchup_strategy",
                "insight": "High-scoring games are common - consider stacking offenses",
                "priority": "High"
            })
        
        return strategies
    
    def _generate_strategic_recommendations(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        recommendations = []
        
        # Long-term trend analysis
        if len(df) > 10:
            recent_games = df.tail(5)
            older_games = df.head(len(df) - 5)
            
            recent_avg = (recent_games['home_score'] + recent_games['away_score']).mean()
            older_avg = (older_games['home_score'] + older_games['away_score']).mean()
            
            if recent_avg > older_avg:
                recommendations.append({
                    "type": "strategic_trend",
                    "insight": "Scoring is increasing - adjust strategies accordingly",
                    "timeframe": "Long-term",
                    "impact": "High"
                })
        
        return recommendations

if __name__ == "__main__":
    agent = InsightGeneratorAgent()
    result = agent.generate_actionable_insights()
    print(json.dumps(result, indent=2))
