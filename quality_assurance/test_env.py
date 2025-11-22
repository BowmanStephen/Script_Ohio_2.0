#!/usr/bin/env python3
"""
Test script to verify .env file is loaded correctly
"""

import os
from pathlib import Path

from starter_pack.utils.cfbd_loader import (
    CFBDLoaderError,
    live_cfbd_session,
    DEFAULT_HOST,
)

# Try to load .env file
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Loaded .env from: {env_path}")
    else:
        print(f"⚠️  .env file not found at: {env_path}")
        print("   Creating one now...")
except ImportError:
    print("⚠️  python-dotenv not installed")
    print("   Install with: pip install python-dotenv")
    print("   Or set environment variables manually in your shell")

# Check for API key
api_key = os.environ.get("CFBD_API_KEY") or os.environ.get("CFBD_API_TOKEN")
if api_key:
    print(f"✅ API key found: {api_key[:10]}...{api_key[-4:]}")
    print(f"   Length: {len(api_key)} characters")
    print("   Status: Ready to use!")
else:
    print("❌ API key not found!")
    print("   Make sure your .env file contains:")
    print("   CFBD_API_KEY=your_actual_key_here")
    print("   or")
    print("   CFBD_API_TOKEN=your_actual_key_here")

host = os.environ.get("CFBD_API_HOST", DEFAULT_HOST)
if api_key:
    try:
        sample_season = int(os.environ.get("TEST_ENV_CFBD_SEASON", 2025))
        with live_cfbd_session(api_key=api_key, host=host) as session:
            # Lightweight probe to confirm auth + host combo works
            session.games_api.get_games(year=sample_season, week=1, season_type="regular")
        print(f"✅ Live CFBD session successful via host {host}")
    except CFBDLoaderError as err:
        print(f"❌ Unable to open CFBD session: {err}")
    except Exception as err:
        print(f"⚠️ Live CFBD probe failed: {err}")

