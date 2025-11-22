import os
import sys
import time
from dotenv import load_dotenv

# Load env vars
load_dotenv()

# Disable GraphQL for this test
os.environ["CFBD_GRAPHQL_DISABLED"] = "true"

# Ensure src is in path
sys.path.append(os.getcwd())

from src.cfbd_client.data_provider import CFBDDataProvider

def verify_fix():
    print("Verifying GraphQL disable fix...")
    
    provider = CFBDDataProvider()
    
    print("Attempting to fetch adjusted metrics (should return empty dict)...")
    try:
        metrics = provider.get_adjusted_team_metrics(team="Ohio State", season=2024)
        print(f"Result: {metrics}")
        
        if metrics and metrics.get("rating") is not None:
            print(f"✅ Success! Returned populated metrics via REST fallback: {metrics}")
        else:
            print(f"⚠️ Unexpected result (empty or missing data): {metrics}")
            
    except Exception as e:
        print(f"❌ Failed with error: {e}")

if __name__ == "__main__":
    verify_fix()
