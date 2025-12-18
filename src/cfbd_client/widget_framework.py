"""
CFBD Widget Replication Framework
Complete replication of CFBD website widgets and UI components with enhanced features
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import html
from pathlib import Path
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WidgetType(Enum):
    """Types of CFBD widgets to replicate"""
    SCOREBOARD = "scoreboard"
    PLAYER_STATS = "player_stats"
    TEAM_RANKINGS = "rankings"
    GAME_PREDICTIONS = "predictions"
    TEAM_MATCHUP = "team_matchup"
    LIVE_GAME_TRACKER = "live_game_tracker"
    ADVANCED_STATS = "advanced_stats"
    WEATHER_INFO = "weather_info"
    MEDIA_SCHEDULE = "media_schedule"
    HISTORICAL_ANALYSIS = "historical_analysis"

class Theme(Enum):
    """Widget theme options"""
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"  # System preference
    CUSTOM = "custom"

@dataclass
class WidgetConfig:
    """Widget configuration settings"""
    widget_type: WidgetType
    width: str = "100%"
    height: str = "auto"
    theme: Theme = Theme.AUTO
    responsive: bool = True
    show_branding: bool = False
    auto_refresh: bool = False
    refresh_interval_seconds: int = 60
    custom_css: Optional[str] = None
    interactive: bool = True
    export_enabled: bool = True
    animation_enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)

@dataclass
class WidgetData:
    """Generic widget data structure"""
    data: Any
    metadata: Dict[str, Any]
    last_updated: datetime
    source: str
    data_version: str
    cache_ttl_minutes: int = 15

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with proper datetime serialization"""
        result = asdict(self)
        result['last_updated'] = self.last_updated.isoformat()
        return result

