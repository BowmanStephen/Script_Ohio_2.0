"""
Database Agent for Script Ohio 2.0
====================================

Intelligent database agent for college football analytics with MCP integration.
Provides advanced database operations, query optimization, and data management.

Capabilities:
- SQL query execution and optimization
- Database schema management
- Data import/export operations
- Performance monitoring
- Query result caching
"""

import sqlite3
import pandas as pd
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import json
import time

# Import MCP server tools when available
try:
    from mcp_tools import DatabaseTool, FileSystemTool
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    logging.warning("MCP tools not available, using local database operations")

class DatabaseAgent:
    """Advanced database agent with MCP integration"""

    def __init__(self, db_path: str = "data/databases/football_analysis.db"):
        self.db_path = Path(db_path)
        self.setup_logging()
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes cache TTL
        self.query_stats = {
            'total_queries': 0,
            'cache_hits': 0,
            'avg_execution_time': 0,
            'slow_queries': []
        }

        # Initialize database
        self.ensure_database_exists()

        # Initialize MCP tools if available
        if MCP_AVAILABLE:
            self.db_tool = DatabaseTool()
            self.fs_tool = FileSystemTool()
            self.logger.info("MCP tools initialized successfully")
        else:
            self.db_tool = None
            self.fs_tool = None
            self.logger.warning("Running in local mode (MCP tools unavailable)")

    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("DatabaseAgent")

    def ensure_database_exists(self):
        """Ensure SQLite database exists and is properly initialized"""
        if not self.db_path.exists():
            self.logger.warning(f"Database file not found: {self.db_path}")
            self.logger.info("Run migration script first: python scripts/migrate_to_database.py")

    def execute_query(self, query: str, params: tuple = None, use_cache: bool = True) -> pd.DataFrame:
        """Execute SQL query with caching and performance monitoring"""
        start_time = time.time()

        # Check cache first
        cache_key = f"{hash(query)}_{hash(params) if params else ''}"
        if use_cache and cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            if time.time() - cache_entry['timestamp'] < self.cache_ttl:
                self.query_stats['cache_hits'] += 1
                self.logger.debug(f"Cache hit for query: {query[:50]}...")
                return cache_entry['data']

        try:
            if self.db_tool and MCP_AVAILABLE:
                # Use MCP database tool
                result = self.db_tool.query(query, params)
                df = pd.DataFrame(result['data']) if result['data'] else pd.DataFrame()
            else:
                # Use local SQLite
                conn = sqlite3.connect(self.db_path)
                df = pd.read_sql_query(query, conn, params=params)
                conn.close()

            # Cache result
            if use_cache:
                self.cache[cache_key] = {
                    'data': df.copy(),
                    'timestamp': time.time()
                }

            # Update statistics
            execution_time = time.time() - start_time
            self.update_query_stats(execution_time, query)

            self.logger.info(f"Query executed successfully in {execution_time:.3f}s, returned {len(df)} rows")
            return df

        except Exception as e:
            self.logger.error(f"Query execution failed: {e}")
            raise

    def update_query_stats(self, execution_time: float, query: str):
        """Update query performance statistics"""
        self.query_stats['total_queries'] += 1

        # Update average execution time
        total_time = self.query_stats['avg_execution_time'] * (self.query_stats['total_queries'] - 1)
        self.query_stats['avg_execution_time'] = (total_time + execution_time) / self.query_stats['total_queries']

        # Track slow queries ( > 1 second )
        if execution_time > 1.0:
            self.query_stats['slow_queries'].append({
                'query': query[:100] + "..." if len(query) > 100 else query,
                'execution_time': execution_time,
                'timestamp': datetime.now().isoformat()
            })

    def get_team_stats(self, team_name: str, season: int = None) -> Dict[str, Any]:
        """Get comprehensive statistics for a specific team"""
        try:
            base_query = """
            SELECT
                season,
                COUNT(*) as games_played,
                SUM(CASE WHEN home_team = ? THEN home_score ELSE away_score END) as points_scored,
                SUM(CASE WHEN home_team = ? THEN away_score ELSE home_score END) as points_allowed,
                SUM(CASE WHEN
                    (home_team = ? AND home_score > away_score) OR
                    (away_team = ? AND away_score > home_score)
                THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN
                    (home_team = ? AND home_score < away_score) OR
                    (away_team = ? AND away_score < home_score)
                THEN 1 ELSE 0 END) as losses
            FROM games
            WHERE (home_team = ? OR away_team = ?)
            """

            params = [team_name] * 8
            if season:
                base_query += " AND season = ?"
                params.append(season)

            base_query += " GROUP BY season ORDER BY season DESC"

            df = self.execute_query(base_query, tuple(params))

            if df.empty:
                return {"error": f"No data found for team: {team_name}"}

            # Calculate additional metrics
            df['win_percentage'] = df['wins'] / (df['wins'] + df['losses'])
            df['points_per_game'] = df['points_scored'] / df['games_played']
            df['points_allowed_per_game'] = df['points_allowed'] / df['games_played']
            df['point_differential'] = df['points_scored'] - df['points_allowed']

            return {
                "team": team_name,
                "season": season,
                "stats": df.to_dict('records')[0] if len(df) == 1 else df.to_dict('records'),
                "query_time": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error getting team stats: {e}")
            return {"error": str(e)}

    def get_conference_rankings(self, season: int = None, week: int = None) -> pd.DataFrame:
        """Get conference rankings for specified season/week"""
        try:
            query = """
            WITH team_stats AS (
                SELECT
                    CASE
                        WHEN home_team = teams.team_name THEN home_team
                        ELSE away_team
                    END as team,
                    COUNT(*) as games_played,
                    SUM(CASE
                        WHEN home_team = teams.team_name THEN
                            CASE WHEN home_score > away_score THEN 1 ELSE 0 END
                        ELSE
                            CASE WHEN away_score > home_score THEN 1 ELSE 0 END
                    END) as wins,
                    SUM(CASE
                        WHEN home_team = teams.team_name THEN
                            CASE WHEN home_score < away_score THEN 1 ELSE 0 END
                        ELSE
                            CASE WHEN away_score < home_score THEN 1 ELSE 0 END
                    END) as losses,
                    SUM(CASE WHEN home_team = teams.team_name THEN home_score ELSE away_score END) as points_scored,
                    SUM(CASE WHEN home_team = teams.team_name THEN away_score ELSE home_score END) as points_allowed
                FROM games
                JOIN teams ON (home_team = teams.team_name OR away_team = teams.team_name)
                WHERE 1=1
            """

            params = []
            if season:
                query += " AND games.season = ?"
                params.append(season)
            if week:
                query += " AND games.week <= ?"
                params.append(week)

            query += """
                GROUP BY teams.team_name
            )
            SELECT
                ts.team,
                t.conference,
                ts.games_played,
                ts.wins,
                ts.losses,
                CASE
                    WHEN ts.wins + ts.losses > 0
                    THEN ROUND(ts.wins * 100.0 / (ts.wins + ts.losses), 2)
                    ELSE 0
                END as win_percentage,
                ts.points_scored,
                ts.points_allowed,
                (ts.points_scored - ts.points_allowed) as point_differential,
                CASE
                    WHEN ts.games_played > 0
                    THEN ROUND((ts.points_scored - ts.points_allowed) * 1.0 / ts.games_played, 2)
                    ELSE 0
                END as avg_point_differential
            FROM team_stats ts
            JOIN teams t ON ts.team = t.team_name
            WHERE t.conference IS NOT NULL
            ORDER BY t.conference, win_percentage DESC, point_differential DESC
            """

            df = self.execute_query(query, tuple(params) if params else None)
            return df

        except Exception as e:
            self.logger.error(f"Error getting conference rankings: {e}")
            return pd.DataFrame()

    def analyze_team_matchup(self, team1: str, team2: str, seasons_back: int = 5) -> Dict[str, Any]:
        """Analyze historical matchup between two teams"""
        try:
            current_year = datetime.now().year
            start_year = current_year - seasons_back

            query = """
            SELECT
                season,
                week,
                home_team,
                away_team,
                home_score,
                away_score,
                CASE
                    WHEN home_team = ? THEN home_score - away_score
                    ELSE away_score - home_score
                END as team1_margin,
                CASE
                    WHEN home_score > away_score THEN home_team
                    ELSE away_team
                END as winner,
                venue,
                season_type
            FROM games
            WHERE (home_team = ? AND away_team = ?)
               OR (home_team = ? AND away_team = ?)
            AND season >= ?
            ORDER BY season DESC, week DESC
            """

            params = [team1, team1, team2, team2, team1, start_year]
            df = self.execute_query(query, tuple(params))

            if df.empty:
                return {"error": f"No matchup history found between {team1} and {team2}"}

            # Calculate matchup statistics
            team1_wins = len(df[df['winner'] == team1])
            team2_wins = len(df[df['winner'] == team2])
            total_games = len(df)

            avg_margin = df['team1_margin'].mean()
            team1_avg_score = df.apply(lambda row: row['home_score'] if row['home_team'] == team1 else row['away_score'], axis=1).mean()
            team2_avg_score = df.apply(lambda row: row['home_score'] if row['home_team'] == team2 else row['away_score'], axis=1).mean()

            return {
                "matchup": f"{team1} vs {team2}",
                "period": f"{start_year}-{current_year}",
                "total_games": total_games,
                "team1_record": f"{team1_wins}-{team2_wins}",
                "team1_win_percentage": round(team1_wins / total_games * 100, 2) if total_games > 0 else 0,
                "avg_margin": round(avg_margin, 2),
                "team1_avg_score": round(team1_avg_score, 2),
                "team2_avg_score": round(team2_avg_score, 2),
                "recent_games": df.head(5).to_dict('records'),
                "analysis_timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error analyzing matchup: {e}")
            return {"error": str(e)}

    def export_query_results(self, query: str, output_path: str, format: str = "csv") -> bool:
        """Export query results to file"""
        try:
            df = self.execute_query(query, use_cache=False)

            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            if format.lower() == "csv":
                df.to_csv(output_file, index=False)
            elif format.lower() == "json":
                df.to_json(output_file, orient='records', indent=2)
            elif format.lower() == "excel":
                df.to_excel(output_file, index=False)
            else:
                raise ValueError(f"Unsupported format: {format}")

            self.logger.info(f"Query results exported to {output_file} ({len(df)} rows)")
            return True

        except Exception as e:
            self.logger.error(f"Error exporting query results: {e}")
            return False

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get database agent performance statistics"""
        return {
            "query_statistics": self.query_stats.copy(),
            "cache_size": len(self.cache),
            "database_path": str(self.db_path),
            "mcp_available": MCP_AVAILABLE,
            "stats_timestamp": datetime.now().isoformat()
        }

    def clear_cache(self):
        """Clear query cache"""
        self.cache.clear()
        self.logger.info("Query cache cleared")

    def optimize_database(self) -> bool:
        """Optimize database performance"""
        try:
            if self.db_tool and MCP_AVAILABLE:
                # Use MCP database optimization
                result = self.db_tool.optimize()
                self.logger.info("Database optimized via MCP tools")
                return True
            else:
                # Local SQLite optimization
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                # Analyze tables
                cursor.execute("ANALYZE")
                self.logger.info("Database analyzed for query optimization")

                # Vacuum database
                cursor.execute("VACUUM")
                self.logger.info("Database vacuumed")

                conn.close()
                return True

        except Exception as e:
            self.logger.error(f"Database optimization failed: {e}")
            return False

# Convenience functions for common operations
def get_top_teams(scoring_type: str = "offense", season: int = None, limit: int = 25) -> pd.DataFrame:
    """Get top teams by scoring"""
    agent = DatabaseAgent()

    if scoring_type == "offense":
        query = """
        SELECT
            team,
            SUM(points_scored) as total_points,
            AVG(points_scored) as avg_points_per_game,
            COUNT(*) as games_played
        FROM team_game_stats
        WHERE 1=1
        """
    else:  # defense
        query = """
        SELECT
            team,
            SUM(points_allowed) as total_points_allowed,
            AVG(points_allowed) as avg_points_allowed_per_game,
            COUNT(*) as games_played
        FROM team_game_stats
        WHERE 1=1
        """

    params = []
    if season:
        query += " AND season = ?"
        params.append(season)

    if scoring_type == "offense":
        query += " ORDER BY avg_points_per_game DESC"
    else:
        query += " ORDER BY avg_points_allowed_per_game ASC"

    query += f" LIMIT {limit}"

    return agent.execute_query(query, tuple(params) if params else None)

if __name__ == "__main__":
    # Example usage
    agent = DatabaseAgent()

    # Test basic functionality
    print("Testing Database Agent...")

    # Get team stats
    ohio_state_stats = agent.get_team_stats("Ohio State")
    print(f"Ohio State Stats: {ohio_state_stats}")

    # Get performance stats
    perf_stats = agent.get_performance_stats()
    print(f"Performance Stats: {perf_stats}")