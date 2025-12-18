#!/usr/bin/env python3
"""
Complete 2025 Enhancement Suite
Integrates all Phase 2 and Phase 3 enhancements:
- Real-time WebSocket processing
- Enhanced box scores
- Historical matchup analysis
- Parallel processing
- Enhanced caching
"""

import os
import sys
import json
import time
import asyncio
import pandas as pd
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.cfbd_client.enhanced_unified_client import EnhancedUnifiedCFBDClient
from src.cfbd_client.websocket_client import CFBDWebSocketClient
from src.cfbd_client.live_game_data_processor import LiveGameProcessor
from src.cfbd_client.enhanced_box_scores import EnhancedBoxScoreClient
from src.cfbd_client.team_matchup_analyzer import TeamMatchupAnalyzer
from src.cfbd_client.parallel_processor import ParallelCFBDProcessor
from src.cfbd_client.enhanced_caching import get_cache_instance, CacheConfig

class CompleteEnhancementSuite:
    """
    Complete integration suite for all 2025 data enhancements

    This suite combines:
    1. Real-time game data processing
    2. Enhanced box scores and analytics
    3. Historical matchup analysis
    4. Parallel processing for performance
    5. Multi-level caching system
    """

    def __init__(self):
        """Initialize complete enhancement suite"""
        print("🚀 Initializing Complete 2025 Enhancement Suite...")

        # Initialize core components
        self.client = EnhancedUnifiedCFBDClient()
        self.cache = get_cache_instance(CacheConfig(
            enable_redis=False,  # Disable Redis for demo
            enable_file_cache=True,
            enable_memory_cache=True,
            memory_max_size=500
        ))
        self.parallel_processor = ParallelCFBDProcessor(max_workers=6)
        self.box_score_client = EnhancedBoxScoreClient()
        self.matchup_analyzer = TeamMatchupAnalyzer()

        # Performance tracking
        self.start_time = datetime.now(timezone.utc)
        self.enhancement_results = {
            'suite_start_time': self.start_time.isoformat(),
            'components': {},
            'performance_metrics': {},
            'data_processed': {},
            'success_rate': 0.0
        }

        print("✅ Enhancement Suite initialized")

    async def run_real_time_demo(self) -> Dict[str, Any]:
        """Demonstrate real-time game processing"""
        print("\n🏈 Running Real-Time Game Processing Demo...")

        results = {
            'component': 'real_time_processing',
            'start_time': datetime.now(timezone.utc).isoformat(),
            'status': 'running',
            'data_processed': {}
        }

        try:
            # Initialize WebSocket client
            ws_client = CFBDWebSocketClient()

            # Add event handlers
            game_updates = []
            score_updates = []

            def handle_game_update(game_data):
                game_updates.append({
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'home_team': game_data.home_team,
                    'home_score': game_data.home_score,
                    'away_team': game_data.away_team,
                    'away_score': game_data.away_score,
                    'status': game_data.game_status
                })

            def handle_score_update(score_data):
                score_updates.append({
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'scoring_team': score_data.scoring_team,
                    'points': score_data.points,
                    'new_score': f"{score_data.new_home_score}-{score_data.new_away_score}"
                })

            ws_client.add_event_handler('game_update', handle_game_update)
            ws_client.add_event_handler('score_update', handle_score_update)

            # Connect and subscribe to games
            await ws_client.connect()
            if ws_client.is_connected:
                await ws_client.subscribe_to_games(year=2025, week=15)

                # Run for demonstration period
                await asyncio.sleep(10)  # 10 seconds demo

                results['data_processed'] = {
                    'game_updates': len(game_updates),
                    'score_updates': len(score_updates),
                    'subscribed_games': len(ws_client.subscribed_games),
                    'websocket_metrics': ws_client.get_metrics()
                }

                await ws_client.disconnect()

            results['status'] = 'completed'
            print(f"✅ Real-time demo: {len(game_updates)} game updates, {len(score_updates)} score updates")

        except Exception as e:
            results['status'] = 'error'
            results['error'] = str(e)
            print(f"❌ Real-time demo error: {e}")

        results['end_time'] = datetime.now(timezone.utc).isoformat()
        self.enhancement_results['components']['real_time_processing'] = results

        return results

    def run_box_score_demo(self) -> Dict[str, Any]:
        """Demonstrate enhanced box score processing"""
        print("\n📊 Running Enhanced Box Score Demo...")

        results = {
            'component': 'enhanced_box_scores',
            'start_time': datetime.now(timezone.utc).isoformat(),
            'status': 'running',
            'data_processed': {}
        }

        try:
            # Get completed games for a recent week
            games = self.client.get_games(year=2025, week=14)
            completed_games = [g for g in games if g.get('complete', False)]

            if completed_games:
                # Process first few games with enhanced box scores
                game_ids = [game.get('id') for game in completed_games[:3] if game.get('id')]

                enhanced_box_scores = {}
                for game_id in game_ids:
                    box_score = self.box_score_client.get_enhanced_box_score(game_id)
                    if box_score:
                        enhanced_box_scores[game_id] = {
                            'teams': f"{box_score.home_team} vs {box_score.away_team}",
                            'final_score': f"{box_score.home_score}-{box_score.away_score}",
                            'total_yards': box_score.home_box_score.total_yards + box_score.away_box_score.total_yards,
                            'player_stats_count': len(box_score.player_stats),
                            'advanced_metrics_count': len(box_score.advanced_metrics)
                        }

                # Export to DataFrame
                df = self.box_score_client.export_box_scores_to_dataframe(
                    {k: v for k, v in enhanced_box_scores.items() if v}
                )

                results['data_processed'] = {
                    'games_processed': len(enhanced_box_scores),
                    'total_players': sum(s.get('player_stats_count', 0) for s in enhanced_box_scores.values()),
                    'dataframe_rows': len(df),
                    'enhanced_box_scores': enhanced_box_scores
                }

                print(f"✅ Box score demo: {len(enhanced_box_scores)} enhanced box scores processed")

            else:
                results['data_processed'] = {'message': 'No completed games found'}
                print("⚠️ No completed games found for box score demo")

            results['status'] = 'completed'

        except Exception as e:
            results['status'] = 'error'
            results['error'] = str(e)
            print(f"❌ Box score demo error: {e}")

        results['end_time'] = datetime.now(timezone.utc).isoformat()
        self.enhancement_results['components']['enhanced_box_scores'] = results

        return results

    def run_matchup_analysis_demo(self) -> Dict[str, Any]:
        """Demonstrate historical matchup analysis"""
        print("\n🥊 Running Historical Matchup Analysis Demo...")

        results = {
            'component': 'matchup_analysis',
            'start_time': datetime.now(timezone.utc).isoformat(),
            'status': 'running',
            'data_processed': {}
        }

        try:
            # Analyze key rivalries
            rivalries = [
                ('Alabama', 'Georgia'),
                ('Ohio State', 'Michigan'),
                ('Texas', 'Oklahoma'),
                ('USC', 'UCLA')
            ]

            matchup_results = {}

            for team1, team2 in rivalries:
                print(f"   Analyzing {team1} vs {team2}...")

                # Get historical statistics
                stats = self.matchup_analyzer.analyze_matchup_statistics(team1, team2)
                rivalry = self.matchup_analyzer.get_rivalry_analysis(team1, team2)
                prediction = self.matchup_analyzer.predict_matchup_outcome(team1, team2)

                matchup_results[f"{team1}_{team2}"] = {
                    'total_games': stats.total_games,
                    'team1_win_pct': stats.team1_win_pct,
                    'team2_win_pct': stats.team2_win_pct,
                    'rivalry_score': rivalry['rivalry_score'],
                    'rivalry_level': rivalry['rivalry_level'],
                    'predicted_winner': prediction.predicted_winner,
                    'confidence': prediction.confidence,
                    'historical_advantage': prediction.historical_advantage
                }

            # Export to DataFrame
            df = self.matchup_analyzer.export_matchup_analysis_to_dataframe(rivalries)

            results['data_processed'] = {
                'rivalries_analyzed': len(matchup_results),
                'dataframe_rows': len(df),
                'matchup_results': matchup_results
            }

            print(f"✅ Matchup analysis demo: {len(matchup_results)} rivalries analyzed")

            results['status'] = 'completed'

        except Exception as e:
            results['status'] = 'error'
            results['error'] = str(e)
            print(f"❌ Matchup analysis demo error: {e}")

        results['end_time'] = datetime.now(timezone.utc).isoformat()
        self.enhancement_results['components']['matchup_analysis'] = results

        return results

    def run_parallel_processing_demo(self) -> Dict[str, Any]:
        """Demonstrate parallel processing performance"""
        print("\n🚀 Running Parallel Processing Demo...")

        results = {
            'component': 'parallel_processing',
            'start_time': datetime.now(timezone.utc).isoformat(),
            'status': 'running',
            'data_processed': {},
            'performance_metrics': {}
        }

        try:
            # Demo 1: Parallel games fetching
            weeks = [12, 13, 14, 15]
            start_time = time.time()
            games_data = self.parallel_processor.parallel_get_games_batch(2025, weeks)
            parallel_games_time = time.time() - start_time

            total_games = sum(len(games) for games in games_data.values())

            # Demo 2: Parallel team statistics
            teams = ['Alabama', 'Georgia', 'Ohio State', 'Michigan', 'Texas', 'Oklahoma', 'USC', 'UCLA']
            start_time = time.time()
            team_stats = self.parallel_processor.parallel_get_team_stats_batch(teams, 2025)
            parallel_stats_time = time.time() - start_time

            # Get performance metrics
            metrics = self.parallel_processor.get_performance_metrics()

            results['data_processed'] = {
                'games_fetch': {
                    'weeks_processed': len(games_data),
                    'total_games': total_games,
                    'execution_time': parallel_games_time
                },
                'team_stats_fetch': {
                    'teams_processed': len(team_stats),
                    'execution_time': parallel_stats_time
                }
            }

            results['performance_metrics'] = asdict(metrics)

            print(f"✅ Parallel processing demo: {total_games} games, {len(team_stats)} teams processed")

            results['status'] = 'completed'

        except Exception as e:
            results['status'] = 'error'
            results['error'] = str(e)
            print(f"❌ Parallel processing demo error: {e}")

        results['end_time'] = datetime.now(timezone.utc).isoformat()
        self.enhancement_results['components']['parallel_processing'] = results

        return results

    def run_caching_demo(self) -> Dict[str, Any]:
        """Demonstrate enhanced caching system"""
        print("\n🗄️ Running Enhanced Caching Demo...")

        results = {
            'component': 'enhanced_caching',
            'start_time': datetime.now(timezone.utc).isoformat(),
            'status': 'running',
            'data_processed': {}
        }

        try:
            # Test cache performance
            cache = self.cache

            # Store and retrieve different data types
            test_data = {
                'games': [{'id': 1, 'home': 'Alabama', 'away': 'Georgia', 'score': '31-24'}],
                'teams': [{'name': 'Alabama', 'conference': 'SEC', 'rank': 1}],
                'ratings': [{'team': 'Alabama', 'elo': 85.5, 'power_rating': 92.3}],
                'stats': [{'team': 'Alabama', 'wins': 10, 'losses': 2, 'conf_wins': 7, 'conf_losses': 1}]
            }

            cache_operations = 0
            cache_hits = 0

            # Test caching operations
            for data_type, data in test_data.items():
                key = f"demo_{data_type}"

                # First cache miss
                start_time = time.time()
                cached_data = cache.get(key, data_type)
                first_access_time = (time.time() - start_time) * 1000

                # Set data
                cache.set(key, data, data_type=data_type)
                cache_operations += 1

                # Second cache hit
                start_time = time.time()
                cached_data = cache.get(key, data_type)
                second_access_time = (time.time() - start_time) * 1000

                if cached_data:
                    cache_hits += 1
                    cache_operations += 1

                print(f"   {data_type}: {second_access_time:.2f}ms (cache)")

            # Get cache metrics
            metrics = cache.get_metrics()
            cache_stats = cache.export_cache_stats()

            results['data_processed'] = {
                'cache_operations': cache_operations,
                'cache_hits': cache_hits,
                'hit_rate': metrics.hit_rate,
                'average_response_time': metrics.average_response_time_ms,
                'total_size_mb': metrics.total_size_mb
            }

            results['performance_metrics'] = cache_stats

            print(f"✅ Caching demo: {cache_hits}/{cache_operations} hits, {metrics.hit_rate:.1f}% hit rate")

            results['status'] = 'completed'

        except Exception as e:
            results['status'] = 'error'
            results['error'] = str(e)
            print(f"❌ Caching demo error: {e}")

        results['end_time'] = datetime.now(timezone.utc).isoformat()
        self.enhancement_results['components']['enhanced_caching'] = results

        return results

    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive enhancement report"""
        print("\n📋 Generating Comprehensive Enhancement Report...")

        # Calculate overall success rate
        components = self.enhancement_results['components']
        total_components = len(components)
        successful_components = len([c for c in components.values() if c.get('status') == 'completed'])
        success_rate = (successful_components / total_components * 100) if total_components > 0 else 0

        self.enhancement_results['success_rate'] = success_rate

        # Generate performance summary
        performance_summary = {
            'overall_success_rate': success_rate,
            'components_completed': successful_components,
            'total_components': total_components,
            'enhancement_duration': (datetime.now(timezone.utc) - self.start_time).total_seconds(),
            'key_achievements': []
        }

        # Extract key metrics from each component
        if 'real_time_processing' in components:
            rt_data = components['real_time_processing']['data_processed']
            performance_summary['key_achievements'].append(
                f"Real-time processing: {rt_data.get('game_updates', 0)} game updates"
            )

        if 'enhanced_box_scores' in components:
            bs_data = components['enhanced_box_scores']['data_processed']
            performance_summary['key_achievements'].append(
                f"Enhanced box scores: {bs_data.get('games_processed', 0)} games processed"
            )

        if 'matchup_analysis' in components:
            ma_data = components['matchup_analysis']['data_processed']
            performance_summary['key_achievements'].append(
                f"Matchup analysis: {ma_data.get('rivalries_analyzed', 0)} rivalries analyzed"
            )

        if 'parallel_processing' in components:
            pp_data = components['parallel_processing']['performance_metrics']
            speedup = pp_data.get('total_time_saved', 0)
            performance_summary['key_achievements'].append(
                f"Parallel processing: {speedup:.1f}s time saved"
            )

        if 'enhanced_caching' in components:
            cache_data = components['enhanced_caching']['data_processed']
            hit_rate = cache_data.get('hit_rate', 0)
            performance_summary['key_achievements'].append(
                f"Enhanced caching: {hit_rate:.1f}% hit rate achieved"
            )

        self.enhancement_results['performance_summary'] = performance_summary

        return self.enhancement_results

    def save_report(self, filename: Optional[str] = None) -> str:
        """Save comprehensive report to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"complete_2025_enhancement_report_{timestamp}.json"

        # Save to reports directory
        reports_dir = os.path.join(os.path.dirname(__file__), "..", "reports")
        os.makedirs(reports_dir, exist_ok=True)

        filepath = os.path.join(reports_dir, filename)

        with open(filepath, 'w') as f:
            json.dump(self.enhancement_results, f, indent=2, default=str)

        print(f"📄 Comprehensive report saved: {filepath}")
        return filepath

    async def run_complete_suite(self):
        """Run complete enhancement suite"""
        print("🎯 Running Complete 2025 Enhancement Suite")
        print("=" * 60)

        # Run all enhancement demos
        demos = [
            ("Real-Time Processing", self.run_real_time_demo),
            ("Enhanced Box Scores", self.run_box_score_demo),
            ("Matchup Analysis", self.run_matchup_analysis_demo),
            ("Parallel Processing", self.run_parallel_processing_demo),
            ("Enhanced Caching", self.run_caching_demo)
        ]

        for demo_name, demo_func in demos:
            try:
                if asyncio.iscoroutinefunction(demo_func):
                    await demo_func()
                else:
                    demo_func()
            except Exception as e:
                logger.error(f"Error in {demo_name}: {e}")

        # Generate comprehensive report
        print(f"\n📊 Generating comprehensive report...")
        report = self.generate_comprehensive_report()

        # Save report
        report_path = self.save_report()

        # Display summary
        print(f"\n🎉 ENHANCEMENT SUITE COMPLETE!")
        print(f"   Success Rate: {report['success_rate']:.1f}%")
        print(f"   Components: {report['performance_summary']['components_completed']}/{report['performance_summary']['total_components']}")
        print(f"   Duration: {report['performance_summary']['enhancement_duration']:.1f}s")

        print(f"\n🏆 Key Achievements:")
        for achievement in report['performance_summary']['key_achievements']:
            print(f"   ✅ {achievement}")

        return report

async def main():
    """Main execution function"""
    suite = CompleteEnhancementSuite()
    await suite.run_complete_suite()

if __name__ == "__main__":
    asyncio.run(main())