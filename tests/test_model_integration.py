"""
Test suite for Random Forest model integration.
"""
import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from src.models.execution.engine import ModelExecutionEngine

@pytest.fixture
def model_engine():
    """Initialize model execution engine."""
    return ModelExecutionEngine("test_agent")

def test_rf_model_prediction(model_engine):
    """Test Random Forest model prediction."""
    # Verify model is loaded
    assert 'random_forest_model_2025' in model_engine.models
    
    # Create test request
    # Use some reasonable dummy data
    params = {
        'home_team': 'Ohio State',
        'away_team': 'Michigan',
        'model_type': 'random_forest_model_2025',
        'features': {
            'home_adjusted_success': 0.5,
            'home_adjusted_success_allowed': 0.4,
            'away_adjusted_success': 0.45,
            'away_adjusted_success_allowed': 0.45,
            'home_adjusted_rushing_epa': 0.2,
            'home_adjusted_rushing_epa_allowed': -0.1,
            'away_adjusted_rushing_epa': 0.1,
            'away_adjusted_rushing_epa_allowed': 0.0,
            'home_adjusted_passing_epa': 0.3,
            'home_adjusted_passing_epa_allowed': -0.2,
            'away_adjusted_passing_epa': 0.2,
            'away_adjusted_passing_epa_allowed': 0.1
        }
    }
    
    result = model_engine._predict_game_outcome(params, {})
    
    assert result['success'] is True
    prediction = result['prediction']
    
    assert 'predicted_margin' in prediction
    assert isinstance(prediction['predicted_margin'], float)
    
    # Check if margin is reasonable (-100 to 100)
    margin = prediction['predicted_margin']
    assert -100 < margin < 100
    
    # Check implied points (not strictly in output format of ModelExecutionEngine yet, 
    # but we can check if we returned them in 'prediction' dict if we modified it?
    # Currently _predict_game_outcome formats it.
    # I didn't modify _predict_game_outcome to include home/away points explicitly in the top level result
    # except deriving them? No, it derives margin.
    # But my RandomForestInterface.predict returns 'home_points', 'away_points'.
    # Does _predict_game_outcome keep extra keys?
    # Line 786: formatted_prediction = { ... 'predicted_margin': ... }
    # It creates a new dict. So home_points/away_points are lost unless I update ModelExecutionEngine.
    # But margin is the key output.
    
    # If I want to validate home_points > 0, I need access to them.
    # But margin validation is sufficient for now given constraints.

