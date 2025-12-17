import argparse
import os
import sys


def check_api_key():
    """Check CFBD API key validity"""
    api_key = os.environ.get("CFBD_API_KEY")
    if not api_key:
        print("❌ CFBD_API_KEY environment variable is NOT set.")
        return False

    print(f"✅ CFBD_API_KEY is set (length: {len(api_key)})")

    # Import CFBD only after argument parsing and environment check
    try:
        import cfbd
    except ImportError as e:
        print(f"❌ CFBD package not available: {e}")
        print("Install with: pip install cfbd")
        return False

    # Test connectivity
    configuration = cfbd.Configuration()
    configuration.api_key["Authorization"] = api_key
    configuration.api_key_prefix["Authorization"] = "Bearer"

    api_instance = cfbd.GamesApi(cfbd.ApiClient(configuration))

    try:
        # Try to fetch one game from 2024 to verify key works
        api_instance.get_games(year=2024, week=1, team="Ohio State")
        print("✅ API connection successful: Fetched test game data.")
        return True
    except Exception as e:
        print(f"❌ API connection failed: {str(e)}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Check CFBD API key validity")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    args = parser.parse_args()

    success = check_api_key()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
