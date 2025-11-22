#!/usr/bin/env python3
"""
Fix Missing Game IDs Script

Fixes games with NaN IDs by generating IDs from game data or CFBD API.
Part of Script Ohio 2.0 data remediation pipeline.
"""

import pandas as pd
from pathlib import Path
import sys
import os

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def generate_game_id_from_key(game_key: str, season: int) -> float:
    """
    Generate a game ID from game_key pattern.
    Format: {season}_{week}_{home_team}_{away_team}
    Returns a float ID based on hash or pattern.
    """
    if pd.isna(game_key):
        return None
    
    # Try to extract or generate ID from game_key
    # Simple hash-based approach for consistent ID generation
    import hashlib
    
    # Create a hash from the game_key string
    hash_obj = hashlib.md5(game_key.encode())
    hash_int = int(hash_obj.hexdigest()[:8], 16)  # First 8 hex chars as int
    
    # Create ID in format similar to CFBD (400000000 + hash_int)
    game_id = 400000000.0 + (hash_int % 100000000)
    
    return game_id


def fetch_game_id_from_cfbd(home_team: str, away_team: str, season: int, week: int) -> float:
    """
    Fetch actual game ID from CFBD API if available.
    """
    try:
        from starter_pack.utils.cfbd_helpers import cfbd_session
        import os
        
        api_key = os.environ.get('CFBD_API_KEY')
        if not api_key:
            return None
        
        with cfbd_session() as session:
            games_api = session.games_api
            games = games_api.get_games(
                year=season,
                week=week,
                team=home_team
            )
            
            if games:
                for game in games:
                    if (game.home_team == home_team and game.away_team == away_team) or \
                       (game.home_team == away_team and game.away_team == home_team):
                        return float(game.id)
    except Exception as e:
        print(f"⚠️ Could not fetch from CFBD API: {e}")
    
    return None


def fix_missing_game_ids():
    """Fix games with NaN IDs."""
    training_file = project_root / "model_pack" / "updated_training_data.csv"
    backup_file = project_root / "model_pack" / "updated_training_data.csv.backup"
    
    if not training_file.exists():
        print("❌ Training data file not found")
        return False
    
    print("📊 Loading training data...")
    df = pd.read_csv(training_file, low_memory=False)
    
    # Find games with NaN IDs
    nan_id_games = df[df['id'].isna()].copy()
    
    if len(nan_id_games) == 0:
        print("✅ No games with NaN IDs found")
        return True
    
    print(f"\n🔍 Found {len(nan_id_games)} games with NaN IDs")
    print(f"   Weeks affected: {sorted(nan_id_games['week'].unique())}")
    print(f"   Seasons affected: {sorted(nan_id_games['season'].unique())}")
    
    # Create backup
    print(f"\n💾 Creating backup: {backup_file}")
    df.to_csv(backup_file, index=False)
    
    fixed_count = 0
    cfbd_fetched = 0
    generated_count = 0
    
    print("\n🔧 Fixing missing IDs...")
    for idx, row in nan_id_games.iterrows():
        # Try CFBD API first if available
        game_id = fetch_game_id_from_cfbd(
            row['home_team'],
            row['away_team'],
            int(row['season']),
            int(row['week'])
        )
        
        if game_id:
            df.at[idx, 'id'] = game_id
            fixed_count += 1
            cfbd_fetched += 1
        elif pd.notna(row.get('game_key')):
            # Generate ID from game_key
            game_id = generate_game_id_from_key(row['game_key'], int(row['season']))
            if game_id:
                # Check if this ID already exists
                if game_id not in df['id'].values:
                    df.at[idx, 'id'] = game_id
                    fixed_count += 1
                    generated_count += 1
                else:
                    # Add small offset to make unique
                    offset = 0
                    while (game_id + offset) in df['id'].values:
                        offset += 1
                    df.at[idx, 'id'] = game_id + offset
                    fixed_count += 1
                    generated_count += 1
        else:
            # Last resort: generate from team names and date
            print(f"⚠️ Cannot generate ID for {row['home_team']} vs {row['away_team']} (week {row['week']})")
    
    # Verify no duplicates remain
    duplicates = df[df.duplicated(subset=['id'], keep=False)]
    if len(duplicates) > 0:
        print(f"\n⚠️ Warning: {len(duplicates)} duplicate IDs remain after fixing")
        print("   These may need manual review")
    
    # Save fixed data
    print(f"\n💾 Saving fixed data to: {training_file}")
    df.to_csv(training_file, index=False)
    
    print("\n✅ Summary:")
    print(f"   Total NaN IDs found: {len(nan_id_games)}")
    print(f"   Fixed: {fixed_count}")
    print(f"   - From CFBD API: {cfbd_fetched}")
    print(f"   - Generated: {generated_count}")
    
    # Verify fix
    remaining_nan = df['id'].isna().sum()
    if remaining_nan == 0:
        print("\n✅ All missing IDs fixed!")
        return True
    else:
        print(f"\n⚠️ {remaining_nan} NaN IDs remain (may need manual review)")
        return False


if __name__ == "__main__":
    success = fix_missing_game_ids()
    sys.exit(0 if success else 1)