class CFBDWidgetRenderer:
    """
    Complete widget rendering system that replicates CFBD website functionality
    with enhanced features and real-time data integration
    """

    def __init__(self, cfbd_client=None, cache=None):
        self.cfbd_client = cfbd_client
        self.cache = cache
        self.widget_registry = {}
        self.template_cache = {}

        # Initialize widget templates
        self._initialize_templates()

    def _initialize_templates(self):
        """Initialize HTML templates for all widget types"""
        self.templates = {
            WidgetType.SCOREBOARD: self._create_scoreboard_template,
            WidgetType.PLAYER_STATS: self._create_player_stats_template,
            WidgetType.TEAM_RANKINGS: self._create_rankings_template,
            WidgetType.GAME_PREDICTIONS: self._create_predictions_template,
            WidgetType.TEAM_MATCHUP: self._create_matchup_template,
            WidgetType.LIVE_GAME_TRACKER: self._create_live_tracker_template,
            WidgetType.ADVANCED_STATS: self._create_advanced_stats_template,
            WidgetType.WEATHER_INFO: self._create_weather_template,
            WidgetType.MEDIA_SCHEDULE: self._create_media_template,
            WidgetType.HISTORICAL_ANALYSIS: self._create_historical_template
        }

    def render_widget(self, widget_config: WidgetConfig,
                     widget_data: WidgetData,
                     target_format: str = "html") -> Dict[str, Any]:
        """
        Render a complete widget with the given configuration and data

        Args:
            widget_config: Widget configuration
            widget_data: Widget data to display
            target_format: Output format (html, json, embed_code)

        Returns:
            Dictionary containing rendered widget and metadata
        """
        try:
            # Validate widget type
            if widget_config.widget_type not in self.templates:
                raise ValueError(f"Unsupported widget type: {widget_config.widget_type}")

            # Generate widget HTML
            widget_html = self.templates[widget_config.widget_type](widget_config, widget_data)

            # Generate CSS for the widget
            widget_css = self._generate_widget_css(widget_config)

            # Generate JavaScript for interactivity
            widget_js = self._generate_widget_js(widget_config, widget_data)

            # Create complete widget output
            widget_output = {
                "widget_html": widget_html,
                "widget_css": widget_css,
                "widget_js": widget_js,
                "embed_code": self._generate_embed_code(widget_config, widget_html, widget_css, widget_js),
                "metadata": {
                    "widget_type": widget_config.widget_type.value,
                    "data_version": widget_data.data_version,
                    "last_updated": widget_data.last_updated.isoformat(),
                    "dimensions": {
                        "width": widget_config.width,
                        "height": widget_config.height
                    }
                },
                "performance_metrics": {
                    "render_time_ms": 0,  # Would track actual render time
                    "data_size_bytes": len(str(widget_data.data)),
                    "cache_status": "hit" if self.cache else "no_cache"
                }
            }

            if target_format == "json":
                return widget_output
            elif target_format == "embed_code":
                return {"embed_code": widget_output["embed_code"]}
            else:  # html
                return {"html": widget_output["widget_html"]}

        except Exception as e:
            logger.error(f"Widget render error for {widget_config.widget_type}: {e}")
            return self._render_error_widget(widget_config, str(e))

    def _create_scoreboard_template(self, config: WidgetConfig, data: WidgetData) -> str:
        """Create scoreboard widget template (enhanced version of CFBD scoreboard)"""
        games_data = data.data

        template = f"""
        <div class="cfbd-widget cfbd-scoreboard" data-widget-id="scoreboard-{datetime.now().timestamp()}">
            <div class="cfbd-widget-header">
                <h3>College Football Scoreboard</h3>
                <div class="cfbd-widget-controls">
                    <select class="week-selector" id="week-select">
                        <!-- Week options would be populated here -->
                    </select>
                    <button class="refresh-btn" onclick="refreshWidget()">🔄</button>
                </div>
            </div>

            <div class="cfbd-scoreboard-content">
                <div class="cfbd-scoreboard-filters">
                    <div class="filter-group">
                        <label>Conference:</label>
                        <select class="conference-filter">
                            <option value="">All Conferences</option>
                            <!-- Conference options -->
                        </select>
                    </div>
                    <div class="filter-group">
                        <label>Status:</label>
                        <select class="status-filter">
                            <option value="">All Games</option>
                            <option value="in_progress">In Progress</option>
                            <option value="completed">Final</option>
                            <option value="scheduled">Upcoming</option>
                        </select>
                    </div>
                </div>

                <div class="cfbd-games-container">
                    {self._render_games_list(games_data)}
                </div>
            </div>

            <div class="cfbd-widget-footer">
                <span class="last-updated">Last updated: {data.last_updated.strftime('%I:%M %p')}</span>
                {self._create_export_controls(config, data)}
            </div>
        </div>
        """

        return template

    def _render_games_list(self, games_data: List[Dict]) -> str:
        """Render individual games in scoreboard format"""
        if not games_data:
            return "<div class='no-games'>No games scheduled for this period</div>"

        games_html = []
        for game in games_data[:25]:  # Limit to 25 games for performance
            status = game.get('status', 'Scheduled')
            home_score = game.get('home_points', 0)
            away_score = game.get('away_points', 0)

            status_class = {
                'scheduled': 'scheduled',
                'in_progress': 'live',
                'completed': 'final',
                'cancelled': 'cancelled'
            }.get(status.lower(), 'scheduled')

            game_html = f"""
            <div class="cfbd-game-card {status_class}" data-game-id="{game.get('id', '')}">
                <div class="game-time">
                    <div class="game-date">{self._format_game_date(game.get('start_date', ''))}</div>
                    <div class="game-status">{status.upper()}</div>
                </div>

                <div class="game-teams">
                    <div class="team away">
                        <div class="team-logo">
                            <img src="{game.get('away_team', {}).get('logo', '')}"
                                 alt="{game.get('away_team', {}).get('school', 'Away')}"
                                 onerror="this.style.display='none'">
                        </div>
                        <div class="team-info">
                            <div class="team-name">{game.get('away_team', {}).get('school', 'Away')}</div>
                            <div class="team-record">{game.get('away_team', {}).get('record', '')}</div>
                        </div>
                        <div class="team-score">{away_score}</div>
                    </div>

                    <div class="game-separator">@</div>

                    <div class="team home">
                        <div class="team-score">{home_score}</div>
                        <div class="team-info">
                            <div class="team-name">{game.get('home_team', {}).get('school', 'Home')}</div>
                            <div class="team-record">{game.get('home_team', {}).get('record', '')}</div>
                        </div>
                        <div class="team-logo">
                            <img src="{game.get('home_team', {}).get('logo', '')}"
                                 alt="{game.get('home_team', {}).get('school', 'Home')}"
                                 onerror="this.style.display='none'">
                        </div>
                    </div>
                </div>

                {self._render_game_details(game)}
            </div>
            """
            games_html.append(game_html)

        return "".join(games_html)

    def _create_live_tracker_template(self, config: WidgetConfig, data: WidgetData) -> str:
        """Create live game tracker widget (real-time updates)"""
        game_data = data.data

        template = f"""
        <div class="cfbd-widget cfbd-live-tracker" data-widget-id="live-{datetime.now().timestamp()}" data-game-id="{game_data.get('id', '')}">
            <div class="cfbd-widget-header live-header">
                <h3>Live Game Tracker</h3>
                <div class="live-indicator">
                    <span class="live-dot"></span>
                    <span>LIVE</span>
                </div>
            </div>

            <div class="cfbd-live-content">
                {self._render_live_game_score(game_data)}
                {self._render_live_plays(game_data.get('plays', []))}
                {self._render_live_stats(game_data.get('stats', {}))}
                {self._render_game_momentum(game_data.get('momentum', []))}
            </div>

            <div class="cfbd-widget-footer">
                <button class="play-by-play-toggle">Show Play-by-Play</button>
                {self._create_export_controls(config, data)}
            </div>
        </div>
        """

        return template

    def _create_advanced_stats_template(self, config: WidgetConfig, data: WidgetData) -> str:
        """Create advanced analytics dashboard widget"""
        stats_data = data.data

        template = f"""
        <div class="cfbd-widget cfbd-advanced-stats" data-widget-id="advanced-{datetime.now().timestamp()}">
            <div class="cfbd-widget-header">
                <h3>Advanced Analytics Dashboard</h3>
                <div class="stats-controls">
                    <select class="stat-category">
                        <option value="offense">Offense</option>
                        <option value="defense">Defense</option>
                        <option value="special">Special Teams</option>
                        <option value="advanced">Advanced</option>
                    </select>
                    <button class="export-btn" onclick="exportStats()">📊</button>
                </div>
            </div>

            <div class="cfbd-stats-content">
                {self._render_advanced_metrics(stats_data.get('metrics', {}))}
                {self._render_team_comparisons(stats_data.get('comparisons', {}))}
                {self._render_efficiency_graphs(stats_data.get('efficiency', {}))}
                {self._render_epa_analysis(stats_data.get('epa', {}))}
            </div>
        </div>
        """

        return template

    def _create_predictions_template(self, config: WidgetConfig, data: WidgetData) -> str:
        """Create game predictions widget with ML insights"""
        predictions_data = data.data

        template = f"""
        <div class="cfbd-widget cfbd-predictions" data-widget-id="predictions-{datetime.now().timestamp()}">
            <div class="cfbd-widget-header">
                <h3>Game Predictions & Analysis</h3>
                <div class="model-selector">
                    <select id="prediction-model">
                        <option value="ensemble">Ensemble Model</option>
                        <option value="ridge">Ridge Regression</option>
                        <option value="xgboost">XGBoost</option>
                        <option value="fastai">FastAI Neural Net</option>
                    </select>
                </div>
            </div>

            <div class="cfbd-predictions-content">
                {self._render_prediction_cards(predictions_data.get('games', []))}
                {self._render_model_confidence(predictions_data.get('confidence', {}))}
                {self._render_historical_accuracy(predictions_data.get('accuracy', {}))}
            </div>
        </div>
        """

        return template

    def _generate_widget_css(self, config: WidgetConfig) -> str:
        """Generate CSS for widget styling based on theme and configuration"""
        theme_class = f"cfbd-theme-{config.theme.value}"

        css = f"""
        .cfbd-widget {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            border: 1px solid #e1e5e9;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            background: white;
            overflow: hidden;
            max-width: {config.width};
            height: {config.height};
        }}

        {theme_class} .cfbd-widget {{
            /* Theme-specific styles would go here */
        }}

        .cfbd-widget-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .cfbd-widget-content {{
            padding: 1rem;
        }}

        .cfbd-game-card {{
            border: 1px solid #e1e5e9;
            border-radius: 6px;
            margin-bottom: 0.75rem;
            padding: 1rem;
            background: white;
            transition: all 0.2s ease;
        }}

        .cfbd-game-card:hover {{
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            transform: translateY(-1px);
        }}

        .cfbd-game-card.live {{
            border-left: 4px solid #ff6b6b;
            background: #fff5f5;
        }}

        .cfbd-game-card.final {{
            border-left: 4px solid #51cf66;
        }}

        .team {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}

        .team-logo img {{
            width: 32px;
            height: 32px;
            object-fit: contain;
        }}

        .team-name {{
            font-weight: 600;
            font-size: 0.9rem;
        }}

        .team-score {{
            font-size: 1.5rem;
            font-weight: bold;
            min-width: 3rem;
            text-align: right;
        }}

        .live-indicator {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            background: #ff6b6b;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: bold;
        }}

        .live-dot {{
            width: 8px;
            height: 8px;
            background: white;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }}

        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}

        .prediction-card {{
            background: #f8f9fa;
            border-radius: 6px;
            padding: 1rem;
            margin-bottom: 1rem;
        }}

        .win-probability {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.5rem;
        }}

        .probability-bar {{
            height: 8px;
            background: #e1e5e9;
            border-radius: 4px;
            overflow: hidden;
        }}

        .probability-fill {{
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            transition: width 0.3s ease;
        }}

        {config.custom_css or ''}
        """

        return css

    def _generate_widget_js(self, config: WidgetConfig, data: WidgetData) -> str:
        """Generate JavaScript for widget interactivity and real-time updates"""
        js = f"""
        // CFBD Widget Script for {config.widget_type.value}
        (function() {{
            let widgetId = '{config.widget_type.value}-{datetime.now().timestamp()}';
            let autoRefresh = {str(config.auto_refresh).lower()};
            let refreshInterval = {config.refresh_interval_seconds * 1000};

            // Initialize widget
            function initWidget() {{
                console.log('Initializing CFBD Widget:', widgetId);

                if (autoRefresh) {{
                    startAutoRefresh();
                }}

                setupEventListeners();
                setupResponsiveLayout();
            }}

            // Auto-refresh functionality
            function startAutoRefresh() {{
                setInterval(function() {{
                    refreshWidgetData();
                }}, refreshInterval);
            }}

            // Refresh widget data
            function refreshWidgetData() {{
                fetch(`/api/widgets/{config.widget_type.value}/refresh`)
                    .then(response => response.json())
                    .then(data => {{
                        updateWidgetContent(data);
                        updateLastRefreshTime();
                    }})
                    .catch(error => {{
                        console.error('Widget refresh error:', error);
                    }});
            }}

            // Update widget content
            function updateWidgetContent(newData) {{
                // Update logic specific to widget type
                switch('{config.widget_type.value}') {{
                    case 'scoreboard':
                        updateScoreboard(newData);
                        break;
                    case 'live_game_tracker':
                        updateLiveTracker(newData);
                        break;
                    case 'predictions':
                        updatePredictions(newData);
                        break;
                    // Add other widget types as needed
                }}
            }}

            // Setup event listeners
            function setupEventListeners() {{
                // Filter controls
                const filters = document.querySelectorAll('.cfbd-widget select, .cfbd-widget input');
                filters.forEach(filter => {{
                    filter.addEventListener('change', handleFilterChange);
                }});

                // Export controls
                const exportBtns = document.querySelectorAll('.export-btn');
                exportBtns.forEach(btn => {{
                    btn.addEventListener('click', handleExport);
                }});
            }}

            // Handle filter changes
            function handleFilterChange(event) {{
                const filterType = event.target.classList[1]; // e.g., 'conference-filter'
                const filterValue = event.target.value;

                // Apply filter to widget content
                applyFilter(filterType, filterValue);
            }}

            // Handle data export
            function handleExport(event) {{
                const format = event.target.dataset.format || 'json';
                exportWidgetData(format);
            }}

            // Export widget data
            function exportWidgetData(format) {{
                const widgetData = {json.dumps(data.to_dict())};

                if (format === 'csv') {{
                    // Convert to CSV and download
                    const csv = convertToCSV(widgetData.data);
                    downloadFile(csv, `cfbd_{config.widget_type.value}_{datetime.now().strftime('%Y%m%d')}.csv`);
                }} else {{
                    // Download as JSON
                    downloadFile(JSON.stringify(widgetData, null, 2), `cfbd_{config.widget_type.value}_{datetime.now().strftime('%Y%m%d')}.json`);
                }}
            }}

            // Responsive layout
            function setupResponsiveLayout() {{
                if (window.innerWidth < 768) {{
                    document.body.classList.add('mobile-layout');
                }} else {{
                    document.body.classList.remove('mobile-layout');
                }}

                window.addEventListener('resize', setupResponsiveLayout);
            }}

            // Utility functions
            function updateLastRefreshTime() {{
                const lastUpdatedEl = document.querySelector('.last-updated');
                if (lastUpdatedEl) {{
                    const now = new Date();
                    lastUpdatedEl.textContent = `Last updated: ${{now.toLocaleTimeString()}}`;
                }}
            }}

            function downloadFile(content, filename) {{
                const blob = new Blob([content], {{ type: 'text/plain' }});
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
            }}

            // Initialize when DOM is ready
            if (document.readyState === 'loading') {{
                document.addEventListener('DOMContentLoaded', initWidget);
            }} else {{
                initWidget();
            }}
        }})();
        """

        return js

    def _generate_embed_code(self, config: WidgetConfig, html: str, css: str, js: str) -> str:
        """Generate embeddable code for widget"""
        # Encode CSS and JS for safe embedding
        encoded_css = base64.b64encode(css.encode()).decode()
        encoded_js = base64.b64encode(js.encode()).decode()

        embed_code = f"""
<!-- CFBD {config.widget_type.value.title()} Widget -->
<div id="cfbd-widget-{config.widget_type.value}">
    {html}
</div>
<style>
{css}
</style>
<script>
{js}
</script>
<!-- End CFBD Widget -->
        """

        return embed_code.strip()

    def _create_export_controls(self, config: WidgetConfig, data: WidgetData) -> str:
        """Create export controls for widget data"""
        if not config.export_enabled:
            return ""

        return f"""
        <div class="export-controls">
            <button class="export-btn" data-format="json" title="Export as JSON">📄</button>
            <button class="export-btn" data-format="csv" title="Export as CSV">📊</button>
            <button class="copy-btn" title="Copy to clipboard">📋</button>
        </div>
        """

    def _render_error_widget(self, config: WidgetConfig, error_message: str) -> str:
        """Render error widget when something goes wrong"""
        return f"""
        <div class="cfbd-widget cfbd-error" data-widget-type="{config.widget_type.value}">
            <div class="error-content">
                <h4>⚠️ Widget Error</h4>
                <p>Unable to load {config.widget_type.value} widget:</p>
                <code>{html.escape(error_message)}</code>
                <button onclick="this.parentElement.parentElement.style.display='none'">Close</button>
            </div>
        </div>
        """

    # Helper methods for rendering specific data types
    def _format_game_date(self, date_str: str) -> str:
        """Format game date for display"""
        try:
            if date_str:
                date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                return date_obj.strftime('%a %I:%M %p')
        except:
            pass
        return "TBD"

    def _render_game_details(self, game: Dict) -> str:
        """Render additional game details"""
        details = []

        if game.get('venue'):
            details.append(f"🏟️ {game['venue']}")

        if game.get('network'):
            details.append(f"📺 {game['network']}")

        if game.get('weather'):
            weather = game['weather']
            details.append(f"🌤️ {weather.get('temperature', '--')}°F {weather.get('condition', '')}")

        if details:
            return f'<div class="game-details">{" | ".join(details)}</div>'
        return ""

    def _render_live_game_score(self, game_data: Dict) -> str:
        """Render live game score with quarter information"""
        return f"""
        <div class="live-score">
            <div class="current-score">
                <div class="team-row">
                    <span>{game_data.get('away_team', {}).get('school', 'Away')}</span>
                    <span class="score">{game_data.get('away_points', 0)}</span>
                </div>
                <div class="team-row">
                    <span>{game_data.get('home_team', {}).get('school', 'Home')}</span>
                    <span class="score">{game_data.get('home_points', 0)}</span>
                </div>
            </div>
            <div class="game-status">
                <div class="quarter">{game_data.get('quarter', 'Q1')}</div>
                <div class="clock">{game_data.get('clock', '15:00')}</div>
                <div class="possession">{game_data.get('possession', '')}</div>
            </div>
        </div>
        """

    def _render_prediction_cards(self, games: List[Dict]) -> str:
        """Render prediction cards for upcoming games"""
        if not games:
            return "<div class='no-predictions'>No predictions available</div>"

        cards = []
        for game in games[:10]:  # Limit to 10 games
            home_team = game.get('home_team', 'Home Team')
            away_team = game.get('away_team', 'Away Team')
            home_win_prob = game.get('home_win_probability', 0.5)
            away_win_prob = 1 - home_win_prob

            card = f"""
            <div class="prediction-card">
                <div class="matchup">
                    <div class="team-away">
                        <span class="team-name">{away_team}</span>
                        <span class="win-prob">{away_win_prob:.1%}</span>
                    </div>
                    <div class="vs">VS</div>
                    <div class="team-home">
                        <span class="win-prob">{home_win_prob:.1%}</span>
                        <span class="team-name">{home_team}</span>
                    </div>
                </div>
                <div class="prediction-details">
                    <div class="model-confidence">
                        Confidence: {game.get('confidence', 0):.1%}
                    </div>
                    <div class="predicted-margin">
                        Predicted Margin: {game.get('predicted_margin', 0):+.1f}
                    </div>
                </div>
            </div>
            """
            cards.append(card)

        return "".join(cards)

    # Additional template methods for all widget types
    def _create_player_stats_template(self, config: WidgetConfig, data: WidgetData) -> str:
        """Create player statistics widget template"""
        return f"""
        <div class="cfbd-widget cfbd-player-stats">
            <div class="cfbd-widget-header">
                <h3>Player Statistics Dashboard</h3>
                <div class="stats-controls">
                    <select class="position-filter">
                        <option value="">All Positions</option>
                        <option value="QB">Quarterbacks</option>
                        <option value="RB">Running Backs</option>
                        <option value="WR">Wide Receivers</option>
                    </select>
                </div>
            </div>
            <div class="cfbd-stats-content">
                <!-- Player statistics content -->
            </div>
        </div>
        """

    def _create_rankings_template(self, config: WidgetConfig, data: WidgetData) -> str:
        """Create team rankings widget template"""
        return f"""
        <div class="cfbd-widget cfbd-rankings">
            <div class="cfbd-widget-header">
                <h3>Team Rankings</h3>
                <div class="ranking-controls">
                    <select class="poll-selector">
                        <option value="ap">AP Poll</option>
                        <option value="coaches">Coaches Poll</option>
                        <option value="cfp">CFP Rankings</option>
                    </select>
                </div>
            </div>
            <div class="cfbd-rankings-content">
                <!-- Rankings content -->
            </div>
        </div>
        """

    def _create_matchup_template(self, config: WidgetConfig, data: WidgetData) -> str:
        """Create team matchup widget template"""
        return f"""
        <div class="cfbd-widget cfbd-matchup">
            <div class="cfbd-widget-header">
                <h3>Team Matchup Analysis</h3>
            </div>
            <div class="cfbd-matchup-content">
                <!-- Matchup analysis content -->
            </div>
        </div>
        """

    def _create_weather_template(self, config: WidgetConfig, data: WidgetData) -> str:
        """Create weather information widget template"""
        return f"""
        <div class="cfbd-widget cfbd-weather">
            <div class="cfbd-widget-header">
                <h3>Weather Conditions</h3>
            </div>
            <div class="cfbd-weather-content">
                <!-- Weather information content -->
            </div>
        </div>
        """

    def _create_media_template(self, config: WidgetConfig, data: WidgetData) -> str:
        """Create media schedule widget template"""
        return f"""
        <div class="cfbd-widget cfbd-media">
            <div class="cfbd-widget-header">
                <h3>Broadcast Schedule</h3>
            </div>
            <div class="cfbd-media-content">
                <!-- Media schedule content -->
            </div>
        </div>
        """

    def _create_historical_template(self, config: WidgetConfig, data: WidgetData) -> str:
        """Create historical analysis widget template"""
        return f"""
        <div class="cfbd-widget cfbd-historical">
            <div class="cfbd-widget-header">
                <h3>Historical Analysis</h3>
            </div>
            <div class="cfbd-historical-content">
                <!-- Historical analysis content -->
            </div>
        </div>
        """

