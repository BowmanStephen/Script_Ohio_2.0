#!/usr/bin/env python3
"""
Simple test for the bowls prediction script.
"""

import json
import sys
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def test_bowls_prediction_output():
    """Test that the bowls prediction script produces valid JSON output."""
    output_path = PROJECT_ROOT / "predictions" / "bowls_2025_predictions.json"
    
    if not output_path.exists():
        print("❌ Output file does not exist")
        return False
    
    try:
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        # Check required fields
        required_fields = ["generated_at", "model", "season", "games"]
        for field in required_fields:
            if field not in data:
                print(f"❌ Missing required field: {field}")
                return False
        
        # Check that season is 2025
        if data["season"] != 2025:
            print(f"❌ Wrong season: {data['season']}")
            return False
        
        # Check that we have games
        if not data["games"]:
            print("❌ No games in output")
            return False
        
        # Check game structure
        required_game_fields = ["home_team", "away_team", "home_win_prob", "predicted_margin"]
        for i, game in enumerate(data["games"][:3]):  # Check first 3 games
            for field in required_game_fields:
                if field not in game:
                    print(f"❌ Game {i} missing field: {field}")
                    return False
            
            # Check probability range
            prob = game["home_win_prob"]
            if not (0.0 <= prob <= 1.0):
                print(f"❌ Game {i} invalid probability: {prob}")
                return False
        
        print(f"✅ Output validation passed")
        print(f"   Model: {data['model']}")
        print(f"   Season: {data['season']}")
        print(f"   Games: {len(data['games'])}")
        
        # Show sample predictions
        print("   Sample predictions:")
        for i, game in enumerate(data["games"][:3]):
            margin_dir = "wins" if game["predicted_margin"] > 0 else "loses"
            print(f"     {i+1}. {game['away_team']} @ {game['home_team']}: "
                  f"{game['home_win_prob']:.1%} home win, "
                  f"{game['home_team']} {margin_dir} by {abs(game['predicted_margin']):.1f}")
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading output: {e}")
        return False


if __name__ == "__main__":
    success = test_bowls_prediction_output()
    sys.exit(0 if success else 1)
