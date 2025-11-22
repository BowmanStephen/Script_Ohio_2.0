import json
import os
from pathlib import Path

def prepare_simulator_data():
    # Define paths
    repo_root = Path(__file__).parent.parent
    input_path = repo_root / 'analysis/week13/week13_unified_data.json'
    output_dir = repo_root / 'web_app/src/data'
    output_path = output_dir / 'week13_data.json'

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load input data
    if not input_path.exists():
        print(f"Error: Input file not found at {input_path}")
        return

    with open(input_path, 'r') as f:
        data = json.load(f)

    # Transform data
    simulator_games = []
    for game_entry in data.get('games', []):
        info = game_entry.get('game_info', {})
        
        # Extract required fields
        # We map directly from game_info as it seems to match the simulator's expectations
        sim_game = {
            "id": info.get("id"),
            "home_team": info.get("home_team"),
            "away_team": info.get("away_team"),
            "spread": info.get("spread"),
            "home_elo": info.get("home_elo"),
            "away_elo": info.get("away_elo"),
            "home_talent": info.get("home_talent"),
            "away_talent": info.get("away_talent"),
            "home_adjusted_epa": info.get("home_adjusted_epa"),
            "away_adjusted_epa": info.get("away_adjusted_epa"),
            "home_adjusted_success": info.get("home_adjusted_success"),
            "away_adjusted_success": info.get("away_adjusted_success"),
            "home_adjusted_explosiveness": info.get("home_adjusted_explosiveness"),
            "away_adjusted_explosiveness": info.get("away_adjusted_explosiveness"),
            "home_points_per_opportunity_offense": info.get("home_points_per_opportunity_offense"),
            "away_points_per_opportunity_offense": info.get("away_points_per_opportunity_offense")
        }
        
        # Handle potential None values for critical numeric fields by defaulting to 0 or reasonable defaults
        # This prevents the simulator from crashing on missing data
        for key, value in sim_game.items():
            if value is None and key not in ['home_team', 'away_team']:
                sim_game[key] = 0.0
                
        simulator_games.append(sim_game)

    # Save to output file
    with open(output_path, 'w') as f:
        json.dump(simulator_games, f, indent=2)

    print(f"Successfully generated {len(simulator_games)} games for the simulator at {output_path}")

if __name__ == "__main__":
    prepare_simulator_data()
