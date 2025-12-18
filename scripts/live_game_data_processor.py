#!/usr/bin/env python3
"""
Real-Time Game Data Processor
Processes live game data from WebSocket client and provides intelligent analysis
"""

import os
import sys
import json
import time
import asyncio
import pandas as pd
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Callable
import logging

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.cfbd_client.websocket_client import CFBDWebSocketClient, LiveGameData, ScoreUpdate, PlayUpdate
from src.cfbd_client.enhanced_unified_client import EnhancedUnifiedCFBDClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LiveGameAnalyzer:
    """Analyzes live game data and provides insights"""

    def __init__(self):
        self.client = EnhancedUnifiedCFBDClient()
        self.game_analytics: Dict[int, Dict[str, Any]] = {}
        self.team_performance: Dict[str, Dict[str, Any]] = {}

    def analyze_scoring_patterns(self, game_id: int, score_updates: List[ScoreUpdate]) -> Dict[str, Any]:
        """Analyze scoring patterns and trends"""
        if not score_updates:
            return {}

        analysis = {
            'total_scores': len(score_updates),
            'scoring_teams': {},
            'scoring_frequency': {},
            'quarter_scoring': {1: 0, 2: 0, 3: 0, 4: 0},  # Would be calculated from actual quarters
            'big_plays': [],
            'momentum_shifts': []
        }

        # Analyze scoring by team
        for update in score_updates:
            team = update.scoring_team
            if team not in analysis['scoring_teams']:
                analysis['scoring_teams'][team] = {
                    'total_points': 0,
                    'score_count': 0,
                    'average_points': 0
                }

            analysis['scoring_teams'][team]['total_points'] += update.points
            analysis['scoring_teams'][team]['score_count'] += 1

        # Calculate averages
        for team in analysis['scoring_teams']:
            data = analysis['scoring_teams'][team]
            data['average_points'] = data['total_points'] / data['score_count']

        return analysis

    def analyze_possession_and_momentum(self, game_id: int, play_updates: List[PlayUpdate]) -> Dict[str, Any]:
        """Analyze possession patterns and momentum"""
        if not play_updates:
            return {}

        analysis = {
            'total_plays': len(play_updates),
            'team_plays': {},
            'play_types': {},
            'yards_per_play': {},
            'momentum_indicator': 0,  # -1 to 1 scale
            'key_drives': []
        }

        # Analyze plays by team
        for play in play_updates:
            team = play.team
            if team not in analysis['team_plays']:
                analysis['team_plays'][team] = {
                    'play_count': 0,
                    'total_yards': 0,
                    'successful_plays': 0
                }

            team_data = analysis['team_plays'][team]
            team_data['play_count'] += 1

            if play.yards_gained:
                team_data['total_yards'] += play.yards_gained

            # Consider successful play based on result
            if play.play_result in ['first_down', 'touchdown']:
                team_data['successful_plays'] += 1

            # Track play types
            play_type = play.play_type
            if play_type not in analysis['play_types']:
                analysis['play_types'][play_type] = 0
            analysis['play_types'][play_type] += 1

        # Calculate yards per play
        for team in analysis['team_plays']:
            data = analysis['team_plays'][team]
            if data['play_count'] > 0:
                analysis['yards_per_play'][team] = data['total_yards'] / data['play_count']

        return analysis

    def update_team_performance(self, game_data: LiveGameData):
        """Update team performance metrics"""
        home_team = game_data.home_team
        away_team = game_data.away_team

        # Initialize team data if not exists
        for team in [home_team, away_team]:
            if team not in self.team_performance:
                self.team_performance[team] = {
                    'games_played': 0,
                    'wins': 0,
                    'losses': 0,
                    'points_scored': 0,
                    'points_allowed': 0,
                    'scoring_efficiency': 0,
                    'defensive_strength': 0,
                    'last_updated': None
                }

        # Update game statistics
        if game_data.game_status == 'completed':
            # Update home team
            home_perf = self.team_performance[home_team]
            home_perf['games_played'] += 1
            home_perf['points_scored'] += game_data.home_score
            home_perf['points_allowed'] += game_data.away_score

            if game_data.home_score > game_data.away_score:
                home_perf['wins'] += 1
            else:
                home_perf['losses'] += 1

            # Update away team
            away_perf = self.team_performance[away_team]
            away_perf['games_played'] += 1
            away_perf['points_scored'] += game_data.away_score
            away_perf['points_allowed'] += game_data.home_score

            if game_data.away_score > game_data.home_score:
                away_perf['wins'] += 1
            else:
                away_perf['losses'] += 1

            # Calculate efficiency metrics
            for team_perf in [home_perf, away_perf]:
                if team_perf['games_played'] > 0:
                    team_perf['scoring_efficiency'] = team_perf['points_scored'] / team_perf['games_played']
                    team_perf['defensive_strength'] = team_perf['points_allowed'] / team_perf['games_played']
                team_perf['last_updated'] = datetime.now(timezone.utc)

