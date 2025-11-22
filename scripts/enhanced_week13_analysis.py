#!/usr/bin/env python3
"""
Enhanced Week 13 Comprehensive Analysis

This script generates a comprehensive analysis for Week 13 games,
including conference championship implications, playoff impact, and advanced insights.

Author: Claude Code Assistant
Created: 2025-11-18
Version: 1.0
"""

import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Set
import json
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns

# Add project root to path
project_root = os.path.dirname(os.path.dirname(__file__))
if os.path.exists(project_root):
    sys.path.insert(0, project_root)

class EnhancedWeek13Analyzer:
    """Enhanced Week 13 analysis with comprehensive insights"""

    def __init__(self):
        self.project_root = Path(project_root)
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'analysis_summary': {},
            'conference_championships': {},
            'playoff_implications': {},
            'rivalry_games': {},
            'top_matchups': {},
            'betting_insights': {},
            'weather_factors': {},
            'strategic_recommendations': []
        }

    def load_week13_data(self) -> Dict:
        """Load all Week 13 related data"""
        print("📊 Loading Week 13 data...")

        data = {
            'predictions': None,
            'comprehensive': None,
            'training_data': None,
            'team_stats': None
        }

        try:
            # Load comprehensive predictions
            comp_file = self.project_root / "predictions" / "week13" / "week13_comprehensive_predictions.csv"
            if comp_file.exists():
                data['comprehensive'] = pd.read_csv(comp_file)
                print(f"  ✅ Loaded comprehensive predictions: {data['comprehensive'].shape}")

            # Load training data for team strength context
            training_file = self.project_root / "model_pack" / "updated_training_data.csv"
            if training_file.exists():
                data['training_data'] = pd.read_csv(training_file)
                print(f"  ✅ Loaded training data: {data['training_data'].shape}")

        except Exception as e:
            print(f"  ❌ Error loading data: {str(e)}")

        return data

    def analyze_conference_championships(self, data: Dict) -> Dict:
        """Analyze conference championship implications"""
        print("\n🏆 Analyzing Conference Championship Implications...")

        if data['comprehensive'] is None:
            print("  ⚠️  No Week 13 data available")
            return {}

        df = data['comprehensive'].copy()

        # Define conference championship games (major conferences)
        championship_matchups = [
            # ACC Championship
            {'home': 'Clemson', 'away': 'SMU', 'conference': 'ACC'},
            # Big 10 Championship
            {'home': 'Oregon', 'away': 'Penn State', 'conference': 'Big Ten'},
            # Big 12 Championship
            {'home': 'Arizona State', 'away': 'Iowa State', 'conference': 'Big 12'},
            # SEC Championship
            {'home': 'Georgia', 'away': 'Texas', 'conference': 'SEC'}
        ]

        championship_analysis = {
            'games': [],
            'playoff_implications': [],
            'team_strength_comparison': []
        }

        for matchup in championship_matchups:
            # Find the game in predictions
            game = df[
                ((df['home_team'] == matchup['home']) & (df['away_team'] == matchup['away'])) |
                ((df['home_team'] == matchup['away']) & (df['away_team'] == matchup['home']))
            ]

            if len(game) > 0:
                game_data = game.iloc[0].to_dict()
                game_data['conference'] = matchup['conference']
                game_data['championship_type'] = 'Conference Championship'

                # Determine playoff implications
                is_favorite = game_data['predicted_winner'] == matchup['home']
                win_prob = game_data['home_win_probability'] if matchup['home'] == game_data['home_team'] else game_data['away_win_probability']

                playoff_implication = {
                    'team': game_data['predicted_winner'],
                    'conference': matchup['conference'],
                    'playoff_probability': 'HIGH' if win_prob > 0.6 else 'MEDIUM' if win_prob > 0.4 else 'LOW',
                    'championship_importance': 'CRITICAL'
                }

                championship_analysis['games'].append(game_data)
                championship_analysis['playoff_implications'].append(playoff_implication)

                print(f"  🏈 {matchup['conference']}: {matchup['home']} vs {matchup['away']}")
                print(f"     Prediction: {game_data['predicted_winner']} ({win_prob:.1%})")

        self.results['conference_championships'] = championship_analysis
        return championship_analysis

    def analyze_rivalry_games(self, data: Dict) -> Dict:
        """Analyze major rivalry games in Week 13"""
        print("\n⚔️ Analyzing Rivalry Games...")

        if data['comprehensive'] is None:
            return {}

        df = data['comprehensive'].copy()

        # Define major rivalries
        rivalries = [
            {'teams': ['Ohio State', 'Michigan'], 'name': 'The Game'},
            {'teams': ['Alabama', 'Auburn'], 'name': 'Iron Bowl'},
            {'teams': ['Oklahoma', 'Oklahoma State'], 'name': 'Bedlam'},
            {'teams': ['Oregon', 'Oregon State'], 'name': 'Civil War'},
            {'teams': ['USC', 'UCLA'], 'name': 'Crosstown Showdown'},
            {'teams': ['Notre Dame', 'USC'], 'name': 'Notre Dame-USC'},
            {'teams': ['Georgia', 'Georgia Tech'], 'name': 'Clean Old-Fashioned Hate'},
            {'teams': ['Florida', 'Florida State'], 'name': 'Sunshine Showdown'}
        ]

        rivalry_analysis = {
            'games': [],
            'competitive_balance': [],
            'historical_context': []
        }

        for rivalry in rivalries:
            # Find the rivalry game
            game = df[
                ((df['home_team'].isin(rivalry['teams'])) & (df['away_team'].isin(rivalry['teams'])))
            ]

            if len(game) > 0:
                game_data = game.iloc[0].to_dict()
                game_data['rivalry_name'] = rivalry['name']
                game_data['rivalry_type'] = 'Historical Rivalry'

                # Analyze competitive balance
                home_win_prob = game_data['home_win_probability']
                competitive_score = abs(home_win_prob - 0.5) * 2  # 0 = perfectly balanced, 1 = one-sided

                game_data['competitive_balance'] = 'HIGHLY_COMPETITIVE' if competitive_score < 0.3 else 'MODERATELY_COMPETITIVE' if competitive_score < 0.6 else 'ONE_SIDED'
                game_data['rivalry_intensity'] = 'EXTREME' if rivalry['name'] in ['The Game', 'Iron Bowl', 'Bedlam'] else 'HIGH'

                rivalry_analysis['games'].append(game_data)

                print(f"  ⚔️  {rivalry['name']}: {game_data['home_team']} vs {game_data['away_team']}")
                print(f"     Prediction: {game_data['predicted_winner']} ({game_data['confidence_level']})")
                print(f"     Balance: {game_data['competitive_balance']}")

        self.results['rivalry_games'] = rivalry_analysis
        return rivalry_analysis

    def analyze_playoff_implications(self, data: Dict) -> Dict:
        """Analyze College Football Playoff implications"""
        print("\n🎯 Analyzing Playoff Implications...")

        if data['comprehensive'] is None:
            return {}

        df = data['comprehensive'].copy()

        # Current projected playoff teams (simplified)
        projected_contenders = [
            'Oregon', 'Georgia', 'Texas', 'Ohio State', 'Penn State',
            'Notre Dame', 'Alabama', 'Ole Miss', 'Miami', 'SMU',
            'Boise State', 'Arizona State'
        ]

        playoff_analysis = {
            'bubble_teams': [],
            'lock_scenarios': [],
            'elimination_games': [],
            'path_to_playoff': []
        }

        # Analyze games involving playoff contenders
        for _, game in df.iterrows():
            teams_involved = [game['home_team'], game['away_team']]
            contenders_in_game = [team for team in teams_involved if team in projected_contenders]

            if len(contenders_in_game) > 0:
                winner = game['predicted_winner']
                loser = teams_involved[0] if teams_involved[1] == winner else teams_involved[1]

                game_analysis = {
                    'game': f"{game['home_team']} vs {game['away_team']}",
                    'predicted_winner': winner,
                    'predicted_loser': loser,
                    'contenders_involved': contenders_in_game,
                    'playoff_impact': self._assess_playoff_impact(winner, loser, contenders_in_game),
                    'win_probability': game['home_win_probability'] if winner == game['home_team'] else game['away_win_probability']
                }

                if winner in projected_contenders:
                    if game_analysis['playoff_impact'] == 'CRITICAL':
                        playoff_analysis['lock_scenarios'].append(game_analysis)
                    elif game_analysis['playoff_impact'] == 'HIGH':
                        playoff_analysis['path_to_playoff'].append(game_analysis)

                if loser in projected_contenders:
                    if game_analysis['playoff_impact'] in ['CRITICAL', 'HIGH']:
                        playoff_analysis['elimination_games'].append(game_analysis)

        print(f"  🎯 Lock scenarios: {len(playoff_analysis['lock_scenarios'])}")
        print(f"  💔 Elimination games: {len(playoff_analysis['elimination_games'])}")
        print(f"  🛤️  Path to playoff: {len(playoff_analysis['path_to_playoff'])}")

        self.results['playoff_implications'] = playoff_analysis
        return playoff_analysis

    def _assess_playoff_impact(self, winner: str, loser: str, contenders: List[str]) -> str:
        """Assess the playoff impact of a game result"""
        # Simplified playoff impact assessment
        high_stakes_teams = ['Oregon', 'Georgia', 'Texas', 'Ohio State', 'Notre Dame']

        if winner in high_stakes_teams and loser in high_stakes_teams:
            return 'CRITICAL'
        elif winner in high_stakes_teams or loser in high_stakes_teams:
            return 'HIGH'
        elif winner in contenders or loser in contenders:
            return 'MEDIUM'
        else:
            return 'LOW'

    def generate_top_matchups(self, data: Dict) -> Dict:
        """Identify and analyze top Week 13 matchups"""
        print("\n🔥 Identifying Top Matchups...")

        if data['comprehensive'] is None:
            return {}

        df = data['comprehensive'].copy()

        # Score matchups based on multiple factors
        def calculate_matchup_score(row):
            score = 0

            # High confidence predictions
            if row['confidence_level'] == 'HIGH':
                score += 3
            elif row['confidence_level'] == 'MEDIUM':
                score += 2

            # Close margins (indicating competitive games)
            if abs(row['predicted_margin']) < 7:
                score += 3
            elif abs(row['predicted_margin']) < 14:
                score += 2

            # Strong teams (based on EPA)
            if abs(row['home_adjusted_epa']) > 0.2 and abs(row['away_adjusted_epa']) > 0.2:
                score += 2

            # Championship games
            if any(champ in f"{row['home_team']} {row['away_team']}"
                   for champ in ['ACC', 'Big Ten', 'Big 12', 'SEC']):
                score += 5

            return score

        df['matchup_score'] = df.apply(calculate_matchup_score, axis=1)

        # Sort by matchup score
        top_matchups = df.nlargest(10, 'matchup_score')

        matchups_analysis = {
            'top_10': [],
            'most_competitive': [],
            'highest_scoring': []
        }

        for _, game in top_matchups.iterrows():
            game_dict = game.to_dict()
            game_dict['matchup_rank'] = len(matchups_analysis['top_10']) + 1

            # Categorize matchup
            if abs(game_dict['predicted_margin']) < 7:
                game_dict['category'] = 'CLASH_OF_TITANS'
            elif game_dict['matchup_score'] >= 8:
                game_dict['category'] = 'MUST_WATCH'
            else:
                game_dict['category'] = 'SOLID_MATCHUP'

            matchups_analysis['top_10'].append(game_dict)

            print(f"  {game_dict['matchup_rank']}. {game_dict['home_team']} vs {game_dict['away_team']}")
            print(f"     Category: {game_dict['category']}")
            print(f"     Prediction: {game_dict['predicted_winner']} by {abs(game_dict['predicted_margin']):.1f}")

        self.results['top_matchups'] = matchups_analysis
        return matchups_analysis

    def generate_betting_insights(self, data: Dict) -> Dict:
        """Generate betting insights for Week 13"""
        print("\n💰 Generating Betting Insights...")

        if data['comprehensive'] is None:
            return {}

        df = data['comprehensive'].copy()

        betting_insights = {
            'value_picks': [],
            'upset_alerts': [],
            'over_under_insights': [],
            'trend_analysis': []
        }

        for _, game in df.iterrows():
            game_dict = game.to_dict()

            # Find value picks (discrepancies between prediction and likely betting lines)
            predicted_margin = game_dict['predicted_margin']
            confidence = game_dict['confidence_score']

            # Simplified value assessment
            if abs(predicted_margin) > 14 and confidence > 0.7:
                game_dict['betting_recommendation'] = 'STRONG_FAVORITE'
                game_dict['value_assessment'] = 'High confidence in large margin'
                betting_insights['value_picks'].append(game_dict)
            elif abs(predicted_margin) < 3 and confidence < 0.6:
                game_dict['betting_recommendation'] = 'POTENTIAL_UPSET'
                game_dict['value_assessment'] = 'Close game with low confidence'
                betting_insights['upset_alerts'].append(game_dict)

        print(f"  💎 Value picks: {len(betting_insights['value_picks'])}")
        print(f"  🎯 Upset alerts: {len(betting_insights['upset_alerts'])}")

        self.results['betting_insights'] = betting_insights
        return betting_insights

    def generate_strategic_recommendations(self, data: Dict) -> List[Dict]:
        """Generate strategic recommendations for Week 13"""
        print("\n🧠 Generating Strategic Recommendations...")

        recommendations = []

        # Conference championship recommendations
        if self.results.get('conference_championships', {}).get('games'):
            recommendations.append({
                'priority': 'CRITICAL',
                'category': 'Conference Championships',
                'recommendation': 'Focus analysis on conference championship games as they have direct playoff implications',
                'games': [game['conference'] for game in self.results['conference_championships']['games']]
            })

        # Playoff bubble recommendations
        if self.results.get('playoff_implications', {}).get('bubble_teams'):
            recommendations.append({
                'priority': 'HIGH',
                'category': 'Playoff Bubble',
                'recommendation': 'Monitor bubble teams closely - Week 13 results will determine final playoff field',
                'impact': 'Multiple teams will be eliminated from playoff contention'
            })

        # Rivalry game recommendations
        if self.results.get('rivalry_games', {}).get('games'):
            recommendations.append({
                'priority': 'MEDIUM',
                'category': 'Rivalry Games',
                'recommendation': 'Expect unexpected outcomes in rivalry games - historical data shows higher variance',
                'note': 'Rivalry games often defy statistical predictions'
            })

        # Betting recommendations
        if self.results.get('betting_insights', {}).get('value_picks'):
            recommendations.append({
                'priority': 'MEDIUM',
                'category': 'Betting Strategy',
                'recommendation': 'Look for value in championship games where public sentiment may skew odds',
                'caution': 'Conference championship games have higher variance'
            })

        self.results['strategic_recommendations'] = recommendations

        for rec in recommendations:
            print(f"  🔴 {rec['priority']}: {rec['category']}")
            print(f"     📝 {rec['recommendation']}")

        return recommendations

    def save_enhanced_analysis(self):
        """Save the enhanced analysis results"""
        print(f"\n💾 Saving enhanced analysis...")

        # Create analysis directory if it doesn't exist
        analysis_dir = self.project_root / "analysis" / "week13"
        analysis_dir.mkdir(parents=True, exist_ok=True)

        # Save comprehensive analysis
        analysis_file = analysis_dir / f"enhanced_week13_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(analysis_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)

        print(f"  ✅ Enhanced analysis saved: {analysis_file}")

        # Save summary as markdown
        summary_file = analysis_dir / f"enhanced_week13_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        self._save_markdown_summary(summary_file)

        return analysis_file

    def _save_markdown_summary(self, file_path: Path):
        """Save a markdown summary of the analysis"""
        with open(file_path, 'w') as f:
            f.write("# Enhanced Week 13 Analysis Summary\n\n")
            f.write(f"**Generated:** {self.results['timestamp']}\n\n")

            # Conference championships
            if 'conference_championships' in self.results and self.results['conference_championships']:
                f.write("## 🏆 Conference Championships\n\n")
                for game in self.results['conference_championships'].get('games', []):
                    f.write(f"### {game.get('conference', 'Unknown')}\n")
                    f.write(f"- **Matchup:** {game['home_team']} vs {game['away_team']}\n")
                    f.write(f"- **Prediction:** {game['predicted_winner']} ({game['confidence_level']})\n")
                    f.write(f"- **Margin:** {abs(game['predicted_margin']):.1f} points\n\n")

            # Top matchups
            if 'top_matchups' in self.results and self.results['top_matchups']:
                f.write("## 🔥 Top Matchups\n\n")
                for game in self.results['top_matchups'].get('top_10', [])[:5]:
                    f.write(f"### {game['matchup_rank']}. {game['home_team']} vs {game['away_team']}\n")
                    f.write(f"- **Category:** {game['category']}\n")
                    f.write(f"- **Prediction:** {game['predicted_winner']} by {abs(game['predicted_margin']):.1f}\n")
                    f.write(f"- **Confidence:** {game['confidence_level']}\n\n")

            # Strategic recommendations
            if 'strategic_recommendations' in self.results:
                f.write("## 🧠 Strategic Recommendations\n\n")
                for rec in self.results['strategic_recommendations']:
                    f.write(f"### 🔴 {rec['priority']}: {rec['category']}\n")
                    f.write(f"{rec['recommendation']}\n\n")

        print(f"  ✅ Markdown summary saved: {file_path}")

    def run_enhanced_analysis(self):
        """Run the complete enhanced analysis"""
        print("🚀 Starting Enhanced Week 13 Analysis...")
        print("="*60)

        try:
            # Load data
            data = self.load_week13_data()

            if not data['comprehensive'] is not None:
                print("❌ No Week 13 data available for analysis")
                return self.results

            # Run analysis components
            self.analyze_conference_championships(data)
            self.analyze_rivalry_games(data)
            self.analyze_playoff_implications(data)
            self.generate_top_matchups(data)
            self.generate_betting_insights(data)
            self.generate_strategic_recommendations(data)

            # Save results
            analysis_file = self.save_enhanced_analysis()

            print(f"\n✅ Enhanced Week 13 analysis complete!")
            print(f"📄 Analysis saved: {analysis_file}")

            return self.results

        except Exception as e:
            print(f"\n❌ Error during analysis: {str(e)}")
            import traceback
            traceback.print_exc()
            return self.results

def main():
    """Main execution function"""
    analyzer = EnhancedWeek13Analyzer()
    results = analyzer.run_enhanced_analysis()
    return results

if __name__ == "__main__":
    results = main()