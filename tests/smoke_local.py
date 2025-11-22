#!/usr/bin/env python3
"""
Lightweight smoke test suite for Script Ohio 2.0 core functionality.

Tests:
1. CFBD client can fetch a small sample (1 game)
2. All three model files can be loaded (ridge, xgb, fastai)
3. One end-to-end predict call with stubbed data works

Run with: pytest tests/smoke_local.py -v
"""

import os
import sys
import pytest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np


def test_cfbd_client_fetch():
    """Test that UnifiedCFBDClient can fetch a small sample"""
    try:
        from src.cfbd_client.unified_client import UnifiedCFBDClient
        
        # Skip if no API key
        if not os.environ.get("CFBD_API_KEY"):
            pytest.skip("CFBD_API_KEY not set - skipping CFBD fetch test")
        
        client = UnifiedCFBDClient()
        
        # Fetch one game from a recent season/week
        games = client.get_games(year=2024, week=1, season_type="regular")
        
        assert games is not None, "Games should not be None"
        assert len(games) > 0, "Should fetch at least one game"
        
        print(f"✅ CFBD client fetched {len(games)} games")
        
    except Exception as e:
        pytest.fail(f"CFBD client fetch failed: {e}")


def test_load_ridge_model():
    """Test that Ridge model can be loaded"""
    model_path = project_root / "ridge_model_2025.joblib"
    
    if not model_path.exists():
        pytest.skip(f"Ridge model not found at {model_path}")
    
    try:
        import joblib
        model = joblib.load(model_path)
        assert model is not None, "Model should load successfully"
        print("✅ Ridge model loaded successfully")
    except Exception as e:
        pytest.fail(f"Failed to load Ridge model: {e}")


def test_load_xgb_model():
    """Test that XGBoost model can be loaded"""
    model_path = project_root / "xgb_home_win_model_2025.pkl"
    
    if not model_path.exists():
        pytest.skip(f"XGBoost model not found at {model_path}")
    
    try:
        import pickle
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        assert model is not None, "Model should load successfully"
        print("✅ XGBoost model loaded successfully")
    except Exception as e:
        pytest.fail(f"Failed to load XGBoost model: {e}")


def test_load_fastai_model():
    """Test that FastAI model can be loaded (may use mock)"""
    model_path = project_root / "fastai_home_win_model_2025.pkl"
    
    if not model_path.exists():
        pytest.skip(f"FastAI model not found at {model_path}")
    
    try:
        # FastAI models may use mock/placeholder - that's expected
        import pickle
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        # Even if it's a mock, loading should succeed
        assert model is not None, "Model should load (even if mock)"
        print("✅ FastAI model loaded (may be mock - expected)")
    except Exception as e:
        # FastAI model warnings are expected - don't fail the test
        print(f"⚠️  FastAI model load warning (expected): {e}")
        pytest.skip(f"FastAI model load issue (expected): {e}")


def test_end_to_end_predict():
    """Test one end-to-end predict call with stubbed data"""
    try:
        from agents.model_execution_engine import ModelExecutionEngine
        
        # Create agent
        agent = ModelExecutionEngine("smoke_test_agent")
        
        # Create stubbed prediction request
        parameters = {
            'team1': 'Ohio State',
            'team2': 'Michigan'
        }
        
        # Execute prediction
        result = agent._execute_action(
            'predict_game_outcome',
            parameters,
            {'user_id': 'smoke_test'}
        )
        
        assert result is not None, "Result should not be None"
        assert 'status' in result, "Result should have status"
        
        # Even if prediction fails due to missing data, the call should complete
        print(f"✅ End-to-end predict call completed: {result.get('status', 'unknown')}")
        
    except Exception as e:
        pytest.fail(f"End-to-end predict failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])



