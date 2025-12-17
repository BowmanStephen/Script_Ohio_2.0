import pandas as pd
import sys

try:
    # Load talent
    talent_df = pd.read_csv('model_pack/data/talent/talent_2025.csv')
    talent_map = talent_df.set_index('team')['talent'].to_dict()
    print(f"Talent value for 'Utah': {talent_map.get('Utah')}")

    # Load training data
    games_df = pd.read_csv('model_pack/updated_training_data.csv', low_memory=False)
    
    # Check 'Utah' formatting
    utah_games = games_df[games_df['home_team'].str.contains('Utah')]
    if not utah_games.empty:
        home_team_val = utah_games.iloc[-1]['home_team']
        print(f"Home Team Value: '{home_team_val}'")
        print(f"Length: {len(home_team_val)}")
        print(f"Codepoints: {[ord(c) for c in home_team_val]}")
        
        # Try mapping
        mapped_val = talent_map.get(home_team_val)
        print(f"Mapped Value in Script: {mapped_val}")
        
    else:
        print("No Utah games found")

except Exception as e:
    print(f"Error: {e}")
