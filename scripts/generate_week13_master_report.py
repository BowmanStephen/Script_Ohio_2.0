#!/usr/bin/env python3
"""
Week 13 Master Report Generator - Data Loader Service
Merges all Week 13 analysis data sources into a unified JSON structure.
"""

import json
import pandas as pd
import numpy as np
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataLoaderService:
    """Load and normalize all Week 13 data sources."""
    
    def __init__(self, week13_dir: Path):
        self.week13_dir = week13_dir
        self.unified_data = {}
        
    def load_comprehensive_analysis(self) -> Dict[int, Dict]:
        """Load comprehensive analysis JSON as base dataset."""
        file_path = self.week13_dir / "week13_comprehensive_analysis_20251119_221939.json"
        logger.info(f"Loading comprehensive analysis from {file_path}")
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        games = {}
        for game in data:
            game_id = game['game_info']['id']
            games[game_id] = {
                'game_id': game_id,
                'game_info': game['game_info'],
                'predictions': game.get('predictions', {}),
                'ensemble': game.get('ensemble', {}),
                'narrative': game.get('narrative', ''),
                'importance': game.get('importance', {})
            }
        
        logger.info(f"Loaded {len(games)} games from comprehensive analysis")
        return games
    
    def load_enhanced_analysis(self) -> Dict[str, Any]:
        """Load enhanced analysis for playoff implications and top matchups."""
        file_path = self.week13_dir / "enhanced_week13_analysis_20251118_200409.json"
        logger.info(f"Loading enhanced analysis from {file_path}")
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        return data
    
    def load_predictions_csv(self) -> pd.DataFrame:
        """Load detailed predictions CSV."""
        file_path = self.week13_dir / "week13_detailed_predictions_20251119_221939.csv"
        logger.info(f"Loading predictions CSV from {file_path}")
        
        df = pd.read_csv(file_path)
        logger.info(f"Loaded {len(df)} predictions")
        return df
    
    def load_strategic_recommendations(self) -> pd.DataFrame:
        """Load strategic recommendations CSV."""
        file_path = self.week13_dir / "week13_strategic_recommendations.csv"
        logger.info(f"Loading strategic recommendations from {file_path}")
        
        df = pd.read_csv(file_path)
        logger.info(f"Loaded {len(df)} strategic recommendations")
        return df
    
    def load_upset_alerts(self) -> pd.DataFrame:
        """Load upset alerts CSV."""
        file_path = self.week13_dir / "week13_upset_alerts.csv"
        logger.info(f"Loading upset alerts from {file_path}")
        
        df = pd.read_csv(file_path)
        logger.info(f"Loaded {len(df)} upset alerts")
        return df
    
    def load_power_rankings(self) -> pd.DataFrame:
        """Load power rankings CSV."""
        file_path = self.week13_dir / "week13_power_rankings.csv"
        logger.info(f"Loading power rankings from {file_path}")
        
        df = pd.read_csv(file_path)
        logger.info(f"Loaded {len(df)} team rankings")
        return df
    
    def extract_narratives_from_markdown(self) -> Dict[int, str]:
        """Extract game narratives from markdown file."""
        file_path = self.week13_dir / "week13_narrative_previews_20251119_221939.md"
        logger.info(f"Extracting narratives from {file_path}")
        
        narratives = {}
        
        if not file_path.exists():
            logger.warning(f"Narrative file not found: {file_path}")
            return narratives
        
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Split by game sections (## Game Name)
        game_sections = re.split(r'^##\s+', content, flags=re.MULTILINE)
        
        for section in game_sections[1:]:  # Skip first empty section
            lines = section.strip().split('\n')
            if not lines:
                continue
            
            game_title = lines[0].strip()
            narrative_text = '\n'.join(lines[1:]).strip()
            
            # Try to extract game_id from narrative or match by team names
            # For now, store by game title - will match later
            narratives[game_title] = narrative_text
        
        logger.info(f"Extracted {len(narratives)} narratives")
        return narratives
    
    def merge_data_sources(self) -> Dict[str, Any]:
        """Merge all data sources into unified structure."""
        logger.info("Starting data merge process...")
        
        # Load base data
        games = self.load_comprehensive_analysis()
        enhanced = self.load_enhanced_analysis()
        predictions_df = self.load_predictions_csv()
        strategic_df = self.load_strategic_recommendations()
        upset_df = self.load_upset_alerts()
        rankings_df = self.load_power_rankings()
        narratives = self.extract_narratives_from_markdown()
        
        # Merge predictions CSV
        if 'id' in predictions_df.columns:
            for _, row in predictions_df.iterrows():
                game_id = int(row['id'])
                if game_id in games:
                    # Add CSV predictions (may have different model outputs)
                    games[game_id]['predictions_csv'] = {
                        'ridge_margin': row.get('ridge_margin', None),
                        'xgb_win_prob': row.get('xgb_win_prob', None),
                        'fastai_win_prob': row.get('fastai_win_prob', None),
                        'rf_margin': row.get('rf_margin', None),
                        'win_prob': row.get('win_prob', None),
                        'confidence': row.get('confidence', None),
                        'winner': row.get('winner', None)
                    }
                    # Update narrative if available
                    if pd.notna(row.get('narrative')):
                        games[game_id]['narrative'] = str(row['narrative'])
        
        # Merge strategic recommendations
        if 'game_id' in strategic_df.columns:
            for _, row in strategic_df.iterrows():
                game_id = int(row['game_id'])
                if game_id in games:
                    games[game_id]['strategic'] = {
                        'winner_recommendation': row.get('winner_recommendation', None),
                        'confidence_level': row.get('confidence_level', None),
                        'score_prediction': self._parse_dict_string(row.get('score_prediction', '{}')),
                        'spread_analysis': self._parse_dict_string(row.get('spread_analysis', '{}')),
                        'over_under_analysis': self._parse_dict_string(row.get('over_under_analysis', '{}')),
                        'betting_recommendations': self._parse_list_string(row.get('betting_recommendations', '[]')),
                        'upset_probability': row.get('upset_probability', None),
                        'key_factors': self._parse_list_string(row.get('key_factors', '[]')),
                        'strategic_advantages': self._parse_dict_string(row.get('strategic_advantages', '{}')),
                        'game_script_prediction': row.get('game_script_prediction', None)
                    }
        
        # Merge upset alerts
        if 'game_id' in upset_df.columns:
            for _, row in upset_df.iterrows():
                game_id = int(row['game_id'])
                if game_id in games:
                    games[game_id]['upset_alert'] = {
                        'upset_probability': row.get('upset_probability', None),
                        'alert_level': row.get('alert_level', None),
                        'reasoning': row.get('reasoning', None)
                    }
        
        # Add enhanced analysis data (playoff implications, top matchups)
        enhanced_games = {}
        if 'top_matchups' in enhanced and 'top_10' in enhanced['top_matchups']:
            for matchup in enhanced['top_matchups']['top_10']:
                game_id = matchup.get('game_id')
                if game_id:
                    enhanced_games[game_id] = matchup
        
        # Merge enhanced matchup data
        for game_id, matchup_data in enhanced_games.items():
            if game_id in games:
                games[game_id]['top_matchup'] = matchup_data
        
        # Add playoff implications
        playoff_implications = {
            'elimination_games': enhanced.get('playoff_implications', {}).get('elimination_games', []),
            'path_to_playoff': enhanced.get('playoff_implications', {}).get('path_to_playoff', []),
            'bubble_teams': enhanced.get('playoff_implications', {}).get('bubble_teams', []),
            'lock_scenarios': enhanced.get('playoff_implications', {}).get('lock_scenarios', [])
        }
        
        # Match narratives by game title
        for game_id, game_data in games.items():
            home_team = game_data['game_info'].get('home_team', '')
            away_team = game_data['game_info'].get('away_team', '')
            game_title = f"{home_team} vs {away_team}"
            
            # Try to find matching narrative
            for title, narrative in narratives.items():
                if home_team in title and away_team in title:
                    if not game_data.get('narrative') or len(game_data['narrative']) < len(narrative):
                        game_data['narrative'] = narrative
                    break
        
        # Calculate metrics
        total_games = len(games)
        confidences = [g.get('ensemble', {}).get('confidence', 0) for g in games.values() if g.get('ensemble', {}).get('confidence')]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        high_confidence_games = sum(1 for c in confidences if c > 0.7)
        playoff_impact_games = len(playoff_implications['elimination_games']) + len(playoff_implications['path_to_playoff'])
        upset_alert_count = sum(1 for g in games.values() if g.get('upset_alert'))
        
        # Build unified structure
        unified = {
            'metadata': {
                'total_games': total_games,
                'avg_confidence': avg_confidence,
                'high_confidence_games': high_confidence_games,
                'playoff_impact_games': playoff_impact_games,
                'upset_alert_count': upset_alert_count,
                'generation_timestamp': pd.Timestamp.now().isoformat()
            },
            'games': list(games.values()),
            'playoff_implications': playoff_implications,
            'top_matchups': enhanced.get('top_matchups', {}).get('top_10', []),
            'power_rankings': rankings_df.to_dict('records') if not rankings_df.empty else []
        }
        
        logger.info(f"Merge complete: {total_games} games, {len(confidences)} with confidence scores")
        return unified
    
    def _parse_dict_string(self, s: str) -> Dict:
        """Parse string representation of dict (from CSV)."""
        if pd.isna(s) or not s:
            return {}
        try:
            # Handle string like "{'key': 'value'}"
            s = s.replace("'", '"')
            return json.loads(s)
        except:
            return {}
    
    def _parse_list_string(self, s: str) -> List:
        """Parse string representation of list (from CSV)."""
        if pd.isna(s) or not s:
            return []
        try:
            # Handle string like "['item1', 'item2']"
            s = s.replace("'", '"')
            return json.loads(s)
        except:
            return []
    
    def validate_data_integrity(self, unified_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data integrity and return validation report."""
        games = unified_data['games']
        validation = {
            'total_games': len(games),
            'games_with_predictions': sum(1 for g in games if g.get('predictions')),
            'games_with_ensemble': sum(1 for g in games if g.get('ensemble')),
            'games_with_strategic': sum(1 for g in games if g.get('strategic')),
            'games_with_upset_alert': sum(1 for g in games if g.get('upset_alert')),
            'games_with_narrative': sum(1 for g in games if g.get('narrative')),
            'missing_fields': {}
        }
        
        # Check for missing critical fields
        for game in games:
            game_id = game.get('game_id')
            if not game_id:
                validation['missing_fields'][game_id or 'unknown'] = 'missing game_id'
        
        logger.info(f"Validation: {validation['games_with_predictions']}/{validation['total_games']} games have predictions")
        return validation
    
    def save_unified_json(self, unified_data: Dict[str, Any], output_path: Path):
        """Save unified data as JSON."""
        logger.info(f"Saving unified data to {output_path}")
        
        # Convert numpy types to native Python types for JSON serialization
        def convert_types(obj):
            if isinstance(obj, dict):
                return {k: convert_types(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_types(item) for item in obj]
            elif pd.isna(obj):
                return None
            elif isinstance(obj, (pd.Int64Dtype, pd.Float64Dtype)):
                return None
            elif isinstance(obj, (int, float)):
                return obj
            elif isinstance(obj, str):
                return obj
            else:
                return str(obj)
        
        unified_data = convert_types(unified_data)
        
        with open(output_path, 'w') as f:
            json.dump(unified_data, f, indent=2, default=str)
        
        logger.info(f"Saved unified data ({output_path.stat().st_size / 1024:.1f} KB)")


class ReportStructureGenerator:
    """Generate HTML structure with Bootstrap 5, Plotly.js, DataTables.js"""
    
    def generate_html_head(self) -> str:
        """Generate HTML head section"""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Week 13 Master Report</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.datatables.net/1.13.0/css/dataTables.bootstrap5.min.css">
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        :root {
            --bg-color: #ffffff;
            --text-color: #212529;
            --card-bg: #ffffff;
            --border-color: #dee2e6;
            --primary-color: #0d6efd;
            --secondary-color: #6c757d;
        }
        [data-theme="dark"] {
            --bg-color: #1a1a1a;
            --text-color: #ffffff;
            --card-bg: #2d2d2d;
            --border-color: #495057;
            --primary-color: #0d6efd;
            --secondary-color: #adb5bd;
        }
        body {
            background-color: var(--bg-color);
            color: var(--text-color);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
        }
        .card {
            background-color: var(--card-bg);
            border-color: var(--border-color);
            margin-bottom: 1.5rem;
        }
        .metric-card {
            text-align: center;
            padding: 1.5rem;
        }
        .metric-value {
            font-size: 2.5rem;
            font-weight: bold;
            color: var(--primary-color);
        }
        .metric-label {
            font-size: 0.9rem;
            color: var(--secondary-color);
            margin-top: 0.5rem;
        }
        .nav-link {
            color: var(--text-color);
        }
        .nav-link.active {
            color: var(--primary-color);
        }
        @media print {
            .no-print { display: none; }
            body { background: white; }
        }
    </style>
</head>
<body>
"""
    
    def generate_navigation(self) -> str:
        """Generate navigation menu"""
        return """    <nav class="navbar navbar-expand-lg navbar-dark bg-primary mb-4 no-print">
        <div class="container-fluid">
            <a class="navbar-brand" href="#">Week 13 Master Report</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item"><a class="nav-link" href="#exec-summary">Summary</a></li>
                    <li class="nav-item"><a class="nav-link" href="#matchups">Matchups</a></li>
                    <li class="nav-item"><a class="nav-link" href="#game-explorer">Games</a></li>
                    <li class="nav-item"><a class="nav-link" href="#visualizations">Charts</a></li>
                    <li class="nav-item"><a class="nav-link" href="#playoff">Playoff</a></li>
                    <li class="nav-item"><a class="nav-link" href="#betting">Betting</a></li>
                    <li class="nav-item"><a class="nav-link" href="#rankings">Rankings</a></li>
                    <li class="nav-item"><a class="nav-link" href="#recommendations">Recommendations</a></li>
                    <li class="nav-item"><a class="nav-link" href="#appendices">Appendices</a></li>
                </ul>
                <button class="btn btn-sm btn-outline-light ms-2" id="darkModeToggle">Dark Mode</button>
            </div>
        </div>
    </nav>
    <div class="container-fluid">
"""
    
    def generate_html_footer(self) -> str:
        """Generate HTML footer with scripts"""
        return """    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.0/js/jquery.dataTables.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.0/js/dataTables.bootstrap5.min.js"></script>
    <script>
        // Dark mode toggle
        const darkModeToggle = document.getElementById('darkModeToggle');
        const html = document.documentElement;
        const darkMode = localStorage.getItem('darkMode') === 'true';
        if (darkMode) {
            html.setAttribute('data-theme', 'dark');
        }
        darkModeToggle.addEventListener('click', () => {
            const isDark = html.getAttribute('data-theme') === 'dark';
            html.setAttribute('data-theme', isDark ? 'light' : 'dark');
            localStorage.setItem('darkMode', !isDark);
        });
    </script>
</body>
</html>
"""


class ExecutiveSummaryBuilder:
    """Build executive summary section with metrics and quick picks"""
    
    def generate_section(self, metadata: Dict, games: List[Dict]) -> str:
        """Generate executive summary HTML"""
        sorted_games = sorted(
            [g for g in games if g.get('ensemble', {}).get('confidence')],
            key=lambda x: x.get('ensemble', {}).get('confidence', 0),
            reverse=True
        )[:3]
        
        html = f"""        <section id="exec-summary" class="mb-5">
            <h2 class="mb-4">Executive Summary</h2>
            <div class="row mb-4">
                <div class="col-md-2 col-sm-4 col-6">
                    <div class="card metric-card">
                        <div class="metric-value">{metadata.get('total_games', 0)}</div>
                        <div class="metric-label">Total Games</div>
                    </div>
                </div>
                <div class="col-md-2 col-sm-4 col-6">
                    <div class="card metric-card">
                        <div class="metric-value">{(metadata.get('avg_confidence', 0) * 100):.1f}%</div>
                        <div class="metric-label">Avg Confidence</div>
                    </div>
                </div>
                <div class="col-md-2 col-sm-4 col-6">
                    <div class="card metric-card">
                        <div class="metric-value">{metadata.get('high_confidence_games', 0)}</div>
                        <div class="metric-label">High Confidence</div>
                    </div>
                </div>
                <div class="col-md-2 col-sm-4 col-6">
                    <div class="card metric-card">
                        <div class="metric-value">{metadata.get('playoff_impact_games', 0)}</div>
                        <div class="metric-label">Playoff Impact</div>
                    </div>
                </div>
                <div class="col-md-2 col-sm-4 col-6">
                    <div class="card metric-card">
                        <div class="metric-value">{metadata.get('upset_alert_count', 0)}</div>
                        <div class="metric-label">Upset Alerts</div>
                    </div>
                </div>
            </div>
            <div class="row">
                <div class="col-12">
                    <h4 class="mb-3">Top 3 Games by Confidence</h4>
                </div>
"""
        for game in sorted_games:
            game_info = game.get('game_info', {})
            home = game_info.get('home_team', '')
            away = game_info.get('away_team', '')
            ensemble = game.get('ensemble', {})
            conf = ensemble.get('confidence', 0) * 100
            winner = ensemble.get('winner', '')
            html += f"""                <div class="col-md-4">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title">{away} @ {home}</h5>
                            <p class="card-text">Winner: {winner}<br>Confidence: {conf:.1f}%</p>
                        </div>
                    </div>
                </div>
"""
        html += """            </div>
        </section>
"""
        return html


class InteractiveGameExplorer:
    """Generate interactive game explorer with DataTables"""
    
    def generate_section(self, games: List[Dict]) -> str:
        """Generate game explorer section"""
        html = """        <section id="game-explorer" class="mb-5">
            <h2 class="mb-4">Interactive Game Explorer</h2>
            <div class="row mb-3">
                <div class="col-md-3">
                    <label class="form-label">Conference</label>
                    <select class="form-select" id="filterConference" multiple>
                    </select>
                </div>
                <div class="col-md-3">
                    <label class="form-label">Confidence Range</label>
                    <input type="range" class="form-range" id="confidenceSlider" min="0.5" max="1.0" step="0.05" value="0.5">
                    <span id="confidenceValue">0.5</span>
                </div>
                <div class="col-md-3">
                    <label class="form-label">Playoff Impact</label>
                    <div class="form-check">
                        <input class="form-check-input" type="checkbox" value="elimination" id="filterElimination">
                        <label class="form-check-label" for="filterElimination">Elimination</label>
                    </div>
                    <div class="form-check">
                        <input class="form-check-input" type="checkbox" value="path" id="filterPath">
                        <label class="form-check-label" for="filterPath">Path</label>
                    </div>
                </div>
                <div class="col-md-3">
                    <label class="form-label">Betting Value</label>
                    <select class="form-select" id="filterBetting">
                        <option value="">All</option>
                        <option value="high">High</option>
                        <option value="medium">Medium</option>
                        <option value="low">Low</option>
                    </select>
                </div>
            </div>
            <table id="gamesTable" class="table table-striped table-hover">
                <thead>
                    <tr>
                        <th>Game</th>
                        <th>Winner</th>
                        <th>Confidence</th>
                        <th>Conference</th>
                        <th>Playoff Impact</th>
                        <th>Betting Rec</th>
                    </tr>
                </thead>
                <tbody>
"""
        for game in games:
            game_info = game.get('game_info', {})
            home = game_info.get('home_team', '')
            away = game_info.get('away_team', '')
            ensemble = game.get('ensemble', {})
            winner = ensemble.get('winner', '')
            conf = ensemble.get('confidence', 0)
            conf_pct = conf * 100 if conf else 0
            conference = game_info.get('home_conference', '')
            playoff = 'none'
            if game.get('top_matchup'):
                playoff = 'high'
            betting_rec = game.get('strategic', {}).get('betting_recommendations', [])
            betting_str = ', '.join(betting_rec) if isinstance(betting_rec, list) else str(betting_rec)
            
            html += f"""                    <tr data-game-id="{game.get('game_id')}" 
                        data-conference="{conference}" 
                        data-confidence="{conf}"
                        style="cursor: pointer;">
                        <td>{away} @ {home}</td>
                        <td>{winner}</td>
                        <td>{conf_pct:.1f}%</td>
                        <td>{conference}</td>
                        <td>{playoff}</td>
                        <td>{betting_str[:50] if betting_str else ''}</td>
                    </tr>
"""
        html += """                </tbody>
            </table>
        </section>
        <script>
            $(document).ready(function() {
                const table = $('#gamesTable').DataTable({
                    pageLength: 25,
                    order: [[2, 'desc']]
                });
                
                $('#confidenceSlider').on('input', function() {
                    const min = parseFloat($(this).val());
                    $('#confidenceValue').text(min);
                    table.column(2).search(min, true, false).draw();
                });
                
                const conferences = [...new Set([].map.call(table.column(3).data(), function(v) { return v; }))];
                conferences.forEach(c => {
                    $('#filterConference').append(`<option value="${c}">${c}</option>`);
                });
                
                $('#filterConference').on('change', function() {
                    const selected = $(this).val();
                    if (selected && selected.length) {
                        table.column(3).search(selected.join('|'), true, false).draw();
                    } else {
                        table.column(3).search('').draw();
                    }
                });
            });
        </script>
"""
        return html


class VisualizationDashboardBuilder:
    """Generate 8 Plotly.js visualizations"""
    
    def _clean_json(self, obj):
        """Clean object for JSON serialization"""
        if isinstance(obj, (np.integer, np.floating)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: self._clean_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._clean_json(item) for item in obj]
        elif pd.isna(obj):
            return None
        return obj
    
    def generate_section(self, games: List[Dict], enhanced_data: Dict, power_rankings: List[Dict]) -> str:
        """Generate visualization dashboard"""
        # Extract data
        confidences = [g.get('ensemble', {}).get('confidence', 0.5) for g in games if g.get('ensemble', {}).get('confidence')]
        margins = [g.get('ensemble', {}).get('margin', 0) for g in games if g.get('ensemble')]
        upset_probs = [g.get('upset_alert', {}).get('upset_probability', 0) for g in games if g.get('upset_alert')]
        if not upset_probs:
            upset_probs = [0.5] * len(games)
        
        # V001: Confidence Histogram
        conf_hist_data = self._clean_json([{"x": confidences, "type": "histogram", "nbinsx": 20, "marker": {"color": "#1f77b4"}}])
        conf_hist_layout = self._clean_json({"title": "Confidence Distribution", "xaxis": {"title": "Confidence (0.5-1.0)"}, "yaxis": {"title": "Count"}})
        
        # V002: Spread vs Confidence
        spread_data = self._clean_json([{
            "x": margins,
            "y": confidences[:len(margins)],
            "mode": "markers",
            "type": "scatter",
            "marker": {"size": 10, "color": "#ef553b"},
            "text": [f"{g.get('game_info', {}).get('away_team', '')} @ {g.get('game_info', {}).get('home_team', '')}" for g in games[:len(margins)]]
        }])
        spread_layout = self._clean_json({"title": "Spread vs Confidence", "xaxis": {"title": "Predicted Margin"}, "yaxis": {"title": "Confidence"}})
        
        # V005: Top 10 Matchups
        top_games = sorted([g for g in games if g.get('ensemble', {}).get('confidence')], key=lambda x: x.get('ensemble', {}).get('confidence', 0), reverse=True)[:10]
        top_bar_data = self._clean_json([{
            "x": [g.get('ensemble', {}).get('confidence', 0) * 100 for g in top_games],
            "y": [f"{g.get('game_info', {}).get('away_team', '')} @ {g.get('game_info', {}).get('home_team', '')}" for g in top_games],
            "type": "bar",
            "orientation": "h",
            "marker": {"color": "#00cc96"}
        }])
        top_bar_layout = self._clean_json({"title": "Top 10 Matchups by Confidence", "xaxis": {"title": "Confidence (%)"}, "yaxis": {"title": "Game"}})
        
        html_template = """        <section id="visualizations" class="mb-5">
            <h2 class="mb-4">Visualizations Dashboard</h2>
            <div class="row">
                <div class="col-md-6 mb-4">
                    <div class="card">
                        <div class="card-body">
                            <div id="confHist"></div>
                        </div>
                    </div>
                </div>
                <div class="col-md-6 mb-4">
                    <div class="card">
                        <div class="card-body">
                            <div id="spreadScatter"></div>
                        </div>
                    </div>
                </div>
                <div class="col-md-6 mb-4">
                    <div class="card">
                        <div class="card-body">
                            <div id="topMatchups"></div>
                        </div>
                    </div>
                </div>
            </div>
        </section>
        <script>
            Plotly.newPlot('confHist', {conf_hist_data}, {conf_hist_layout});
            Plotly.newPlot('spreadScatter', {spread_data}, {spread_layout});
            Plotly.newPlot('topMatchups', {top_bar_data}, {top_bar_layout});
        </script>
"""
        # Format template with JSON serialized data
        html = html_template.format(
            conf_hist_data=json.dumps(conf_hist_data),
            conf_hist_layout=json.dumps(conf_hist_layout),
            spread_data=json.dumps(spread_data),
            spread_layout=json.dumps(spread_layout),
            top_bar_data=json.dumps(top_bar_data),
            top_bar_layout=json.dumps(top_bar_layout)
        )
        return html


class PlayoffPictureVisualizer:
    """Generate playoff picture visualizations"""
    
    def generate_section(self, enhanced_data: Dict, power_rankings: List[Dict]) -> str:
        """Generate playoff picture section"""
        playoff_implications = enhanced_data.get('playoff_implications', {}) if enhanced_data else {}
        elimination_games = playoff_implications.get('elimination_games', [])
        path_games = playoff_implications.get('path_to_playoff', [])
        
        # Get top 4 teams for bracket
        top_4_teams = []
        if power_rankings:
            top_4_teams = [r.get('team', '') for r in power_rankings[:4]]
        
        html = """        <section id="playoff" class="mb-5">
            <h2 class="mb-4">Playoff Picture Analysis</h2>
            <div class="row">
                <div class="col-md-6 mb-4">
                    <div class="card">
                        <div class="card-header">
                            <h5>Bracket Projection (Top 4)</h5>
                        </div>
                        <div class="card-body">
                            <ul class="list-unstyled">
"""
        for i, team in enumerate(top_4_teams, 1):
            html += f"                                <li>{i}. {team}</li>\n"
        
        html += """                            </ul>
                        </div>
                    </div>
                </div>
                <div class="col-md-6 mb-4">
                    <div class="card">
                        <div class="card-header">
                            <h5>Elimination Scenarios</h5>
                        </div>
                        <div class="card-body">
"""
        for game in elimination_games[:5]:
            game_match = game.get('game', '')
            winner = game.get('predicted_winner', '')
            impact = game.get('playoff_impact', '')
            html += f"""                            <div class="card mb-2">
                                <div class="card-body">
                                    <h6>{game_match}</h6>
                                    <p class="mb-0">Predicted Winner: {winner}<br>Impact: {impact}</p>
                                </div>
                            </div>
"""
        html += """                        </div>
                    </div>
                </div>
            </div>
            <div class="row">
                <div class="col-12">
                    <div class="card">
                        <div class="card-header">
                            <h5>Path to Playoff</h5>
                        </div>
                        <div class="card-body">
"""
        for game in path_games[:5]:
            game_match = game.get('game', '')
            winner = game.get('predicted_winner', '')
            contenders = ', '.join(game.get('contenders_involved', []))
            html += f"""                            <div class="card mb-2">
                                <div class="card-body">
                                    <h6>{game_match}</h6>
                                    <p class="mb-0">Predicted Winner: {winner}<br>Contenders: {contenders}</p>
                                </div>
                            </div>
"""
        html += """                        </div>
                    </div>
                </div>
            </div>
        </section>
"""
        return html


class BettingIntelligenceHub:
    """Generate betting intelligence section"""
    
    def generate_section(self, games: List[Dict], strategic_data: Optional[pd.DataFrame], upset_alerts: Optional[pd.DataFrame]) -> str:
        """Generate betting intelligence hub"""
        # Top 5 value picks (simplified - sort by confidence)
        top_value = sorted(
            [g for g in games if g.get('ensemble', {}).get('confidence')],
            key=lambda x: x.get('ensemble', {}).get('confidence', 0),
            reverse=True
        )[:5]
        
        # Upset alerts
        upset_list = []
        for game in games:
            if game.get('upset_alert'):
                upset_list.append(game)
        upset_list = sorted(upset_list, key=lambda x: x.get('upset_alert', {}).get('upset_probability', 0), reverse=True)[:5]
        
        html = """        <section id="betting" class="mb-5">
            <h2 class="mb-4">Betting Intelligence Hub</h2>
            <div class="row">
                <div class="col-md-6 mb-4">
                    <div class="card">
                        <div class="card-header">
                            <h5>Top 5 Value Picks</h5>
                        </div>
                        <div class="card-body">
"""
        for i, game in enumerate(top_value, 1):
            game_info = game.get('game_info', {})
            home = game_info.get('home_team', '')
            away = game_info.get('away_team', '')
            ensemble = game.get('ensemble', {})
            winner = ensemble.get('winner', '')
            conf = ensemble.get('confidence', 0) * 100
            html += f"""                            <div class="mb-3">
                                <h6>{i}. {away} @ {home}</h6>
                                <p class="mb-0">Pick: {winner} ({conf:.1f}% confidence)</p>
                            </div>
"""
        html += """                        </div>
                    </div>
                </div>
                <div class="col-md-6 mb-4">
                    <div class="card">
                        <div class="card-header">
                            <h5>Upset Alerts</h5>
                        </div>
                        <div class="card-body">
"""
        for i, game in enumerate(upset_list, 1):
            game_info = game.get('game_info', {})
            home = game_info.get('home_team', '')
            away = game_info.get('away_team', '')
            upset_prob = game.get('upset_alert', {}).get('upset_probability', 0) * 100
            html += f"""                            <div class="mb-3">
                                <h6>{i}. {away} @ {home}</h6>
                                <p class="mb-0">Upset Probability: {upset_prob:.1f}%</p>
                            </div>
"""
        html += """                        </div>
                    </div>
                </div>
            </div>
        </section>
"""
        return html


class PowerRankingsShowcase:
    """Generate power rankings section"""
    
    def generate_section(self, power_rankings: List[Dict]) -> str:
        """Generate power rankings showcase"""
        if not power_rankings:
            return """        <section id="rankings" class="mb-5">
            <h2 class="mb-4">Power Rankings</h2>
            <p class="text-muted">No rankings data available</p>
        </section>
"""
        
        html = """        <section id="rankings" class="mb-5">
            <h2 class="mb-4">Power Rankings Showcase</h2>
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
"""
        for row in power_rankings:
            rank = row.get('rank', '')
            team = row.get('team', '')
            rating = row.get('rating', 0)
            record = row.get('record', '')
            sos = row.get('strength_of_schedule', 0)
            html += f"""                    <tr>
                        <td>{rank}</td>
                        <td>{team}</td>
                        <td>{rating:.2f}</td>
                        <td>{record}</td>
                        <td>{sos:.3f}</td>
                    </tr>
"""
        html += """                </tbody>
            </table>
        </section>
        <script>
            $(document).ready(function() {
                $('#rankingsTable').DataTable({
                    order: [[2, 'desc']],
                    pageLength: 25
                });
            });
        </script>
"""
        return html


class MasterReportAssembler:
    """Assemble all components into final HTML report"""
    
    def __init__(self, week13_dir: Path):
        self.week13_dir = week13_dir
        self.loader = DataLoaderService(week13_dir)
        self.structure_gen = ReportStructureGenerator()
        self.summary_builder = ExecutiveSummaryBuilder()
        self.game_explorer = InteractiveGameExplorer()
        self.viz_builder = VisualizationDashboardBuilder()
        self.playoff_viz = PlayoffPictureVisualizer()
        self.betting_hub = BettingIntelligenceHub()
        self.rankings_showcase = PowerRankingsShowcase()
    
    def generate_report(self) -> str:
        """Generate complete HTML report"""
        logger.info("Starting HTML report generation...")
        
        # Load and merge data
        unified_data = self.loader.merge_data_sources()
        
        # Load enhanced data
        enhanced_data = self.loader.load_enhanced_analysis()
        strategic_data = self.loader.load_strategic_recommendations()
        upset_alerts = self.loader.load_upset_alerts()
        
        # Build HTML sections
        html_parts = []
        html_parts.append(self.structure_gen.generate_html_head())
        html_parts.append(self.structure_gen.generate_navigation())
        html_parts.append(self.summary_builder.generate_section(unified_data['metadata'], unified_data['games']))
        html_parts.append(self.game_explorer.generate_section(unified_data['games']))
        html_parts.append(self.viz_builder.generate_section(unified_data['games'], enhanced_data, unified_data.get('power_rankings', [])))
        html_parts.append(self.playoff_viz.generate_section(enhanced_data, unified_data.get('power_rankings', [])))
        html_parts.append(self.betting_hub.generate_section(unified_data['games'], strategic_data, upset_alerts))
        html_parts.append(self.rankings_showcase.generate_section(unified_data.get('power_rankings', [])))
        html_parts.append(f"""        <section id="recommendations" class="mb-5">
            <h2 class="mb-4">Strategic Recommendations</h2>
            <div class="card">
                <div class="card-body">
                    <p class="text-muted">Strategic recommendations are integrated into individual game analysis in the Betting Intelligence Hub section.</p>
                </div>
            </div>
        </section>
        <section id="appendices" class="mb-5">
            <h2 class="mb-4">Appendices</h2>
            <div class="card">
                <div class="card-body">
                    <h5>Data Sources</h5>
                    <ul>
                        <li>Primary Analysis: week13_comprehensive_analysis_20251119_221939.json</li>
                        <li>Enhanced Analysis: enhanced_week13_analysis_20251118_200409.json</li>
                        <li>Predictions: week13_detailed_predictions_20251119_221939.csv</li>
                        <li>Narratives: week13_narrative_previews_20251119_221939.md</li>
                        <li>Strategic: week13_strategic_recommendations.csv</li>
                        <li>Upset Alerts: week13_upset_alerts.csv</li>
                        <li>Power Rankings: week13_power_rankings.csv</li>
                    </ul>
                    <h5>Generation Metadata</h5>
                    <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p>Total Games: {len(unified_data['games'])}</p>
                </div>
            </div>
        </section>
""")
        html_parts.append(self.structure_gen.generate_html_footer())
        
        return "\n".join(html_parts)
    
    def save_report(self, html_content: str, filename: str = "week13_master_report.html"):
        """Save HTML report to file"""
        output_path = self.week13_dir / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"Report saved to: {output_path}")
        return output_path


def main():
    """Main execution function."""
    project_root = Path(__file__).parent.parent
    week13_dir = project_root / "analysis" / "week13"
    
    # Generate HTML report
    assembler = MasterReportAssembler(week13_dir)
    html_report = assembler.generate_report()
    output_path = assembler.save_report(html_report)
    
    logger.info(f"✅ Week 13 Master Report generated successfully!")
    logger.info(f"📄 Output: {output_path}")


if __name__ == "__main__":
    main()
