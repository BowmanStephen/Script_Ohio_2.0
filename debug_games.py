import cfbd
from cfbd import Configuration, ApiClient, GamesApi
import os
import pandas as pd

# Key provided by user
API_KEY = "3nSBeJV4ODZlJLxQZ/H0vWG3DRAfTSPU2PporK/5K+BJininva/bPx5G4iNjeOsb"

# Configure CFBD API
configuration = Configuration()
configuration.access_token = API_KEY
configuration.host = "https://api.collegefootballdata.com"

api_client = ApiClient(configuration)
games_api = GamesApi(api_client)

print("Fetching Week 13 games...")
try:
    games = games_api.get_games(year=2025, week=13)
    if len(games) > 0:
        g = games[0]
        print(f"Sample game object: {g}")
        
        # Check if to_dict exists
        if hasattr(g, 'to_dict'):
            d = g.to_dict()
            print(f"\nto_dict() output keys: {list(d.keys())}")
            print(f"home_team in dict: {d.get('home_team')}")
            print(f"away_team in dict: {d.get('away_team')}")
            
            # Check if keys match what we expect
            print(f"home_conference in dict: {d.get('home_conference')}")
        else:
            print("Game object has no to_dict method")

except Exception as e:
    print(f"Error: {e}")
