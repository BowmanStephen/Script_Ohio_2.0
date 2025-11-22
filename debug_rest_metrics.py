import os
import sys
from dotenv import load_dotenv

# Load env vars
load_dotenv()

# Ensure src is in path
sys.path.append(os.getcwd())

from src.cfbd_client.client import CFBDClient

def test_sp_ratings():
    print("Testing get_sp_ratings...")
    
    key = os.getenv("CFBD_API_KEY")
    if not key:
        print("❌ Error: CFBD_API_KEY not found")
        return

    client = CFBDClient(api_key=key)
    
    try:
        data = client.get_sp_ratings(year=2024, team="Ohio State")
        print(f"✅ Success! Data: {data}")
    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    test_sp_ratings()