class LiveGameProcessor:
    """Main processor for live game data with WebSocket integration"""

    def __init__(self):
        self.client = CFBDWebSocketClient()
        self.analyzer = LiveGameAnalyzer()
        self.processed_games: Dict[int, Dict[str, Any]] = {}
        self.score_updates: Dict[int, List[ScoreUpdate]] = {}
        self.play_updates: Dict[int, List[PlayUpdate]] = {}

        # Output directories
        self.output_dir = os.path.join(os.path.dirname(__file__), "..", "data", "live", "2025")
        os.makedirs(self.output_dir, exist_ok=True)

        # Setup event handlers
        self._setup_event_handlers()

        logger.info("🔄 Live Game Data Processor initialized")

    def _setup_event_handlers(self):
        """Setup WebSocket event handlers"""
        self.client.add_event_handler('game_update', self.handle_game_update)
        self.client.add_event_handler('score_update', self.handle_score_update)
        self.client.add_event_handler('play_update', self.handle_play_update)
        self.client.add_event_handler('connection_status', self.handle_connection_status)

    async def handle_game_update(self, game_data: LiveGameData):
        """Handle live game updates"""
        logger.info(f"🏈 Game Update: {game_data.home_team} {game_data.home_score} - {game_data.away_team} {game_data.away_score}")

        # Store game data
        self.processed_games[game_data.game_id] = {
            'game_data': game_data,
            'last_update': datetime.now(timezone.utc),
            'analysis': {}
        }

        # Analyze scoring patterns if we have score updates
        if game_data.game_id in self.score_updates:
            scoring_analysis = self.analyzer.analyze_scoring_patterns(
                game_data.game_id,
                self.score_updates[game_data.game_id]
            )
            self.processed_games[game_data.game_id]['analysis']['scoring'] = scoring_analysis

        # Analyze play patterns if we have play updates
        if game_data.game_id in self.play_updates:
            play_analysis = self.analyzer.analyze_possession_and_momentum(
                game_data.game_id,
                self.play_updates[game_data.game_id]
            )
            self.processed_games[game_data.game_id]['analysis']['plays'] = play_analysis

        # Update team performance
        self.analyzer.update_team_performance(game_data)

        # Save updated data
        await self.save_game_data(game_data.game_id)

    async def handle_score_update(self, score_data: ScoreUpdate):
        """Handle scoring updates"""
        logger.info(f"🎯 Score: {score_data.scoring_team} +{score_data.points} - "
                   f"{score_data.new_home_score}-{score_data.new_away_score}")

        # Store score update
        if score_data.game_id not in self.score_updates:
            self.score_updates[score_data.game_id] = []
        self.score_updates[score_data.game_id].append(score_data)

        # Update game data
        if score_data.game_id in self.processed_games:
            game_data = self.processed_games[score_data.game_id]['game_data']
            game_data.home_score = score_data.new_home_score
            game_data.away_score = score_data.new_away_score
            game_data.last_updated = score_data.timestamp

    async def handle_play_update(self, play_data: PlayUpdate):
        """Handle play-by-play updates"""
        logger.info(f"📝 Play: {play_data.team} - {play_data.description} ({play_data.yards_gained} yards)")

        # Store play update
        if play_data.game_id not in self.play_updates:
            self.play_updates[play_data.game_id] = []
        self.play_updates[play_data.game_id].append(play_data)

        # Limit stored plays to prevent memory issues
        if len(self.play_updates[play_data.game_id]) > 500:
            self.play_updates[play_data.game_id] = self.play_updates[play_data.game_id][-400:]

    async def handle_connection_status(self, status_data: Dict[str, Any]):
        """Handle connection status updates"""
        logger.info(f"🔌 Connection: {status_data['status']}")
        if status_data['status'] == 'disconnected':
            logger.warning("⚠️ WebSocket disconnected - attempting to reconnect")

    async def start_processing(self, year: int = 2025, week: Optional[int] = None):
        """Start processing live game data"""
        logger.info(f"🚀 Starting live game data processing for {year}, week {week or 'current'}")

        # Connect to WebSocket
        await self.client.connect()

        if not self.client.is_connected:
            logger.error("❌ Failed to connect to WebSocket")
            return

        try:
            # Subscribe to games
            await self.client.subscribe_to_games(year=year, week=week)

            # Keep processing alive
            logger.info("📡 Processing live game data... Press Ctrl+C to stop")

            # Save initial state
            await self.save_all_data()

            # Run indefinitely (or until stopped)
            while self.client.is_connected:
                await asyncio.sleep(60)  # Check every minute

                # Save data periodically
                await self.save_all_data()

        except KeyboardInterrupt:
            logger.info("🛑 Stopping live game processing...")
        finally:
            await self.client.disconnect()
            await self.save_all_data()

    async def save_game_data(self, game_id: int):
        """Save data for specific game"""
        if game_id not in self.processed_games:
            return

        data = self.processed_games[game_id]
        filename = f"game_{game_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(self.output_dir, filename)

        # Convert data to serializable format
        serializable_data = {
            'game_id': game_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'game_data': {
                'game_id': data['game_data'].game_id,
                'home_team': data['game_data'].home_team,
                'away_team': data['game_data'].away_team,
                'home_score': data['game_data'].home_score,
                'away_score': data['game_data'].away_score,
                'quarter': data['game_data'].quarter,
                'time_remaining': data['game_data'].time_remaining,
                'possession': data['game_data'].possession,
                'game_status': data['game_data'].game_status,
                'last_updated': data['game_data'].last_updated.isoformat() if data['game_data'].last_updated else None
            },
            'analysis': data.get('analysis', {}),
            'score_updates_count': len(self.score_updates.get(game_id, [])),
            'play_updates_count': len(self.play_updates.get(game_id, []))
        }

        with open(filepath, 'w') as f:
            json.dump(serializable_data, f, indent=2)

    async def save_all_data(self):
        """Save all processed data"""
        # Save game data
        for game_id in list(self.processed_games.keys()):
            await self.save_game_data(game_id)

        # Save team performance data
        team_perf_file = os.path.join(self.output_dir, "team_performance.json")
        with open(team_perf_file, 'w') as f:
            json.dump(self.analyzer.team_performance, f, indent=2, default=str)

        # Save processing summary
        summary = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'total_games_processed': len(self.processed_games),
            'active_subscriptions': len(self.client.subscribed_games),
            'live_games_count': len(self.client.live_games),
            'websocket_metrics': self.client.get_metrics()
        }

        summary_file = os.path.join(self.output_dir, "processing_summary.json")
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)

        logger.info(f"💾 Saved data to {self.output_dir}")

    def get_processing_summary(self) -> Dict[str, Any]:
        """Get summary of current processing state"""
        return {
            'games_processed': len(self.processed_games),
            'active_games': len([g for g in self.processed_games.values()
                               if g['game_data'].game_status == 'in_progress']),
            'completed_games': len([g for g in self.processed_games.values()
                                  if g['game_data'].game_status == 'completed']),
            'total_score_updates': sum(len(updates) for updates in self.score_updates.values()),
            'total_play_updates': sum(len(updates) for updates in self.play_updates.values()),
            'team_performance_metrics': len(self.analyzer.team_performance)
        }

async def main():
    """Main execution function"""
    print("🚀 Starting Live Game Data Processor")
    print("=" * 50)

    processor = LiveGameProcessor()

    try:
        # Start processing for current week
        await processor.start_processing(year=2025, week=15)  # Championship week

    except Exception as e:
        logger.error(f"❌ Error in main processing loop: {e}")
    finally:
        # Final save
        await processor.save_all_data()

        # Print summary
        summary = processor.get_processing_summary()
        print(f"\n📊 PROCESSING SUMMARY:")
        print(f"  Games processed: {summary['games_processed']}")
        print(f"  Active games: {summary['active_games']}")
        print(f"  Completed games: {summary['completed_games']}")
        print(f"  Score updates: {summary['total_score_updates']}")
        print(f"  Play updates: {summary['total_play_updates']}")

if __name__ == "__main__":
    asyncio.run(main())