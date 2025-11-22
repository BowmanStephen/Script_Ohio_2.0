#!/usr/bin/env python3
"""
Test script for simplified agent system
"""

import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents.simplified import SimplifiedOrchestrator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    print("=" * 60)
    print("Simplified Agent System Test")
    print("=" * 60)
    
    orchestrator = SimplifiedOrchestrator()
    
    # Test 1: Prediction
    print("\n1. Testing Prediction:")
    print("-" * 60)
    result = orchestrator.process_request(
        "Predict Ohio State vs Michigan",
        home_team="Ohio State",
        away_team="Michigan"
    )
    
    if 'error' not in result:
        print(f"✅ Matchup: {result['matchup']}")
        print(f"✅ Ensemble Prediction: {result['models']['ensemble']['home_win_probability']:.1%} home win")
        print(f"✅ Predicted Margin: {result['models']['ensemble']['predicted_margin']:.1f} points")
        print(f"✅ Recommendation: {result['recommendation']}")
        print(f"\nModel Breakdown:")
        for model_name, pred in result['models'].items():
            if 'error' not in pred:
                print(f"  • {model_name}: {pred.get('home_win_probability', 0):.1%} home win")
        print(f"\nExplanation:\n{result['explanation']}")
    else:
        print(f"❌ Error: {result['error']}")
    
    # Test 2: Learning
    print("\n2. Testing Learning:")
    print("-" * 60)
    result = orchestrator.process_request("Explain EPA")
    if 'error' not in result:
        print(f"✅ Recommended Notebooks: {result.get('recommended_notebooks', [])}")
        print(f"✅ Explanation: {result.get('explanation', '')}")
    else:
        print(f"❌ Error: {result['error']}")
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
