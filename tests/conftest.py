#!/usr/bin/env python3
"""
pytest configuration for Script Ohio 2.0 testing

This module provides common configuration and fixtures for the test suite.
"""

import os
import sys
import pytest
import tempfile
import shutil
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set testing environment variable
os.environ['TESTING'] = 'true'

# Set default CFBD_API_KEY for tests (tests can override with monkeypatch.delenv())
# This prevents UnifiedCFBDClient and CFBDGraphQLClient from raising
# ValueError due to missing API key during initialization.
if 'CFBD_API_KEY' not in os.environ:
    os.environ['CFBD_API_KEY'] = 'test_api_key'

@pytest.fixture(scope="session")
def test_data_dir():
    """Provide test data directory"""
    return project_root / "tests" / "fixtures"

@pytest.fixture
def temp_workspace():
    """Provide a temporary workspace for testing"""
    temp_dir = tempfile.mkdtemp()
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture
def sample_analytics_request():
    """Sample analytics request for testing"""
    from agents.analytics_orchestrator import AnalyticsRequest
    import uuid

    return AnalyticsRequest(
        request_id=str(uuid.uuid4()),
        user_id="test_user_001",
        query="Analyze team performance metrics",
        query_type="analysis",
        parameters={"teams": ["Ohio State", "Michigan"]},
        context_hints={"skill_level": "intermediate"}
    )

@pytest.fixture
def sample_user_context():
    """Sample user context for testing"""
    return {
        "detected_role": "analyst",
        "skill_level": "intermediate",
        "preferences": {"focus_areas": ["efficiency", "predictions"]}
    }
