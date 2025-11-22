"""
Visualization Agent for Script Ohio 2.0
========================================

Advanced visualization agent with MCP integration for college football analytics.
Provides dynamic chart generation, interactive dashboards, and professional exports.

Capabilities:
- Multiple chart types (bar, line, pie, scatter, heatmap)
- Interactive visualizations with ECharts
- Professional export formats (PNG, SVG, PDF)
- Dashboard generation
- Real-time data visualization
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import json
import base64
from io import BytesIO

# Import MCP server tools when available
try:
    from mcp_tools import EChartsTool, DatawrapperTool, QuickChartTool
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    logging.warning("MCP visualization tools not available, using local libraries")

class VisualizationAgent:
    """Advanced visualization agent with MCP integration"""

    def __init__(self, output_dir: str = "data/exports"):
        self.output_dir = Path(output_dir)
        self.setup_logging()
        self.setup_style()

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize MCP tools if available
        if MCP_AVAILABLE:
            self.echarts_tool = EChartsTool()
            self.datawrapper_tool = DatawrapperTool()
            self.quickchart_tool = QuickChartTool()
            self.logger.info("MCP visualization tools initialized successfully")
        else:
            self.echarts_tool = None
            self.datawrapper_tool = None
            self.quickchart_tool = None
            self.logger.warning("Running in local mode (MCP tools unavailable)")

    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("VisualizationAgent")

    def setup_style(self):
        """Setup visualization style and theme"""
        # Set style for matplotlib/seaborn
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")

        # College football themed colors
        self.colors = {
            'primary': '#DC143C',      # Crimson
            'secondary': '#FFD700',    # Gold
            'tertiary': '#1E3A8A',     # Navy
            'success': '#22C55E',      # Green
            'warning': '#F59E0B',      # Amber
            'danger': '#EF4444',       # Red
            'info': '#3B82F6',         # Blue
            'neutral': '#6B7280'       # Gray
        }

    def create_team_rankings_chart(self, data: pd.DataFrame, chart_type: str = "bar",
                                 title: str = "Team Rankings", export_format: str = "png") -> str:
        """Create team rankings visualization"""
        try:
            if data.empty:
                raise ValueError("No data provided for visualization")

            # Prepare data
            if 'team' in data.columns and 'win_percentage' in data.columns:
                plot_data = data.sort_values('win_percentage', ascending=True).tail(20)
                x_col = 'win_percentage'
                y_col = 'team'
            else:
                # Try to auto-detect columns
                numeric_cols = data.select_dtypes(include=[np.number]).columns
                text_cols = data.select_dtypes(include=['object']).columns

                if len(numeric_cols) > 0 and len(text_cols) > 0:
                    x_col = numeric_cols[0]
                    y_col = text_cols[0]
                    plot_data = data.sort_values(x_col, ascending=True).tail(20)
                else:
                    raise ValueError("Cannot determine data columns for visualization")

            if self.echarts_tool and MCP_AVAILABLE:
                # Use MCP ECharts tool
                chart_config = {
                    'title': {'text': title, 'left': 'center'},
                    'tooltip': {'trigger': 'axis'},
                    'grid': {'left': '3%', 'right': '4%', 'bottom': '3%', 'containLabel': True},
                    'xAxis': {'type': 'value'},
                    'yAxis': {'type': 'category', 'data': plot_data[y_col].tolist()},
                    'series': [{
                        'type': 'bar',
                        'data': plot_data[x_col].tolist(),
                        'itemStyle': {'color': self.colors['primary']}
                    }]
                }

                result = self.echarts_tool.create_chart(chart_config, export_format)
                output_path = self.output_dir / f"team_rankings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{export_format}"

                if result.get('success'):
                    with open(output_path, 'wb') as f:
                        f.write(result['data'])
                    self.logger.info(f"ECharts visualization saved to {output_path}")
                    return str(output_path)

            # Fallback to matplotlib
            plt.figure(figsize=(12, 8))
            plt.barh(plot_data[y_col], plot_data[x_col], color=self.colors['primary'])
            plt.title(title, fontsize=16, fontweight='bold')
            plt.xlabel(x_col.replace('_', ' ').title(), fontsize=12)
            plt.ylabel(y_col.replace('_', ' ').title(), fontsize=12)
            plt.grid(axis='x', alpha=0.3)
            plt.tight_layout()

            output_path = self.output_dir / f"team_rankings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{export_format}"
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()

            self.logger.info(f"Matplotlib visualization saved to {output_path}")
            return str(output_path)

        except Exception as e:
            self.logger.error(f"Error creating team rankings chart: {e}")
            raise

    def create_conference_comparison(self, data: pd.DataFrame, metric: str = "win_percentage") -> str:
        """Create conference comparison chart"""
        try:
            if data.empty or 'conference' not in data.columns:
                raise ValueError("Data must contain conference column")

            # Aggregate by conference
            conf_stats = data.groupby('conference').agg({
                metric: 'mean',
                'team': 'count'
            }).reset_index()
            conf_stats.columns = ['conference', f'avg_{metric}', 'team_count']

            # Sort by metric
            conf_stats = conf_stats.sort_values(f'avg_{metric}', ascending=True)

            if self.datawrapper_tool and MCP_AVAILABLE:
                # Use MCP Datawrapper tool
                chart_data = conf_stats[['conference', f'avg_{metric}']].to_dict('records')

                chart_config = {
                    'title': f'Conference Comparison - {metric.replace("_", " ").title()}',
                    'type': 'bar-chart',
                    'data': chart_data,
                    'xColumn': 'conference',
                    'yColumn': f'avg_{metric}',
                    'theme': 'datawrapper'
                }

                result = self.datawrapper_tool.create_chart(chart_config)
                if result.get('success'):
                    output_path = self.output_dir / f"conference_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                    with open(output_path, 'w') as f:
                        f.write(result['html'])
                    self.logger.info(f"Datawrapper chart saved to {output_path}")
                    return str(output_path)

            # Fallback to matplotlib
            plt.figure(figsize=(14, 8))
            bars = plt.barh(conf_stats['conference'], conf_stats[f'avg_{metric}'],
                          color=[self.colors['primary'], self.colors['secondary'], self.colors['tertiary']] * 5)

            # Add value labels on bars
            for i, bar in enumerate(bars):
                width = bar.get_width()
                plt.text(width + 0.001, bar.get_y() + bar.get_height()/2,
                        f'{width:.3f}', ha='left', va='center')

            plt.title(f'Conference Comparison - {metric.replace("_", " ").title()}',
                     fontsize=16, fontweight='bold')
            plt.xlabel(metric.replace('_', ' ').title(), fontsize=12)
            plt.ylabel('Conference', fontsize=12)
            plt.grid(axis='x', alpha=0.3)
            plt.tight_layout()

            output_path = self.output_dir / f"conference_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()

            self.logger.info(f"Conference comparison chart saved to {output_path}")
            return str(output_path)

        except Exception as e:
            self.logger.error(f"Error creating conference comparison: {e}")
            raise

    def create_season_trends(self, data: pd.DataFrame, teams: List[str] = None,
                           metric: str = "win_percentage") -> str:
        """Create season trends visualization"""
        try:
            if data.empty or 'season' not in data.columns:
                raise ValueError("Data must contain season column")

            if teams:
                # Filter for specific teams
                data = data[data['team'].isin(teams)]

            # Pivot data for trend lines
            if 'team' in data.columns:
                trend_data = data.pivot_table(values=metric, index='season', columns='team', aggfunc='mean')
            else:
                # Aggregate by season
                trend_data = data.groupby('season')[metric].mean().to_frame()
                trend_data.columns = ['Average']

            if self.echarts_tool and MCP_AVAILABLE:
                # Use MCP ECharts tool for interactive line chart
                series = []
                for column in trend_data.columns:
                    series.append({
                        'name': column,
                        'type': 'line',
                        'data': trend_data[column].fillna(0).tolist(),
                        'smooth': True
                    })

                chart_config = {
                    'title': {'text': f'Season Trends - {metric.replace("_", " ").title()}', 'left': 'center'},
                    'tooltip': {'trigger': 'axis'},
                    'legend': {'data': list(trend_data.columns), 'bottom': 0},
                    'grid': {'left': '3%', 'right': '4%', 'bottom': '15%', 'containLabel': True},
                    'xAxis': {
                        'type': 'category',
                        'data': trend_data.index.tolist()
                    },
                    'yAxis': {'type': 'value'},
                    'series': series
                }

                result = self.echarts_tool.create_chart(chart_config, 'html')
                if result.get('success'):
                    output_path = self.output_dir / f"season_trends_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                    with open(output_path, 'w') as f:
                        f.write(result['html'])
                    self.logger.info(f"Interactive season trends saved to {output_path}")
                    return str(output_path)

            # Fallback to matplotlib
            plt.figure(figsize=(14, 8))

            for column in trend_data.columns:
                plt.plot(trend_data.index, trend_data[column],
                        marker='o', linewidth=2, markersize=6, label=column)

            plt.title(f'Season Trends - {metric.replace("_", " ").title()}', fontsize=16, fontweight='bold')
            plt.xlabel('Season', fontsize=12)
            plt.ylabel(metric.replace('_', ' ').title(), fontsize=12)
            plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.grid(True, alpha=0.3)
            plt.tight_layout()

            output_path = self.output_dir / f"season_trends_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()

            self.logger.info(f"Season trends chart saved to {output_path}")
            return str(output_path)

        except Exception as e:
            self.logger.error(f"Error creating season trends: {e}")
            raise

    def create_matchup_heatmap(self, data: pd.DataFrame) -> str:
        """Create matchup heatmap showing team performance against each other"""
        try:
            if data.empty or not all(col in data.columns for col in ['team', 'opponent', 'result']):
                raise ValueError("Data must contain team, opponent, and result columns")

            # Create win-loss matrix
            teams = sorted(set(data['team'].unique()) | set(data['opponent'].unique()))
            matrix = pd.DataFrame(0, index=teams, columns=teams)

            for _, row in data.iterrows():
                team, opponent = row['team'], row['opponent']
                result = row['result']

                if result == 'W':  # Win
                    matrix.loc[team, opponent] = 1
                elif result == 'L':  # Loss
                    matrix.loc[team, opponent] = -1
                # Tie = 0, already set

            # Create heatmap
            plt.figure(figsize=(16, 12))
            sns.heatmap(matrix, annot=True, cmap='RdYlGn', center=0,
                       square=True, linewidths=0.5, cbar_kws={'label': 'Result (1=Win, 0=Tie, -1=Loss)'})

            plt.title('Team Matchup Performance Heatmap', fontsize=16, fontweight='bold')
            plt.xlabel('Opponent', fontsize=12)
            plt.ylabel('Team', fontsize=12)
            plt.tight_layout()

            output_path = self.output_dir / f"matchup_heatmap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()

            self.logger.info(f"Matchup heatmap saved to {output_path}")
            return str(output_path)

        except Exception as e:
            self.logger.error(f"Error creating matchup heatmap: {e}")
            raise

    def create_dashboard(self, data_sources: Dict[str, pd.DataFrame], title: str = "Analytics Dashboard") -> str:
        """Create comprehensive analytics dashboard"""
        try:
            # Create subplots
            fig, axes = plt.subplots(2, 2, figsize=(16, 12))
            fig.suptitle(title, fontsize=20, fontweight='bold')

            # 1. Top Teams Bar Chart
            if 'rankings' in data_sources:
                rankings_data = data_sources['rankings']
                if not rankings_data.empty and 'win_percentage' in rankings_data.columns:
                    top_teams = rankings_data.nlargest(10, 'win_percentage')
                    axes[0, 0].barh(range(len(top_teams)), top_teams['win_percentage'],
                                   color=self.colors['primary'])
                    axes[0, 0].set_yticks(range(len(top_teams)))
                    axes[0, 0].set_yticklabels(top_teams['team'])
                    axes[0, 0].set_title('Top 10 Teams by Win %')
                    axes[0, 0].set_xlabel('Win Percentage')

            # 2. Conference Distribution
            if 'conference_stats' in data_sources:
                conf_data = data_sources['conference_stats']
                if not conf_data.empty and 'conference' in conf_data.columns:
                    conf_counts = conf_data['conference'].value_counts()
                    axes[0, 1].pie(conf_counts.values, labels=conf_counts.index, autopct='%1.1f%%')
                    axes[0, 1].set_title('Conference Distribution')

            # 3. Season Trends
            if 'season_data' in data_sources:
                season_data = data_sources['season_data']
                if not season_data.empty and 'season' in season_data.columns:
                    season_avg = season_data.groupby('season')['win_percentage'].mean()
                    axes[1, 0].plot(season_avg.index, season_avg.values,
                                   marker='o', linewidth=2, color=self.colors['secondary'])
                    axes[1, 0].set_title('Average Win % by Season')
                    axes[1, 0].set_xlabel('Season')
                    axes[1, 0].set_ylabel('Win Percentage')
                    axes[1, 0].grid(True, alpha=0.3)

            # 4. Points Distribution
            if 'scoring_data' in data_sources:
                scoring_data = data_sources['scoring_data']
                if not scoring_data.empty:
                    points_cols = [col for col in scoring_data.columns if 'points' in col.lower()]
                    if points_cols:
                        for col in points_cols[:3]:  # Limit to 3 series
                            axes[1, 1].hist(scoring_data[col].dropna(), alpha=0.7,
                                          label=col.replace('_', ' ').title(), bins=20)
                        axes[1, 1].set_title('Points Distribution')
                        axes[1, 1].set_xlabel('Points')
                        axes[1, 1].set_ylabel('Frequency')
                        axes[1, 1].legend()

            plt.tight_layout()

            output_path = self.output_dir / f"dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()

            self.logger.info(f"Dashboard saved to {output_path}")
            return str(output_path)

        except Exception as e:
            self.logger.error(f"Error creating dashboard: {e}")
            raise

    def export_chart_data(self, chart_path: str, include_config: bool = True) -> Dict[str, Any]:
        """Export chart data and configuration for reproducibility"""
        try:
            chart_file = Path(chart_path)
            if not chart_file.exists():
                raise FileNotFoundError(f"Chart file not found: {chart_path}")

            export_data = {
                'chart_path': str(chart_file),
                'chart_type': chart_file.suffix[1:],  # Remove dot
                'file_size': chart_file.stat().st_size,
                'created_at': datetime.now().isoformat()
            }

            if include_config:
                export_data['visualization_config'] = {
                    'colors': self.colors,
                    'output_directory': str(self.output_dir),
                    'mcp_available': MCP_AVAILABLE
                }

            # Save export data
            export_path = self.output_dir / f"chart_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(export_path, 'w') as f:
                json.dump(export_data, f, indent=2)

            self.logger.info(f"Chart export data saved to {export_path}")
            return export_data

        except Exception as e:
            self.logger.error(f"Error exporting chart data: {e}")
            raise

# Convenience functions for common visualizations
def create_team_performance_chart(team_name: str, data: pd.DataFrame, seasons: List[int] = None) -> str:
    """Create performance chart for a specific team"""
    agent = VisualizationAgent()

    team_data = data[data['team'] == team_name].copy()
    if seasons:
        team_data = team_data[team_data['season'].isin(seasons)]

    return agent.create_season_trends(team_data, [team_name], 'win_percentage')

def create_conference_power_rankings(data: pd.DataFrame) -> str:
    """Create conference power rankings visualization"""
    agent = VisualizationAgent()
    return agent.create_conference_comparison(data, 'win_percentage')

if __name__ == "__main__":
    # Example usage
    agent = VisualizationAgent()

    # Create sample data for testing
    sample_data = pd.DataFrame({
        'team': ['Ohio State', 'Michigan', 'Penn State', 'Wisconsin', 'Iowa'],
        'win_percentage': [0.85, 0.78, 0.72, 0.68, 0.65],
        'conference': ['Big Ten', 'Big Ten', 'Big Ten', 'Big Ten', 'Big Ten']
    })

    # Test visualization creation
    print("Testing Visualization Agent...")

    chart_path = agent.create_team_rankings_chart(sample_data, title="Test Rankings")
    print(f"Chart created: {chart_path}")

    conf_chart = agent.create_conference_comparison(sample_data)
    print(f"Conference chart created: {conf_chart}")