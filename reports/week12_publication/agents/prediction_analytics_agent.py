#!/usr/bin/env python3
"""
Prediction Analytics Agent

Advanced statistical analysis for Week 12 college football predictions.
Provides insights, confidence intervals, and betting analytics.

Author: Script Ohio 2.0 Agent System
Date: 2025-11-14
"""

import pandas as pd
import numpy as np
import scipy.stats as stats
from pathlib import Path
from typing import Dict, List, Tuple, Any
import json
import logging
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Set up professional logging
log_dir = Path("reports/week12_publication/assets")
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'prediction_analytics.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('PredictionAnalyticsAgent')

class PredictionAnalyticsAgent:
    """
    Advanced analytics agent for Week 12 predictions.
    Provides statistical insights, confidence analysis, and betting recommendations.
    """

    def __init__(self):
        self.project_root = Path(".")
        self.data_dir = self.project_root / "model_pack"
        self.output_dir = self.project_root / "reports/week12_publication/assets/data"
        self.predictions = None
        self.analytics_results = None

    def load_predictions(self) -> bool:
        """Load Week 12 prediction data"""
        try:
            logger.info("📊 Loading Week 12 predictions for analytics...")

            predictions_path = self.output_dir / "week12_predictions_detailed.csv"

            if predictions_path.exists():
                self.predictions = pd.read_csv(predictions_path)
                logger.info(f"✅ Loaded {len(self.predictions)} predictions")
                return True
            else:
                logger.error(f"❌ Predictions file not found: {predictions_path}")
                return False

        except Exception as e:
            logger.error(f"❌ Failed to load predictions: {e}")
            return False

    def calculate_confidence_intervals(self) -> Dict[str, Any]:
        """Calculate confidence intervals for predictions"""
        try:
            logger.info("📈 Calculating confidence intervals...")

            if self.predictions is None:
                return {}

            # Extract prediction margins and probabilities
            margins = self.predictions['ensemble_margin'].dropna()
            win_probs = self.predictions['ensemble_win_probability'].dropna()

            if len(margins) == 0:
                logger.warning("⚠️  No valid margin predictions found")
                return {}

            # Calculate confidence intervals
            confidence_levels = [0.90, 0.95, 0.99]
            margin_intervals = {}
            prob_intervals = {}

            for conf_level in confidence_levels:
                alpha = 1 - conf_level
                t_critical = stats.t.ppf(1 - alpha/2, len(margins) - 1)

                # Margin confidence intervals
                margin_mean = margins.mean()
                margin_std = margins.std()
                margin_margin = t_critical * (margin_std / np.sqrt(len(margins)))

                margin_intervals[f'{int(conf_level*100)}%'] = {
                    'lower': float(margin_mean - margin_margin),
                    'upper': float(margin_mean + margin_margin),
                    'mean': float(margin_mean),
                    'std': float(margin_std)
                }

                # Win probability confidence intervals
                prob_mean = win_probs.mean()
                prob_std = win_probs.std()
                prob_margin = t_critical * (prob_std / np.sqrt(len(win_probs)))

                prob_intervals[f'{int(conf_level*100)}%'] = {
                    'lower': float(prob_mean - prob_margin),
                    'upper': float(prob_mean + prob_margin),
                    'mean': float(prob_mean),
                    'std': float(prob_std)
                }

            confidence_analysis = {
                'margin_confidence_intervals': margin_intervals,
                'win_probability_confidence_intervals': prob_intervals,
                'sample_size': len(margins),
                'confidence_levels': confidence_levels
            }

            logger.info(f"✅ Calculated confidence intervals for {len(margins)} predictions")
            return confidence_analysis

        except Exception as e:
            logger.error(f"❌ Confidence interval calculation failed: {e}")
            return {}

    def analyze_prediction_distribution(self) -> Dict[str, Any]:
        """Analyze the distribution of predictions"""
        try:
            logger.info("📊 Analyzing prediction distributions...")

            if self.predictions is None:
                return {}

            margins = self.predictions['ensemble_margin'].dropna()
            win_probs = self.predictions['ensemble_win_probability'].dropna()
            confidence_scores = self.predictions['confidence_score'].dropna()

            distribution_analysis = {
                'margin_distribution': {
                    'mean': float(margins.mean()),
                    'median': float(margins.median()),
                    'std': float(margins.std()),
                    'min': float(margins.min()),
                    'max': float(margins.max()),
                    'q25': float(margins.quantile(0.25)),
                    'q75': float(margins.quantile(0.75)),
                    'skewness': float(margins.skew()),
                    'kurtosis': float(margins.kurtosis())
                },
                'win_probability_distribution': {
                    'mean': float(win_probs.mean()),
                    'median': float(win_probs.median()),
                    'std': float(win_probs.std()),
                    'min': float(win_probs.min()),
                    'max': float(win_probs.max()),
                    'q25': float(win_probs.quantile(0.25)),
                    'q75': float(win_probs.quantile(0.75))
                },
                'confidence_distribution': {
                    'mean': float(confidence_scores.mean()),
                    'median': float(confidence_scores.median()),
                    'std': float(confidence_scores.std()),
                    'high_confidence_games': int((confidence_scores > 0.7).sum()),
                    'low_confidence_games': int((confidence_scores < 0.3).sum())
                }
            }

            # Categorize prediction types
            close_games = (abs(margins) < 7).sum()  # Within one touchdown
            blowouts = (abs(margins) > 21).sum()    # More than three touchdowns
            moderate_games = len(margins) - close_games - blowouts

            distribution_analysis['game_categories'] = {
                'close_games': int(close_games),
                'blowout_predictions': int(blowouts),
                'moderate_predictions': int(moderate_games),
                'total_games': len(margins)
            }

            logger.info(f"✅ Distribution analysis complete: {close_games} close, {blowouts} blowouts")
            return distribution_analysis

        except Exception as e:
            logger.error(f"❌ Distribution analysis failed: {e}")
            return {}

    def identify_key_insights(self) -> Dict[str, Any]:
        """Identify key insights and interesting patterns"""
        try:
            logger.info("🔍 Identifying key insights...")

            if self.predictions is None:
                return {}

            insights = {
                'highest_confidence_games': [],
                'lowest_confidence_games': [],
                'closest_predictions': [],
                'largest_mismatches': [],
                'upset_specials': [],
                'rivalry_highlights': []
            }

            # Sort by different criteria
            df_sorted = self.predictions.copy()

            # Highest confidence games
            high_conf = df_sorted.nlargest(5, 'confidence_score')[['home_team', 'away_team', 'ensemble_predicted_winner', 'ensemble_margin', 'confidence_score']]
            insights['highest_confidence_games'] = high_conf.to_dict('records')

            # Lowest confidence games (only include those with some confidence)
            low_conf = df_sorted[df_sorted['confidence_score'] > 0.1].nsmallest(5, 'confidence_score')[['home_team', 'away_team', 'ensemble_predicted_winner', 'ensemble_margin', 'confidence_score']]
            insights['lowest_confidence_games'] = low_conf.to_dict('records')

            # Closest predictions (most competitive games)
            df_sorted['abs_margin'] = df_sorted['ensemble_margin'].abs()
            close_games = df_sorted.nsmallest(5, 'abs_margin')[['home_team', 'away_team', 'ensemble_predicted_winner', 'ensemble_margin', 'confidence_score']]
            insights['closest_predictions'] = close_games.to_dict('records')

            # Largest predicted margins (biggest blowouts)
            largest_margins = df_sorted.nlargest(5, 'abs_margin')[['home_team', 'away_team', 'ensemble_predicted_winner', 'ensemble_margin', 'confidence_score']]
            insights['largest_mismatches'] = largest_margins.to_dict('records')

            # Potential upsets (away teams favored with moderate confidence)
            away_favored = df_sorted[(df_sorted['ensemble_margin'] < 0) & (df_sorted['confidence_score'] > 0.4)]
            if len(away_favored) > 0:
                upset_games = away_favored[['home_team', 'away_team', 'ensemble_predicted_winner', 'ensemble_margin', 'confidence_score']]
                insights['upset_specials'] = upset_games.to_dict('records')

            # Rivalry games (common college football rivalries)
            rivalry_matchups = [
                ('Ohio State', 'Michigan'), ('Michigan', 'Ohio State'),
                ('Alabama', 'Auburn'), ('Auburn', 'Alabama'),
                ('Georgia', 'Tennessee'), ('Tennessee', 'Georgia'),
                ('Florida State', 'Miami'), ('Miami', 'Florida State')
            ]

            for home, away in rivalry_matchups:
                rivalry_game = df_sorted[
                    (df_sorted['home_team'] == home) & (df_sorted['away_team'] == away)
                ]
                if len(rivalry_game) > 0:
                    rivalry_info = rivalry_game.iloc[0][['home_team', 'away_team', 'ensemble_predicted_winner', 'ensemble_margin', 'confidence_score']].to_dict()
                    insights['rivalry_highlights'].append(rivalry_info)

            # Statistical insights
            home_win_prob = (df_sorted['ensemble_margin'] > 0).mean()
            avg_margin = df_sorted['ensemble_margin'].mean()
            avg_confidence = df_sorted['confidence_score'].mean()

            insights['summary_statistics'] = {
                'home_team_win_rate': float(home_win_prob),
                'average_predicted_margin': float(avg_margin),
                'average_confidence': float(avg_confidence),
                'total_games_analyzed': len(df_sorted)
            }

            logger.info(f"✅ Key insights identified: {len(insights['rivalry_highlights'])} rivalry games, "
                       f"{len(insights['upset_specials'])} potential upsets")

            return insights

        except Exception as e:
            logger.error(f"❌ Key insights analysis failed: {e}")
            return {}

    def generate_betting_analytics(self) -> Dict[str, Any]:
        """Generate betting-focused analytics and recommendations"""
        try:
            logger.info("💰 Generating betting analytics...")

            if self.predictions is None:
                return {}

            betting_insights = {
                'value_opportunities': [],
                'high_value_picks': [],
                'risk_assessment': [],
                'confidence_rankings': []
            }

            # Simple value betting simulation (assuming even money for demonstration)
            df_betting = self.predictions.copy()

            # Calculate expected value (EV) for home team wins
            # Assuming -110 odds for both sides (vig removed)
            implied_probability = 0.5  # Even odds
            actual_prob = df_betting['ensemble_win_probability']

            # EV = (Actual Probability * Payout) - (Implied Probability * Stake)
            # For even money: EV = Actual_Probability - 0.5
            df_betting['home_team_ev'] = actual_prob - implied_probability
            df_betting['away_team_ev'] = (1 - actual_prob) - implied_probability

            # Identify value opportunities (positive EV)
            home_value = df_betting[df_betting['home_team_ev'] > 0.05].nlargest(5, 'home_team_ev')
            away_value = df_betting[df_betting['away_team_ev'] > 0.05].nlargest(5, 'away_team_ev')

            if len(home_value) > 0:
                home_value_picks = home_value[[
                    'home_team', 'away_team', 'ensemble_predicted_winner',
                    'ensemble_win_probability', 'home_team_ev', 'confidence_score'
                ]].rename(columns={'home_team_ev': 'expected_value'})
                betting_insights['value_opportunities'].extend(home_value_picks.to_dict('records'))

            if len(away_value) > 0:
                away_value_picks = away_value[[
                    'home_team', 'away_team', 'ensemble_predicted_winner',
                    'ensemble_win_probability', 'away_team_ev', 'confidence_score'
                ]].rename(columns={'away_team_ev': 'expected_value'})
                betting_insights['value_opportunities'].extend(away_value_picks.to_dict('records'))

            # High confidence picks (for straight bets)
            high_conf_games = df_betting[df_betting['confidence_score'] > 0.8].nlargest(5, 'confidence_score')
            if len(high_conf_games) > 0:
                high_conf_picks = high_conf_games[[
                    'home_team', 'away_team', 'ensemble_predicted_winner',
                    'ensemble_margin', 'confidence_score', 'ensemble_win_probability'
                ]]
                betting_insights['high_value_picks'] = high_conf_picks.to_dict('records')

            # Risk assessment (low confidence, high variance games)
            low_conf_games = df_betting[df_betting['confidence_score'] < 0.3]
            if len(low_conf_games) > 0:
                risk_games = low_conf_games[[
                    'home_team', 'away_team', 'ensemble_predicted_winner',
                    'ensemble_margin', 'confidence_score'
                ]].nlargest(5, 'ensemble_margin')
                betting_insights['risk_assessment'] = risk_games.to_dict('records')

            # Confidence rankings
            confidence_ranked = df_betting.sort_values('confidence_score', ascending=False).head(10)
            betting_insights['confidence_rankings'] = confidence_ranked[[
                'home_team', 'away_team', 'ensemble_predicted_winner',
                'ensemble_margin', 'confidence_score'
            ]].to_dict('records')

            # Summary metrics
            total_games = len(df_betting)
            positive_ev_games = len(df_betting[(df_betting['home_team_ev'] > 0) | (df_betting['away_team_ev'] > 0)])
            high_conf_games = len(df_betting[df_betting['confidence_score'] > 0.7])

            betting_insights['summary'] = {
                'total_games': int(total_games),
                'value_opportunities': int(positive_ev_games),
                'high_confidence_picks': int(high_conf_games),
                'average_home_ev': float(df_betting['home_team_ev'].mean()),
                'average_away_ev': float(df_betting['away_team_ev'].mean())
            }

            logger.info(f"✅ Betting analytics complete: {positive_ev_games} value opportunities found")
            return betting_insights

        except Exception as e:
            logger.error(f"❌ Betting analytics failed: {e}")
            return {}

    def create_performance_benchmarks(self) -> Dict[str, Any]:
        """Create performance benchmarks and validation metrics"""
        try:
            logger.info("📈 Creating performance benchmarks...")

            if self.predictions is None:
                return {}

            benchmarks = {
                'model_performance_metrics': {},
                'prediction_accuracy_indicators': {},
                'risk_reward_analysis': {}
            }

            # Model performance metrics (using available data)
            df = self.predictions.copy()

            # If actual results are available, calculate accuracy
            if 'actual_margin' in df.columns and df['actual_margin'].notna().any():
                actual_available = df[df['actual_margin'].notna()]

                # Margin prediction accuracy
                margin_errors = abs(actual_available['ensemble_margin'] - actual_available['actual_margin'])
                benchmarks['model_performance_metrics']['margin_mae'] = float(margin_errors.mean())
                benchmarks['model_performance_metrics']['margin_rmse'] = float(np.sqrt((margin_errors**2).mean()))

                # Win prediction accuracy
                actual_home_wins = actual_available['actual_margin'] > 0
                predicted_home_wins = actual_available['ensemble_margin'] > 0
                win_accuracy = (actual_home_wins == predicted_home_wins).mean()
                benchmarks['model_performance_metrics']['win_prediction_accuracy'] = float(win_accuracy)

            # Prediction quality indicators
            benchmarks['prediction_accuracy_indicators'] = {
                'confidence_distribution': {
                    'high_confidence_games': int((df['confidence_score'] > 0.7).sum()),
                    'medium_confidence_games': int(((df['confidence_score'] >= 0.3) & (df['confidence_score'] <= 0.7)).sum()),
                    'low_confidence_games': int((df['confidence_score'] < 0.3).sum())
                },
                'prediction_consensus': {
                    'model_agreement_rate': float((df['ensemble_margin_std'] < 5).mean()) if 'ensemble_margin_std' in df.columns else 0.5
                },
                'extreme_predictions': {
                    'games_predicted_over_30_points': int((df['ensemble_margin'].abs() > 30).sum()),
                    'games_predicted_under_3_points': int((df['ensemble_margin'].abs() < 3).sum())
                }
            }

            # Risk-reward analysis
            df['abs_margin'] = df['ensemble_margin'].abs()
            df['risk_score'] = 1 - df['confidence_score']  # Inverse of confidence

            high_risk_high_reward = df[(df['risk_score'] > 0.5) & (df['abs_margin'] > 14)]
            low_risk_low_reward = df[(df['risk_score'] < 0.3) & (df['abs_margin'] < 10)]

            benchmarks['risk_reward_analysis'] = {
                'high_risk_high_reward_opportunities': len(high_risk_high_reward),
                'low_risk_low_reward_games': len(low_risk_low_reward),
                'average_risk_score': float(df['risk_score'].mean()),
                'risk_return_correlation': float(df[['risk_score', 'abs_margin']].corr().iloc[0, 1])
            }

            # Quality control metrics
            quality_metrics = {
                'data_completeness': {
                    'total_predictions': len(df),
                    'complete_predictions': len(df.dropna(subset=['ensemble_margin', 'confidence_score'])),
                    'completeness_rate': float(len(df.dropna(subset=['ensemble_margin', 'confidence_score'])) / len(df))
                },
                'prediction_range': {
                    'min_predicted_margin': float(df['ensemble_margin'].min()),
                    'max_predicted_margin': float(df['ensemble_margin'].max()),
                    'margin_range': float(df['ensemble_margin'].max() - df['ensemble_margin'].min())
                }
            }

            benchmarks['quality_metrics'] = quality_metrics

            logger.info(f"✅ Performance benchmarks created for {len(df)} predictions")
            return benchmarks

        except Exception as e:
            logger.error(f"❌ Performance benchmarks failed: {e}")
            return {}

    def save_analytics_results(self, all_results: Dict[str, Any]) -> bool:
        """Save comprehensive analytics results"""
        try:
            logger.info("💾 Saving analytics results...")

            # Save main analytics results
            analytics_path = self.output_dir / "week12_prediction_analytics.json"
            with open(analytics_path, 'w') as f:
                json.dump(all_results, f, indent=2, default=str)
            logger.info(f"✅ Analytics saved: {analytics_path}")

            # Save executive summary
            summary = {
                'report_metadata': {
                    'title': 'Week 12 College Football Prediction Analytics',
                    'generated_at': datetime.now().isoformat(),
                    'games_analyzed': len(self.predictions) if self.predictions is not None else 0
                },
                'key_findings': {
                    'average_confidence': all_results.get('distribution_analysis', {}).get('confidence_distribution', {}).get('mean', 0),
                    'high_confidence_games': all_results.get('distribution_analysis', {}).get('confidence_distribution', {}).get('high_confidence_games', 0),
                    'close_competitive_games': all_results.get('distribution_analysis', {}).get('game_categories', {}).get('close_games', 0),
                    'predicted_blowouts': all_results.get('distribution_analysis', {}).get('game_categories', {}).get('blowout_predictions', 0)
                },
                'betting_insights': {
                    'value_opportunities': all_results.get('betting_analytics', {}).get('summary', {}).get('value_opportunities', 0),
                    'high_confidence_picks': all_results.get('betting_analytics', {}).get('summary', {}).get('high_confidence_picks', 0)
                }
            }

            summary_path = self.output_dir / "analytics_executive_summary.json"
            with open(summary_path, 'w') as f:
                json.dump(summary, f, indent=2)
            logger.info(f"✅ Executive summary saved: {summary_path}")

            # Create CSV with key insights for easy consumption
            if all_results.get('key_insights'):
                key_insights = all_results['key_insights']

                # High confidence games CSV
                if key_insights.get('highest_confidence_games'):
                    high_conf_df = pd.DataFrame(key_insights['highest_confidence_games'])
                    high_conf_path = self.output_dir / "high_confidence_games.csv"
                    high_conf_df.to_csv(high_conf_path, index=False)
                    logger.info(f"✅ High confidence games saved: {high_conf_path}")

                # Close predictions CSV
                if key_insights.get('closest_predictions'):
                    close_df = pd.DataFrame(key_insights['closest_predictions'])
                    close_path = self.output_dir / "close_predictions.csv"
                    close_df.to_csv(close_path, index=False)
                    logger.info(f"✅ Close predictions saved: {close_path}")

            return True

        except Exception as e:
            logger.error(f"❌ Saving analytics results failed: {e}")
            return False

    def run_complete_analytics(self) -> Tuple[bool, Dict[str, Any]]:
        """Execute complete analytics pipeline"""
        logger.info("🚀 Starting Prediction Analytics Pipeline...")
        start_time = datetime.now()

        # Step 1: Load predictions
        if not self.load_predictions():
            return False, {}

        # Step 2: Calculate confidence intervals
        confidence_intervals = self.calculate_confidence_intervals()

        # Step 3: Analyze distributions
        distribution_analysis = self.analyze_prediction_distribution()

        # Step 4: Identify key insights
        key_insights = self.identify_key_insights()

        # Step 5: Generate betting analytics
        betting_analytics = self.generate_betting_analytics()

        # Step 6: Create performance benchmarks
        performance_benchmarks = self.create_performance_benchmarks()

        # Compile all results
        self.analytics_results = {
            'confidence_intervals': confidence_intervals,
            'distribution_analysis': distribution_analysis,
            'key_insights': key_insights,
            'betting_analytics': betting_analytics,
            'performance_benchmarks': performance_benchmarks,
            'analysis_timestamp': datetime.now().isoformat()
        }

        # Step 7: Save results
        if not self.save_analytics_results(self.analytics_results):
            return False, {}

        execution_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"✅ Prediction Analytics completed in {execution_time:.2f} seconds")

        return True, self.analytics_results

# Main execution
if __name__ == "__main__":
    agent = PredictionAnalyticsAgent()
    success, results = agent.run_complete_analytics()

    if success:
        print("\n🎉 Prediction Analytics Completed Successfully!")
        print(f"📊 Analyzed predictions for {len(agent.predictions)} games")
        high_conf = results.get('distribution_analysis', {}).get('confidence_distribution', {}).get('high_confidence_games', 0)
        print(f"🎯 Identified {high_conf} high confidence games")
        value_ops = results.get('betting_analytics', {}).get('summary', {}).get('value_opportunities', 0)
        print(f"💰 Found {value_ops} betting value opportunities")
        print("📁 Results saved to: reports/week12_publication/assets/data/")
        exit(0)
    else:
        print("\n❌ Prediction Analytics Failed!")
        exit(1)