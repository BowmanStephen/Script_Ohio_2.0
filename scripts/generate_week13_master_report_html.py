#!/usr/bin/env python3
"""
Week 13 Master Report HTML Generator
Generates comprehensive interactive HTML report with all sections.
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

class Week13MasterReportGenerator:
    """Generate comprehensive Week 13 master report HTML."""
    
    def __init__(self, week13_dir: Path):
        self.week13_dir = week13_dir
        self.unified_data = None
        self.games_df = None
        
    def load_unified_data(self):
        """Load unified data JSON."""
        file_path = self.week13_dir / "week13_unified_data.json"
        with open(file_path, 'r') as f:
            self.unified_data = json.load(f)
        
        # Convert games to DataFrame for easier manipulation
        games = self.unified_data['games']
        self.games_df = pd.DataFrame([
            {
                'game_id': g['game_id'],
                'home_team': g['game_info']['home_team'],
                'away_team': g['game_info']['away_team'],
                'home_conference': g['game_info'].get('home_conference', ''),
                'away_conference': g['game_info'].get('away_conference', ''),
                'confidence': g.get('ensemble', {}).get('confidence', 0),
                'winner': g.get('ensemble', {}).get('winner', ''),
                'margin': g.get('ensemble', {}).get('margin', 0),
                'spread': g['game_info'].get('spread', 0),
                'upset_prob': g.get('strategic', {}).get('upset_probability', 0) if g.get('strategic') else 0,
                'betting_rec': ', '.join(g.get('strategic', {}).get('betting_recommendations', [])) if g.get('strategic') else '',
                'playoff_impact': self._get_playoff_impact(g['game_id']),
                'narrative': g.get('narrative', '')
            }
            for g in games
        ])
    
    def _get_playoff_impact(self, game_id: int) -> str:
        """Get playoff impact level for a game."""
        playoff = self.unified_data.get('playoff_implications', {})
        
        # Check elimination games
        for game in playoff.get('elimination_games', []):
            if 'game' in game:
                # Try to match game_id from game string
                if str(game_id) in str(game.get('game', '')):
                    return 'ELIMINATION'
        
        # Check path to playoff
        for game in playoff.get('path_to_playoff', []):
            if 'game' in game:
                if str(game_id) in str(game.get('game', '')):
                    return 'PATH'
        
        return 'NONE'
    
    def generate_html(self) -> str:
        """Generate complete HTML report."""
        metadata = self.unified_data['metadata']
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Week 13 Master Report - Script Ohio 2.0</title>
    
    <!-- Bootstrap 5.1.3 -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    
    <!-- Plotly.js -->
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    
    <!-- DataTables.js -->
    <link rel="stylesheet" href="https://cdn.datatables.net/1.13.0/css/dataTables.bootstrap5.min.css">
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.0/js/jquery.dataTables.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.0/js/dataTables.bootstrap5.min.js"></script>
    
    <style>
        :root {{
            --primary-color: #1e3a8a;
            --secondary-color: #3b82f6;
            --success-color: #10b981;
            --warning-color: #f59e0b;
            --danger-color: #ef4444;
            --bg-color: #ffffff;
            --text-color: #1f2937;
            --card-bg: #ffffff;
            --border-color: #e5e7eb;
        }}
        
        [data-theme="dark"] {{
            --bg-color: #111827;
            --text-color: #f9fafb;
            --card-bg: #1f2937;
            --border-color: #374151;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            line-height: 1.6;
            transition: background-color 0.3s, color 0.3s;
        }}
        
        .navbar {{
            background-color: var(--primary-color) !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            position: sticky;
            top: 0;
            z-index: 1000;
        }}
        
        .navbar-brand {{
            font-weight: bold;
            font-size: 1.5rem;
        }}
        
        .section {{
            padding: 3rem 0;
            scroll-margin-top: 80px;
        }}
        
        .section-title {{
            font-size: 2.5rem;
            font-weight: bold;
            margin-bottom: 2rem;
            color: var(--primary-color);
            border-bottom: 3px solid var(--secondary-color);
            padding-bottom: 1rem;
        }}
        
        .metric-card {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 1.5rem;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transition: transform 0.2s;
            height: 100%;
        }}
        
        .metric-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}
        
        .metric-value {{
            font-size: 2.5rem;
            font-weight: bold;
            color: var(--primary-color);
            margin: 0.5rem 0;
        }}
        
        .metric-label {{
            font-size: 1rem;
            color: #6b7280;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .chart-container {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 1.5rem;
            margin-bottom: 2rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        .game-card {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            transition: all 0.2s;
            cursor: pointer;
        }}
        
        .game-card:hover {{
            border-color: var(--secondary-color);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}
        
        .confidence-badge {{
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.875rem;
            font-weight: bold;
        }}
        
        .confidence-high {{ background-color: #d1fae5; color: #065f46; }}
        .confidence-medium {{ background-color: #fef3c7; color: #92400e; }}
        .confidence-low {{ background-color: #fee2e2; color: #991b1b; }}
        
        .filter-panel {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 1.5rem;
            margin-bottom: 2rem;
        }}
        
        .dark-mode-toggle {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 1000;
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: var(--primary-color);
            color: white;
            border: none;
            font-size: 1.5rem;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            transition: transform 0.2s;
        }}
        
        .dark-mode-toggle:hover {{
            transform: scale(1.1);
        }}
        
        @media print {{
            .navbar, .dark-mode-toggle, .filter-panel {{
                display: none;
            }}
            .section {{
                page-break-inside: avoid;
            }}
        }}
        
        @media (max-width: 768px) {{
            .section-title {{
                font-size: 1.75rem;
            }}
            .metric-value {{
                font-size: 2rem;
            }}
        }}
    </style>
</head>
<body>
    <!-- Navigation -->
    <nav class="navbar navbar-dark navbar-expand-lg">
        <div class="container">
            <a class="navbar-brand" href="#">Week 13 Master Report</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item"><a class="nav-link" href="#executive-summary">Summary</a></li>
                    <li class="nav-item"><a class="nav-link" href="#top-matchups">Top Matchups</a></li>
                    <li class="nav-item"><a class="nav-link" href="#game-explorer">Games</a></li>
                    <li class="nav-item"><a class="nav-link" href="#visualizations">Charts</a></li>
                    <li class="nav-item"><a class="nav-link" href="#playoff-picture">Playoff</a></li>
                    <li class="nav-item"><a class="nav-link" href="#betting-hub">Betting</a></li>
                    <li class="nav-item"><a class="nav-link" href="#rankings">Rankings</a></li>
                </ul>
            </div>
        </div>
    </nav>
    
    <!-- Dark Mode Toggle -->
    <button class="dark-mode-toggle" onclick="toggleDarkMode()" aria-label="Toggle dark mode">
        🌙
    </button>
    
    <main>
        {self._generate_executive_summary(metadata)}
        {self._generate_top_matchups()}
        {self._generate_game_explorer()}
        {self._generate_visualizations()}
        {self._generate_playoff_picture()}
        {self._generate_betting_hub()}
        {self._generate_power_rankings()}
        {self._generate_appendices()}
    </main>
    
    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    
    <script>
        // Dark Mode Toggle
        function toggleDarkMode() {{
            const body = document.body;
            const currentTheme = body.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            body.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            document.querySelector('.dark-mode-toggle').textContent = newTheme === 'dark' ? '☀️' : '🌙';
        }}
        
        // Load saved theme
        const savedTheme = localStorage.getItem('theme') || 'light';
        document.body.setAttribute('data-theme', savedTheme);
        document.querySelector('.dark-mode-toggle').textContent = savedTheme === 'dark' ? '☀️' : '🌙';
        
        // Smooth scroll
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {{
            anchor.addEventListener('click', function (e) {{
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {{
                    target.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                }}
            }});
        }});
        
        // Initialize DataTables
        $(document).ready(function() {{
            $('#gamesTable').DataTable({{
                pageLength: 25,
                order: [[2, 'desc']], // Sort by confidence descending
                responsive: true
            }});
            
            $('#rankingsTable').DataTable({{
                pageLength: 25,
                order: [[0, 'asc']], // Sort by rank
                responsive: true
            }});
        }});
        
        // Game detail modal - load data from embedded JSON
        const unifiedData = {json.dumps(self.unified_data, default=str)};
        const gameDataMap = {{}};
        unifiedData.games.forEach(game => {{
            gameDataMap[game.game_id] = game;
        }});
        
        function showGameDetail(gameId) {{
            const game = gameDataMap[gameId];
            if (!game) {{
                console.error('Game not found:', gameId);
                return;
            }}
            
            const modal = document.getElementById('gameDetailModal');
            const modalBody = modal.querySelector('.modal-body');
            
            const gameInfo = game.game_info || {{}};
            const ensemble = game.ensemble || {{}};
            const strategic = game.strategic || {{}};
            const predictions = game.predictions || {{}};
            
            let bettingHtml = '';
            if (strategic.winner_recommendation) {{
                bettingHtml = `
                <hr>
                <h5>Betting Analysis</h5>
                <p><strong>Recommendation:</strong> ${{strategic.winner_recommendation || 'N/A'}}</p>
                <p><strong>Betting Recs:</strong> ${{(strategic.betting_recommendations || []).join(', ') || 'N/A'}}</p>
                <p><strong>Upset Probability:</strong> ${{strategic.upset_probability ? (strategic.upset_probability * 100).toFixed(1) + '%' : 'N/A'}}</p>
                `;
            }}
            
            modalBody.innerHTML = `
                <h4>${{gameInfo.away_team || 'Away'}} @ ${{gameInfo.home_team || 'Home'}}</h4>
                <hr>
                <div class="row">
                    <div class="col-md-6">
                        <h5>Prediction</h5>
                        <p><strong>Winner:</strong> ${{ensemble.winner || 'N/A'}}</p>
                        <p><strong>Confidence:</strong> ${{ensemble.confidence ? (ensemble.confidence * 100).toFixed(1) + '%' : 'N/A'}}</p>
                        <p><strong>Margin:</strong> ${{ensemble.margin !== undefined ? ensemble.margin.toFixed(1) : 'N/A'}}</p>
                        <p><strong>Spread:</strong> ${{gameInfo.spread !== undefined ? gameInfo.spread : 'N/A'}}</p>
                    </div>
                    <div class="col-md-6">
                        <h5>Model Predictions</h5>
                        <p><strong>Ridge Margin:</strong> ${{predictions.ridge_margin !== undefined ? predictions.ridge_margin.toFixed(2) : 'N/A'}}</p>
                        <p><strong>XGB Win Prob:</strong> ${{predictions.xgb_win_prob !== undefined ? (predictions.xgb_win_prob * 100).toFixed(1) + '%' : 'N/A'}}</p>
                        <p><strong>RF Margin:</strong> ${{predictions.rf_margin !== undefined ? predictions.rf_margin.toFixed(2) : 'N/A'}}</p>
                    </div>
                </div>
                ${{bettingHtml}}
                <hr>
                <h5>Narrative</h5>
                <div>${{game.narrative || 'No narrative available.'}}</div>
            `;
            
            const bsModal = new bootstrap.Modal(modal);
            bsModal.show();
        }}
        
        // Filter functionality
        $('#confidenceSlider').on('input', function() {{
            const value = $(this).val();
            $('#confidenceValue').text(value);
            const table = $('#gamesTable').DataTable();
            $.fn.dataTable.ext.search.push(function(settings, data, dataIndex) {{
                const confidence = parseFloat(data[2].replace('%', '')) / 100;
                return confidence >= parseFloat(value);
            }});
            table.draw();
        }});
        
        // Conference filter
        const conferences = [...new Set({json.dumps([g['game_info'].get('home_conference', '') for g in self.unified_data['games'] if g['game_info'].get('home_conference')])})];
        conferences.forEach(conf => {{
            $('#conferenceFilter').append(`<option value="${{conf}}">${{conf}}</option>`);
        }});
        
        $('#conferenceFilter').on('change', function() {{
            const selected = $(this).val();
            const table = $('#gamesTable').DataTable();
            if (selected) {{
                table.column(0).search(selected).draw();
            }} else {{
                table.column(0).search('').draw();
            }}
        }});
        
        // Export functionality
        function exportData(format) {{
            const table = $('#gamesTable').DataTable();
            if (format === 'csv') {{
                const data = table.data().toArray();
                const csv = convertToCSV(data);
                downloadFile(csv, 'week13_games.csv', 'text/csv');
            }} else if (format === 'json') {{
                const data = table.data().toArray();
                downloadFile(JSON.stringify(data), 'week13_games.json', 'application/json');
            }}
        }}
        
        function convertToCSV(data) {{
            const headers = ['Game', 'Winner', 'Confidence', 'Spread', 'Betting Rec', 'Upset Prob'];
            const rows = data.map(row => row.join(','));
            return [headers.join(','), ...rows].join('\\n');
        }}
        
        function downloadFile(content, filename, mimeType) {{
            const blob = new Blob([content], {{ type: mimeType }});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            a.click();
            URL.revokeObjectURL(url);
        }}
    </script>
    
    {self._generate_chart_scripts()}
    
    <!-- Game Detail Modal -->
    <div class="modal fade" id="gameDetailModal" tabindex="-1">
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Game Details</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <!-- Content populated by JavaScript -->
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                </div>
            </div>
        </div>
    </div>
</body>
</html>"""
        return html
    
    def _generate_executive_summary(self, metadata: Dict) -> str:
        """Generate executive summary section."""
        total_games = metadata['total_games']
        avg_conf = metadata['avg_confidence']
        high_conf = metadata['high_confidence_games']
        playoff_impact = metadata['playoff_impact_games']
        upset_count = metadata['upset_alert_count']
        
        # Get top 5 games by confidence
        top_games = self.games_df.nlargest(5, 'confidence')
        
        top_games_html = ''
        for _, game in top_games.iterrows():
            conf_class = 'confidence-high' if game['confidence'] > 0.7 else 'confidence-medium' if game['confidence'] > 0.5 else 'confidence-low'
            top_games_html += f"""
            <div class="game-card" onclick="showGameDetail({game['game_id']})">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <h5>{game['away_team']} @ {game['home_team']}</h5>
                        <p class="mb-0">Predicted Winner: <strong>{game['winner']}</strong></p>
                    </div>
                    <span class="confidence-badge {conf_class}">
                        {(game['confidence'] * 100):.1f}%
                    </span>
                </div>
            </div>"""
        
        return f"""
        <section id="executive-summary" class="section">
            <div class="container">
                <h1 class="section-title">Executive Summary Dashboard</h1>
                
                <!-- Metrics Cards -->
                <div class="row g-4 mb-5">
                    <div class="col-md-4 col-lg-2">
                        <div class="metric-card">
                            <div class="metric-value">{total_games}</div>
                            <div class="metric-label">Total Games</div>
                        </div>
                    </div>
                    <div class="col-md-4 col-lg-2">
                        <div class="metric-card">
                            <div class="metric-value">{(avg_conf * 100):.1f}%</div>
                            <div class="metric-label">Avg Confidence</div>
                        </div>
                    </div>
                    <div class="col-md-4 col-lg-2">
                        <div class="metric-card">
                            <div class="metric-value">{high_conf}</div>
                            <div class="metric-label">High Confidence</div>
                        </div>
                    </div>
                    <div class="col-md-4 col-lg-2">
                        <div class="metric-card">
                            <div class="metric-value">{playoff_impact}</div>
                            <div class="metric-label">Playoff Impact</div>
                        </div>
                    </div>
                    <div class="col-md-4 col-lg-2">
                        <div class="metric-card">
                            <div class="metric-value">{upset_count}</div>
                            <div class="metric-label">Upset Alerts</div>
                        </div>
                    </div>
                </div>
                
                <!-- Quick Picks -->
                <div class="row">
                    <div class="col-12">
                        <h3 class="mb-4">Top 5 Quick Picks</h3>
                        {top_games_html}
                    </div>
                </div>
            </div>
        </section>"""
    
    def _generate_top_matchups(self) -> str:
        """Generate top matchups section."""
        top_matchups = self.unified_data.get('top_matchups', [])[:10]
        
        matchups_html = ''
        for matchup in top_matchups:
            game_id = matchup.get('game_id', '')
            home = matchup.get('home_team', '')
            away = matchup.get('away_team', '')
            winner = matchup.get('predicted_winner', '')
            conf = matchup.get('confidence_score', 0)
            category = matchup.get('category', '')
            
            matchups_html += f"""
            <div class="game-card">
                <div class="row">
                    <div class="col-md-8">
                        <h5>{away} @ {home}</h5>
                        <p class="mb-1"><strong>Predicted Winner:</strong> {winner}</p>
                        <p class="mb-1"><strong>Category:</strong> {category}</p>
                        <p class="mb-0"><strong>Confidence:</strong> {(conf * 100):.1f}%</p>
                    </div>
                    <div class="col-md-4 text-end">
                        <span class="confidence-badge confidence-high">{(conf * 100):.1f}%</span>
                    </div>
                </div>
            </div>"""
        
        return f"""
        <section id="top-matchups" class="section">
            <div class="container">
                <h2 class="section-title">Top Matchups Explorer</h2>
                {matchups_html}
            </div>
        </section>"""
    
    def _generate_game_explorer(self) -> str:
        """Generate interactive game explorer section."""
        # Build table data
        table_rows = ''
        for _, game in self.games_df.iterrows():
            conf_class = 'confidence-high' if game['confidence'] > 0.7 else 'confidence-medium' if game['confidence'] > 0.5 else 'confidence-low'
            table_rows += f"""
            <tr onclick="showGameDetail({game['game_id']})" style="cursor: pointer;">
                <td>{game['away_team']} @ {game['home_team']}</td>
                <td>{game['winner']}</td>
                <td><span class="confidence-badge {conf_class}">{(game['confidence'] * 100):.1f}%</span></td>
                <td>{game['spread']:.1f}</td>
                <td>{game['betting_rec'] or 'N/A'}</td>
                <td>{(game['upset_prob'] * 100):.1f}%</td>
                <td>{game['playoff_impact']}</td>
            </tr>"""
        
        return f"""
        <section id="game-explorer" class="section">
            <div class="container">
                <h2 class="section-title">Interactive Game Explorer</h2>
                
                <div class="filter-panel">
                    <div class="row g-3">
                        <div class="col-md-3">
                            <label class="form-label">Conference</label>
                            <select class="form-select" id="conferenceFilter">
                                <option value="">All Conferences</option>
                            </select>
                        </div>
                        <div class="col-md-3">
                            <label class="form-label">Confidence Range</label>
                            <input type="range" class="form-range" id="confidenceSlider" min="0.5" max="1.0" step="0.05" value="0.5">
                            <small id="confidenceValue">0.5</small>
                        </div>
                        <div class="col-md-3">
                            <label class="form-label">Playoff Impact</label>
                            <div>
                                <input type="checkbox" id="playoffElimination" class="form-check-input">
                                <label class="form-check-label" for="playoffElimination">Elimination</label>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <button class="btn btn-primary" onclick="exportData('csv')">Export CSV</button>
                            <button class="btn btn-secondary" onclick="exportData('json')">Export JSON</button>
                        </div>
                    </div>
                </div>
                
                <div class="table-responsive">
                    <table id="gamesTable" class="table table-striped table-hover">
                        <thead>
                            <tr>
                                <th>Game</th>
                                <th>Winner</th>
                                <th>Confidence</th>
                                <th>Spread</th>
                                <th>Betting Rec</th>
                                <th>Upset Prob</th>
                                <th>Playoff Impact</th>
                            </tr>
                        </thead>
                        <tbody>
                            {table_rows}
                        </tbody>
                    </table>
                </div>
            </div>
        </section>"""
    
    def _generate_visualizations(self) -> str:
        """Generate visualizations section with all 8 charts."""
        return """
        <section id="visualizations" class="section">
            <div class="container">
                <h2 class="section-title">Visualizations Dashboard</h2>
                
                <div class="row">
                    <div class="col-md-6">
                        <div class="chart-container">
                            <div id="confidenceHistogram"></div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="chart-container">
                            <div id="spreadConfidenceScatter"></div>
                        </div>
                    </div>
                </div>
                
                <div class="row">
                    <div class="col-md-6">
                        <div class="chart-container">
                            <div id="upsetBubble"></div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="chart-container">
                            <div id="conferenceRadar"></div>
                        </div>
                    </div>
                </div>
                
                <div class="row">
                    <div class="col-md-6">
                        <div class="chart-container">
                            <div id="topMatchupsBar"></div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="chart-container">
                            <div id="playoffHeatmap"></div>
                        </div>
                    </div>
                </div>
                
                <div class="row">
                    <div class="col-md-6">
                        <div class="chart-container">
                            <div id="gameScriptTimeline"></div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="chart-container">
                            <div id="talentPerformanceGap"></div>
                        </div>
                    </div>
                </div>
            </div>
        </section>"""
    
    def _generate_playoff_picture(self) -> str:
        """Generate playoff picture section."""
        playoff = self.unified_data.get('playoff_implications', {})
        elimination_games = playoff.get('elimination_games', [])
        path_games = playoff.get('path_to_playoff', [])
        bubble_teams = playoff.get('bubble_teams', [])
        lock_scenarios = playoff.get('lock_scenarios', [])
        
        elimination_html = ''
        for game in elimination_games:
            elimination_html += f"""
            <div class="game-card" style="border-left: 4px solid #ef4444;">
                <h5>{game.get('game', 'N/A')}</h5>
                <p><strong>Impact:</strong> <span class="badge bg-danger">{game.get('playoff_impact', 'N/A')}</span></p>
                <p><strong>Predicted Winner:</strong> {game.get('predicted_winner', 'N/A')}</p>
                <p><strong>Predicted Loser:</strong> {game.get('predicted_loser', 'N/A')}</p>
                <p><strong>Contenders Involved:</strong> {', '.join(game.get('contenders_involved', []))}</p>
                <p><strong>Win Probability:</strong> {(game.get('win_probability', 0) * 100):.1f}%</p>
            </div>"""
        
        path_html = ''
        for game in path_games:
            path_html += f"""
            <div class="game-card" style="border-left: 4px solid #10b981;">
                <h5>{game.get('game', 'N/A')}</h5>
                <p><strong>Impact:</strong> <span class="badge bg-success">{game.get('playoff_impact', 'N/A')}</span></p>
                <p><strong>Predicted Winner:</strong> {game.get('predicted_winner', 'N/A')}</p>
                <p><strong>Contenders:</strong> {', '.join(game.get('contenders_involved', []))}</p>
                <p><strong>Win Probability:</strong> {(game.get('win_probability', 0) * 100):.1f}%</p>
            </div>"""
        
        bubble_html = f"<p>{len(bubble_teams)} bubble teams identified.</p>" if bubble_teams else "<p>No bubble teams identified.</p>"
        lock_html = f"<p>{len(lock_scenarios)} lock scenarios identified.</p>" if lock_scenarios else "<p>No lock scenarios identified.</p>"
        
        return f"""
        <section id="playoff-picture" class="section">
            <div class="container">
                <h2 class="section-title">Playoff Picture Analysis</h2>
                
                <div class="row mb-4">
                    <div class="col-md-6">
                        <h3>Elimination Scenarios</h3>
                        <p class="text-muted">Games that could eliminate contenders from playoff contention</p>
                        {elimination_html if elimination_html else '<p>No elimination games identified.</p>'}
                    </div>
                    <div class="col-md-6">
                        <h3>Path to Playoff</h3>
                        <p class="text-muted">Critical games for playoff contenders</p>
                        {path_html if path_html else '<p>No path to playoff games identified.</p>'}
                    </div>
                </div>
                
                <div class="row">
                    <div class="col-md-6">
                        <h4>Bubble Teams</h4>
                        {bubble_html}
                    </div>
                    <div class="col-md-6">
                        <h4>Lock Scenarios</h4>
                        {lock_html}
                    </div>
                </div>
                
                <div class="row mt-4">
                    <div class="col-12">
                        <div class="chart-container">
                            <div id="playoffBracket"></div>
                        </div>
                    </div>
                </div>
            </div>
        </section>"""
    
    def _generate_betting_hub(self) -> str:
        """Generate betting intelligence hub section."""
        # Get top value picks from strategic recommendations
        strategic_games = [g for g in self.unified_data['games'] if g.get('strategic')]
        strategic_games.sort(key=lambda x: x.get('strategic', {}).get('confidence_level', 0), reverse=True)
        top_picks = strategic_games[:5]
        
        picks_html = ''
        for idx, game in enumerate(top_picks, 1):
            strategic = game.get('strategic', {})
            score_pred = strategic.get('score_prediction', {})
            spread_analysis = strategic.get('spread_analysis', {})
            over_under = strategic.get('over_under_analysis', {})
            
            picks_html += f"""
            <div class="game-card">
                <div class="d-flex justify-content-between align-items-start mb-2">
                    <h5>#{idx} {game['game_info']['away_team']} @ {game['game_info']['home_team']}</h5>
                    <span class="badge bg-success">Value Pick</span>
                </div>
                <p><strong>Winner Recommendation:</strong> {strategic.get('winner_recommendation', 'N/A')}</p>
                <p><strong>Confidence Level:</strong> {(strategic.get('confidence_level', 0) * 100):.1f}%</p>
                <p><strong>Score Prediction:</strong> {score_pred.get('home_score', 'N/A')} - {score_pred.get('away_score', 'N/A')}</p>
                <p><strong>Spread Analysis:</strong> {spread_analysis.get('recommendation', 'N/A')}</p>
                <p><strong>Over/Under:</strong> {over_under.get('recommendation', 'N/A')}</p>
                <p><strong>Betting Recommendations:</strong> {', '.join(strategic.get('betting_recommendations', []))}</p>
            </div>"""
        
        # Upset alerts
        upset_games = [g for g in self.unified_data['games'] if g.get('strategic', {}).get('upset_probability', 0) > 0.3]
        upset_games.sort(key=lambda x: x.get('strategic', {}).get('upset_probability', 0), reverse=True)
        upset_html = ''
        for game in upset_games[:5]:
            strategic = game.get('strategic', {})
            upset_prob = strategic.get('upset_probability', 0)
            upset_html += f"""
            <div class="game-card" style="border-left: 4px solid #ef4444;">
                <h5>{game['game_info']['away_team']} @ {game['game_info']['home_team']}</h5>
                <p><strong>Upset Probability:</strong> <span class="text-danger">{(upset_prob * 100):.1f}%</span></p>
                <p><strong>Predicted Winner:</strong> {game.get('ensemble', {}).get('winner', 'N/A')}</p>
                <p><strong>Key Factors:</strong> {', '.join(strategic.get('key_factors', []))}</p>
            </div>"""
        
        # Over/Under value plays
        over_under_games = [g for g in strategic_games if g.get('strategic', {}).get('over_under_analysis', {}).get('recommendation')]
        over_under_html = ''
        for game in over_under_games[:5]:
            strategic = game.get('strategic', {})
            over_under = strategic.get('over_under_analysis', {})
            over_under_html += f"""
            <div class="game-card">
                <h5>{game['game_info']['away_team']} @ {game['game_info']['home_team']}</h5>
                <p><strong>Recommendation:</strong> <strong>{over_under.get('recommendation', 'N/A')}</strong></p>
                <p><strong>Predicted Total:</strong> {over_under.get('predicted_total', 'N/A'):.1f}</p>
            </div>"""
        
        return f"""
        <section id="betting-hub" class="section">
            <div class="container">
                <h2 class="section-title">Betting Intelligence Hub</h2>
                
                <div class="row mb-4">
                    <div class="col-md-6">
                        <h3>Top 5 Value Picks</h3>
                        {picks_html}
                    </div>
                    <div class="col-md-6">
                        <h3>Upset Alerts</h3>
                        {upset_html if upset_html else '<p>No high-probability upset alerts.</p>'}
                    </div>
                </div>
                
                <div class="row">
                    <div class="col-12">
                        <h3>Over/Under Value Plays</h3>
                        {over_under_html if over_under_html else '<p>No over/under recommendations available.</p>'}
                    </div>
                </div>
                
                <div class="row mt-4">
                    <div class="col-12">
                        <div class="chart-container">
                            <div id="confidenceLineAnalysis"></div>
                        </div>
                    </div>
                </div>
            </div>
        </section>"""
    
    def _generate_power_rankings(self) -> str:
        """Generate power rankings section."""
        rankings = self.unified_data.get('power_rankings', [])
        
        table_rows = ''
        for rank in rankings:
            table_rows += f"""
            <tr>
                <td>{rank.get('rank', 'N/A')}</td>
                <td>{rank.get('team', 'N/A')}</td>
                <td>{rank.get('rating', 0):.2f}</td>
                <td>{rank.get('record', 'N/A')}</td>
                <td>{rank.get('strength_of_schedule', 0):.3f}</td>
            </tr>"""
        
        return f"""
        <section id="rankings" class="section">
            <div class="container">
                <h2 class="section-title">Power Rankings Showcase</h2>
                
                <div class="table-responsive">
                    <table id="rankingsTable" class="table table-striped table-hover">
                        <thead>
                            <tr>
                                <th>Rank</th>
                                <th>Team</th>
                                <th>Rating</th>
                                <th>Record</th>
                                <th>Strength of Schedule</th>
                            </tr>
                        </thead>
                        <tbody>
                            {table_rows}
                        </tbody>
                    </table>
                </div>
            </div>
        </section>"""
    
    def _generate_appendices(self) -> str:
        """Generate appendices section."""
        metadata = self.unified_data['metadata']
        return f"""
        <section id="appendices" class="section">
            <div class="container">
                <h2 class="section-title">Appendices</h2>
                
                <div class="row">
                    <div class="col-md-6">
                        <h3>Data Sources</h3>
                        <ul>
                            <li>week13_comprehensive_analysis_20251119_221939.json</li>
                            <li>enhanced_week13_analysis_20251118_200409.json</li>
                            <li>week13_detailed_predictions_20251119_221939.csv</li>
                            <li>week13_strategic_recommendations.csv</li>
                            <li>week13_upset_alerts.csv</li>
                            <li>week13_power_rankings.csv</li>
                        </ul>
                    </div>
                    <div class="col-md-6">
                        <h3>Metadata</h3>
                        <p><strong>Generation Time:</strong> {metadata.get('generation_timestamp', 'N/A')}</p>
                        <p><strong>Total Games:</strong> {metadata.get('total_games', 0)}</p>
                        <p><strong>Average Confidence:</strong> {(metadata.get('avg_confidence', 0) * 100):.1f}%</p>
                    </div>
                </div>
            </div>
        </section>"""
    
    def _generate_chart_scripts(self) -> str:
        """Generate all 8 Plotly chart scripts."""
        # V001: Confidence Distribution (histogram)
        confidences = self.games_df['confidence'].dropna()
        hist_data = {
            'x': confidences.tolist(),
            'type': 'histogram',
            'nbinsx': 20,
            'marker': {'color': '#3b82f6'},
            'name': 'Confidence'
        }
        hist_layout = {
            'title': 'V001: Confidence Distribution',
            'xaxis': {'title': 'Confidence Score (0.5-1.0)', 'range': [0.5, 1.0]},
            'yaxis': {'title': 'Count'},
            'height': 400
        }
        
        # V002: Spread vs Confidence (scatter with color/size encoding)
        scatter_data = {
            'x': self.games_df['margin'].tolist(),
            'y': self.games_df['confidence'].tolist(),
            'mode': 'markers',
            'type': 'scatter',
            'marker': {
                'size': [abs(m) * 2 + 5 for m in self.games_df['margin'].tolist()],
                'color': self.games_df['upset_prob'].tolist(),
                'colorscale': 'Reds',
                'showscale': True,
                'colorbar': {'title': 'Upset Prob'}
            },
            'text': [f"{row['away_team']} @ {row['home_team']}" for _, row in self.games_df.iterrows()],
            'name': 'Games'
        }
        scatter_layout = {
            'title': 'V002: Spread vs Confidence',
            'xaxis': {'title': 'Predicted Margin'},
            'yaxis': {'title': 'Confidence'},
            'height': 400
        }
        
        # V003: Upset Probability vs Betting Rec (bubble chart)
        bubble_data = {
            'x': self.games_df['upset_prob'].tolist(),
            'y': self.games_df['confidence'].tolist(),
            'mode': 'markers',
            'type': 'scatter',
            'marker': {
                'size': [c * 30 + 10 for c in self.games_df['confidence'].tolist()],
                'color': self.games_df['playoff_impact'].apply(lambda x: 1 if x != 'NONE' else 0).tolist(),
                'colorscale': [[0, '#e5e7eb'], [1, '#ef4444']],
                'showscale': True,
                'colorbar': {'title': 'Playoff Impact'}
            },
            'text': [f"{row['away_team']} @ {row['home_team']}" for _, row in self.games_df.iterrows()],
            'name': 'Games'
        }
        bubble_layout = {
            'title': 'V003: Upset Probability vs Betting Recommendation',
            'xaxis': {'title': 'Upset Probability'},
            'yaxis': {'title': 'Confidence'},
            'height': 400
        }
        
        # V004: Conference Strength Radar (simplified as bar chart for now)
        conf_counts = self.games_df['home_conference'].value_counts()
        radar_data = {
            'x': conf_counts.index.tolist(),
            'y': conf_counts.values.tolist(),
            'type': 'bar',
            'marker': {'color': '#8b5cf6'}
        }
        radar_layout = {
            'title': 'V004: Conference Strength (Game Count)',
            'xaxis': {'title': 'Conference'},
            'yaxis': {'title': 'Number of Games'},
            'height': 400
        }
        
        # V005: Top 10 Matchups Comparison (horizontal bar)
        top_10 = self.games_df.nlargest(10, 'confidence')
        bar_data = {
            'x': top_10['confidence'].tolist(),
            'y': [f"{row['away_team']} @ {row['home_team']}" for _, row in top_10.iterrows()],
            'type': 'bar',
            'orientation': 'h',
            'marker': {
                'color': top_10['confidence'].tolist(),
                'colorscale': 'Viridis',
                'showscale': True
            },
            'name': 'Confidence'
        }
        bar_layout = {
            'title': 'V005: Top 10 Matchups Comparison',
            'xaxis': {'title': 'Confidence'},
            'yaxis': {'title': 'Game', 'categoryorder': 'total ascending'},
            'height': 400
        }
        
        # V006: Playoff Impact Matrix (heatmap)
        playoff_games = [g for g in self.unified_data['games'] if self._get_playoff_impact(g['game_id']) != 'NONE']
        if playoff_games:
            teams = set()
            for g in playoff_games:
                teams.add(g['game_info']['home_team'])
                teams.add(g['game_info']['away_team'])
            teams = sorted(list(teams))[:10]  # Limit to top 10
            
            heatmap_data = {
                'z': [[1 if teams[i] in [g['game_info']['home_team'], g['game_info']['away_team']] else 0 
                       for g in playoff_games[:10]] for i in range(len(teams))],
                'x': [f"Game {i+1}" for i in range(min(10, len(playoff_games)))],
                'y': teams,
                'type': 'heatmap',
                'colorscale': 'Reds',
                'showscale': True
            }
            heatmap_layout = {
                'title': 'V006: Playoff Impact Matrix',
                'xaxis': {'title': 'Games'},
                'yaxis': {'title': 'Teams'},
                'height': 400
            }
        else:
            heatmap_data = {'z': [[0]], 'x': ['No Data'], 'y': ['No Data'], 'type': 'heatmap'}
            heatmap_layout = {'title': 'V006: Playoff Impact Matrix', 'height': 400}
        
        # V007: Game Script Timeline (line chart for top 3 matchups)
        top_3 = self.games_df.nlargest(3, 'confidence')
        timeline_data = []
        for idx, (_, game) in enumerate(top_3.iterrows()):
            # Simulated quarter-by-quarter scores
            quarters = ['Q1', 'Q2', 'Q3', 'Q4']
            home_scores = [0, game['margin'] * 0.25, game['margin'] * 0.5, game['margin']]
            away_scores = [0, -game['margin'] * 0.25, -game['margin'] * 0.5, -game['margin']]
            
            timeline_data.append({
                'x': quarters,
                'y': home_scores,
                'type': 'scatter',
                'mode': 'lines+markers',
                'name': f"{game['home_team']} (Home)",
                'line': {'color': f'hsl({idx * 120}, 70%, 50%)'}
            })
            timeline_data.append({
                'x': quarters,
                'y': away_scores,
                'type': 'scatter',
                'mode': 'lines+markers',
                'name': f"{game['away_team']} (Away)",
                'line': {'color': f'hsl({idx * 120 + 60}, 70%, 50%)', 'dash': 'dash'}
            })
        timeline_layout = {
            'title': 'V007: Game Script Timeline (Top 3 Matchups)',
            'xaxis': {'title': 'Quarter'},
            'yaxis': {'title': 'Score Margin'},
            'height': 400
        }
        
        # V008: Talent vs Performance Gap (scatter)
        talent_data = []
        for _, game in self.games_df.iterrows():
            game_data = next((g for g in self.unified_data['games'] if g['game_id'] == game['game_id']), None)
            if game_data:
                home_talent = game_data['game_info'].get('home_talent', 0)
                away_talent = game_data['game_info'].get('away_talent', 0)
                home_epa = game_data['game_info'].get('home_adjusted_epa', 0)
                away_epa = game_data['game_info'].get('away_adjusted_epa', 0)
                
                talent_data.append({
                    'x': home_talent,
                    'y': home_epa,
                    'team': game['home_team'],
                    'type': 'home'
                })
                talent_data.append({
                    'x': away_talent,
                    'y': away_epa,
                    'team': game['away_team'],
                    'type': 'away'
                })
        
        if talent_data:
            talent_df = pd.DataFrame(talent_data)
            talent_scatter = {
                'x': talent_df['x'].tolist(),
                'y': talent_df['y'].tolist(),
                'mode': 'markers',
                'type': 'scatter',
                'marker': {
                    'size': 10,
                    'color': talent_df['type'].apply(lambda x: '#3b82f6' if x == 'home' else '#ef4444').tolist(),
                    'opacity': 0.6
                },
                'text': talent_df['team'].tolist(),
                'name': 'Teams'
            }
            talent_layout = {
                'title': 'V008: Talent vs Performance Gap',
                'xaxis': {'title': 'Talent Rating'},
                'yaxis': {'title': 'Adjusted EPA'},
                'height': 400
            }
        else:
            talent_scatter = {'x': [0], 'y': [0], 'type': 'scatter', 'mode': 'markers'}
            talent_layout = {'title': 'V008: Talent vs Performance Gap', 'height': 400}
        
        return f"""
    <script>
        // V001: Confidence Distribution
        Plotly.newPlot('confidenceHistogram', [{json.dumps(hist_data)}], {json.dumps(hist_layout)});
        
        // V002: Spread vs Confidence
        Plotly.newPlot('spreadConfidenceScatter', [{json.dumps(scatter_data)}], {json.dumps(scatter_layout)});
        
        // V003: Upset Probability vs Betting Rec
        Plotly.newPlot('upsetBubble', [{json.dumps(bubble_data)}], {json.dumps(bubble_layout)});
        
        // V004: Conference Strength
        Plotly.newPlot('conferenceRadar', [{json.dumps(radar_data)}], {json.dumps(radar_layout)});
        
        // V005: Top 10 Matchups
        Plotly.newPlot('topMatchupsBar', [{json.dumps(bar_data)}], {json.dumps(bar_layout)});
        
        // V006: Playoff Impact Matrix
        Plotly.newPlot('playoffHeatmap', [{json.dumps(heatmap_data)}], {json.dumps(heatmap_layout)});
        
        // V007: Game Script Timeline
        Plotly.newPlot('gameScriptTimeline', {json.dumps(timeline_data)}, {json.dumps(timeline_layout)});
        
        // V008: Talent vs Performance
        Plotly.newPlot('talentPerformanceGap', [{json.dumps(talent_scatter)}], {json.dumps(talent_layout)});
        
        // Confidence vs Line Analysis (for betting hub)
        const confidenceLineData = {{
            x: {json.dumps([g.get('ensemble', {}).get('margin', 0) for g in self.unified_data['games']])},
            y: {json.dumps([g.get('ensemble', {}).get('confidence', 0) for g in self.unified_data['games']])},
            mode: 'markers',
            type: 'scatter',
            marker: {{
                size: 10,
                color: {json.dumps([g.get('game_info', {}).get('spread', 0) for g in self.unified_data['games']])},
                colorscale: 'RdYlGn',
                showscale: true,
                colorbar: {{title: 'Spread'}}
            }},
            text: {json.dumps([f"{g['game_info']['away_team']} @ {g['game_info']['home_team']}" for g in self.unified_data['games']])},
            name: 'Games'
        }};
        const confidenceLineLayout = {{
            title: 'Confidence vs Line Analysis',
            xaxis: {{title: 'Predicted Margin'}},
            yaxis: {{title: 'Confidence'}},
            height: 400
        }};
        Plotly.newPlot('confidenceLineAnalysis', [confidenceLineData], confidenceLineLayout);
    </script>"""


def main():
    """Main execution function."""
    project_root = Path(__file__).parent.parent
    week13_dir = project_root / "analysis" / "week13"
    output_path = week13_dir / "week13_master_report.html"
    
    generator = Week13MasterReportGenerator(week13_dir)
    generator.load_unified_data()
    html = generator.generate_html()
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ Master report generated: {output_path}")
    print(f"   File size: {output_path.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()

