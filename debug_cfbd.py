import cfbd
from cfbd import Configuration, ApiClient, GamesApi
from cfbd.rest import ApiException
import os

# Key provided by user
API_KEY = "3nSBeJV4ODZlJLxQZ/H0vWG3DRAfTSPU2PporK/5K+BJininva/bPx5G4iNjeOsb"

print(f"Testing with key: {API_KEY[:5]}...{API_KEY[-5:]}")

# Configuration 3: Access Token
print("\n--- Test 3: Access Token Configuration ---")
configuration = Configuration()
# Setting access_token directly instead of api_key dict
configuration.access_token = API_KEY
configuration.host = "https://api.collegefootballdata.com"

try:
    api_client = ApiClient(configuration)
    games_api = GamesApi(api_client)
    games = games_api.get_games(year=2024, week=1)
    print(f"✅ Success! Found {len(games)} games.")
except ApiException as e:
    print(f"❌ Failed: {e.status} - {e.reason}")
except Exception as e:
    print(f"❌ Error: {e}")
