#!/usr/bin/env python3
"""
Script to test Tier 3 CFBD access and verify premium endpoints.
This script will help us understand what premium features are available
and test the actual rate limits for Tier 3 membership.
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from cfbd_client.unified_client import UnifiedCFBDClient
    from config.cfbd_config import CFBDConfig
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running this from the project root directory")
    sys.exit(1)


def test_basic_endpoints(client):
    """Test basic CFBD endpoints that should work for any tier"""
    print("\n🔍 Testing Basic Endpoints")
    print("=" * 50)

    try:
        # Test games endpoint
        print("Testing games endpoint...")
        games = client.get_games(year=2025, week=1)
        print(f"✅ Games: Found {len(games)} games for 2025 week 1")

        # Test teams endpoint
        print("Testing teams endpoint...")
        teams = client.get_teams()
        print(f"✅ Teams: Found {len(teams)} teams")

        # Test ratings endpoint
        print("Testing ratings endpoint...")
        ratings = client.get_ratings(year=2025)
        print(f"✅ Ratings: Found {len(ratings)} rating entries")

    except Exception as e:
        print(f"❌ Basic endpoint test failed: {e}")
        return False

    return True


def test_premium_endpoints(client):
    """Test Tier 4 premium endpoints"""
    print("\n⭐ Testing Premium Endpoints")
    print("=" * 50)

    premium_results = {}

    # Test PPA endpoints
    try:
        print("Testing PPA teams endpoint...")
        # This is a hypothetical endpoint - we need to check if it exists
        # For now, let's try to access through the metrics API
        if hasattr(client.metrics_api, "get_ppa"):
            ppa_teams = client.metrics_api.get_ppa(year=2025)
            premium_results["ppa_teams"] = len(ppa_teams) if ppa_teams else 0
            print(f"✅ PPA Teams: Found {premium_results['ppa_teams']} entries")
        else:
            print("⚠️ PPA endpoint not available in current CFBD client")
            premium_results["ppa_teams"] = "not_available"

    except Exception as e:
        print(f"❌ PPA endpoint test failed: {e}")
        premium_results["ppa_teams"] = "error"

    # Test WEPA endpoints
    try:
        print("Testing WEPA endpoint...")
        if hasattr(client.metrics_api, "get_wepa"):
            wepa_data = client.metrics_api.get_wepa(year=2025)
            premium_results["wepa"] = len(wepa_data) if wepa_data else 0
            print(f"✅ WEPA: Found {premium_results['wepa']} entries")
        else:
            print("⚠️ WEPA endpoint not available in current CFBD client")
            premium_results["wepa"] = "not_available"

    except Exception as e:
        print(f"❌ WEPA endpoint test failed: {e}")
        premium_results["wepa"] = "error"

    # Test live data endpoints
    try:
        print("Testing live scoreboard endpoint...")
        if hasattr(client.games_api, "get_scoreboard"):
            live_games = client.games_api.get_scoreboard(year=2025, week=15)
            premium_results["live_scoreboard"] = len(live_games) if live_games else 0
            print(
                f"✅ Live Scoreboard: Found {premium_results['live_scoreboard']} live games"
            )
        else:
            print("⚠️ Live scoreboard endpoint not available in current CFBD client")
            premium_results["live_scoreboard"] = "not_available"

    except Exception as e:
        print(f"❌ Live scoreboard test failed: {e}")
        premium_results["live_scoreboard"] = "error"

    # Test weather data
    try:
        print("Testing weather data endpoint...")
        # Weather might be available through games endpoint with weather parameter
        games_with_weather = client.get_games(year=2025, week=15)  # Modify as needed
        premium_results["weather"] = (
            "basic_available"  # Need to check if weather data is included
        )
        print(f"✅ Weather: Basic weather data may be available")

    except Exception as e:
        print(f"❌ Weather data test failed: {e}")
        premium_results["weather"] = "error"

    # Test advanced metrics
    try:
        print("Testing advanced win probability endpoint...")
        win_probs = client.get_win_probabilities(year=2025, week=15)
        premium_results["win_probability"] = len(win_probs) if win_probs else 0
        print(f"✅ Win Probability: Found {premium_results['win_probability']} entries")

    except Exception as e:
        print(f"❌ Win probability test failed: {e}")
        premium_results["win_probability"] = "error"

    return premium_results


def test_rate_limiting(client):
    """Test actual rate limits for Tier 4"""
    print("\n⚡ Testing Rate Limits")
    print("=" * 50)

    # Test rapid requests to see actual rate limit
    request_times = []
    max_requests = 20

    print(f"Making {max_requests} rapid requests to test rate limiting...")

    for i in range(max_requests):
        start_time = time.time()
        try:
            # Use a lightweight endpoint
            client.get_conferences()
            end_time = time.time()
            request_times.append(end_time - start_time)
            print(f"Request {i+1}: {request_times[-1]:.3f}s")

        except Exception as e:
            print(f"❌ Request {i+1} failed: {e}")
            break

    if request_times:
        avg_time = sum(request_times) / len(request_times)
        max_time = max(request_times)
        min_time = min(request_times)

        print(f"\n📊 Rate Limit Test Results:")
        print(f"Average request time: {avg_time:.3f}s")
        print(f"Fastest request: {min_time:.3f}s")
        print(f"Slowest request: {max_time:.3f}s")
        print(f"Estimated rate limit: {1/avg_time:.1f} requests/second")

        return {
            "avg_time": avg_time,
            "max_time": max_time,
            "min_time": min_time,
            "estimated_rps": 1 / avg_time,
            "successful_requests": len(request_times),
        }

    return None


def test_graphql_access(client):
    """Test GraphQL API access"""
    print("\n🔗 Testing GraphQL Access")
    print("=" * 50)

    try:
        if client.graphql_client:
            print("✅ GraphQL client initialized")

            # Test basic GraphQL query
            if hasattr(client.graphql_client, "get_scoreboard"):
                scoreboard = client.get_scoreboard_graphql(year=2025, week=15)
                if scoreboard:
                    print(f"✅ GraphQL Scoreboard: Data retrieved")
                    return True
                else:
                    print("⚠️ GraphQL Scoreboard: No data returned")
                    return False
            else:
                print("⚠️ GraphQL client exists but no get_scoreboard method")
                return False
        else:
            print("❌ GraphQL client not initialized")
            return False

    except Exception as e:
        print(f"❌ GraphQL test failed: {e}")
        return False


def main():
    """Main test function"""
    print("🎯 Script Ohio 2.0 - Tier 4 Access Test")
    print("=" * 60)
    print(f"Testing at: {datetime.now().isoformat()}")

    # Check API key
    if not os.getenv("CFBD_API_KEY"):
        print("❌ CFBD_API_KEY environment variable not set")
        return

    # Initialize client
    try:
        config = CFBDConfig.from_env()
        print(f"📋 Config: {config.host}")
        print(f"📋 Rate Limit: {config.max_requests_per_second} req/sec")

        client = UnifiedCFBDClient(config)

    except Exception as e:
        print(f"❌ Failed to initialize CFBD client: {e}")
        return

    # Run tests
    results = {
        "timestamp": datetime.now().isoformat(),
        "config": {
            "host": config.host,
            "max_requests_per_second": config.max_requests_per_second,
            "rate_limit_delay": config.rate_limit_delay,
        },
    }

    # Test basic endpoints
    results["basic_endpoints"] = test_basic_endpoints(client)

    # Test premium endpoints
    results["premium_endpoints"] = test_premium_endpoints(client)

    # Test rate limiting
    rate_limit_results = test_rate_limiting(client)
    if rate_limit_results:
        results["rate_limit_test"] = rate_limit_results

    # Test GraphQL
    results["graphql_access"] = test_graphql_access(client)

    # Save results
    results_file = Path("tier4_test_results.json")
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n💾 Results saved to: {results_file}")

    # Summary
    print("\n📊 Summary")
    print("=" * 30)
    basic_status = "✅ Working" if results["basic_endpoints"] else "❌ Failed"
    print(f"Basic Endpoints: {basic_status}")

    graphql_status = "✅ Working" if results["graphql_access"] else "❌ Failed"
    print(f"GraphQL Access: {graphql_status}")

    if "rate_limit_test" in results:
        estimated_rps = results["rate_limit_test"]["estimated_rps"]
        print(f"Estimated Rate Limit: {estimated_rps:.1f} req/sec")

        if estimated_rps > 10:
            print("🎉 Appears to have premium rate limits!")
        else:
            print("⚠️ Rate limits appear to be at basic tier levels")

    print("\n🏁 Test complete!")


if __name__ == "__main__":
    main()
