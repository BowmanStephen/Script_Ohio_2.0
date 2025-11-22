#!/usr/bin/env python3
"""
Enhanced Week 13 Analysis Script
================================

Creates comprehensive Week 13 analysis with:
- Conference championship implications
- Playoff impact analysis
- Rivalry game highlights
- Weather and situational factors
- Betting market context
- Advanced statistical breakdowns

Usage:
    python scripts/enhance_week13_analysis.py
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

import pandas as pd

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Output directory
ANALYSIS_DIR = PROJECT_ROOT / "analysis" / "week13"
ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)


class Week13AnalysisEnhancer:
    """Enhance Week 13 analysis with comprehensive insights"""
    
    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.analysis_dir = ANALYSIS_DIR
        # Use canonical path for weekly enhanced data
        from model_pack.utils.path_utils import get_weekly_enhanced_dir
        self.week13_data_dir = get_weekly_enhanced_dir(13, 2025)
        self.starter_games = self.project_root / "starter_pack" / "data" / "games.csv"
        
        # Results storage
        self.enhanced_analysis = {
            "analysis_date": datetime.now().isoformat(),
            "week": 13,
            "season": 2025,
            "enhancements": {}
        }
    
    def load_week13_data(self) -> pd.DataFrame:
        """Load Week 13 games data"""
        print("\n" + "=" * 80)
        print("LOADING WEEK 13 DATA")
        print("=" * 80)
        
        # Try enhanced games first
        enhanced_games_path = self.week13_data_dir / "week13_enhanced_games.csv"
        if enhanced_games_path.exists():
            print(f"Loading: {enhanced_games_path}")
            return pd.read_csv(enhanced_games_path, low_memory=False)
        
        # Fallback to starter pack
        if self.starter_games.exists():
            print(f"Loading from starter pack: {self.starter_games}")
            games_df = pd.read_csv(self.starter_games, low_memory=False)
            week13_games = games_df[
                (games_df['season'] == 2025) & 
                (games_df['week'] == 13)
            ].copy()
            return week13_games
        
        raise FileNotFoundError("Week 13 data not found")
    
    def analyze_conference_championship_implications(self, games_df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze conference championship implications"""
        print("\n" + "=" * 80)
        print("ANALYZING CONFERENCE CHAMPIONSHIP IMPLICATIONS")
        print("=" * 80)
        
        # Identify conference games
        conference_games = games_df[
            (games_df['home_conference'].notna()) &
            (games_df['away_conference'].notna()) &
            (games_df['home_conference'] == games_df['away_conference'])
        ].copy()
        
        # Group by conference
        conference_analysis = {}
        for conf in conference_games['home_conference'].unique():
            conf_games = conference_games[conference_games['home_conference'] == conf]
            conference_analysis[conf] = {
                "game_count": len(conf_games),
                "teams": sorted(set(conf_games['home_team'].tolist() + conf_games['away_team'].tolist())),
                "games": conf_games[['home_team', 'away_team', 'id']].to_dict('records')
            }
        
        print(f"Found {len(conference_games)} conference games")
        print(f"Conferences: {list(conference_analysis.keys())}")
        
        self.enhanced_analysis["enhancements"]["conference_championship"] = {
            "total_conference_games": len(conference_games),
            "conferences": conference_analysis,
            "championship_impact": "High - Week 13 typically includes key conference matchups"
        }
        
        return conference_analysis
    
    def analyze_playoff_implications(self, games_df: pd.DataFrame) -> Dict[str, Any]:
        """Identify playoff-impact games"""
        print("\n" + "=" * 80)
        print("ANALYZING PLAYOFF IMPLICATIONS")
        print("=" * 80)
        
        # Load existing analysis if available
        existing_analysis_path = self.analysis_dir / "week13_comprehensive_analysis.json"
        playoff_games = []
        
        if existing_analysis_path.exists():
            with open(existing_analysis_path, 'r') as f:
                existing = json.load(f)
                # Extract high-impact games from existing analysis
                team_rankings = existing.get("team_rankings", [])
                top_teams = {team["team"] for team in team_rankings[:20]}  # Top 20 teams
        
        # Identify games with top teams
        high_impact_games = []
        for _, game in games_df.iterrows():
            home_team = game.get('home_team', '')
            away_team = game.get('away_team', '')
            
            # Check if either team is highly ranked (would need rankings data)
            # For now, use Elo ratings as proxy
            home_elo = game.get('home_elo', 0) or game.get('home_start_elo', 0) or 0
            away_elo = game.get('away_elo', 0) or game.get('away_start_elo', 0) or 0
            
            if home_elo > 1800 or away_elo > 1800:  # Top teams typically have Elo > 1800
                high_impact_games.append({
                    "game_id": game.get('id'),
                    "home_team": home_team,
                    "away_team": away_team,
                    "home_elo": float(home_elo),
                    "away_elo": float(away_elo),
                    "playoff_impact": "High"
                })
        
        print(f"Found {len(high_impact_games)} high-impact games")
        
        self.enhanced_analysis["enhancements"]["playoff_implications"] = {
            "high_impact_games": high_impact_games,
            "total_high_impact": len(high_impact_games),
            "playoff_race_status": "Week 13 is critical for playoff positioning"
        }
        
        return {"high_impact_games": high_impact_games}
    
    def identify_rivalry_games(self, games_df: pd.DataFrame) -> Dict[str, Any]:
        """Identify rivalry games"""
        print("\n" + "=" * 80)
        print("IDENTIFYING RIVALRY GAMES")
        print("=" * 80)
        
        # Common rivalry patterns (Week 13 often has rivalry games)
        known_rivalries = [
            ("Ohio State", "Michigan"),
            ("Alabama", "Auburn"),
            ("Oklahoma", "Texas"),
            ("USC", "UCLA"),
            ("Florida", "Florida State"),
            ("Clemson", "South Carolina"),
            ("Georgia", "Georgia Tech"),
            ("Notre Dame", "USC"),
            ("Oregon", "Oregon State"),
            ("Washington", "Washington State")
        ]
        
        rivalry_games = []
        for _, game in games_df.iterrows():
            home_team = str(game.get('home_team', '')).strip()
            away_team = str(game.get('away_team', '')).strip()
            
            # Check for known rivalries
            for team1, team2 in known_rivalries:
                if (team1 in home_team and team2 in away_team) or \
                   (team2 in home_team and team1 in away_team):
                    rivalry_games.append({
                        "game_id": game.get('id'),
                        "home_team": home_team,
                        "away_team": away_team,
                        "rivalry": f"{team1} vs {team2}",
                        "rivalry_type": "Traditional"
                    })
                    break
        
        print(f"Found {len(rivalry_games)} rivalry games")
        
        self.enhanced_analysis["enhancements"]["rivalry_games"] = {
            "total_rivalries": len(rivalry_games),
            "games": rivalry_games,
            "rivalry_week": "Week 13 is Rivalry Week in college football"
        }
        
        return {"rivalry_games": rivalry_games}
    
    def analyze_situational_factors(self, games_df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze situational factors (home/away, rest days, etc.)"""
        print("\n" + "=" * 80)
        print("ANALYZING SITUATIONAL FACTORS")
        print("=" * 80)
        
        situational_analysis = {
            "home_games": len(games_df[games_df.get('neutral_site', False) == False]),
            "neutral_site_games": len(games_df[games_df.get('neutral_site', False) == True]),
            "conference_games": len(games_df[
                (games_df.get('home_conference', '').notna()) &
                (games_df.get('away_conference', '').notna()) &
                (games_df.get('home_conference') == games_df.get('away_conference'))
            ])
        }
        
        # Analyze by day of week (if start_date available)
        if 'start_date' in games_df.columns:
            games_df['start_date'] = pd.to_datetime(games_df['start_date'], errors='coerce')
            games_df['day_of_week'] = games_df['start_date'].dt.day_name()
            day_distribution = games_df['day_of_week'].value_counts().to_dict()
            situational_analysis["day_distribution"] = day_distribution
        
        print(f"Home games: {situational_analysis['home_games']}")
        print(f"Neutral site: {situational_analysis['neutral_site_games']}")
        print(f"Conference games: {situational_analysis['conference_games']}")
        
        self.enhanced_analysis["enhancements"]["situational_factors"] = situational_analysis
        
        return situational_analysis
    
    def add_betting_market_context(self, games_df: pd.DataFrame) -> Dict[str, Any]:
        """Add betting market context"""
        print("\n" + "=" * 80)
        print("ADDING BETTING MARKET CONTEXT")
        print("=" * 80)
        
        betting_analysis = {
            "games_with_spreads": 0,
            "average_abs_spread": 0.0,
            "close_games": 0,  # Spread < 7
            "blowout_potential": 0  # Spread > 14
        }
        
        if 'spread' in games_df.columns:
            spreads = games_df['spread'].dropna()
            if len(spreads) > 0:
                betting_analysis["games_with_spreads"] = len(spreads)
                betting_analysis["average_abs_spread"] = float(spreads.abs().mean())
                betting_analysis["close_games"] = int((spreads.abs() < 7).sum())
                betting_analysis["blowout_potential"] = int((spreads.abs() > 14).sum())
        
        print(f"Games with spreads: {betting_analysis['games_with_spreads']}")
        print(f"Average absolute spread: {betting_analysis['average_abs_spread']:.2f}")
        print(f"Close games (<7): {betting_analysis['close_games']}")
        print(f"Blowout potential (>14): {betting_analysis['blowout_potential']}")
        
        self.enhanced_analysis["enhancements"]["betting_market"] = betting_analysis
        
        return betting_analysis
    
    def generate_advanced_statistical_breakdowns(self, games_df: pd.DataFrame) -> Dict[str, Any]:
        """Generate advanced statistical breakdowns"""
        print("\n" + "=" * 80)
        print("GENERATING ADVANCED STATISTICAL BREAKDOWNS")
        print("=" * 80)
        
        # Robust FBS check
        if 'home_classification' in games_df.columns and 'away_classification' in games_df.columns:
            fbs_games_count = len(games_df[
                (games_df['home_classification'] == 'fbs') &
                (games_df['away_classification'] == 'fbs')
            ])
        else:
            # Assume all are FBS if classification missing (since we filtered for FBS in acquisition)
            fbs_games_count = len(games_df)

        statistical_breakdowns = {
            "total_games": len(games_df),
            "fbs_games": fbs_games_count,
            "teams_involved": len(set(games_df['home_team'].dropna().tolist() + 
                                    games_df['away_team'].dropna().tolist())),
            "conferences_represented": len(set(
                games_df['home_conference'].dropna().tolist() + 
                games_df['away_conference'].dropna().tolist()
            ))
        }
        
        # Elo distribution
        if 'home_elo' in games_df.columns or 'home_start_elo' in games_df.columns:
            home_elo_col = 'home_elo' if 'home_elo' in games_df.columns else 'home_start_elo'
            away_elo_col = 'away_elo' if 'away_elo' in games_df.columns else 'away_start_elo'
            
            all_elos = pd.concat([
                games_df[home_elo_col].dropna(),
                games_df[away_elo_col].dropna()
            ])
            
            statistical_breakdowns["elo_statistics"] = {
                "mean": float(all_elos.mean()),
                "median": float(all_elos.median()),
                "min": float(all_elos.min()),
                "max": float(all_elos.max()),
                "std": float(all_elos.std())
            }
        
        print(f"Total games: {statistical_breakdowns['total_games']}")
        print(f"FBS games: {statistical_breakdowns['fbs_games']}")
        print(f"Teams involved: {statistical_breakdowns['teams_involved']}")
        
        self.enhanced_analysis["enhancements"]["statistical_breakdowns"] = statistical_breakdowns
        
        return statistical_breakdowns
    
    def save_enhanced_analysis(self) -> Path:
        """Save enhanced analysis"""
        output_path = self.analysis_dir / "week13_enhanced_analysis.json"
        
        with open(output_path, 'w') as f:
            json.dump(self.enhanced_analysis, f, indent=2, default=str)
        
        print(f"\n✅ Enhanced analysis saved to: {output_path}")
        return output_path
    
    def run_enhancement(self) -> Dict[str, Any]:
        """Run complete enhancement process"""
        print("=" * 80)
        print("WEEK 13 ANALYSIS ENHANCEMENT")
        print("=" * 80)
        print(f"Enhancement Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Season: 2025, Week: 13")
        
        # Load Week 13 data
        games_df = self.load_week13_data()
        print(f"Loaded {len(games_df)} Week 13 games")
        
        # Run all enhancements
        self.analyze_conference_championship_implications(games_df)
        self.analyze_playoff_implications(games_df)
        self.identify_rivalry_games(games_df)
        self.analyze_situational_factors(games_df)
        self.add_betting_market_context(games_df)
        self.generate_advanced_statistical_breakdowns(games_df)
        
        # Save enhanced analysis
        output_path = self.save_enhanced_analysis()
        
        return {
            "status": "success",
            "output_path": str(output_path),
            "games_analyzed": len(games_df),
            "enhancements": list(self.enhanced_analysis["enhancements"].keys())
        }


def main():
    """Main execution"""
    enhancer = Week13AnalysisEnhancer()
    results = enhancer.run_enhancement()
    
    print("\n" + "=" * 80)
    print("ENHANCEMENT COMPLETE")
    print("=" * 80)
    print(f"Output: {results['output_path']}")
    print(f"Games Analyzed: {results['games_analyzed']}")
    print(f"Enhancements: {', '.join(results['enhancements'])}")
    
    return 0 if results['status'] == 'success' else 1


if __name__ == "__main__":
    sys.exit(main())
