import os
import cfbd
from cfbd.rest import ApiException

# Key from user
API_KEY = "3nSBeJV4ODZlJLxQZ/H0vWG3DRAfTSPU2PporK/5K+BJininva/bPx5G4iNjeOsb"

def test_auth(key_prefix="Bearer"):
    print(f"Testing with key_prefix: {key_prefix}")
    configuration = cfbd.Configuration()
    configuration.api_key['Authorization'] = API_KEY
    configuration.api_key_prefix['Authorization'] = key_prefix
    configuration.host = "https://api.collegefootballdata.com"

    api_instance = cfbd.GamesApi(cfbd.ApiClient(configuration))

    try:
        # Try to fetch one game
        games = api_instance.get_games(year=2024, week=1, team="Ohio State")
        print(f"✅ Success! Found {len(games)} games.")
        return True
    except ApiException as e:
        print(f"❌ Failed: {e.status} {e.reason}")
        print(f"Response body: {e.body}")
        return False

print("--- Test 1: Standard Configuration ---")
test_auth("Bearer")

print("\n--- Test 2: No Prefix (in case key has it) ---")
# Temporarily modifying key to include Bearer if that was the issue, but here we test empty prefix
configuration = cfbd.Configuration()
configuration.api_key['Authorization'] = f"Bearer {API_KEY}"
# configuration.api_key_prefix['Authorization'] = 'Bearer' # Don't set prefix if key has it
configuration.host = "https://api.collegefootballdata.com"
api_instance = cfbd.GamesApi(cfbd.ApiClient(configuration))
try:
    games = api_instance.get_games(year=2024, week=1, team="Ohio State")
    print(f"✅ Success (Manual Bearer)! Found {len(games)} games.")
except ApiException as e:
    print(f"❌ Failed (Manual Bearer): {e.status} {e.reason}")

