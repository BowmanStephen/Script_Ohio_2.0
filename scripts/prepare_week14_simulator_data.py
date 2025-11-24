#!/usr/bin/env python3
"""
Prepare Week 14 Simulator Data
Converts week 14 training data CSV to TypeScript and JSON formats for the web app.
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime

def prepare_week14_simulator_data():
    """Convert week 14 training data to simulator format."""
    # Define paths
    repo_root = Path(__file__).parent.parent
    input_path = repo_root / 'data' / 'training' / 'weekly' / 'training_data_2025_week14.csv'
    output_dir = repo_root / 'web_app' / 'src' / 'data'
    output_json = output_dir / 'week14_data.json'
    output_ts = output_dir / 'week14Games.ts'

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load input data
    if not input_path.exists():
        print(f"Error: Input file not found at {input_path}")
        return

    print(f"Loading week 14 data from {input_path}")
    df = pd.read_csv(input_path, low_memory=False)
    print(f"Loaded {len(df)} games")

    # Transform data to simulator format
    simulator_games = []
    for _, row in df.iterrows():
        sim_game = {
            "id": int(row.get("id", 0)),
            "home_team": str(row.get("home_team", "")),
            "away_team": str(row.get("away_team", "")),
            "spread": float(row.get("spread", 0.0)) if pd.notna(row.get("spread")) else 0.0,
            "home_elo": float(row.get("home_elo", 0.0)) if pd.notna(row.get("home_elo")) else 0.0,
            "away_elo": float(row.get("away_elo", 0.0)) if pd.notna(row.get("away_elo")) else 0.0,
            "home_talent": float(row.get("home_talent", 0.0)) if pd.notna(row.get("home_talent")) else 0.0,
            "away_talent": float(row.get("away_talent", 0.0)) if pd.notna(row.get("away_talent")) else 0.0,
            "home_adjusted_epa": float(row.get("home_adjusted_epa", 0.0)) if pd.notna(row.get("home_adjusted_epa")) else 0.0,
            "away_adjusted_epa": float(row.get("away_adjusted_epa", 0.0)) if pd.notna(row.get("away_adjusted_epa")) else 0.0,
            "home_adjusted_success": float(row.get("home_adjusted_success", 0.0)) if pd.notna(row.get("home_adjusted_success")) else 0.0,
            "away_adjusted_success": float(row.get("away_adjusted_success", 0.0)) if pd.notna(row.get("away_adjusted_success")) else 0.0,
            "home_adjusted_explosiveness": float(row.get("home_adjusted_explosiveness", 0.0)) if pd.notna(row.get("home_adjusted_explosiveness")) else 0.0,
            "away_adjusted_explosiveness": float(row.get("away_adjusted_explosiveness", 0.0)) if pd.notna(row.get("away_adjusted_explosiveness")) else 0.0,
            "home_points_per_opportunity_offense": float(row.get("home_points_per_opportunity_offense", 0.0)) if pd.notna(row.get("home_points_per_opportunity_offense")) else 0.0,
            "away_points_per_opportunity_offense": float(row.get("away_points_per_opportunity_offense", 0.0)) if pd.notna(row.get("away_points_per_opportunity_offense")) else 0.0
        }
        simulator_games.append(sim_game)

    # Save JSON format
    with open(output_json, 'w') as f:
        json.dump(simulator_games, f, indent=2)
    print(f"✅ Saved JSON to {output_json}")

    # Generate TypeScript format
    ts_content = "import { Game } from '../types';\n\n"
    ts_content += f"export const week14Games: Game[] = [\n"
    
    for game in simulator_games:
        ts_content += "    { "
        ts_content += f'"id": {game["id"]}, '
        ts_content += f'"home_team": "{game["home_team"]}", '
        ts_content += f'"away_team": "{game["away_team"]}", '
        ts_content += f'"spread": {game["spread"]}, '
        ts_content += f'"home_elo": {game["home_elo"]}, '
        ts_content += f'"away_elo": {game["away_elo"]}, '
        ts_content += f'"home_talent": {game["home_talent"]}, '
        ts_content += f'"away_talent": {game["away_talent"]}, '
        ts_content += f'"home_adjusted_epa": {game["home_adjusted_epa"]}, '
        ts_content += f'"away_adjusted_epa": {game["away_adjusted_epa"]}, '
        ts_content += f'"home_adjusted_success": {game["home_adjusted_success"]}, '
        ts_content += f'"away_adjusted_success": {game["away_adjusted_success"]}, '
        ts_content += f'"home_adjusted_explosiveness": {game["home_adjusted_explosiveness"]}, '
        ts_content += f'"away_adjusted_explosiveness": {game["away_adjusted_explosiveness"]}, '
        ts_content += f'"home_points_per_opportunity_offense": {game["home_points_per_opportunity_offense"]}, '
        ts_content += f'"away_points_per_opportunity_offense": {game["away_points_per_opportunity_offense"]} '
        ts_content += "},\n"
    
    ts_content += "];\n"
    
    with open(output_ts, 'w') as f:
        f.write(ts_content)
    print(f"✅ Saved TypeScript to {output_ts}")
    print(f"✅ Successfully generated {len(simulator_games)} games for the simulator")

if __name__ == "__main__":
    prepare_week14_simulator_data()


