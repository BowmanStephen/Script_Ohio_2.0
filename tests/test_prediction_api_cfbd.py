"""
Tests for CFBD BFF endpoints in prediction_api.py
"""
import pytest
import json
from unittest.mock import Mock, patch
import os
os.environ['FLASK_TESTING'] = 'true'
from api.prediction_api import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_check(client):
    """Test health check endpoint"""
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'

def test_cfbd_games_endpoint(client):
    """Test CFBD games proxy endpoint"""
    with patch('src.cfbd_client.unified_client.UnifiedCFBDClient') as MockClient:
        # Setup mock
        mock_instance = MockClient.return_value
        mock_instance.get_games.return_value = [{'id': 1, 'home_team': 'Ohio State'}]
        
        # Test request
        response = client.get('/api/cfbd/games?year=2025&week=1')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert len(data['data']) == 1
        assert data['data'][0]['home_team'] == 'Ohio State'
        
        # Verify client call
        mock_instance.get_games.assert_called_with(year=2025, week=1, season_type='regular', team=None)

def test_cfbd_scoreboard_endpoint_rest(client):
    """Test scoreboard endpoint using REST fallback"""
    with patch('src.cfbd_client.unified_client.UnifiedCFBDClient') as MockClient:
        mock_instance = MockClient.return_value
        # Mock GraphQL returning None to force REST
        mock_instance.get_scoreboard_graphql.return_value = None
        mock_instance.get_games.return_value = [{'id': 1, 'home_team': 'Ohio State'}]
        
        response = client.get('/api/cfbd/scoreboard?year=2025&week=1')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['source'] == 'rest'
        assert len(data['data']) == 1

def test_cfbd_media_endpoint(client):
    """Test media endpoint"""
    with patch('src.cfbd_client.unified_client.UnifiedCFBDClient') as MockClient:
        mock_instance = MockClient.return_value
        mock_instance.get_game_media.return_value = [{'outlet': 'ESPN'}]
        
        response = client.get('/api/cfbd/media?year=2025&week=1')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['data'][0]['outlet'] == 'ESPN'

def test_cfbd_calendar_endpoint(client):
    """Test calendar endpoint"""
    with patch('src.cfbd_client.unified_client.UnifiedCFBDClient') as MockClient:
        mock_instance = MockClient.return_value
        mock_instance.get_calendar.return_value = [{'week': 1}]
        
        response = client.get('/api/cfbd/calendar?year=2025')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['data'][0]['week'] == 1

def test_cfbd_box_score_endpoint(client):
    """Test box score endpoint"""
    with patch('src.cfbd_client.unified_client.UnifiedCFBDClient') as MockClient:
        mock_instance = MockClient.return_value
        mock_instance.get_box_score.return_value = {'teams': {}}
        
        response = client.get('/api/cfbd/box-score?game_id=123')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'teams' in data['data']

def test_cfbd_matchup_endpoint(client):
    """Test matchup endpoint"""
    with patch('src.cfbd_client.unified_client.UnifiedCFBDClient') as MockClient:
        mock_instance = MockClient.return_value
        mock_instance.get_team_matchup.return_value = {'team1': 'OSU', 'team2': 'UM'}
        
        response = client.get('/api/cfbd/matchup?team1=OSU&team2=UM')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['data']['team1'] == 'OSU'

def test_cfbd_recruiting_endpoint(client):
    """Test recruiting endpoint"""
    with patch('src.cfbd_client.unified_client.UnifiedCFBDClient') as MockClient:
        mock_instance = MockClient.return_value
        mock_instance.get_recruiting_graphql.return_value = None
        mock_instance.get_recruiting.return_value = [{'name': 'Player'}]
        
        response = client.get('/api/cfbd/recruiting?year=2025&team=OSU')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['data'][0]['name'] == 'Player'
