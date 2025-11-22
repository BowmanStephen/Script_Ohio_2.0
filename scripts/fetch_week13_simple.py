#!/usr/bin/env python3
"""
Simple script to fetch Week 13 games and generate predictions
"""

import os
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

import pandas as pd
import cfbd

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Rate limiting
RATE_LIMIT_DELAY = 0.17

def rate_limit():
    """Simple rate limiter"""
    time.sleep(RATE_LIMIT_DELAY)

def fetch_week13_games(api_key: str):
    """Fetch Week 13 2025 games from CFBD API"""
    print("Fetching Week 13 2025 games from CFBD API...")
    
    # Configure CFBD client
    configuration = cfbd.Configuration()
    # Remove "Bearer " if already present in the key
    clean_key = api_key.replace("Bearer ", "").strip()
    configuration.api_key['Authorization'] = clean_key
    configuration.api_key_prefix['Authorization'] = 'Bearer'
    configuration.host = "https://api.collegefootballdata.com"
    
    api_client = cfbd.ApiClient(configuration)
    games_api = cfbd.GamesApi(api_client)
    
    # Fetch games
    rate_limit()
    games = games_api.get_games(year=2025, week=13, season_type="regular")
    
    if not games:
        print("⚠️  No games returned for Week 13. CFBD may not be updated yet.")
        return None
    
    # Convert to DataFrame
    rows = []
    for game in games:
        data = game.to_dict()
        rows.append(data)
    
    df = pd.DataFrame(rows)
    df["fetched_at_utc"] = datetime.now(timezone.utc).isoformat()
    
    print(f"✅ Fetched {len(df)} games for Week 13")
    
    # Load existing games and merge
    games_path = PROJECT_ROOT / "starter_pack" / "data" / "games.csv"
    if games_path.exists():
        existing = pd.read_csv(games_path, low_memory=False)
        # Combine and deduplicate
        combined = pd.concat([existing, df], ignore_index=True, sort=False)
        combined = combined.drop_duplicates(subset=["id"], keep="last")
        combined = combined.sort_values(["season", "week", "start_date"], na_position="last")
        combined = combined.reset_index(drop=True)
        print(f"   Total games in file: {len(combined)}")
    else:
        combined = df
        games_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save
    combined.to_csv(games_path, index=False)
    print(f"✅ Saved to: {games_path}")
    
    # Also save to 2025_games.csv if it exists
    games_2025_path = PROJECT_ROOT / "starter_pack" / "data" / "2025_games.csv"
    if games_2025_path.exists():
        existing_2025 = pd.read_csv(games_2025_path, low_memory=False)
        combined_2025 = pd.concat([existing_2025, df], ignore_index=True, sort=False)
        combined_2025 = combined_2025.drop_duplicates(subset=["id"], keep="last")
        combined_2025 = combined_2025.sort_values(["season", "week", "start_date"], na_position="last")
        combined_2025 = combined_2025.reset_index(drop=True)
        combined_2025.to_csv(games_2025_path, index=False)
        print(f"✅ Updated: {games_2025_path}")
    
    return df

def main():
    api_key = os.environ.get("CFBD_API_KEY")
    if not api_key:
        print("❌ ERROR: CFBD_API_KEY environment variable not set")
        return 1
    
    print("=" * 80)
    print("FETCHING WEEK 13 GAMES")
    print("=" * 80)
    print()
    
    try:
        games_df = fetch_week13_games(api_key)
        
        if games_df is not None and len(games_df) > 0:
            print(f"\n✅ Successfully fetched {len(games_df)} Week 13 games")
            print("\nSample games:")
            for idx, game in games_df.head(5).iterrows():
                home = game.get('home_team', 'TBD')
                away = game.get('away_team', 'TBD')
                print(f"  {away} @ {home}")
            
            print("\n" + "=" * 80)
            print("Next: Generate predictions with:")
            print("  python3 scripts/run_weekly_analysis.py --week 13 --season 2025 --step predictions")
            print("=" * 80)
        else:
            print("\n⚠️  No games fetched. Week 13 may not be available yet in CFBD.")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())

