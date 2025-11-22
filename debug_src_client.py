import os
import sys
from dotenv import load_dotenv

# Load env vars
load_dotenv()

# Ensure src is in path
sys.path.append(os.getcwd())

from src.cfbd_client.client import CFBDClient

def test_client():
    print("Testing src.cfbd_client.client.CFBDClient...")
    
    key = os.getenv("CFBD_API_KEY")
    if not key:
        print("❌ Error: CFBD_API_KEY not found in environment")
        return

    print(f"Key found: {key[:5]}...{key[-5:]}")
    
    client = CFBDClient(api_key=key)
    
    try:
        # Try a simple request
        games = client.get_games(year=2024, week=1, season_type="regular", team="Ohio State")
        print(f"✅ Success! Found {len(games)} games.")
    except Exception as e:
        print(f"❌ Failed with error: {e}")

if __name__ == "__main__":
    test_client()