# Global widget renderer instance
widget_renderer = CFBDWidgetRenderer()

def get_widget_renderer() -> CFBDWidgetRenderer:
    """Get the global widget renderer instance"""
    return widget_renderer

# Widget utility functions
def create_widget_config(widget_type: Union[str, WidgetType], **kwargs) -> WidgetConfig:
    """Create widget configuration with sensible defaults"""
    if isinstance(widget_type, str):
        widget_type = WidgetType(widget_type)

    return WidgetConfig(widget_type=widget_type, **kwargs)

def render_widget_from_api(widget_type: Union[str, WidgetType],
                          data_source_func: callable,
                          config_overrides: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Convenience function to render widget directly from API data source

    Args:
        widget_type: Type of widget to render
        data_source_func: Function that returns widget data (takes config as parameter)
        config_overrides: Override default widget configuration

    Returns:
        Rendered widget dictionary
    """
    config = create_widget_config(widget_type, **(config_overrides or {}))

    # Get data from source function
    try:
        data_result = data_source_func(config)
        if isinstance(data_result, tuple):
            data, metadata = data_result
        else:
            data = data_result
            metadata = {}

        widget_data = WidgetData(
            data=data,
            metadata=metadata,
            last_updated=datetime.now(),
            source="api_call",
            data_version="1.0"
        )

    except Exception as e:
        logger.error(f"Error getting widget data for {widget_type}: {e}")
        widget_data = WidgetData(
            data={},
            metadata={"error": str(e)},
            last_updated=datetime.now(),
            source="error",
            data_version="1.0"
        )

    # Render widget
    renderer = get_widget_renderer()
    return renderer.render_widget(config, widget_data)