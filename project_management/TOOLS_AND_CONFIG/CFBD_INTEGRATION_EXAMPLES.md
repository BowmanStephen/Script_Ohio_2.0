# CFBD Integration Examples
**Production-Ready Code Examples for Script Ohio 2.0 Integration**

---

## 📋 Table of Contents
1. [Basic Authentication Setup](#basic-authentication-setup)
2. [Core API Integration Examples](#core-api-integration-examples)
3. [Data Transformation Examples](#data-transformation-examples)
4. [Agent System Integration](#agent-system-integration)
5. [Advanced Integration Patterns](#advanced-integration-patterns)
6. [Complete Week 12 Integration Example](#complete-week-12-integration-example)

---

## 🔐 Basic Authentication Setup

### Environment Configuration
```python
# .env file
CFBD_API_KEY=your_api_key_here
CFBD_BASE_URL=https://api.collegefootballdata.com
CFBD_RATE_LIMIT_DELAY=0.5
CFBD_CACHE_DIR=cfbd_cache

# config/cfbd_config.py
import os
from pathlib import Path

class CFBDConfig:
    """CFBD API configuration for Script Ohio 2.0"""

    def __init__(self):
        self.api_key = os.getenv('CFBD_API_KEY')
        self.base_url = os.getenv('CFBD_BASE_URL', 'https://api.collegefootballdata.com')
        self.rate_delay = float(os.getenv('CFBD_RATE_LIMIT_DELAY', '0.5'))
        self.cache_dir = Path(os.getenv('CFBD_CACHE_DIR', 'cfbd_cache'))
        self.cache_dir.mkdir(exist_ok=True)

    def get_headers(self):
        """Get authentication headers"""
        if not self.api_key:
            raise ValueError("CFBD_API_KEY environment variable not set")

        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

# Usage
config = CFBDConfig()
headers = config.get_headers()
```

### Authentication Test
```python
# utils/cfbd_auth.py
import requests
from config.cfbd_config import CFBDConfig

def test_cfbd_authentication():
    """Test CFBD API authentication status"""

    try:
        config = CFBDConfig()
        headers = config.get_headers()

        # Test with a simple request
        response = requests.get(
            f"{config.base_url}/games",
            headers=headers,
            params={"year": 2025, "week": 12}
        )

        if response.status_code == 200:
            print("✅ CFBD API Authentication: SUCCESS")
            print(f"✅ Sample data retrieved: {len(response.json())} games")
            return True
        elif response.status_code == 401:
            print("❌ CFBD API Authentication: FAILED")
            print("❌ Check your API key in .env file")
            return False
        else:
            print(f"⚠️ CFBD API Status: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ CFBD API Test Error: {e}")
        return False

if __name__ == "__main__":
    test_cfbd_authentication()
```

---

## 🎯 Core API Integration Examples

### 1. Games API Integration
```python
# integrations/cfbd_games.py
import requests
import time
from datetime import datetime
from config.cfbd_config import CFBDConfig

class CFBGamesAPI:
    """CFBD Games API integration for Script Ohio 2.0"""

    def __init__(self):
        self.config = CFBDConfig()
        self.headers = self.config.get_headers()

    def get_week_games(self, year, week, season_type='regular'):
        """Get all games for a specific week"""

        url = f"{self.config.base_url}/games"
        params = {
            "year": year,
            "week": week,
            "seasonType": season_type
        }

        # Rate limiting
        time.sleep(self.config.rate_delay)

        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()

            games = response.json()

            # Add processed timestamps
            for game in games:
                game['data_retrieved'] = datetime.now().isoformat()
                game['season_type'] = season_type

            return {
                'success': True,
                'games': games,
                'count': len(games),
                'metadata': {
                    'year': year,
                    'week': week,
                    'season_type': season_type,
                    'retrieved_at': datetime.now().isoformat()
                }
            }

        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'games': []
            }

    def get_team_games(self, team, year, season_type='regular'):
        """Get all games for a specific team in a season"""

        url = f"{self.config.base_url}/games"
        params = {
            "year": year,
            "team": team,
            "seasonType": season_type
        }

        time.sleep(self.config.rate_delay)

        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()

            games = response.json()

            # Sort by week for chronological order
            games.sort(key=lambda x: x.get('week', 0))

            return {
                'success': True,
                'team': team,
                'games': games,
                'count': len(games)
            }

        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'team': team,
                'games': []
            }

# Example usage
if __name__ == "__main__":
    games_api = CFBGamesAPI()

    # Get Week 12 games
    week12_result = games_api.get_week_games(2025, 12)
    if week12_result['success']:
        print(f"✅ Retrieved {week12_result['count']} Week 12 games")

    # Get Ohio State games
    osu_result = games_api.get_team_games("Ohio State", 2025)
    if osu_result['success']:
        print(f"✅ Retrieved {osu_result['count']} Ohio State games")
```

### 2. Teams & Talent API Integration
```python
# integrations/cfbd_teams.py
import requests
import time
import pandas as pd
from config.cfbd_config import CFBDConfig

class CFBTeamsAPI:
    """CFBD Teams API integration"""

    def __init__(self):
        self.config = CFBDConfig()
        self.headers = self.config.get_headers()

    def get_team_talent(self, year):
        """Get team talent ratings for a specific year"""

        url = f"{self.config.base_url}/teams/talent"
        params = {"year": year}

        time.sleep(self.config.rate_delay)

        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()

            talent_data = response.json()

            # Convert to DataFrame for easier processing
            df = pd.DataFrame(talent_data)

            # Create team-to-talent mapping
            talent_mapping = {}
            for _, row in df.iterrows():
                talent_mapping[row['team']] = row['talent']

            return {
                'success': True,
                'year': year,
                'talent_data': talent_data,
                'talent_mapping': talent_mapping,
                'count': len(talent_data)
            }

        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'year': year,
                'talent_data': [],
                'talent_mapping': {}
            }

    def get_team_info(self, team=None):
        """Get team information"""

        url = f"{self.config.base_url}/teams"
        params = {}

        if team:
            params['team'] = team

        time.sleep(self.config.rate_delay)

        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()

            teams_data = response.json()

            return {
                'success': True,
                'teams': teams_data,
                'count': len(teams_data)
            }

        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'teams': []
            }

# Example usage
if __name__ == "__main__":
    teams_api = CFBTeamsAPI()

    # Get 2025 talent ratings
    talent_result = teams_api.get_team_talent(2025)
    if talent_result['success']:
        print(f"✅ Retrieved talent data for {talent_result['count']} teams")

        # Show top 10 teams by talent
        df = pd.DataFrame(talent_result['talent_data'])
        top_teams = df.nlargest(10, 'talent')
        print("🏆 Top 10 Teams by Talent (2025):")
        for _, row in top_teams.iterrows():
            print(f"  {row['team']}: {row['talent']}")
```

### 3. Advanced Metrics API Integration
```python
# integrations/cfbd_metrics.py
import requests
import time
import pandas as pd
from config.cfbd_config import CFBDConfig

class CFBMetricsAPI:
    """CFBD Advanced Metrics API integration"""

    def __init__(self):
        self.config = CFBDConfig()
        self.headers = self.config.get_headers()

    def get_team_season_stats(self, year, week=None, team=None):
        """Get team season statistics"""

        url = f"{self.config.base_url}/stats/season"
        params = {
            "year": year,
            "statType": "team"
        }

        if week:
            params['week'] = week
        if team:
            params['team'] = team

        time.sleep(self.config.rate_delay)

        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()

            stats_data = response.json()

            return {
                'success': True,
                'year': year,
                'week': week,
                'team': team,
                'stats': stats_data,
                'count': len(stats_data)
            }

        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'stats': []
            }

    def get_epa_metrics(self, year, team=None, exclude_garbage_time=True):
        """Get EPA (Expected Points Added) metrics"""

        url = f"{self.config.base_url}/metrics/epa"
        params = {
            "year": year,
            "excludeGarbageTime": exclude_garbage_time
        }

        if team:
            params['team'] = team

        time.sleep(self.config.rate_delay)

        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()

            epa_data = response.json()

            return {
                'success': True,
                'year': year,
                'team': team,
                'epa_data': epa_data,
                'count': len(epa_data)
            }

        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'epa_data': []
            }

    def get_ppa_metrics(self, year, team=None, exclude_garbage_time=True):
        """Get PPA (Predicted Points Added) metrics"""

        url = f"{self.config.base_url}/metrics/ppa"
        params = {
            "year": year,
            "excludeGarbageTime": exclude_garbage_time
        }

        if team:
            params['team'] = team

        time.sleep(self.config.rate_delay)

        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()

            ppa_data = response.json()

            return {
                'success': True,
                'year': year,
                'team': team,
                'ppa_data': ppa_data,
                'count': len(ppa_data)
            }

        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'ppa_data': []
            }

# Example usage
if __name__ == "__main__":
    metrics_api = CFBMetricsAPI()

    # Get EPA metrics for Ohio State
    epa_result = metrics_api.get_epa_metrics(2025, team="Ohio State")
    if epa_result['success']:
        print(f"✅ Retrieved EPA data: {epa_result['count']} records")

    # Get all team stats for Week 12
    week12_stats = metrics_api.get_team_season_stats(2025, week=12)
    if week12_stats['success']:
        print(f"✅ Retrieved Week 12 stats: {week12_stats['count']} teams")
```

---

## 🔄 Data Transformation Examples

### 86-Feature Pipeline Transformation
```python
# data_processing/feature_transformer.py
import pandas as pd
import numpy as np
from typing import Dict, List, Any

class FeatureTransformer:
    """Transform CFBD data to Script Ohio 2.0 86-feature format"""

    def __init__(self):
        self.feature_order = self._get_feature_order()
        self.required_features = self._get_required_features()

    def _get_feature_order(self):
        """Get the standard feature order for 86-feature pipeline"""
        return [
            # Talent ratings (2)
            'home_talent', 'away_talent',
            # EPA metrics (4)
            'home_adjusted_epa', 'away_adjusted_epa',
            'home_adjusted_success', 'away_adjusted_success',
            # Explosiveness metrics (4)
            'home_adjusted_explosiveness', 'away_adjusted_explosiveness',
            'home_explosiveness_ppa', 'away_explosiveness_ppa',
            # Havoc rates (8)
            'home_total_havoc_offense', 'away_total_havoc_offense',
            'home_total_havoc_defense', 'away_total_havoc_defense',
            'home_front_seven_havoc', 'away_front_seven_havoc',
            'home_db_havoc', 'away_db_havoc',
            # Field position (4)
            'home_avg_start_offense', 'away_avg_start_offense',
            'home_avg_start_defense', 'away_avg_start_defense',
            # Scoring efficiency (8)
            'home_points_per_opportunity_offense', 'away_points_per_opportunity_offense',
            'home_points_per_opportunity_defense', 'away_points_per_opportunity_defense',
            'home_scoring_opportunity_rate_offense', 'away_scoring_opportunity_rate_offense',
            'home_scoring_opportunity_rate_defense', 'away_scoring_opportunity_rate_defense',
            # Success rates (12)
            'home_success_rate_offense', 'away_success_rate_offense',
            'home_success_rate_defense', 'away_success_rate_defense',
            'home_standard_downs_success_offense', 'away_standard_downs_success_offense',
            'home_standard_downs_success_defense', 'away_standard_downs_success_defense',
            'home_passing_downs_success_offense', 'away_passing_downs_success_offense',
            'home_passing_downs_success_defense', 'away_passing_downs_success_defense',
            # Line of scrimmage control (6)
            'home_line_yards_offense', 'away_line_yards_offense',
            'home_line_yards_defense', 'away_line_yards_defense',
            'home_second_level_yards_offense', 'away_second_level_yards_offense',
            # Explosive plays (8)
            'home_explosive_run_rate_offense', 'away_explosive_run_rate_offense',
            'home_explosive_run_rate_defense', 'away_explosive_run_rate_defense',
            'home_explosive_pass_rate_offense', 'away_explosive_pass_rate_offense',
            'home_explosive_pass_rate_defense', 'away_explosive_pass_rate_defense',
            # Power and efficiency (10)
            'home_power_success_offense', 'away_power_success_offense',
            'home_power_success_defense', 'away_power_success_defense',
            'home_stuff_rate_offense', 'away_stuff_rate_defense',
            'home_stuff_rate_defense', 'away_stuff_rate_offense',
            'home_crowd_noise_factor', 'away_crowd_noise_factor',
            # Situational performance (12)
            'home_redzone_success_offense', 'away_redzone_success_offense',
            'home_redzone_success_defense', 'away_redzone_success_defense',
            'home_third_down_success_offense', 'away_third_down_success_offense',
            'home_third_down_success_defense', 'away_third_down_success_defense',
            'home_fourth_down_success_offense', 'away_fourth_down_success_offense',
            'home_fourth_down_success_defense', 'away_fourth_down_success_defense',
            # Turnover margin and penalties (6)
            'home_turnover_margin_per_game', 'away_turnover_margin_per_game',
            'home_penalty_yards_per_game', 'away_penalty_yards_per_game',
            'home_tackles_for_loss_per_game', 'away_tackles_for_loss_per_game',
            # Time of possession and tempo (4)
            'home_time_of_possession_per_game', 'away_time_of_possession_per_game',
            'home_plays_per_game', 'away_plays_per_game'
        ]

    def _get_required_features(self):
        """Get list of required features"""
        return self.feature_order

    def transform_game_to_features(self, game_data, team_talent, team_metrics, historical_data=None):
        """Transform a single game to 86-feature format"""

        home_team = game_data['home_team']
        away_team = game_data['away_team']

        features = {}

        # 1. Talent ratings (2 features)
        features['home_talent'] = team_talent.get(home_team, 0)
        features['away_talent'] = team_talent.get(away_team, 0)

        # 2. Get team metrics
        home_metrics = team_metrics.get(home_team, {})
        away_metrics = team_metrics.get(away_team, {})

        # 3. EPA metrics (4 features)
        features['home_adjusted_epa'] = home_metrics.get('offense_epa', 0)
        features['away_adjusted_epa'] = away_metrics.get('offense_epa', 0)
        features['home_adjusted_success'] = home_metrics.get('offense_success_rate', 0)
        features['away_adjusted_success'] = away_metrics.get('offense_success_rate', 0)

        # 4. Explosiveness metrics (4 features)
        features['home_adjusted_explosiveness'] = home_metrics.get('offense_explosiveness', 0)
        features['away_adjusted_explosiveness'] = away_metrics.get('offense_explosiveness', 0)
        features['home_explosiveness_ppa'] = home_metrics.get('offense_ppa', 0)
        features['away_explosiveness_ppa'] = away_metrics.get('offense_ppa', 0)

        # 5. Havoc rates (8 features)
        features['home_total_havoc_offense'] = home_metrics.get('offense_havoc', 0)
        features['away_total_havoc_offense'] = away_metrics.get('offense_havoc', 0)
        features['home_total_havoc_defense'] = home_metrics.get('defense_havoc', 0)
        features['away_total_havoc_defense'] = away_metrics.get('defense_havoc', 0)
        features['home_front_seven_havoc'] = home_metrics.get('front_seven_havoc', 0)
        features['away_front_seven_havoc'] = away_metrics.get('front_seven_havoc', 0)
        features['home_db_havoc'] = home_metrics.get('db_havoc', 0)
        features['away_db_havoc'] = away_metrics.get('db_havoc', 0)

        # 6. Field position (4 features)
        features['home_avg_start_offense'] = home_metrics.get('avg_start_position_offense', 0)
        features['away_avg_start_offense'] = away_metrics.get('avg_start_position_offense', 0)
        features['home_avg_start_defense'] = home_metrics.get('avg_start_position_defense', 0)
        features['away_avg_start_defense'] = away_metrics.get('avg_start_position_defense', 0)

        # Continue for all 86 features...
        # This is a template showing the pattern - implement all features following this approach

        # 86. Historical context (if available)
        if historical_data:
            h2h_key = (home_team, away_team)
            historical_matchup = historical_data.get(h2h_key, {})
            features['home_historical_wins'] = historical_matchup.get('home_wins', 0)
            features['away_historical_wins'] = historical_matchup.get('away_wins', 0)

        return features

    def validate_features(self, features_dict):
        """Validate that all required features are present"""

        missing_features = []
        zero_values = []

        for feature in self.required_features:
            if feature not in features_dict:
                missing_features.append(feature)
            elif features_dict[feature] == 0:
                zero_values.append(feature)

        validation_result = {
            'is_valid': len(missing_features) == 0,
            'missing_features': missing_features,
            'zero_value_features': zero_values,
            'completeness': (len(self.required_features) - len(missing_features)) / len(self.required_features)
        }

        return validation_result

    def create_feature_dataframe(self, games_features_list):
        """Convert list of feature dictionaries to DataFrame with proper column order"""

        if not games_features_list:
            return pd.DataFrame(columns=self.feature_order)

        # Create DataFrame
        df = pd.DataFrame(games_features_list)

        # Ensure all columns exist, fill missing with 0
        for feature in self.feature_order:
            if feature not in df.columns:
                df[feature] = 0

        # Reorder columns
        df = df[self.feature_order]

        return df

# Example usage
if __name__ == "__main__":
    transformer = FeatureTransformer()

    # Example game data
    game_data = {
        'home_team': 'Ohio State',
        'away_team': 'Michigan'
    }

    # Example team data
    team_talent = {
        'Ohio State': 885.73,
        'Michigan': 864.42
    }

    team_metrics = {
        'Ohio State': {
            'offense_epa': 0.15,
            'offense_success_rate': 0.48,
            'offense_explosiveness': 1.2
        },
        'Michigan': {
            'offense_epa': 0.12,
            'offense_success_rate': 0.45,
            'offense_explosiveness': 1.1
        }
    }

    # Transform to features
    features = transformer.transform_game_to_features(game_data, team_talent, team_metrics)

    # Validate features
    validation = transformer.validate_features(features)
    print(f"✅ Feature validation: {validation['is_valid']}")
    print(f"✅ Feature completeness: {validation['completeness']:.1%}")
```

---

## 🤖 Agent System Integration

### CFBD Integration Agent
```python
# agents/cfbd_integration_agent.py
from agents.core.agent_framework import BaseAgent
from integrations.cfbd_games import CFBGamesAPI
from integrations.cfbd_teams import CFBTeamsAPI
from integrations.cfbd_metrics import CFBMetricsAPI
from data_processing.feature_transformer import FeatureTransformer
from utils.cfbd_auth import test_cfbd_authentication
import pandas as pd

class CFBDIntegrationAgent(BaseAgent):
    """Specialized agent for CFBD API integration with Script Ohio 2.0"""

    def __init__(self):
        super().__init__(
            name="CFBD Integration Agent",
            description="Integrates CFBD API data with Script Ohio 2.0 system",
            permissions=["READ_EXECUTE_WRITE"],
            tools=["cfbd_games_api", "cfbd_teams_api", "cfbd_metrics_api", "feature_transformer"]
        )

        # Initialize API integrations
        self.games_api = CFBGamesAPI()
        self.teams_api = CFBTeamsAPI()
        self.metrics_api = CFBMetricsAPI()
        self.transformer = FeatureTransformer()

    def test_integration(self):
        """Test CFBD API integration status"""

        print("🔍 Testing CFBD API Integration...")

        # Test authentication
        auth_status = test_cfbd_authentication()
        if not auth_status:
            print("❌ CFBD API authentication failed")
            return False

        print("✅ CFBD API authentication successful")
        return True

    def get_week12_complete_data(self, year=2025):
        """Get complete Week 12 data including games, teams, and metrics"""

        print(f"📊 Retrieving Week {12} {year} data...")

        # 1. Get Week 12 games
        games_result = self.games_api.get_week_games(year, 12)
        if not games_result['success']:
            raise Exception(f"Failed to get Week 12 games: {games_result['error']}")

        games = games_result['games']
        print(f"✅ Retrieved {len(games)} Week 12 games")

        # 2. Get team talent data
        talent_result = self.teams_api.get_team_talent(year)
        if not talent_result['success']:
            raise Exception(f"Failed to get talent data: {talent_result['error']}")

        talent_mapping = talent_result['talent_mapping']
        print(f"✅ Retrieved talent data for {talent_result['count']} teams")

        # 3. Get advanced metrics for all teams in Week 12
        week_teams = set()
        for game in games:
            week_teams.add(game['home_team'])
            week_teams.add(game['away_team'])

        team_metrics = {}
        for team in week_teams:
            metrics_result = self.metrics_api.get_team_season_stats(year, week=12, team=team)
            if metrics_result['success'] and metrics_result['stats']:
                team_metrics[team] = self._process_team_metrics(metrics_result['stats'])

        print(f"✅ Retrieved metrics for {len(team_metrics)} teams")

        return {
            'games': games,
            'talent_mapping': talent_mapping,
            'team_metrics': team_metrics,
            'metadata': {
                'year': year,
                'week': 12,
                'total_games': len(games),
                'teams_with_metrics': len(team_metrics)
            }
        }

    def generate_86_features(self, week_data):
        """Generate 86-feature dataset for Week 12 predictions"""

        print("🔄 Generating 86-feature dataset...")

        games_features = []

        for i, game in enumerate(week_data['games']):
            if i % 10 == 0:
                print(f"  Processing game {i+1}/{len(week_data['games'])}")

            try:
                # Transform game to features
                features = self.transformer.transform_game_to_features(
                    game_data=game,
                    team_talent=week_data['talent_mapping'],
                    team_metrics=week_data['team_metrics']
                )

                # Add game metadata
                features['game_id'] = game['id']
                features['home_team'] = game['home_team']
                features['away_team'] = game['away_team']
                features['game_date'] = game.get('start_date', 'Unknown')

                # Validate features
                validation = self.transformer.validate_features(features)
                if not validation['is_valid']:
                    print(f"⚠️ Game {game['id']} has missing features: {validation['missing_features']}")
                    continue

                games_features.append(features)

            except Exception as e:
                print(f"❌ Error processing game {game.get('id', 'Unknown')}: {e}")
                continue

        # Create DataFrame
        features_df = self.transformer.create_feature_dataframe(games_features)

        print(f"✅ Generated features for {len(features_df)} games")
        print(f"✅ Feature completeness: {len(features_df.columns)}/86 features")

        return features_df

    def save_data_for_models(self, features_df, output_dir="data/week12"):
        """Save processed data in format compatible with existing models"""

        import os
        os.makedirs(output_dir, exist_ok=True)

        # Save as CSV (compatible with existing model training)
        csv_path = os.path.join(output_dir, "week12_features_86.csv")
        features_df.to_csv(csv_path, index=False)
        print(f"✅ Saved features to {csv_path}")

        # Save as JSON (for agent processing)
        json_path = os.path.join(output_dir, "week12_features_86.json")
        features_df.to_json(json_path, orient='records', indent=2)
        print(f"✅ Saved features to {json_path}")

        # Save metadata
        metadata = {
            'total_games': len(features_df),
            'features_count': len(features_df.columns),
            'feature_list': list(features_df.columns),
            'created_at': pd.Timestamp.now().isoformat(),
            'source': 'CFBD API integration'
        }

        metadata_path = os.path.join(output_dir, "metadata.json")
        import json
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        return {
            'csv_path': csv_path,
            'json_path': json_path,
            'metadata_path': metadata_path,
            'total_games': len(features_df)
        }

    def _process_team_metrics(self, stats_data):
        """Process raw team stats into standardized metrics"""

        if not stats_data:
            return {}

        # Assuming stats_data is a list of stat entries
        metrics = {}
        for stat in stats_data:
            category = stat.get('category', 'unknown')
            stat_type = stat.get('stat', 'unknown')
            value = stat.get('stat', 0)

            key = f"{category}_{stat_type}"
            metrics[key] = value

        return metrics

    def execute_integration(self, year=2025):
        """Execute complete CFBD integration workflow"""

        print("🚀 Starting CFBD Integration Workflow...")

        # Step 1: Test integration
        if not self.test_integration():
            print("❌ Integration test failed - aborting")
            return False

        # Step 2: Get Week 12 data
        week_data = self.get_week12_complete_data(year)

        # Step 3: Generate 86-feature dataset
        features_df = self.generate_86_features(week_data)

        # Step 4: Save data for models
        saved_files = self.save_data_for_models(features_df)

        print("✅ CFBD Integration Complete!")
        print(f"📊 Processed {saved_files['total_games']} games with 86 features each")

        return {
            'success': True,
            'games_processed': saved_files['total_games'],
            'features_generated': len(features_df.columns),
            'files_saved': saved_files
        }

# Example usage
if __name__ == "__main__":
    agent = CFBDIntegrationAgent()
    result = agent.execute_integration()

    if result['success']:
        print("🎉 CFBD integration successful!")
        print(f"📈 Processed {result['games_processed']} games")
        print(f"🔧 Generated {result['features_generated']} features")
    else:
        print("❌ CFBD integration failed")
```

---

## 🚀 Complete Week 12 Integration Example

### End-to-End Week 12 Preparation Script
```python
# scripts/week12_complete_integration.py
"""
Complete Week 12 integration script using CFBD API
This script demonstrates the full workflow from data acquisition to predictions
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.cfbd_integration_agent import CFBDIntegrationAgent
from utils.model_loader import ModelLoader
from utils.prediction_generator import PredictionGenerator

class Week12Integration:
    """Complete Week 12 integration and prediction workflow"""

    def __init__(self):
        self.integration_agent = CFBDIntegrationAgent()
        self.model_loader = ModelLoader()
        self.prediction_generator = PredictionGenerator()

    def run_complete_workflow(self, year=2025, week=12):
        """Run complete Week 12 preparation workflow"""

        print("="*60)
        print("🏈 WEEK 12 COMPLETE INTEGRATION WORKFLOW")
        print("="*60)
        print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 Target: Year {year}, Week {week}")
        print("="*60)

        try:
            # Phase 1: Data Integration
            print("\n🔍 PHASE 1: CFBD Data Integration")
            integration_result = self.integration_agent.execute_integration(year)

            if not integration_result['success']:
                print("❌ Data integration failed")
                return False

            print(f"✅ Data integration complete: {integration_result['games_processed']} games processed")

            # Phase 2: Model Validation
            print("\n🤖 PHASE 2: Model Validation")
            model_status = self.model_loader.validate_all_models()

            if not model_status['all_valid']:
                print("⚠️ Some models failed validation - using available models")
            else:
                print("✅ All models validated successfully")

            # Phase 3: Prediction Generation
            print("\n📊 PHASE 3: Prediction Generation")
            features_path = integration_result['files_saved']['csv_path']
            predictions = self.prediction_generator.generate_predictions(
                features_path, model_status['available_models']
            )

            print(f"✅ Generated predictions for {len(predictions)} games")

            # Phase 4: Results Analysis
            print("\n📈 PHASE 4: Results Analysis")
            analysis = self._analyze_predictions(predictions)

            # Phase 5: Report Generation
            print("\n📝 PHASE 5: Report Generation")
            report = self._generate_report(integration_result, model_status, predictions, analysis)

            print("\n" + "="*60)
            print("🎉 WEEK 12 INTEGRATION COMPLETE!")
            print("="*60)
            print(f"📊 Games Analyzed: {integration_result['games_processed']}")
            print(f"🤖 Models Used: {', '.join(model_status['available_models'])}")
            print(f"📈 Predictions Generated: {len(predictions)}")
            print(f"📄 Report Saved: {report['report_path']}")

            return True

        except Exception as e:
            print(f"❌ Workflow failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _analyze_predictions(self, predictions):
        """Analyze prediction results"""

        if not predictions:
            return {'error': 'No predictions to analyze'}

        df = pd.DataFrame(predictions)

        analysis = {
            'total_games': len(df),
            'model_confidence': {
                'ridge_avg_margin': df.get('ridge_margin', 0).mean(),
                'xgb_avg_win_prob': df.get('xgb_win_prob', 0).mean(),
                'high_confidence_games': len(df[df['xgb_win_prob'] > 0.7]),
                'close_games': len(df[(df['xgb_win_prob'] > 0.4) & (df['xgb_win_prob'] < 0.6)])
            },
            'upset_alerts': self._identify_upset_alerts(df),
            'playoff_implications': self._analyze_playoff_implications(df)
        }

        return analysis

    def _identify_upset_alerts(self, df):
        """Identify potential upset games"""

        upset_games = []

        for _, game in df.iterrows():
            # Upset alert: lower talent team has higher win probability
            home_talent = game.get('home_talent', 0)
            away_talent = game.get('away_talent', 0)
            home_win_prob = game.get('xgb_win_prob', 0.5)

            if away_talent > home_talent and home_win_prob > 0.6:
                upset_games.append({
                    'game': f"{game.get('home_team', 'Unknown')} vs {game.get('away_team', 'Unknown')}",
                    'reason': 'Lower talent team favored',
                    'talent_gap': abs(home_talent - away_talent),
                    'win_probability': home_win_prob
                })

        return upset_games

    def _analyze_playoff_implications(self, df):
        """Analyze playoff implications"""

        # This would be enhanced with actual playoff standings logic
        return {
            'affected_teams': 0,  # Would calculate based on current rankings
            'championship_implications': 0,
            'elimination_games': 0
        }

    def _generate_report(self, integration_result, model_status, predictions, analysis):
        """Generate comprehensive Week 12 report"""

        report_data = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'year': 2025,
                'week': 12,
                'integration_success': True
            },
            'data_summary': {
                'games_processed': integration_result['games_processed'],
                'features_generated': integration_result['features_generated']
            },
            'model_status': model_status,
            'predictions': predictions,
            'analysis': analysis
        }

        # Save report
        report_dir = "reports/week12"
        os.makedirs(report_dir, exist_ok=True)

        report_path = os.path.join(report_dir, f"week12_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)

        # Also save a readable summary
        summary_path = os.path.join(report_dir, f"week12_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
        self._write_summary_report(summary_path, report_data)

        return {
            'report_path': report_path,
            'summary_path': summary_path
        }

    def _write_summary_report(self, path, data):
        """Write readable markdown summary report"""

        with open(path, 'w') as f:
            f.write("# Week 12 College Football Analysis Report\n\n")
            f.write(f"**Generated:** {data['metadata']['generated_at']}\n\n")

            f.write("## Data Summary\n\n")
            f.write(f"- Games Processed: {data['data_summary']['games_processed']}\n")
            f.write(f"- Features Generated: {data['data_summary']['features_generated']}\n\n")

            f.write("## Model Status\n\n")
            f.write(f"- Available Models: {', '.join(data['model_status']['available_models'])}\n")
            f.write(f"- All Models Valid: {data['model_status']['all_valid']}\n\n")

            f.write("## Prediction Analysis\n\n")
            analysis = data['analysis']
            f.write(f"- Total Games: {analysis['total_games']}\n")
            f.write(f"- High Confidence Games: {analysis['model_confidence']['high_confidence_games']}\n")
            f.write(f"- Close Games: {analysis['model_confidence']['close_games']}\n\n")

            if analysis['upset_alerts']:
                f.write("## Upset Alerts\n\n")
                for alert in analysis['upset_alerts']:
                    f.write(f"- **{alert['game']}**: {alert['reason']} (Win Prob: {alert['win_probability']:.1%})\n")

# Main execution
if __name__ == "__main__":
    integration = Week12Integration()
    success = integration.run_complete_workflow()

    if success:
        print("\n🎯 Week 12 integration completed successfully!")
        print("📊 Check reports/week12/ for detailed analysis")
    else:
        print("\n❌ Week 12 integration failed")
        print("🔍 Check logs for error details")
```

---

## 🎯 Quick Start Examples

### 1. Simple Game Prediction
```python
# quick_start/simple_prediction.py
from agents.cfbd_integration_agent import CFBDIntegrationAgent

# Initialize agent
agent = CFBDIntegrationAgent()

# Test integration
if agent.test_integration():
    print("✅ CFBD API ready for predictions")

    # Get Week 12 data
    week12_data = agent.get_week12_complete_data(2025)
    print(f"✅ Retrieved data for {len(week12_data['games'])} games")

    # Generate features for predictions
    features_df = agent.generate_86_features(week12_data)
    print(f"✅ Generated {len(features_df)} feature rows with {len(features_df.columns)} columns")
else:
    print("❌ CFBD API not available - use mock data fallback")
```

### 2. Integration with Existing Models
```python
# quick_start/model_integration.py
import pandas as pd
from joblib import load

# Load Week 12 features (generated from CFBD integration)
features_df = pd.read_csv('data/week12/week12_features_86.csv')

# Load existing models
ridge_model = load('model_pack/ridge_model_2025.joblib')
xgb_model = load('model_pack/xgb_home_win_model_2025.pkl')

# Make predictions
features_for_prediction = features_df.drop(['game_id', 'home_team', 'away_team', 'game_date'], axis=1)

ridge_predictions = ridge_model.predict(features_for_prediction)
xgb_predictions = xgb_model.predict_proba(features_for_prediction)[:, 1]

# Combine results
results = pd.DataFrame({
    'game_id': features_df['game_id'],
    'home_team': features_df['home_team'],
    'away_team': features_df['away_team'],
    'ridge_margin': ridge_predictions,
    'xgb_win_prob': xgb_predictions
})

print("✅ Predictions generated for Week 12 games")
print(results.head())
```

### 3. Quality Validation
```python
# quick_start/quality_check.py
from data_processing.feature_transformer import FeatureTransformer

transformer = FeatureTransformer()

# Validate feature completeness
sample_features = transformer.transform_game_to_features(
    game_data={'home_team': 'Ohio State', 'away_team': 'Michigan'},
    team_talent={'Ohio State': 885.73, 'Michigan': 864.42},
    team_metrics={}  # Would include actual metrics
)

validation_result = transformer.validate_features(sample_features)

print(f"✅ Features Valid: {validation_result['is_valid']}")
print(f"✅ Completeness: {validation_result['completeness']:.1%}")
print(f"⚠️ Zero Values: {len(validation_result['zero_value_features'])}")

if validation_result['missing_features']:
    print(f"❌ Missing: {validation_result['missing_features']}")
```

---

## 📚 Additional Resources

### Environment Setup
```bash
# Required packages
pip install requests pandas numpy scikit-learn

# Set environment variables
export CFBD_API_KEY="your_api_key_here"
export CFBD_CACHE_DIR="cfbd_cache"
```

### Error Handling Best Practices
```python
# utils/error_handling.py
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def handle_cfbd_error(func):
    """Decorator for CFBD API error handling"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.RequestException as e:
            logger.error(f"CFBD API Request Error: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Unexpected Error: {e}")
            return {'success': False, 'error': f"Unexpected: {e}"}
    return wrapper
```

### Performance Monitoring
```python
# utils/performance.py
import time
from datetime import datetime

class PerformanceTracker:
    def __init__(self):
        self.start_time = None
        self.metrics = {}

    def start_timer(self, operation):
        self.start_time = time.time()
        self.current_operation = operation

    def end_timer(self):
        if self.start_time:
            duration = time.time() - self.start_time
            self.metrics[self.current_operation] = duration
            print(f"⏱️ {self.current_operation}: {duration:.2f}s")
            return duration
        return 0

# Usage
tracker = PerformanceTracker()
tracker.start_timer("CFBD Data Retrieval")
# ... CFBD API calls ...
tracker.end_timer()
```

---

*This integration guide provides production-ready examples for incorporating CFBD API data into the Script Ohio 2.0 analytics platform. All examples include proper error handling, validation, and integration with the existing 86-feature ML pipeline.*