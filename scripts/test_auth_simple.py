#!/usr/bin/env python3
"""Simple test to verify CFBD authentication works"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def test_direct_cfbd():
    """Test direct CFBD authentication using working pattern"""
    print("🔑 Testing Direct CFBD Authentication")

    try:
        import cfbd

        # Use the working pattern from create_2025_starter_pack_data.py
        if not os.getenv("CFBD_API_KEY"):
            print("❌ CFBD_API_KEY not set")
            return False

        configuration = cfbd.Configuration()
        configuration.api_key["Authorization"] = os.getenv("CFBD_API_KEY")
        configuration.api_key_prefix["Authorization"] = "Bearer"
        configuration.host = "https://api.collegefootballdata.com"

        with cfbd.ApiClient(configuration) as api_client:
            games_api = cfbd.GamesApi(api_client)

            # Test with a simple request
            games = games_api.get_games(year=2025, week=1, seasonType="regular")

            print(f"✅ Direct CFBD Authentication: Found {len(games) if games else 0} games")
            return True

    except Exception as e:
        print(f"❌ Direct CFBD Authentication failed: {e}")
        return False

def test_unified_client():
    """Test unified client authentication"""
    print("\n🔧 Testing Unified Client Authentication")

    try:
        from cfbd_client.unified_client import UnifiedCFBDClient
        from config.cfbd_config import CFBDConfig

        config = CFBDConfig.from_env()
        client = UnifiedCFBDClient(config)

        # Test simple request
        teams = client.get_teams()

        print(f"✅ Unified Client: Found {len(teams) if teams else 0} teams")
        return True

    except Exception as e:
        print(f"❌ Unified Client failed: {e}")
        return False

def main():
    print("🧪 CFBD Authentication Test")
    print("=" * 40)

    direct_result = test_direct_cfbd()
    unified_result = test_unified_client()

    print(f"\n📊 Results:")
    print(f"Direct CFBD: {'✅ Working' if direct_result else '❌ Failed'}")
    print(f"Unified Client: {'✅ Working' if unified_result else '❌ Failed'}")

    if direct_result and not unified_result:
        print("\n💡 Recommendation: Fix unified client authentication")
        print("Issue: Unified client may be stripping Bearer prefix incorrectly")
    elif not direct_result:
        print("\n💡 Recommendation: Check API key validity")
    else:
        print("\n🎉 Both authentication methods working!")

if __name__ == "__main__":
    main()