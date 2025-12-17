#!/usr/bin/env python3
"""
Fallback bowls 2025 prediction script that outputs JSON.

This script:
1. Uses existing postseason data (no CFBD API required)
2. Computes simple predictions using Massey ratings  
3. Outputs JSON to predictions/bowls_2025_predictions.json

This version works without CFBD API key by using existing data.
"""

import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

# Add project root to Python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from src.ratings.massey_ratings import MasseyConfig, generate_massey_ratings
    from model_pack.utils.path_utils import get_postseason_training_file
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure dependencies are installed and project structure is intact")
    sys.exit(1)


def get_bowl_games_from_data():
    """Get 2025 bowl games from existing postseason data."""
    try:
        postseason_path = get_postseason_training_file(season=2025, base_path=PROJECT_ROOT)
        if not postseason_path.exists():
            print(f"❌ Postseason data not found at {postseason_path}")
            return []
        
        df = pd.read_csv(postseason_path, low_memory=False).dropna(how="all")
        
        # Filter for postseason games
        if "season_type" in df.columns:
            df = df[df["season_type"] == "postseason"].copy()
        
        # Convert to list of dictionaries
        games_list = []
        for _, row in df.iterrows():
            game = {
                "id": row.get("id"),
                "home_team": row.get("home_team"),
                "away_team": row.get("away_team"),
                "start_date": row.get("start_date") or row.get("game_date", ''),
            }
            games_list.append(game)
        
        print(f"✅ Found {len(games_list)} bowl games from existing data")
        return games_list
        
    except Exception as e:
        print(f"❌ Error loading bowl games from data: {e}")
        return []


def load_or_generate_massey_ratings():
    """Load existing Massey ratings or generate new ones."""
    ratings_path = PROJECT_ROOT / "src" / "ratings" / "massey_ratings_2025.csv"
    
    if ratings_path.exists():
        print(f"✅ Loading existing Massey ratings from {ratings_path}")
        ratings_df = pd.read_csv(ratings_path)
        print(f"✅ Loaded ratings for {len(ratings_df)} teams")
        return ratings_df
    else:
        print("⚠️ No existing Massey ratings found, generating new ones...")
        try:
            config = MasseyConfig(season=2025)
            ratings_df, _ = generate_massey_ratings(config, persist=True)
            print(f"✅ Generated and saved ratings for {len(ratings_df)} teams")
            return ratings_df
        except Exception as e:
            print(f"❌ Error generating Massey ratings: {e}")
            return pd.DataFrame()


def predict_game_outcome(home_team, away_team, ratings_df, home_field_advantage=2.3):
    """
    Simple prediction using Massey rating difference.
    """
    # Get team ratings
    home_rating = ratings_df[ratings_df['team'] == home_team]['rating']
    away_rating = ratings_df[ratings_df['team'] == away_team]['rating']
    
    if home_rating.empty or away_rating.empty:
        # Default prediction if we don't have ratings
        print(f"⚠️ No ratings found for {home_team} vs {away_team}, using default")
        return 0.5, 0.0
    
    home_rating = float(home_rating.iloc[0])
    away_rating = float(away_rating.iloc[0])
    
    # Simple prediction: rating difference + home field advantage
    predicted_margin = (home_rating - away_rating) + home_field_advantage
    
    # Convert margin to win probability using simple logistic function
    scale_factor = 15.0
    home_win_prob = 1 / (1 + pow(10, -predicted_margin / scale_factor))
    
    return home_win_prob, predicted_margin


def backup_file_if_exists(file_path: Path):
    """Create backup of file if it exists."""
    if file_path.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = file_path.parent / f"{file_path.stem}_backup_{timestamp}{file_path.suffix}"
        shutil.copy2(file_path, backup_path)
        print(f"⚠️ Backed up existing file to: {backup_path}")


def main():
    """Main function to generate bowl predictions."""
    print("🏈 Starting bowls 2025 prediction script (fallback version)")
    
    # Get bowl games from existing data
    bowl_games = get_bowl_games_from_data()
    if not bowl_games:
        return 1
    
    # Load or generate Massey ratings
    ratings_df = load_or_generate_massey_ratings()
    if ratings_df.empty:
        print("❌ Could not load or generate team ratings")
        return 1
    
    # Get home field advantage from ratings if available
    if not ratings_df.empty and 'hfa' in ratings_df.columns:
        home_field_advantage = float(ratings_df['hfa'].iloc[0])
        print(f"✅ Using computed home field advantage: {home_field_advantage:.2f}")
    else:
        home_field_advantage = 2.3  # Default value
        print(f"⚠️ Using default home field advantage: {home_field_advantage}")
    
    # Generate predictions for each bowl game
    predictions = []
    for game in bowl_games:
        home_team = game.get('home_team')
        away_team = game.get('away_team')
        
        if not home_team or not away_team:
            print(f"⚠️ Skipping game with missing teams: {game}")
            continue
        
        # Generate prediction
        win_prob, margin = predict_game_outcome(
            home_team, away_team, ratings_df, home_field_advantage
        )
        
        prediction = {
            "id": game.get('id'),
            "date": game.get('start_date') or game.get('game_date', ''),
            "home_team": home_team,
            "away_team": away_team,
            "home_win_prob": round(win_prob, 6),
            "predicted_margin": round(margin, 6)
        }
        predictions.append(prediction)
    
    # Create output JSON - fallback specific filename
    output_data = {
        "generated_at": datetime.now().isoformat() + "Z",
        "model": "simple-rating-diff-v1-fallback",
        "model_type": "simple_ratings",
        "season": 2025,
        "data_source": "existing_postseason_data",
        "home_field_advantage": home_field_advantage,
        "games": predictions
    }

    # Write output - use fallback-specific filename to avoid conflicts
    output_path = PROJECT_ROOT / "predictions" / "bowls_2025_predictions_simple.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Safety: Check if file exists and warn
    if output_path.exists():
        print(f"⚠️ File {output_path} already exists")
        response = input("Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("❌ Aborted - file would be overwritten")
            return 1
        backup_file_if_exists(output_path)

    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"✅ Generated {len(predictions)} simple bowl predictions (fallback)")
    print(f"✅ Output saved to: {output_path}")
    print(f"   Model: Simple rating difference with HFA={home_field_advantage:.2f}")
    
    # Show sample predictions
    if predictions:
        print("\n📊 Sample predictions:")
        for i, pred in enumerate(predictions[:3]):
            margin_dir = "wins" if pred["predicted_margin"] > 0 else "loses" 
            print(f"  {i+1}. {pred['away_team']} @ {pred['home_team']}: "
                  f"{pred['home_win_prob']:.1%} home win, "
                  f"{pred['home_team']} {margin_dir} by {abs(pred['predicted_margin']):.1f}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
