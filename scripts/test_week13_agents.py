#!/usr/bin/env python3
"""Quick test script for Week 13 agents"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.weekly_matchup_analysis_agent import WeeklyMatchupAnalysisAgent
from agents.weekly_prediction_generation_agent import WeeklyPredictionGenerationAgent
from agents.weekly_model_validation_agent import WeeklyModelValidationAgent
from agents.weekly_analysis_orchestrator import WeeklyAnalysisOrchestrator

def test_week13_agents():
    """Test that all Week 13 agents can be instantiated"""
    print("Testing Week 13 agent instantiation...")
    
    try:
        # Test matchup agent
        matchup_agent = WeeklyMatchupAnalysisAgent(week=13, season=2025)
        print("✅ WeeklyMatchupAnalysisAgent instantiated")
        
        # Test prediction agent
        prediction_agent = WeeklyPredictionGenerationAgent(week=13, season=2025)
        print("✅ WeeklyPredictionGenerationAgent instantiated")
        
        # Test validation agent
        validation_agent = WeeklyModelValidationAgent(week=13, season=2025)
        print("✅ WeeklyModelValidationAgent instantiated")
        
        # Test orchestrator
        orchestrator = WeeklyAnalysisOrchestrator(week=13, season=2025)
        print("✅ WeeklyAnalysisOrchestrator instantiated")
        
        print("\n✅ All Week 13 agents instantiated successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_week13_agents()
