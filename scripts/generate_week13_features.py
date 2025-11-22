import pandas as pd
import os
from pathlib import Path

# Define paths
PROJECT_ROOT = Path(__file__).parent.parent
RAW_GAMES_PATH = PROJECT_ROOT / 'model_pack' / '2025_raw_games.csv'
OUTPUT_DIR = PROJECT_ROOT / 'data' / 'week13' / 'enhanced'
OUTPUT_FEATURES_PATH = OUTPUT_DIR / 'week13_features_86.csv'
OUTPUT_GAMES_PATH = OUTPUT_DIR / 'week13_enhanced_games.csv'

def main():
    print("Generating Week 13 features from raw games...")
    
    # Load raw games
    if not RAW_GAMES_PATH.exists():
        print(f"Error: {RAW_GAMES_PATH} not found.")
        return
    
    df = pd.read_csv(RAW_GAMES_PATH)
    print(f"Loaded {len(df)} total games.")
    
    # Filter for Week 13
    week13_df = df[df['week'] == 13].copy()
    print(f"Found {len(week13_df)} Week 13 games.")
    
    if len(week13_df) == 0:
        print("No Week 13 games found. Check data acquisition.")
        return

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Rename 'id' to 'game_id' for compatibility if needed, or keep both
    week13_df['game_id'] = week13_df['id']
    
    # Save features file
    week13_df.to_csv(OUTPUT_FEATURES_PATH, index=False)
    print(f"Saved features to {OUTPUT_FEATURES_PATH}")
    
    # Save enhanced games file (same content for now, maybe subset columns if needed)
    week13_df.to_csv(OUTPUT_GAMES_PATH, index=False)
    print(f"Saved enhanced games to {OUTPUT_GAMES_PATH}")

if __name__ == "__main__":
    main()
